"""Hybrid PQ/classical wrappers and utilities.

This module provides helpers to combine two KEMs (e.g., classical + PQ) into
one hybrid KEM and similarly combine signatures. The combination derives a
final shared key via a small HKDF over both shared secrets.
"""
from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import Tuple, Dict, Any
import base64
from secrets import token_bytes
import os
import logging


logger = logging.getLogger(__name__)


def _hkdf_extract(salt: bytes, ikm: bytes) -> bytes:
    return hmac.new(salt or b"", ikm, hashlib.sha256).digest()


def _hkdf_expand(prk: bytes, info: bytes, length: int = 32) -> bytes:
    # very small HKDF expand: single-block only (sufficient for 32 bytes)
    t = hmac.new(prk, info + b"\x01", hashlib.sha256).digest()
    return t[:length]


def hkdf_okm(inputs: Tuple[bytes, ...], length: int = 32) -> bytes:
    """Derive an output key from multiple input secrets via HKDF-SHA256.

    This is a convenience combining extract+expand. Salt is empty (not
    ideal but simple); for real use, pass a proper salt.
    """
    ikm = b"".join(inputs)
    prk = _hkdf_extract(b"", ikm)
    return _hkdf_expand(prk, b"hybrid-kem", length)


@dataclass
class CombinedCiphertext:
    a_ct: bytes
    b_ct: bytes


class HybridKEM:
    """Combine two KEM instances (they must provide encapsulate/decapsulate).

    Example usage:
        hybrid = HybridKEM(kem_a, kem_b)
        pk_a, sk_a = kem_a.generate_keypair()
        pk_b, sk_b = kem_b.generate_keypair()
        ct, ss = hybrid.encapsulate((pk_a, pk_b))
        ss2 = hybrid.decapsulate((sk_a, sk_b), ct)
        assert ss == ss2
    """

    def __init__(self, kem_a, kem_b):
        self.kem_a = kem_a
        self.kem_b = kem_b

    def generate_keypair(self):
        a = self.kem_a.generate_keypair()
        b = self.kem_b.generate_keypair()
        return (a.public, b.public), (a.private, b.private)

    def encapsulate(self, public_pair: Tuple[bytes, bytes]) -> Tuple[CombinedCiphertext, bytes]:
        a_pub, b_pub = public_pair
        a_ct, a_ss = self.kem_a.encapsulate(a_pub)
        b_ct, b_ss = self.kem_b.encapsulate(b_pub)
        ss = hkdf_okm((a_ss, b_ss), length=32)
        return CombinedCiphertext(a_ct=a_ct, b_ct=b_ct), ss

    def decapsulate(self, private_pair: Tuple[bytes, bytes], combined_ct: CombinedCiphertext) -> bytes:
        a_sk, b_sk = private_pair
        a_ss = self.kem_a.decapsulate(a_sk, combined_ct.a_ct)
        b_ss = self.kem_b.decapsulate(b_sk, combined_ct.b_ct)
        ss = hkdf_okm((a_ss, b_ss), length=32)
        return ss


class HybridSigner:
    """Combine two signature schemes by producing both signatures and
    verifying both. The combined signature is simply the concatenation of
    both signatures.
    """

    def __init__(self, signer_a, signer_b):
        self.signer_a = signer_a
        self.signer_b = signer_b

    def sign(self, private_pair: Tuple[bytes, bytes], message: bytes) -> bytes:
        a_sk, b_sk = private_pair
        sig_a = self.signer_a.sign(a_sk, message)
        sig_b = self.signer_b.sign(b_sk, message)
        return sig_a + b"::" + sig_b

    def verify(self, public_pair: Tuple[bytes, bytes], message: bytes, signature: bytes) -> bool:
        a_pk, b_pk = public_pair
        try:
            sig_a, sig_b = signature.split(b"::", 1)
        except Exception:
            return False
        return self.signer_a.verify(a_pk, message, sig_a) and self.signer_b.verify(b_pk, message, sig_b)


__all__ = ["HybridKEM", "HybridSigner", "CombinedCiphertext", "hkdf_okm", "TLSHybridHandshake"]


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


def _ub64(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))


