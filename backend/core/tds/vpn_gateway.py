"""backend.core.tds.vpn_gateway
--------------------------------
AI-enhanced VPN gateway managing encrypted sessions.

This module provides a small, well-documented VPNGateway class that manages
per-session symmetric keys, (de-)encryption helpers and a lightweight
anomaly detector that scores session traffic (packet rates) for simple
AI-like behavioral detection. The crypto backend uses AES-GCM when the
`cryptography` package is available; otherwise a non-production insecure
XOR fallback is used (with clear warning).

The API is intentionally small and testable:
  - create_session(session_id, key=None)
  - close_session(session_id)
  - encrypt_for_session(session_id, plaintext, aad=b"") -> bytes
  - decrypt_for_session(session_id, blob, aad=b"") -> plaintext
  - process_incoming(session_id, encrypted_blob) -> dict (plaintext, meta, anomaly_score)

This keeps the module safe to import in CI/dev environments even when
cryptography isn't installed.
"""

from __future__ import annotations

import os
import time
import secrets
import struct
import threading
import logging
from typing import Dict, Optional, Tuple, Any
import subprocess
import shutil
from typing import List

# zero-trust integration
try:
    from backend.core.tds import zero_trust
except Exception:
    zero_trust = None  # type: ignore


class WireGuardManager:
    """Minimal WireGuard control layer.

    Prefers a Python control library when available; otherwise falls back to
    calling `wg`/`ip` subprocesses. This class is intentionally small and
    defensive — it will raise informative errors if the runtime does not
    provide the required system binaries or libraries.
    """

    def __init__(self, interface: str = "jarvis0"):
        self.interface = interface
        self._has_pyroute2 = False
        try:
            # pyroute2 provides netlink control for WireGuard (if installed)
            from pyroute2 import IPRoute

            self._ipr = IPRoute()
            self._has_pyroute2 = True
        except Exception:
            self._ipr = None
            self._has_pyroute2 = False

        # fallback to CLI tools
        self._wg_cmd = shutil.which("wg")
        self._ip_cmd = shutil.which("ip")
        if not self._has_pyroute2 and (self._wg_cmd is None or self._ip_cmd is None):
            raise RuntimeError("no WireGuard control available: install pyroute2 or ensure 'wg' and 'ip' binaries are present")

        # ensure interface exists when possible
        try:
            self.ensure_interface()
        except Exception:
            # don't fail construction — let callers decide to proceed
            logger.exception("failed to ensure WireGuard interface %s", self.interface)

    def ensure_interface(self) -> None:
        if self._has_pyroute2:
            # create link if missing
            links = [l.get_attr("IFLA_IFNAME") for l in self._ipr.get_links()]
            if self.interface not in links:
                # create a dummy wireguard link — pyroute2 supports generic link creation
                self._ipr.link("add", ifname=self.interface, kind="wireguard")
                self._ipr.link("set", index=self._ipr.link_lookup(ifname=self.interface)[0], state="up")
        else:
            # use ip link add
            try:
                subprocess.check_call([self._ip_cmd, "link", "add", "dev", self.interface, "type", "wireguard"])
                subprocess.check_call([self._ip_cmd, "link", "set", self.interface, "up"])
            except Exception:
                # ignore if already exists or failed
                pass

    def add_peer(self, peer_name: str, public_key: str, allowed_ips: List[str]) -> None:
        """Add a peer to the WireGuard interface for a session.

        peer_name is an identifier used for bookkeeping (mapped to AllowedIPs comment).
        """
        # Build allowed-ips string
        allowed = ",".join(allowed_ips)
        if self._has_pyroute2:
            # use wg setconf is not directly exposed; fallback to subprocess
            pass

        # fallback to wg command
        if self._wg_cmd:
            try:
                # 'wg set <iface> peer <pubkey> allowed-ips <cidr>'
                subprocess.check_call([self._wg_cmd, "set", self.interface, "peer", public_key, "allowed-ips", allowed])
            except Exception:
                logger.exception("failed to add peer %s via wg", peer_name)

    def remove_peer(self, public_key: str) -> None:
        if self._wg_cmd:
            try:
                subprocess.check_call([self._wg_cmd, "set", self.interface, "peer", public_key, "remove"])  # type: ignore - wg supports remove
            except Exception:
                logger.exception("failed to remove peer %s via wg", public_key)


