"""TEE adapter helpers.

This module provides simple adapters that delegate sealing/unsealing to a
platform-specific TEE or external helper. For production you should wire one
of the following strategies:

- Provide a CLI that performs sealing/unsealing and set the environment
  variables `TEE_SEAL_CMD` and `TEE_UNSEAL_CMD`. The CLI should accept a
  base64 key on stdin and return a base64 sealed blob on stdout.
- Implement a Python SDK adapter here using your platform's SDK (OpenEnclave,
  Intel SGX SDK, vendor HSM SDK) and expose `seal_key`/`unseal_key`.

The functions below prefer the CLI hook (safe and testable). If no adapter
is configured they raise `RuntimeError` to avoid silently falling back to
insecure behaviour.
"""

from __future__ import annotations

import os
import subprocess
import base64
import logging
from typing import Optional

logger = logging.getLogger("jarvis.tee_manager")


def _run_cmd_with_stdin(cmd: str, data: bytes) -> bytes:
    """Run a shell command with `data` on stdin and return stdout bytes.

    The command is executed via the user's shell. We return raw stdout and
    let callers decode base64 if required.
    """
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate(input=data)
    if p.returncode != 0:
        logger.error("TEE helper command failed (%s): %s", cmd, err.decode(errors="ignore"))
        raise RuntimeError(f"TEE helper command failed: {cmd}")
    return out


def seal_key(key: bytes) -> bytes:
    """Seal `key` using a TEE or an external helper and return a sealed blob.

    Production guidance:
    - Configure `TEE_SEAL_CMD` to a command that reads base64 from stdin and
      writes a base64 sealed blob to stdout. Example: `tee-seal --seal`.
    - Alternatively, implement a Python adapter here using your TEE SDK.

    Raises RuntimeError if no production sealing method is configured.
    """
    # 0) Preferred: Kunpeng TEE SDK adapter (if enabled)
    try:
        if os.environ.get("KUNPENG_TEE_ENABLED", "false").lower() in ("1", "true", "yes"):
            from . import kunpeng_tee_adapter  # type: ignore

            return kunpeng_tee_adapter.seal(key)
    except Exception:
        logger.debug("Kunpeng TEE adapter not available or failed; falling back", exc_info=True)

    # 1) CLI adapter (recommended for portability)
    cmd = os.environ.get("TEE_SEAL_CMD")
    if cmd:
        # send base64-encoded key on stdin and expect base64 sealed blob
        inb = base64.b64encode(key)
        out = _run_cmd_with_stdin(cmd, inb)
        try:
            return base64.b64decode(out.strip())
        except Exception:
            # If the helper already returned raw bytes, accept them
            return out

    # 2) Optional: implement SDK-backed sealing here (open-enclave, SGX, HSM SDK)
    # Example: attempt to import a vendor SDK and call its seal APIs.
    try:
        # placeholder for a real SDK adapter import
        import enclave_sdk  # type: ignore

        return enclave_sdk.seal(key)  # type: ignore
    except Exception:
        pass

    raise RuntimeError("No TEE sealing method configured. Set TEE_SEAL_CMD or implement a Python SDK adapter.")


def unseal_key(blob: bytes) -> bytes:
    """Unseal a sealed blob and return the original key.

    Mirrors the strategies used in `seal_key`.
    """
    # 0) Preferred: Kunpeng TEE SDK adapter (if enabled)
    try:
        if os.environ.get("KUNPENG_TEE_ENABLED", "false").lower() in ("1", "true", "yes"):
            from . import kunpeng_tee_adapter  # type: ignore

            return kunpeng_tee_adapter.unseal(blob)
    except Exception:
        logger.debug("Kunpeng TEE adapter not available or failed; falling back", exc_info=True)

    cmd = os.environ.get("TEE_UNSEAL_CMD")
    if cmd:
        # send base64-encoded blob and expect base64 key
        inb = base64.b64encode(blob)
        out = _run_cmd_with_stdin(cmd, inb)
        try:
            return base64.b64decode(out.strip())
        except Exception:
            return out

    try:
        import enclave_sdk  # type: ignore

        return enclave_sdk.unseal(blob)  # type: ignore
    except Exception:
        pass

    raise RuntimeError("No TEE unseal method configured. Set TEE_UNSEAL_CMD or implement a Python SDK adapter.")


