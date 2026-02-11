"""Adapter for Huawei Kunpeng TEE SDK (guarded).

This module attempts to expose a minimal adapter for Kunpeng TEE (TAE)
integrations. It probes for a Python SDK (common names tried) or a
native library provided via `KUNPENG_TEE_LIB` and falls back to a
safe no-op adapter unless `KUNPENG_TEE_REQUIRED` is set.

API provided:
- init() -> None
- finalize() -> None
- seal(data: bytes) -> bytes
- unseal(blob: bytes) -> bytes
- run_payload(payload: bytes) -> bytes

Notes:
- The real TEE SDK APIs vary by vendor and version. This adapter uses
  runtime probing to call the available functions. If you have a specific
  SDK, provide its Python package name in `KUNPENG_TEE_PYSDK` or set
  `KUNPENG_TEE_LIB` to the path of a native shared library exposing the
  expected symbols (init/finalize/seal/unseal/run).
"""

from __future__ import annotations

import os
import logging
import pickle
from typing import Optional

logger = logging.getLogger("jarvis.kunpeng_tee_adapter")


class _NoopAdapter:
    """Fallback adapter when no Kunpeng TEE SDK is available.

    By default this adapter raises on seal/unseal to avoid silent
    insecure behavior. If `KUNPENG_TEE_ALLOW_LOCAL_FALLBACK` is set to a
    truthy value, it will perform local (insecure) operations.
    """

    def __init__(self):
        self.allow_local = os.environ.get("KUNPENG_TEE_ALLOW_LOCAL_FALLBACK", "false").lower() in (
            "1",
            "true",
            "yes",
        )

    def init(self) -> None:
        logger.debug("Kunpeng TEE noop adapter init")

    def finalize(self) -> None:
        logger.debug("Kunpeng TEE noop adapter finalize")

    def seal(self, data: bytes) -> bytes:
        if self.allow_local:
            logger.warning("Kunpeng TEE not available: performing local (insecure) seal")
            return pickle.dumps(data)
        raise RuntimeError("Kunpeng TEE SDK not available and local fallback disabled")

    def unseal(self, blob: bytes) -> bytes:
        if self.allow_local:
            logger.warning("Kunpeng TEE not available: performing local (insecure) unseal")
            return pickle.loads(blob)
        raise RuntimeError("Kunpeng TEE SDK not available and local fallback disabled")

    def run_payload(self, payload: bytes) -> bytes:
        # local fallback: unpickle a tuple(func, args, kwargs) and run it.
        if self.allow_local:
            logger.warning("Kunpeng TEE not available: running payload locally (insecure)")
            try:
                fn, args, kwargs = pickle.loads(payload)
                return pickle.dumps(fn(*args, **kwargs))
            except Exception as e:
                logger.exception("Local payload execution failed: %s", e)
                raise
        raise RuntimeError("Kunpeng TEE SDK not available and local fallback disabled")


def _probe_python_sdk() -> Optional[object]:
    """Try to import common Python SDK wrappers for Kunpeng TEE.

    Returns the imported module object or None.
    """
    candidates = [
        os.environ.get("KUNPENG_TEE_PYSDK"),
        "kunpeng_tae",
        "kunpeng_tee",
        "huaweitee",
        "tae_sdk",
    ]
    for name in filter(None, candidates):
        try:
            mod = __import__(name)
            logger.info("Found Kunpeng TEE Python SDK: %s", name)
            return mod
        except Exception:
            logger.debug("Kunpeng TEE SDK candidate not importable: %s", name, exc_info=True)
    return None


def _probe_native_lib(path: str):
    """Attempt to load a native shared lib and wrap expected symbols.

    This function is intentionally conservative: it only attempts to
    load if the env var is explicitly set. We use ctypes to avoid
    coupling to any particular packaging.
    """
    try:
        import ctypes

        lib = ctypes.CDLL(path)
        logger.info("Loaded Kunpeng TEE native lib: %s", path)
        return lib
    except Exception:
        logger.exception("Failed to load Kunpeng TEE native lib: %s", path)
        return None


