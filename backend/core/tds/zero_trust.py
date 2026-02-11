"""Zero-trust helpers for mobile biometric + PQC flows.

This module provides a tiny, guarded implementation used by the mobile app
flows. In production this should be replaced with real biometric token
validation (e.g., platform attestation verification, signature checks) and
securely stored handshake state.
"""
from __future__ import annotations

import base64
import os
import secrets
import threading
from typing import Dict, Optional

_HANDSHAKES: Dict[str, Dict] = {}
_lock = threading.Lock()


def generate_handshake(device_id: str) -> Dict[str, str]:
    """Create a new handshake entry and return handshake_id + challenge.

    The challenge should be signed/processed by the device-side PQC key.
    """
    hid = secrets.token_urlsafe(16)
    challenge = secrets.token_bytes(32)
    with _lock:
        _HANDSHAKES[hid] = {
            "device_id": device_id,
            "challenge_b64": base64.urlsafe_b64encode(challenge).decode(),
            "biometric_verified": False,
            "pqc_verified": False,
        }
    return {"handshake_id": hid, "challenge": _HANDSHAKES[hid]["challenge_b64"]}


def verify_biometric_token(token: str) -> bool:
    """Verify a biometric attestation token.

    This is a placeholder: in production, validate platform attestation or
    biometric attestation service response. For dev mode we accept a
    special token "dev-biom" or truthy env var.
    """
    start = time.time()
    try:
        if os.environ.get("DEV_ACCEPT_BIOMETRIC") in ("1", "true", "True"):
            logger.debug("verify_biometric_token: dev accept enabled, token accepted")
            return True
        if token == "dev-biom":
            logger.debug("verify_biometric_token: dev token received, accepted")
            return True
        # Real verification would go here (signature checks, attestation payload)
        logger.debug("verify_biometric_token: token not accepted")
        return False
    finally:
        dur = (time.time() - start) * 1000.0
        logger.info("verify_biometric_token finished in %.1fms", dur)


def mark_biometric_verified(handshake_id: str) -> bool:
    with _lock:
        h = _HANDSHAKES.get(handshake_id)
        if not h:
            return False
        h["biometric_verified"] = True
        return True


def is_handshake_ready(handshake_id: str) -> bool:
    with _lock:
        h = _HANDSHAKES.get(handshake_id)
        if not h:
            return False
        return bool(h.get("biometric_verified"))


def get_handshake(handshake_id: str) -> Optional[Dict]:
    with _lock:
        return _HANDSHAKES.get(handshake_id)

import logging
import time
from typing import Dict, Any, Optional
import os
import json

logger = logging.getLogger("jarvis.zero_trust")


class AttestationError(RuntimeError):
    pass