# Try to use AES-GCM via cryptography if available
_HAS_AESGCM = False
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    _HAS_AESGCM = True
except Exception:
    AESGCM = None  # type: ignore

logger = logging.getLogger("jarvis.vpn_gateway")
logging.basicConfig(level=logging.INFO)

# KeyStore location (repo-local run/keystore)
KEYSTORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../run/keystore"))
os.makedirs(KEYSTORE_DIR, exist_ok=True)


class KeyStore:
    """Simple keystore that persists session keys encrypted with a master key.

    The master key is read from the environment variable `JARVIS_MASTER_KEY`.
    If `cryptography` is available, AES-GCM is used to encrypt keys at rest.
    Otherwise keys are stored base64-encoded (NOT recommended for production).
    """

    def __init__(self, dirpath: str = KEYSTORE_DIR):
        self.dirpath = dirpath
        os.makedirs(self.dirpath, exist_ok=True)
        # derive a 32-byte AES key from env if available
        mk = os.environ.get("JARVIS_MASTER_KEY")
        if mk:
            import hashlib

            self._master = hashlib.sha256(mk.encode("utf-8")).digest()
        else:
            self._master = None
        # Try to integrate TPM attestation to obtain a device-bound master key or
        # to enable sealing via a TEE. These are optional and must not break when
        # the hardware integration modules are placeholders.
        self._use_tpm = False
        try:
            from hardware_integration import tpm_attestation
            from hardware_integration import tee_manager

            # Call attest(); if it returns a dict with a 'master_secret' or similar
            # field, derive the master key from it.
            att = None
            try:
                att = tpm_attestation.attest()
            except Exception:
                att = None

            if isinstance(att, dict):
                # Common placeholder returns keys/status; accept a 'master_secret'
                ms = att.get("master_secret") or att.get("device_key")
                if ms:
                    import hashlib

                    self._master = hashlib.sha256(str(ms).encode("utf-8")).digest()
                    self._use_tpm = True
            # Keep references (if available) for sealing/unsealing
            self._tpm = tpm_attestation
            self._tee = tee_manager
        except Exception:
            self._tpm = None
            self._tee = None

    def _path(self, session_id: str) -> str:
        safe = session_id.replace("/", "_")
        return os.path.join(self.dirpath, f"{safe}.key")

    def save_key(self, session_id: str, key: bytes) -> None:
        p = self._path(session_id)
        # If a TEE is available, prefer sealing the key inside the enclave
        try:
            if self._tee is not None and hasattr(self._tee, "seal_key"):
                sealed = self._tee.seal_key(key)
                with open(p, "wb") as f:
                    f.write(b"TEESEALED:" + sealed)
                return
        except Exception:
            logger.exception("tee sealing failed; falling back to master-key encryption")
        # If a master key is available prefer AES-GCM encryption at rest.
        if self._master:
            if _HAS_AESGCM:
                aes = AESGCM(self._master)
                nonce = secrets.token_bytes(12)
                ct = aes.encrypt(nonce, key, b"")
                with open(p, "wb") as f:
                    f.write(b"AESGCM:" + nonce + ct)
                return
            else:
                # In production we require cryptography for AES-GCM when using a master key
                # If you're in dev and explicitly opt-in, allow insecure storage via env.
                if os.environ.get("JARVIS_ALLOW_INSECURE_STORAGE") in ("1", "true", "True"):
                    import base64

                    with open(p, "wb") as f:
                        f.write(b"B64:" + base64.b64encode(key))
                    logger.warning("Storing key in base64 because JARVIS_ALLOW_INSECURE_STORAGE is set (dev only)")
                    return
                raise RuntimeError("cryptography is required for master-key encryption in production; set JARVIS_ALLOW_INSECURE_STORAGE=1 for dev only")

        # No TEE and no master: only allow insecure storage when explicitly opted-in
        if os.environ.get("JARVIS_ALLOW_INSECURE_STORAGE") in ("1", "true", "True"):
            import base64

            with open(p, "wb") as f:
                f.write(b"B64:" + base64.b64encode(key))
            logger.warning("Storing key in base64 because JARVIS_ALLOW_INSECURE_STORAGE is set (dev only)")
            return

        raise RuntimeError("No secure keystore configured: configure TEE or set JARVIS_MASTER_KEY (or set JARVIS_ALLOW_INSECURE_STORAGE=1 for dev)")

    def load_key(self, session_id: str) -> Optional[bytes]:
        p = self._path(session_id)
        if not os.path.exists(p):
            return None
        with open(p, "rb") as f:
            data = f.read()
        # If data is a TEE-sealed blob, attempt to unseal via TEE
        try:
            if data.startswith(b"TEESEALED:") and self._tee is not None and hasattr(self._tee, "unseal_key"):
                sealed = data.split(b"TEESEALED:", 1)[1]
                return self._tee.unseal_key(sealed)
        except Exception:
            logger.exception("failed to unseal TEE blob; falling back to other methods")
        if data.startswith(b"AESGCM:") and self._master and _HAS_AESGCM:
            aes = AESGCM(self._master)
            nonce = data.split(b"AESGCM:", 1)[1][:12]
            ct = data.split(b"AESGCM:", 1)[1][12:]
            return aes.decrypt(nonce, ct, b"")

        if data.startswith(b"B64:"):
            # allowed only when explicitly opted-in for dev/testing
            if os.environ.get("JARVIS_ALLOW_INSECURE_STORAGE") in ("1", "true", "True"):
                import base64

                try:
                    return base64.b64decode(data.split(b"B64:", 1)[1])
                except Exception:
                    return None
            raise RuntimeError("Insecure key storage detected but JARVIS_ALLOW_INSECURE_STORAGE is not set")

        # Unknown or unsupported format; fail loudly to avoid silent insecurity
        raise RuntimeError("Unknown or unsupported key format in keystore")

    def delete_key(self, session_id: str) -> None:
        p = self._path(session_id)
        try:
            if os.path.exists(p):
                os.unlink(p)
        except Exception:
            pass