class TLSHybridHandshake:
    """Simple TLS-like hybrid KEM handshake for AI nodes.

    This implements a lightweight, testable handshake that combines two KEMs
    (e.g. classical + PQ) into a single derived master secret using HKDF.

    Flow (simplified):
      - Client: generates ephemeral keypairs for both KEMs and sends a
        ClientHello containing the public keys and a client_nonce.
      - Server: encapsulates to each client public key (producing ciphertexts
        and shared secrets), replies with ServerHello containing the
        ciphertexts and a server_nonce.
      - Client: decapsulates the ciphertexts using its private keys to recover
        the per-kem shared secrets. Both sides derive the same master secret
        via hkdf_okm(a_ss, b_ss, client_nonce, server_nonce).

    Notes:
      - Messages are encoded as JSON with base64 fields for portability.
      - The class is intentionally small and meant for simulation/emulation
        in AI node testing. For production use embed this into a proper TLS
        stack and use validated crypto primitives and salts.
    """

    def __init__(self, kem_a, kem_b):
        """kem_a and kem_b must implement generate_keypair(), encapsulate(pub)
        and decapsulate(sk, ct) methods (same as HybridKEM uses).
        """
        self.kem_a = kem_a
        self.kem_b = kem_b

    def client_create_hello(self, nonce: bytes | None = None) -> Tuple[Dict[str, Any], Tuple[bytes, bytes]]:
        """Create a ClientHello containing ephemeral public keys.

        Returns (client_hello_dict, (a_private, b_private)) where the private
        tuple must be kept by the client to finish the handshake.
        """
        # generate ephemeral keypairs
        a_kp = self.kem_a.generate_keypair()
        b_kp = self.kem_b.generate_keypair()
        client_nonce = nonce or token_bytes(32)
        ch = {
            "type": "client_hello",
            "nonce": _b64(client_nonce),
            "kems": {
                "a": _b64(a_kp.public),
                "b": _b64(b_kp.public),
            },
        }
        # return the private keys so caller can complete the handshake
        return ch, (a_kp.private, b_kp.private)

    def server_process_client_hello(self, client_hello: Dict[str, Any]) -> Dict[str, Any]:
        """Server processes client hello, encapsulates to client pubs and returns ServerHello.

        Server creates ciphertexts (for each KEM) and includes a server_nonce.
        """
        if client_hello.get("type") != "client_hello":
            raise ValueError("expected client_hello")
        client_nonce = _ub64(client_hello["nonce"])
        a_pub = _ub64(client_hello["kems"]["a"])
        b_pub = _ub64(client_hello["kems"]["b"])

        a_ct, a_ss = self.kem_a.encapsulate(a_pub)
        b_ct, b_ss = self.kem_b.encapsulate(b_pub)

        server_nonce = token_bytes(32)
        sh = {
            "type": "server_hello",
            "nonce": _b64(server_nonce),
            "ct": {
                "a": _b64(a_ct),
                "b": _b64(b_ct),
            },
        }

        # store transient secrets on the server side to derive the master
        # In a real implementation these would be kept in secure memory.
        sh["_server_ss"] = {
            "a": _b64(a_ss),
            "b": _b64(b_ss),
            "client_nonce": _b64(client_nonce),
        }
        return sh

    def client_finish(self, private_pair: Tuple[bytes, bytes], server_hello: Dict[str, Any], client_nonce: bytes) -> bytes:
        """Client decapsulates server ciphertexts and derives master secret.

        Returns the derived master secret (bytes).
        """
        if server_hello.get("type") != "server_hello":
            raise ValueError("expected server_hello")
        server_nonce = _ub64(server_hello["nonce"])
        a_ct = _ub64(server_hello["ct"]["a"])
        b_ct = _ub64(server_hello["ct"]["b"])
        a_sk, b_sk = private_pair

        a_ss = self.kem_a.decapsulate(a_sk, a_ct)
        b_ss = self.kem_b.decapsulate(b_sk, b_ct)

        master = hkdf_okm((a_ss, b_ss, client_nonce, server_nonce), length=48)
        return master

    def server_derive_master(self, server_hello: Dict[str, Any]) -> bytes:
        """Server derives the master secret from stored transient secrets.

        This reads the internal `_server_ss` field produced by
        `server_process_client_hello`. In real code, server should keep the
        secrets in secure memory and remove them after deriving the master.
        """
        meta = server_hello.get("_server_ss")
        if not meta:
            raise ValueError("missing server-side shared secret material")
        a_ss = _ub64(meta["a"])
        b_ss = _ub64(meta["b"])
        client_nonce = _ub64(meta["client_nonce"])
        server_nonce = _ub64(server_hello["nonce"])
        master = hkdf_okm((a_ss, b_ss, client_nonce, server_nonce), length=48)
        return master