def _make_adapter():
    # 0) If platform detection is enabled and we are not on Atlas/HiSilicon,
    #    prefer not to enable Kunpeng TEE implicitly. Users can override with
    #    KUNPENG_TEE_ENABLED.
    try:
        from . import platform_detector  # type: ignore

        # If platform_detector says unknown and the adapter isn't explicitly
        # enabled, fall back to noop adapter.
        if not (os.environ.get("KUNPENG_TEE_ENABLED", "").lower() in ("1", "true", "yes")):
            if platform_detector.detect_platform() == "unknown":
                logger.info("Platform not Atlas/HiSilicon; Kunpeng TEE adapter not enabled by default")
                return _NoopAdapter()
    except Exception:
        # If platform detection fails, proceed with normal probing.
        logger.debug("Platform detector not available; continuing SDK probe")

    # 1) try Python SDK
    py = _probe_python_sdk()
    if py is not None:
        # Wrap expected API surface. We don't know exact names, so probe common ones.
        class PyAdapter:
            def init(self):
                for n in ("init", "initialize", "tae_init"):
                    if hasattr(py, n):
                        getattr(py, n)()
                        return

            def finalize(self):
                for n in ("finalize", "shutdown", "tae_finalize"):
                    if hasattr(py, n):
                        getattr(py, n)()
                        return

            def seal(self, data: bytes) -> bytes:
                for n in ("seal", "seal_data", "encrypt_seal"):
                    if hasattr(py, n):
                        return getattr(py, n)(data)
                raise RuntimeError("Python Kunpeng TEE SDK present but seal API not found")

            def unseal(self, blob: bytes) -> bytes:
                for n in ("unseal", "unseal_data", "decrypt_unseal"):
                    if hasattr(py, n):
                        return getattr(py, n)(blob)
                raise RuntimeError("Python Kunpeng TEE SDK present but unseal API not found")

            def run_payload(self, payload: bytes) -> bytes:
                for n in ("run", "run_payload", "invoke"):
                    if hasattr(py, n):
                        return getattr(py, n)(payload)
                raise RuntimeError("Python Kunpeng TEE SDK present but run API not found")

        return PyAdapter()

    # 2) try native lib path from env
    libpath = os.environ.get("KUNPENG_TEE_LIB")
    if libpath:
        lib = _probe_native_lib(libpath)
        if lib is not None:
            class NativeAdapter:
                def init(self):
                    for sym in ("init", "tae_init"):
                        if hasattr(lib, sym):
                            getattr(lib, sym)()
                            return

                def finalize(self):
                    for sym in ("finalize", "tae_finalize"):
                        if hasattr(lib, sym):
                            getattr(lib, sym)()
                            return

                def seal(self, data: bytes) -> bytes:
                    # native symbol conventions vary; we expect a function that
                    # accepts (char* in, size_t in_len, char** out, size_t* out_len)
                    # This is best-effort and may need adapting.
                    if hasattr(lib, "seal"):
                        fn = getattr(lib, "seal")
                        fn.restype = ctypes.POINTER(ctypes.c_ubyte)
                        # Not implementing full marshalling here; raise to indicate
                        raise RuntimeError("Native Kunpeng TEE 'seal' exists but adapter marshalling is not implemented in this scaffold")
                    raise RuntimeError("Native Kunpeng TEE library loaded but 'seal' symbol not found")

                def unseal(self, blob: bytes) -> bytes:
                    raise RuntimeError("Native unseal marshalling not implemented in scaffold")

                def run_payload(self, payload: bytes) -> bytes:
                    raise RuntimeError("Native run_payload marshalling not implemented in scaffold")

            return NativeAdapter()

    # 3) fallback noop adapter
    return _NoopAdapter()


# create singleton adapter on import
_adapter = _make_adapter()


def init() -> None:
    _adapter.init()


def finalize() -> None:
    _adapter.finalize()


def seal(data: bytes) -> bytes:
    return _adapter.seal(data)


def unseal(blob: bytes) -> bytes:
    return _adapter.unseal(blob)


def run_payload(payload: bytes) -> bytes:
    return _adapter.run_payload(payload)