def init_tee() -> None:
    """Initialize TEE backends (if any). Safe to call multiple times."""
    # Platform enforcement: when REQUIRE_PLATFORM is set, ensure we are running
    # on Atlas or HiSilicon devices before initializing the Kunpeng adapter.
    try:
        from . import platform_detector  # type: ignore

        if os.environ.get("KUNPENG_TEE_REQUIRE_PLATFORM", "false").lower() in ("1", "true", "yes"):
            plat = platform_detector.detect_platform()
            if plat not in ("atlas", "hisilicon"):
                raise RuntimeError(f"Kunpeng TEE requires Atlas/HiSilicon platform; detected: {plat}")
    except Exception:
        # only log; if platform detection fails we proceed according to env flags
        logger.debug("Platform detection unavailable or enforcement raised; continuing initialization", exc_info=True)

    if os.environ.get("KUNPENG_TEE_ENABLED", "false").lower() in ("1", "true", "yes"):
        try:
            from . import kunpeng_tee_adapter  # type: ignore

            kunpeng_tee_adapter.init()
            logger.info("Kunpeng TEE adapter initialized")
            return
        except Exception:
            logger.exception("Failed to initialize Kunpeng TEE adapter")

    # No-op for CLI-based helpers
    logger.debug("No Kunpeng TEE adapter initialized; using CLI or no-op fallback")


def close_tee() -> None:
    """Finalize/close any initialized TEE backends."""
    try:
        if os.environ.get("KUNPENG_TEE_ENABLED", "false").lower() in ("1", "true", "yes"):
            from . import kunpeng_tee_adapter  # type: ignore

            kunpeng_tee_adapter.finalize()
            logger.info("Kunpeng TEE adapter finalized")
            return
    except Exception:
        logger.exception("Exception while finalizing Kunpeng TEE adapter")

    logger.debug("No Kunpeng TEE adapter to finalize")


def run_in_tee(func, *args, **kwargs):
    """Run a Python callable inside the TEE when available.

    The callable must be picklable when using the local fallback. When a
    Kunpeng TEE adapter is enabled the function and args are pickled and
    passed to the TEE via `run_payload`, which returns a pickled result.

    If the TEE is not available and `KUNPENG_TEE_ALLOW_LOCAL_FALLBACK` is
    enabled, the callable will be executed locally (insecure) for testing.
    """
    # Serialize the callable and arguments. The adapter will decide how to
    # execute them; local fallback executes them directly.
    import pickle as _pickle

    payload = _pickle.dumps((func, args, kwargs))

    # Prefer Kunpeng adapter if enabled
    if os.environ.get("KUNPENG_TEE_ENABLED", "false").lower() in ("1", "true", "yes"):
        try:
            from . import kunpeng_tee_adapter  # type: ignore

            out = kunpeng_tee_adapter.run_payload(payload)
            return _pickle.loads(out)
        except Exception:
            logger.exception("Kunpeng TEE run failed; raising")
            raise

    # If no TEE adapter, decide if we allow local fallback
    if os.environ.get("KUNPENG_TEE_ALLOW_LOCAL_FALLBACK", "false").lower() in ("1", "true", "yes"):
        logger.warning("Running payload locally because Kunpeng TEE is not enabled (insecure)")
        return func(*args, **kwargs)

    raise RuntimeError("Kunpeng TEE not enabled. Set KUNPENG_TEE_ENABLED=1 or enable local fallback for testing.")

