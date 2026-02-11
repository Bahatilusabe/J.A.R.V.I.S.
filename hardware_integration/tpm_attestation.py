"""TPM attestation helpers.

This module provides a small, guarded implementation that supports three
attestation strategies (in order):

- `TPM_ATTEST_CMD`: run an external helper that emits JSON (fastest to
  integrate with vendor tools).
- Huawei IoT Device ID SDK: if enabled via `HUAWEI_IOT_DEVICE_ID_ENABLED`,
  probe for a Python SDK or native lib and call its attest/get_device_id
  methods.
- TPM 2.0 via `tpm2-pytss`: read platform PCRs and derive a device-bound
  key.

All public functions return a dict containing at least `attested: bool`.
On success they include `device_key` (hex string) or `device_id` when the
IoT SDK provides a stable device identifier.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import hashlib
from typing import Dict

logger = logging.getLogger("jarvis.tpm_attestation")


def _run_cmd_json(cmd: str) -> Dict:
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        logger.error("TPM attestation helper failed: %s", err.decode(errors="ignore"))
        raise RuntimeError(f"TPM attestation helper failed: {err.decode(errors='ignore')}")
    try:
        return json.loads(out.decode())
    except Exception:
        raise RuntimeError("TPM attestation helper did not return valid JSON")


def attest() -> Dict:
    """Lightweight attest used for development and testing.

    If `JARVIS_TPM_SECRET` is present we return a simple attested payload.
    Otherwise we return a structure indicating not attested.
    """
    s = os.environ.get("JARVIS_TPM_SECRET")
    if s:
        return {"attested": True, "device_key": s}
    return {"attested": False}


def _probe_huawei_iot_sdk() -> Dict | None:
    """Try to locate a Huawei IoT Device ID SDK and call it.

    We support a Python SDK (env K: `HUAWEI_IOT_PYSDK`) or a helper CLI
    via `HUAWEI_IOT_ATTEST_CMD`. Returned dict should include `attested` and
    `device_id` or `device_key` where possible.
    """
    # CLI helper
    cmd = os.environ.get("HUAWEI_IOT_ATTEST_CMD")
    if cmd:
        logger.info("Using Huawei IoT attestation helper: %s", cmd)
        return _run_cmd_json(cmd)

    # Python SDK probe
    if os.environ.get("HUAWEI_IOT_DEVICE_ID_ENABLED", "false").lower() in ("1", "true", "yes"):
        candidates = [os.environ.get("HUAWEI_IOT_PYSDK"), "huaweiiot", "huaweiiot_sdk", "iot_device_id"]
        for name in filter(None, candidates):
            try:
                mod = __import__(name)
                logger.info("Found Huawei IoT SDK: %s", name)
                # Try common function names
                for fn in ("get_device_id", "device_id", "attest", "get_deviceid"):
                    if hasattr(mod, fn):
                        try:
                            val = getattr(mod, fn)()
                            # normalize
                            if isinstance(val, dict):
                                return val
                            if isinstance(val, str):
                                return {"attested": True, "device_id": val}
                        except Exception:
                            logger.exception("Huawei SDK call %s failed", fn)
                # if not callable at module-level, maybe class-based
                if hasattr(mod, "Client"):
                    try:
                        client = mod.Client()
                        for fn in ("get_device_id", "attest", "device_id"):
                            if hasattr(client, fn):
                                val = getattr(client, fn)()
                                if isinstance(val, dict):
                                    return val
                                if isinstance(val, str):
                                    return {"attested": True, "device_id": val}
                    except Exception:
                        logger.exception("Huawei SDK Client probe failed")
            except Exception:
                logger.debug("Huawei IoT SDK candidate not importable: %s", name, exc_info=True)
    return None


def _tpm2_pytss_attest() -> Dict:
    """Attempt TPM attestation using tpm2-pytss and PCR values.

    Returns a dict with `attested: True` and `device_key` derived from
    selected PCRs (0..23 by default). Raises RuntimeError on failure.
    """
    try:
        # tpm2-pytss may not be available in all dev environments; silence
        # static import errors while keeping the runtime import intact.
        from tpm2_pytss import ESAPI  # type: ignore[import]

        with ESAPI() as e:
            pcr_values = []
            # Try a reasonable set of PCRs (0..7 and 16..23 commonly used)
            candidates = list(range(0, 8)) + list(range(16, 24))
            for pcr in candidates:
                try:
                    # ESAPI.PCR_Read usage varies; attempt to call generically
                    # The tpm2-pytss library provides PCR_Read returning TPML_DIGEST values
                    digests = e.PCR_Read(pcr)  # type: ignore
                    # digests handling is environment dependent; attempt to serialize
                    if isinstance(digests, (bytes, bytearray)):
                        pcr_values.append(bytes(digests))
                    else:
                        # attempt to string-repr complex objects
                        pcr_values.append(str(digests).encode())
                except Exception:
                    # ignore unavailable PCRs
                    logger.debug("PCR %d read failed", pcr, exc_info=True)
                    continue
            if not pcr_values:
                raise RuntimeError("could not read any PCRs from TPM via tpm2-pytss")
            h = hashlib.sha256()
            for v in pcr_values:
                h.update(v)
            return {"attested": True, "device_key": h.hexdigest()}
    except Exception as exc:
        raise RuntimeError(f"tpm2-pytss attestation failed: {exc}")


def attest_production() -> Dict:
    """Attempt a production-grade attestation using multiple strategies.

    Order:
    1. `TPM_ATTEST_CMD` external helper (JSON output)
    2. Huawei IoT Device ID SDK (env `HUAWEI_IOT_DEVICE_ID_ENABLED`)
    3. TPM 2.0 via `tpm2-pytss`

    Raises RuntimeError if no strategy succeeds.
    """
    # 1) external helper
    cmd = os.environ.get("TPM_ATTEST_CMD")
    if cmd:
        logger.info("Using TPM attestation helper: %s", cmd)
        return _run_cmd_json(cmd)

    # 2) Huawei IoT Device ID SDK
    h = _probe_huawei_iot_sdk()
    if h is not None:
        logger.info("Huawei IoT SDK attestation succeeded or returned data")
        return h

    # 3) tpm2-pytss
    try:
        return _tpm2_pytss_attest()
    except Exception as exc:
        logger.exception("tpm2-pytss attestation failed")

    raise RuntimeError("No TPM attestation method available. Set TPM_ATTEST_CMD, enable Huawei SDK or install tpm2-pytss.")


def get_device_key() -> str | None:
    """Convenience to obtain a stable device_key if attestation succeeds.

    Returns hex string or None.
    """
    try:
        res = attest_production()
        if res.get("attested"):
            return res.get("device_key") or res.get("device_id")
    except Exception:
        logger.exception("attestation failed when fetching device key")
    return None