class _InsecureXor:
    """Very small insecure fallback cipher for environments without cryptography.

    DO NOT use this in production. It provides deterministic reversible
    transformations so unit tests and local demos can run without native
    dependencies.
    """

    def __init__(self, key: bytes):
        # key may be any length; expand/repeat when xoring
        self._key = key

    def encrypt(self, nonce: bytes, plaintext: bytes, aad: bytes = b"") -> bytes:
        key = self._key
        out = bytearray(plaintext)
        for i in range(len(out)):
            out[i] ^= key[(i + len(nonce)) % len(key)]
        return bytes(out)

    def decrypt(self, nonce: bytes, ciphertext: bytes, aad: bytes = b"") -> bytes:
        # symmetric
        return self.encrypt(nonce, ciphertext, aad)


class AnomalyDetector:
    """Simple moving-statistics detector for packet rates.

    Uses an online algorithm (Welford) to track mean/stddev of an observed
    scalar (packets/sec). The anomaly score returned is (value - mean) / std
    (clipped). Higher -> more anomalous.
    """

    def __init__(self, alpha: float = 0.2):
        # exponential smoothing factor for rate measurement
        self.alpha = float(alpha)
        self._ema: Optional[float] = None
        # Welford variables for variance (keeps stability)
        self._count = 0
        self._mean = 0.0
        self._m2 = 0.0

    def update(self, value: float) -> float:
        # update EMA
        if self._ema is None:
            self._ema = value
        else:
            self._ema = self.alpha * value + (1 - self.alpha) * self._ema

        # update Welford
        self._count += 1
        delta = value - self._mean
        self._mean += delta / self._count
        delta2 = value - self._mean
        self._m2 += delta * delta2

        std = self.stddev()
        if std == 0:
            return 0.0
        score = (value - self._mean) / std
        return float(score)

    def stddev(self) -> float:
        if self._count < 2:
            return 0.0
        return (self._m2 / (self._count - 1)) ** 0.5