class HuaweiKMSHybridAdapter:
    """Adapter to protect/unprotect derived master secrets using Huawei Cloud KMS.

    This class attempts to use a Huawei KMS SDK if available (gated import).
    If the SDK is not installed or credentials are not configured, it falls
    back to a simple disk-based emulator (not secure) which stores encrypted
    blobs under the path given by HUAWEI_KMS_EMULATOR_DIR (env var) or
    `.kms_emulator/` under the repository root.

    This adapter demonstrates how to integrate the TLS-like PQC handshake
    with Cloud KMS hybrid encryption: you derive a master_secret from the
    handshake and then call `protect_master_secret` to have KMS wrap it.
    """

    def __init__(self, use_emulator: bool | None = None, emulator_dir: str | None = None):
        # Decide whether to use emulator: default is to use emulator unless
        # a real Huawei SDK is present and use_emulator is explicitly False.
        self._sdk_client = None
        self._use_emulator = True if use_emulator is None else bool(use_emulator)
        self._emulator_dir = emulator_dir or os.environ.get("HUAWEI_KMS_EMULATOR_DIR", ".kms_emulator")
        if not os.path.isdir(self._emulator_dir):
            try:
                os.makedirs(self._emulator_dir, exist_ok=True)
            except Exception:
                pass

        if not self._use_emulator:
            # Try to import a Huawei KMS SDK (gated). The exact package name and
            # APIs may vary across SDK versions. We'll try to build a client if
            # credentials are provided via environment variables. If anything
            # fails we fall back to emulator mode.
            try:
                # Attempt to import common SDK modules. If these imports fail
                # we'll revert to emulator mode.
                from huaweicloudsdkkms.v1 import KmsClient  # type: ignore
                from huaweicloudsdkcore.auth.credentials import BasicCredentials  # type: ignore
                from huaweicloudsdkkms.v1.region.kms_region import KmsRegion  # type: ignore

                ak = os.environ.get("HUAWEICLOUD_AK")
                sk = os.environ.get("HUAWEICLOUD_SK")
                project_id = os.environ.get("HUAWEICLOUD_PROJECT_ID")
                region = os.environ.get("HUAWEICLOUD_REGION")
                key_id = os.environ.get("HUAWEICLOUD_KMS_KEY_ID")

                if not (ak and sk and project_id and region and key_id):
                    # Missing runtime credentials; don't attempt network calls.
                    raise RuntimeError("missing Huawei KMS credentials in environment variables")

                creds = BasicCredentials(ak, sk).with_project_id(project_id)
                builder = KmsClient.new_builder().with_credentials(creds).with_region(KmsRegion.value_of(region))
                client = builder.build()

                # Save client and configuration for use by protect/unprotect.
                self._sdk_client = client
                self._kms_key_id = key_id
                self._use_emulator = False
            except Exception as e:  # pragma: no cover - environment dependent
                logger.debug("Huawei KMS SDK not available or not configured: %s", e)
                self._sdk_client = None
                self._use_emulator = True

    def protect_master_secret(self, master_secret: bytes, metadata: dict | None = None) -> dict:
        """Protect (wrap) the master_secret with KMS.

        Returns a dict containing at least an `encrypted_blob` (base64) and
        metadata including a resource identifier. In emulator mode the blob is
        stored on disk and `resource_id` is a filename.
        """
        metadata = metadata or {}
        if not self._use_emulator and self._sdk_client:
            # Attempt to call the Huawei KMS SDK encrypt API in a defensive way.
            # SDKs differ across versions; try common model/request class names
            # and response attribute names. On any failure we fall back to the
            # emulator behavior below.
            try:
                # Try to import common request model
                try:
                    from huaweicloudsdkkms.v1.model import EncryptRequest  # type: ignore
                    ReqCls = EncryptRequest
                except Exception:
                    # some SDKs might name it differently or expect a dict
                    ReqCls = None

                if ReqCls is not None:
                    req = ReqCls(key_id=self._kms_key_id, plaintext=_b64(master_secret))
                    resp = self._sdk_client.encrypt(req)
                else:
                    # Try calling encrypt with kwargs (some bindings accept this)
                    resp = self._sdk_client.encrypt(key_id=self._kms_key_id, plaintext=_b64(master_secret))

                # Inspect response for common ciphertext attributes
                encrypted_blob = None
                for attr in ("ciphertext", "cipher_text", "ciphertext_base64", "ciphertext_blob", "ciphertext_str"):
                    encrypted_blob = getattr(resp, attr, None)
                    if encrypted_blob:
                        break
                # Some SDKs return a dict-like response under .to_dict()
                if not encrypted_blob:
                    try:
                        d = resp.to_dict()
                        for k in ("ciphertext", "cipher_text", "ciphertext_base64"):
                            if k in d:
                                encrypted_blob = d[k]
                                break
                    except Exception:
                        pass

                if not encrypted_blob:
                    raise RuntimeError("encrypt response missing ciphertext")

                return {"resource_id": getattr(resp, "key_id", self._kms_key_id), "encrypted_blob": encrypted_blob, "metadata": metadata}
            except Exception as e:
                logger.debug("Huawei KMS SDK encrypt/decorate failed, falling back to emulator: %s", e)

    # Emulator: write to file and return base64 blob + filename
        rid = token_bytes(8).hex()
        fname = os.path.join(self._emulator_dir, f"kms_blob_{rid}.bin")
        try:
            with open(fname, "wb") as fh:
                fh.write(master_secret)
        except Exception as e:
            raise RuntimeError(f"failed to write emulator blob: {e}")
        return {"resource_id": f"emulator://{rid}", "encrypted_blob": _b64(master_secret), "path": fname, "metadata": metadata}

    def unprotect_master_secret(self, resp: dict) -> bytes:
        """Unwrap/decrypt a protected master secret using KMS or emulator.

        If `resp` is a KMS response dict from `protect_master_secret`, this
        will return the original plaintext master_secret.
        """
        if not self._use_emulator and self._sdk_client:
            # Attempt to call the Huawei KMS SDK decrypt API defensively.
            try:
                # Try to import common request model
                try:
                    from huaweicloudsdkkms.v1.model import DecryptRequest  # type: ignore
                    DecReq = DecryptRequest
                except Exception:
                    DecReq = None

                enc_blob = resp.get("encrypted_blob")
                if enc_blob is None:
                    raise RuntimeError("missing encrypted_blob in response")

                if DecReq is not None:
                    req = DecReq(key_id=self._kms_key_id, ciphertext=enc_blob)
                    dec = self._sdk_client.decrypt(req)
                else:
                    dec = self._sdk_client.decrypt(key_id=self._kms_key_id, ciphertext=enc_blob)

                # extract plaintext from response
                plaintext = None
                for attr in ("plaintext", "plain_text", "plaintext_base64"):
                    plaintext = getattr(dec, attr, None)
                    if plaintext:
                        break
                if not plaintext:
                    try:
                        d = dec.to_dict()
                        for k in ("plaintext", "plain_text", "plaintext_base64"):
                            if k in d:
                                plaintext = d[k]
                                break
                    except Exception:
                        pass

                if not plaintext:
                    raise RuntimeError("decrypt response missing plaintext")

                # If plaintext is base64-encoded, decode it; otherwise assume raw
                try:
                    return _ub64(plaintext) if isinstance(plaintext, str) else bytes(plaintext)
                except Exception:
                    return plaintext
            except Exception as e:
                logger.debug("Huawei KMS SDK decrypt failed, falling back to emulator: %s", e)

        # Emulator: read the file if present, else decode the base64 blob.
        path = resp.get("path")
        if path and os.path.isfile(path):
            with open(path, "rb") as fh:
                return fh.read()
        if "encrypted_blob" in resp:
            return _ub64(resp["encrypted_blob"])
        raise RuntimeError("invalid emulator response: missing blob")