def attest_device(device_info: Dict[str, Any]) -> Dict[str, Any]:
    """Attempt to attest a device.

    Steps:
    1. Prefer TPM-based attestation if available (call
       `hardware_integration.tpm_attestation.attest()`). If it returns a
       dict with `attested: True` treat as success and return enriched
       result.
    2. If TPM attestation is not available or returns not-attested,
       perform a lightweight policy evaluation based on `device_info`.

    The returned dict contains at least:
      - attested: bool
      - score: float (0.0..1.0) heuristic trust score
      - timestamp: unix epoch
      - device_id: optional identifier
      - claims: raw attestation/inspection data

    This function does not throw on missing hardware modules; instead it
    returns an attestation dict indicating failure which callers can
    enforce as needed.
    """
    timestamp = int(time.time())

    # Try to enrich device_info with Huawei IAM attributes if available
    try:
        from hardware_integration import huawei_iam  # may be injected in tests

        try:
            iam_attrs = huawei_iam.get_device_attributes(device_info.get("device_id"))
            if isinstance(iam_attrs, dict):
                # merge but prefer explicit device_info fields
                enriched = {**iam_attrs, **device_info}
                device_info = enriched
                logger.debug("Enriched device_info from Huawei IAM: %s", list(iam_attrs.keys()))
        except Exception as exc:
            logger.debug("Huawei IAM lookup failed: %s", exc)
    except Exception:
        # Huawei IAM client not available in this environment
        logger.debug("Huawei IAM client not available; continuing")

    # 1) Try TPM attestation (if present in environment)
    try:
        from hardware_integration import tpm_attestation  # local import

        try:
            att = tpm_attestation.attest()
        except Exception as exc:  # attestation attempted but failed
            logger.debug("TPM attestation attempt failed: %s", exc)
            att = None

        if isinstance(att, dict) and att.get("attested"):
            # enrich and return
            result = {
                "attested": True,
                "score": 1.0,
                "timestamp": timestamp,
                "device_id": att.get("device_id") or att.get("device_key"),
                "claims": att,
                "raw": att,
            }
            logger.info("Device attested via TPM: %s", result.get("device_id"))
            return result
    except Exception:
        # hardware_integration may be missing in test/dev; fall through
        logger.debug("TPM attestation not available; falling back to policy checks")

    # 2) Lightweight policy fallback
    # 2a) If OPA is configured, prefer evaluating an attestation policy there
    opa_url = os.environ.get("JARVIS_OPA_URL")
    opa_policy_path = os.environ.get("JARVIS_ATTESTATION_POLICY", "jarvis/attestation/allow")
    if opa_url:
        try:
            decision = _evaluate_opa_policy(opa_url, opa_policy_path, {"device": device_info})
            # expected decision is a dict like {"allowed": True, "score": 0.9, "reasons": [...]}
            if isinstance(decision, dict):
                result = {
                    "attested": bool(decision.get("allowed")),
                    "score": float(decision.get("score", 1.0 if decision.get("allowed") else 0.0)),
                    "timestamp": timestamp,
                    "device_id": device_info.get("device_id"),
                    "claims": decision.get("claims", {}),
                    "raw": {"opa_result": decision, "device_info": device_info},
                    "reasons": decision.get("reasons", []),
                }
                logger.info("OPA attestation decision: %s", result)
                return result
        except Exception as exc:
            logger.debug("OPA attestation evaluation failed: %s", exc)

    # 2b) Heuristic scoring: prefer up-to-date patch_age_days, secure_boot, and known vendor
    score = 0.0
    reasons = []

    # secure boot / trusted boot
    if device_info.get("secure_boot"):
        score += 0.4
        reasons.append("secure_boot")

    # patch age (days)
    patch_age = device_info.get("patch_age_days")
    if patch_age is not None:
        try:
            patch_age = float(patch_age)
            if patch_age <= 30:
                score += 0.4
                reasons.append("recent_patches")
            elif patch_age <= 90:
                score += 0.2
            else:
                reasons.append("stale_patches")
        except Exception:
            reasons.append("patch_age_unknown")

    # vendor allow-list (short experimental list)
    vendor = device_info.get("vendor")
    if vendor and vendor.lower() in ("trustedco", "acme-corp"):
        score += 0.2
        reasons.append("trusted_vendor")

    # normalize score
    if score > 1.0:
        score = 1.0

    attested = score >= 0.6

    result = {
        "attested": bool(attested),
        "score": float(score),
        "timestamp": timestamp,
        "device_id": device_info.get("device_id"),
        "claims": {k: device_info.get(k) for k in ("secure_boot", "patch_age_days", "vendor") if k in device_info},
        "raw": device_info,
        "reasons": reasons,
    }

    logger.debug("Attestation fallback result: %s", result)
    return result