class VPNGateway:
    """Manages encrypted sessions and performs lightweight anomaly detection."""

    def __init__(self, rekey_interval: int = 3600):
        # sessions: session_id -> metadata
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.rekey_interval = int(rekey_interval)
        # keystore for persistent session keys
        self.keystore = KeyStore()
        # optional model for anomaly detection (scikit-learn / torch), loaded via hook
        self.model = None
        # runtime policy: anomaly threshold and suspend action
        self.policy = {
            "anomaly_threshold": float(os.environ.get("JARVIS_ANOMALY_THRESHOLD", 10.0)),
            "suspend_seconds": int(os.environ.get("JARVIS_SUSPEND_SECONDS", 60)),
        }
        # optional WireGuard manager (only enabled when env var is set)
        self.use_wireguard = os.environ.get("JARVIS_USE_WIREGUARD") in ("1", "true", "True")
        if self.use_wireguard:
            try:
                self.wg = WireGuardManager(interface=os.environ.get("JARVIS_WG_INTERFACE", "jarvis0"))
            except Exception:
                logger.exception("failed to initialize WireGuard manager; continuing without wg control")
                self.wg = None
        else:
            self.wg = None

    def _new_key(self) -> bytes:
        # generate a 32-byte key for AES-256 if AESGCM available, otherwise any bytes
        return secrets.token_bytes(32)

    def create_session(self, session_id: str, key: Optional[bytes] = None) -> Dict[str, Any]:
        """Create a session with a symmetric key (or generate one).

        Returns session metadata.
        """
        with self._lock:
            if session_id in self.sessions:
                raise ValueError("session already exists")
            # If a key already persisted in keystore, load and reuse it unless
            # an explicit key was provided.
            if key is None:
                try:
                    loaded = self.keystore.load_key(session_id)
                    if loaded:
                        key = loaded
                except Exception:
                    key = None
            key = key or self._new_key()
            if _HAS_AESGCM:
                cipher = AESGCM(key)
            else:
                cipher = _InsecureXor(key)
                logger.warning("cryptography not available; using insecure XOR fallback for VPNGateway")

            meta = {
                "key": key,
                "cipher": cipher,
                "created_at": time.time(),
                "last_seen": None,
                "packets": 0,
                "bytes": 0,
                "detector": AnomalyDetector(),
            }
            # persist key
            try:
                self.keystore.save_key(session_id, key)
            except Exception:
                logger.exception("failed to persist key for session %s", session_id)
            self.sessions[session_id] = meta
            # If WireGuard is enabled, attempt to create a peer mapping for this session.
            if self.wg is not None:
                try:
                    # Expect callers to provide a WireGuard public key via session metadata
                    pub = meta.get("wg_pubkey") or os.environ.get("JARVIS_DEFAULT_WG_PUBKEY")
                    allowed_ips = meta.get("wg_allowed_ips") or ["10.0.0.0/24"]
                    if pub:
                        self.wg.add_peer(session_id, pub, allowed_ips)
                except Exception:
                    logger.exception("failed to add wg peer for session %s", session_id)
            return {"session_id": session_id, "created_at": meta["created_at"]}

    def close_session(self, session_id: str) -> bool:
        with self._lock:
            if session_id not in self.sessions:
                return False
            # attempt cleanup
            del self.sessions[session_id]
            return True

    def rekey_session(self, session_id: str) -> bool:
        """Replace session key with a fresh one."""
        with self._lock:
            if session_id not in self.sessions:
                return False
            key = self._new_key()
            if _HAS_AESGCM:
                cipher = AESGCM(key)
            else:
                cipher = _InsecureXor(key)
            self.sessions[session_id]["key"] = key
            self.sessions[session_id]["cipher"] = cipher
            self.sessions[session_id]["created_at"] = time.time()
            # reset counters but keep detector state
            self.sessions[session_id]["packets"] = 0
            self.sessions[session_id]["bytes"] = 0
            try:
                self.keystore.save_key(session_id, key)
            except Exception:
                logger.exception("failed to persist rekey for %s", session_id)
            return True

    def suspend_session(self, session_id: str, until: Optional[float] = None) -> None:
        """Mark a session suspended until a given epoch time. Null means indefinitely."""
        if session_id not in self.sessions:
            return
        self.sessions[session_id]["suspended_until"] = until

    def is_suspended(self, session_id: str) -> bool:
        s = self.sessions.get(session_id)
        if not s:
            return False
        until = s.get("suspended_until")
        if until is None:
            return False
        return time.time() < until

    def encrypt_for_session(self, session_id: str, plaintext: bytes, aad: bytes = b"") -> bytes:
        """Encrypt plaintext for a session and return blob: nonce || ciphertext || tag if needed.

        For AESGCM we produce: nonce(12) || ciphertext || tag(16). For the insecure fallback
        we produce: nonce(8) || ciphertext (nonce is just used as salt).
        """
        if session_id not in self.sessions:
            raise KeyError("unknown session")
        if self.is_suspended(session_id):
            raise PermissionError("session suspended due to policy/anomaly")
        meta = self.sessions[session_id]
        cipher = meta["cipher"]
        if _HAS_AESGCM and isinstance(cipher, AESGCM):
            nonce = secrets.token_bytes(12)
            ct = cipher.encrypt(nonce, plaintext, aad)
            return nonce + ct
        else:
            # insecure fallback
            nonce = secrets.token_bytes(8)
            ct = cipher.encrypt(nonce, plaintext, aad)
            return nonce + ct

    def decrypt_for_session(self, session_id: str, blob: bytes, aad: bytes = b"") -> bytes:
        if session_id not in self.sessions:
            raise KeyError("unknown session")
        if self.is_suspended(session_id):
            raise PermissionError("session suspended due to policy/anomaly")
        meta = self.sessions[session_id]
        cipher = meta["cipher"]
        if _HAS_AESGCM and isinstance(cipher, AESGCM):
            if len(blob) < 12 + 16:
                raise ValueError("blob too short")
            nonce = blob[:12]
            ct = blob[12:]
            return cipher.decrypt(nonce, ct, aad)
        else:
            if len(blob) < 8:
                raise ValueError("blob too short")
            nonce = blob[:8]
            ct = blob[8:]
            return cipher.decrypt(nonce, ct, aad)

    def process_incoming(self, session_id: str, blob: bytes, now: Optional[float] = None, dest_addr: Optional[str] = None) -> Dict[str, Any]:
        """Process an incoming encrypted blob for a session.

        Returns a dict: {plaintext: bytes, meta: {...}, anomaly_score: float}
        """
        now = now or time.time()
        if session_id not in self.sessions:
            raise KeyError("unknown session")
        try:
            plaintext = self.decrypt_for_session(session_id, blob)
        except Exception as e:
            logger.debug("decrypt failed: %s", e)
            raise

        with self._lock:
            s = self.sessions[session_id]
            prev_last = s.get("last_seen")
            if prev_last is None:
                interval = None
            else:
                interval = now - prev_last
            s["last_seen"] = now
            s["packets"] += 1
            s["bytes"] += len(plaintext)

        # derive a simple packets/sec estimate
        pps = 0.0
        if interval is None or interval == 0:
            pps = float(s["packets"])
        else:
            pps = 1.0 / interval

        # If a model is loaded, use it (expect model.predict or predict_proba accepting 2D array)
        score = 0.0
        if self.model is not None:
            try:
                # model expects a 2D array-like input
                import numpy as _np

                X = _np.array([[pps]])
                if hasattr(self.model, "predict_proba"):
                    probs = self.model.predict_proba(X)
                    # take probability of positive class if two-class
                    if probs.shape[1] >= 2:
                        score = float(probs[0, 1])
                    else:
                        score = float(probs[0, 0])
                else:
                    pred = self.model.predict(X)
                    score = float(pred[0])
            except Exception:
                logger.exception("model scoring failed; falling back to AnomalyDetector")
                detector: AnomalyDetector = s["detector"]
                score = detector.update(pps)
        else:
            detector: AnomalyDetector = s["detector"]
            score = detector.update(pps)

        meta = {
            "session_id": session_id,
            "packets": s["packets"],
            "bytes": s["bytes"],
            "last_seen": s["last_seen"],
            "pps": pps,
        }

        # apply runtime policy: auto-suspend if anomaly score exceeds threshold
        action = None
        try:
            thresh = float(self.policy.get("anomaly_threshold", 1e9))
            if score > thresh:
                sec = int(self.policy.get("suspend_seconds", 60))
                self.suspend_session(session_id, until=time.time() + sec)
                action = {"suspended_until": time.time() + sec}
        except Exception:
            logger.exception("policy evaluation failed")

        # If zero-trust micro-segmentation is available and a destination is supplied,
        # consult it and enforce deny decisions.
        if dest_addr and zero_trust is not None:
            try:
                seg = zero_trust.enforce_microsegmentation({"role": "user", **{}}, dest_addr)
                if not seg.get("allowed"):
                    # take conservative action: suspend the session briefly and raise
                    self.suspend_session(session_id, until=time.time() + int(self.policy.get("suspend_seconds", 60)))
                    raise PermissionError(f"micro-segmentation denied: {seg.get('reason')}")
            except PermissionError:
                raise
            except Exception:
                logger.exception("micro-segmentation check failed; allowing by default")

        out = {"plaintext": plaintext, "meta": meta, "anomaly_score": score}
        if action is not None:
            out["action"] = action
        # Apply dynamic AI-managed policy hooks (e.g., narrow allowed-ips) when score exceeds threshold
        try:
            dyn_thresh = float(self.policy.get("dynamic_narrow_threshold", os.environ.get("JARVIS_DYNAMIC_NARROW_THRESHOLD", 1000000)))
        except Exception:
            dyn_thresh = 1e9

        if score > dyn_thresh:
            try:
                self._apply_dynamic_policy(session_id, score, dest_addr)
            except Exception:
                logger.exception("dynamic policy application failed")

        # attempt to restore previously narrowed allowed-ips if score falls below restore threshold
        try:
            restore_thresh = float(self.policy.get("dynamic_restore_threshold", os.environ.get("JARVIS_DYNAMIC_RESTORE_THRESHOLD", 0.5)))
        except Exception:
            restore_thresh = 0.5

        if score < restore_thresh:
            try:
                s = self.sessions.get(session_id)
                if s and s.get("wg_prev_allowed_ips") and s.get("wg_pubkey") and self.wg is not None:
                    prev = s.pop("wg_prev_allowed_ips")
                    try:
                        self.wg.add_peer(session_id, s.get("wg_pubkey"), prev)
                        s["wg_allowed_ips"] = list(prev)
                        logger.info("Restored allowed-ips for %s -> %s", session_id, prev)
                    except Exception:
                        logger.exception("failed to restore wg allowed-ips for %s", session_id)
            except Exception:
                logger.exception("dynamic policy restore check failed")

        return out

    def _apply_dynamic_policy(self, session_id: str, score: float, dest_addr: Optional[str] = None) -> None:
        """Apply an AI-managed dynamic policy for a session.

        Current behavior: when an anomaly score exceeds configured threshold,
        narrow the WireGuard "AllowedIPs" for the session's peer to the
        observed destination IP (single-host /32 or /128) to limit lateral movement.

        This function is defensive: it requires a WireGuard manager (`self.wg`)
        and a stored `wg_pubkey` in the session metadata to operate. It updates
        the session metadata `wg_allowed_ips` with the new narrower set.
        """
        if self.wg is None:
            logger.debug("dynamic policy requested but no WireGuard manager configured")
            return

        s = self.sessions.get(session_id)
        if not s:
            logger.debug("dynamic policy: unknown session %s", session_id)
            return

        pub = s.get("wg_pubkey")
        if not pub:
            logger.debug("dynamic policy: session %s has no wg_pubkey", session_id)
            return

    # Determine narrowed allowed-ips: prefer explicit policy override or dest
        narrowed = None
        # env override: JARVIS_NARROW_TO (e.g. /32 suffix) - not used here except to choose suffix
        suffix = os.environ.get("JARVIS_NARROW_SUFFIX", "/32")
        if dest_addr:
            # produce a single-host CIDR
            try:
                import ipaddress

                ip = ipaddress.ip_address(dest_addr)
                if ip.version == 4:
                    narrowed = f"{dest_addr}{suffix}"
                else:
                    narrowed = f"{dest_addr}{suffix if suffix.startswith('/') else '/128'}"
            except Exception:
                narrowed = None

        if narrowed is None:
            # fallback: use a conservative local-only rule
            narrowed = "127.0.0.1/32"

        new_allowed = [narrowed]
        # Before making an enforcement change, consult OPA if available
        opa_allowed = True
        try:
            opa_url = os.environ.get("JARVIS_OPA_URL")
            opa_path = os.environ.get("JARVIS_DYNAMIC_POLICY_PATH", "jarvis/dynamic/allow")
            if opa_url and zero_trust is not None and hasattr(zero_trust, "_evaluate_opa_policy"):
                # input describes the proposed change and current session
                opa_input = {"session": session_id, "score": score, "proposed": {"allowed_ips": new_allowed, "pubkey": pub}}
                try:
                    decision = zero_trust._evaluate_opa_policy(opa_url, opa_path, opa_input)
                    # expect decision like {"allowed": True/False, ...}
                    if isinstance(decision, dict) and not decision.get("allowed", True):
                        opa_allowed = False
                        logger.info("OPA vetoed dynamic policy for %s: %s", session_id, decision)
                except Exception:
                    logger.exception("OPA dynamic policy evaluation failed; defaulting to allow")
        except Exception:
            logger.exception("dynamic policy OPA consult failed")

        if not opa_allowed:
            return

        try:
            # attempt to update peer on WireGuard and persist old allowed-ips for restore
            old_allowed = s.get("wg_allowed_ips")
            # store the original allowed-ips only once so we can restore later
            if old_allowed and not s.get("wg_prev_allowed_ips"):
                s["wg_prev_allowed_ips"] = list(old_allowed)

            self.wg.add_peer(session_id, pub, new_allowed)
            # persist change in session metadata
            s["wg_allowed_ips"] = new_allowed
            logger.info("Applied dynamic narrow allowed-ips for %s -> %s", session_id, new_allowed)
        except Exception:
            logger.exception("failed to apply dynamic peer update for %s", session_id)

    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            raise KeyError("unknown session")
        s = self.sessions[session_id]
        return {
            "session_id": session_id,
            "created_at": s["created_at"],
            "last_seen": s["last_seen"],
            "packets": s["packets"],
            "bytes": s["bytes"],
        }

    def load_model(self, model_path: str) -> bool:
        """Attempt to load an ML model from disk.

        Supports joblib / sklearn saved models. If loading fails, returns False
        and the gateway continues to use the fallback `AnomalyDetector` per-session.
        """
        try:
            # prefer joblib if available
            try:
                import joblib

                model = joblib.load(model_path)
            except Exception:
                # try sklearn.externals.joblib
                try:
                    from sklearn.externals import joblib as _jb

                    model = _jb.load(model_path)
                except Exception:
                    model = None
            if model is None:
                return False
            # attach model
            self.model = model
            logger.info("loaded anomaly model from %s", model_path)
            return True
        except Exception:
            logger.exception("failed to load model %s", model_path)
            return False


def establish_tunnel(config: dict) -> Dict[str, Any]:
    """Convenience function kept for backwards compatibility.

    It simply creates a VPNGateway, makes a session using config['session_id'] if
    present, and returns basic info. This is intended for demo/testing.
    """
    gw = VPNGateway()
    sid = config.get("session_id", f"s-{secrets.token_hex(4)}")
    gw.create_session(sid)
    return {"status": "tunnel_established", "session_id": sid}