def enforce_microsegmentation(session_meta: Dict[str, Any], dest_addr: str, proto: Optional[str] = None, policy: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Enforce a simple micro-segmentation rule for a session.

    Parameters
    - session_meta: metadata about the session (may include `role`,
      `allowed_cidrs` list or `allowed_segments`)
    - dest_addr: destination IPv4/IPv6 address string
    - proto: optional protocol (tcp/udp) string
    - policy: optional external policy dict to override defaults

    Returns a dict: {allowed: bool, reason: str}
    """
    # admin bypass
    role = session_meta.get("role")
    if role == "admin":
        return {"allowed": True, "reason": "admin_bypass"}

    # policy override
    effective_policy = policy or {}

    # If OPA is configured, consult micro-segmentation policy first
    opa_url = os.environ.get("JARVIS_OPA_URL")
    opa_seg_path = os.environ.get("JARVIS_SEGMENTATION_POLICY", "jarvis/segmentation/allow")
    if opa_url:
        try:
            opa_input = {"session": session_meta, "dest": {"addr": dest_addr, "proto": proto}}
            decision = _evaluate_opa_policy(opa_url, opa_seg_path, opa_input)
            if isinstance(decision, dict) and "allowed" in decision:
                return {"allowed": bool(decision.get("allowed")), "reason": decision.get("reason", "opa_decision"), "details": decision}
        except Exception as exc:
            logger.debug("OPA segmentation evaluation failed: %s", exc)

    # 1) If policy provides explicit allow/deny for segments, use it
    allowed_cidrs = session_meta.get("allowed_cidrs") or effective_policy.get("allowed_cidrs")
    if allowed_cidrs:
        try:
            import ipaddress

            dest_ip = ipaddress.ip_address(dest_addr)
            for c in allowed_cidrs:
                try:
                    net = ipaddress.ip_network(c, strict=False)
                    if dest_ip in net:
                        return {"allowed": True, "reason": "cidr_allowed"}
                except Exception:
                    # skip invalid cidrs
                    continue
            return {"allowed": False, "reason": "cidr_denied"}
        except Exception as exc:
            logger.debug("CIDR check failed: %s", exc)

    # 2) Segment-name based mapping (session_meta.allowed_segments must match dest_segment)
    allowed_segments = session_meta.get("allowed_segments") or effective_policy.get("allowed_segments")
    dest_segment = session_meta.get("dest_segment") or effective_policy.get("dest_segment")
    if allowed_segments is not None and dest_segment is not None:
        if dest_segment in allowed_segments:
            return {"allowed": True, "reason": "segment_allowed"}
        return {"allowed": False, "reason": "segment_denied"}

    # 3) Default: allow intra-VPN traffic (no dest_addr or loopback) else deny
    if not dest_addr:
        return {"allowed": True, "reason": "no_dest_specified"}

    # conservative default deny
    return {"allowed": False, "reason": "default_deny"}


def _evaluate_opa_policy(opa_url: str, policy_path: str, input_data: Dict[str, Any]) -> Any:
    """Evaluate a policy in an OPA server.

    - opa_url: base URL of OPA (e.g. http://localhost:8181)
    - policy_path: package/path within OPA data API, e.g. "jarvis/attestation/allow"
    - input_data: object to send as `input` to OPA

    Returns the `result` field returned by OPA (may be bool, dict, etc.).

    This function tries to use the `requests` library; if unavailable it falls
    back to urllib and returns Python objects parsed from JSON. Any network or
    parsing error raises an exception which callers should handle.
    """
    # build URL: POST {opa_url.rstrip('/')}/v1/data/{policy_path}
    base = opa_url.rstrip("/")
    url = f"{base}/v1/data/{policy_path.lstrip('/') }"
    payload = {"input": input_data}

    # Try requests first (convenient for tests/CI)
    try:
        import requests

        resp = requests.post(url, json=payload, timeout=5)
        resp.raise_for_status()
        body = resp.json()
        return body.get("result")
    except Exception:
        # fallback to urllib
        try:
            from urllib import request as _request
            from urllib.error import HTTPError

            req = _request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
            with _request.urlopen(req, timeout=5) as r:
                data = r.read().decode("utf-8")
                body = json.loads(data)
                return body.get("result")
        except Exception as exc:
            logger.debug("OPA call failed to %s: %s", url, exc)
            raise

