"""Kyber KEM wrapper with gated pyOQS usage and a safe emulator fallback.

Provides a small, consistent API for keygen/encapsulate/decapsulate. If
`pyOQS` (the Python OQS binding) is installed the wrapper will use it. If
not, an emulator that simulates the KEM behavior (INSECURE — for testing
only) is used.
"""
from __future__ import annotations

import ctypes
import hashlib
import logging
import os
from dataclasses import dataclass
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


@dataclass
class KeyPair:
    public: bytes
    private: bytes


class _OQSKEMStruct(ctypes.Structure):
    _fields_ = [
        ("method_name", ctypes.c_char_p),
        ("alg_version", ctypes.c_char_p),
        ("claimed_nist_level", ctypes.c_uint8),
        ("ind_cca", ctypes.c_bool),
        ("length_public_key", ctypes.c_size_t),
        ("length_secret_key", ctypes.c_size_t),
        ("length_ciphertext", ctypes.c_size_t),
        ("length_shared_secret", ctypes.c_size_t),
    ]


class KyberKEM:
    """Kyber KEM using liboqs C binding when available.

    Fallback order:
      1. liboqs C library via ctypes
      2. pyOQS Python bindings (if installed)
      3. insecure emulator (for tests/dev only)

    Usage:
        kem = KyberKEM("Kyber512")
        kp = kem.generate_keypair()
        ct, ss = kem.encapsulate(kp.public)
        ss2 = kem.decapsulate(kp.private, ct)
        assert ss == ss2
    """

    def __init__(self, algorithm: str = "Kyber512"):
        self.algorithm = algorithm
        self._backend = "emulator"
        self._lib = None
        self._kem_ptr = None
        # Try liboqs C binding via cffi first (more ABI-robust), then ctypes, then pyOQS, then emulator.
        try:
            self._try_cffi()
            self._backend = "liboqs-cffi"
        except Exception as exc:  # pragma: no cover - gated to system lib
            logger.debug("cffi liboqs loader failed or cffi not available: %s", exc)
            self._lib = None
            self._kem_ptr = None
            # Fallback to ctypes loader (older behavior)
            try:
                self._lib = self._load_liboqs()
                self._init_c_api()
                self._kem_ptr = self._lib.OQS_KEM_new(self.algorithm.encode("ascii"))
                if not self._kem_ptr:
                    raise RuntimeError("OQS_KEM_new returned NULL")
                self._kem = ctypes.cast(self._kem_ptr, ctypes.POINTER(_OQSKEMStruct))
                # sanity-check
                _ = int(self._kem.contents.length_public_key)
                self._backend = "liboqs-ctypes"
            except Exception as exc2:  # pragma: no cover - gated to system lib
                logger.debug("liboqs C library not available via ctypes: %s", exc2)
                self._lib = None
                self._kem_ptr = None
                # Try pyOQS next
                try:
                    import oqs  # type: ignore

                    self._oqs = oqs
                    self._backend = "oqs"
                except Exception:
                    self._oqs = None
                    self._backend = "emulator"
                    logger.debug("pyOQS not available; using Kyber emulator")

    def _load_liboqs(self) -> ctypes.CDLL:
        """Try to load the liboqs shared library from common locations."""
        candidates = [
            "liboqs.so",
            "liboqs.dylib",
            "/usr/local/lib/liboqs.dylib",
            "/opt/homebrew/lib/liboqs.dylib",
            "/usr/lib/liboqs.so",
        ]
        last_exc = None
        for c in candidates:
            try:
                lib = ctypes.CDLL(c)
                logger.debug("Loaded liboqs from %s", c)
                return lib
            except Exception as e:
                last_exc = e
        raise RuntimeError(f"Could not load liboqs: {last_exc}")

    def _try_cffi(self):
        """Attempt to load liboqs via cffi and prepare function bindings.

        This is more robust across platforms/ABI mismatches than raw ctypes
        because cffi can compile a small shim when necessary. If cffi is not
        available or loading fails we raise an exception and let callers fall
        back to ctypes or pyOQS.
        """
        try:
            from cffi import FFI
        except Exception as e:  # pragma: no cover - environment dependent
            raise RuntimeError("cffi not installed") from e

        ffi = FFI()
        # Minimal declarations we need from liboqs. These mirror the C API.
        ffi.cdef(
            """
            typedef unsigned char uint8_t;
            typedef unsigned long size_t;
            typedef unsigned char uint8_t;
            typedef struct OQS_KEM {
                const char *method_name;
                const char *alg_version;
                uint8_t claimed_nist_level;
                unsigned char ind_cca;
                size_t length_public_key;
                size_t length_secret_key;
                size_t length_ciphertext;
                size_t length_shared_secret;
            } OQS_KEM;

            OQS_KEM *OQS_KEM_new(const char *method_name);
            void OQS_KEM_free(OQS_KEM *kem);

            int OQS_KEM_keypair(const OQS_KEM *kem, uint8_t *public_key, uint8_t *secret_key);
            int OQS_KEM_encaps(const OQS_KEM *kem, uint8_t *ct, uint8_t *ss, const uint8_t *public_key);
            int OQS_KEM_decaps(const OQS_KEM *kem, uint8_t *ss, const uint8_t *ct, const uint8_t *secret_key);
            """
        )

        # Try to locate the shared library similar to ctypes loader
        candidates = [
            "liboqs.so",
            "liboqs.dylib",
            "/usr/local/lib/liboqs.dylib",
            "/opt/homebrew/lib/liboqs.dylib",
            "/usr/lib/liboqs.so",
        ]
        last_exc = None
        dl = None
        for c in candidates:
            try:
                dl = ffi.dlopen(c)
                logger.debug("cffi: loaded liboqs from %s", c)
                break
            except Exception as e:
                last_exc = e

        if dl is None:
            raise RuntimeError(f"cffi: could not dlopen liboqs: {last_exc}")

        # Create and store useful handles
        kem_ptr = dl.OQS_KEM_new(self.algorithm.encode("ascii"))
        if kem_ptr == ffi.NULL:
            raise RuntimeError("cffi: OQS_KEM_new returned NULL")

        # Cast to our struct to read lengths
        kem_struct = ffi.cast("OQS_KEM *", kem_ptr)
        try:
            pub_len = int(kem_struct.length_public_key)
            # sanity read to force access
            _ = pub_len
        except Exception as e:
            # If we cannot read expected fields, unwind and fail to let ctypes take over
            dl.OQS_KEM_free(kem_ptr)
            raise RuntimeError("cffi: failed to read OQS_KEM struct fields") from e

        # Save for later usage
        self._ffi = ffi
        self._lib = dl
        self._kem_ptr = kem_ptr
        self._kem = kem_struct

    def _init_c_api(self):
        """Declare argument and return types for the liboqs functions we use."""
        lib = self._lib
        # OQS_KEM *OQS_KEM_new(const char *method_name);
        lib.OQS_KEM_new.argtypes = [ctypes.c_char_p]
        lib.OQS_KEM_new.restype = ctypes.c_void_p
        # void OQS_KEM_free(OQS_KEM *kem);
        lib.OQS_KEM_free.argtypes = [ctypes.c_void_p]
        lib.OQS_KEM_free.restype = None
        # int OQS_KEM_keypair(const OQS_KEM *kem, uint8_t *public_key, uint8_t *secret_key);
        lib.OQS_KEM_keypair.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        lib.OQS_KEM_keypair.restype = ctypes.c_int
        # int OQS_KEM_encaps(const OQS_KEM *kem, uint8_t *ct, uint8_t *ss, const uint8_t *public_key);
        lib.OQS_KEM_encaps.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        lib.OQS_KEM_encaps.restype = ctypes.c_int
        # int OQS_KEM_decaps(const OQS_KEM *kem, uint8_t *ss, const uint8_t *ct, const uint8_t *secret_key);
        lib.OQS_KEM_decaps.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        lib.OQS_KEM_decaps.restype = ctypes.c_int

    def generate_keypair(self) -> KeyPair:
        # cffi-backed liboqs
        if getattr(self, "_ffi", None) is not None:
            ffi = self._ffi
            kem = self._kem
            pub_len = int(kem.length_public_key)
            sk_len = int(kem.length_secret_key)
            pub_buf = ffi.new(f"uint8_t[{pub_len}]")
            sk_buf = ffi.new(f"uint8_t[{sk_len}]")
            rc = self._lib.OQS_KEM_keypair(self._kem_ptr, pub_buf, sk_buf)
            if rc != 0:
                raise RuntimeError("OQS_KEM_keypair failed (cffi)")
            pub = bytes(ffi.buffer(pub_buf, pub_len))
            sk = bytes(ffi.buffer(sk_buf, sk_len))
            return KeyPair(public=pub, private=sk)
        # ctypes-backed liboqs
        if self._backend and self._backend.startswith("liboqs"):
            kem = self._kem.contents
            pub_len = int(kem.length_public_key)
            sk_len = int(kem.length_secret_key)
            pub_buf = (ctypes.c_ubyte * pub_len)()
            sk_buf = (ctypes.c_ubyte * sk_len)()
            rc = self._lib.OQS_KEM_keypair(self._kem_ptr, ctypes.byref(pub_buf), ctypes.byref(sk_buf))
            if rc != 0:
                raise RuntimeError("OQS_KEM_keypair failed")
            pub = bytes(bytearray(pub_buf))
            sk = bytes(bytearray(sk_buf))
            return KeyPair(public=pub, private=sk)
        if self._backend == "oqs":
            kem = self._oqs.KEM(self.algorithm)
            pub, priv = kem.generate_keypair()
            return KeyPair(public=pub, private=priv)
        # Emulator: deterministic-ish but insecure
        priv = os.urandom(32)
        pub = hashlib.sha256(priv).digest()
        return KeyPair(public=pub, private=priv)

    def encapsulate(self, public: bytes) -> Tuple[bytes, bytes]:
        """Return (ciphertext, shared_secret)."""
        # cffi-backed path
        if getattr(self, "_ffi", None) is not None:
            ffi = self._ffi
            kem = self._kem
            ct_len = int(kem.length_ciphertext)
            ss_len = int(kem.length_shared_secret)
            ct_buf = ffi.new(f"uint8_t[{ct_len}]")
            ss_buf = ffi.new(f"uint8_t[{ss_len}]")
            pub_buf = ffi.new(f"uint8_t[{len(public)}]", public)
            rc = self._lib.OQS_KEM_encaps(self._kem_ptr, ct_buf, ss_buf, pub_buf)
            if rc != 0:
                raise RuntimeError("OQS_KEM_encaps failed (cffi)")
            ct = bytes(ffi.buffer(ct_buf, ct_len))
            ss = bytes(ffi.buffer(ss_buf, ss_len))
            return ct, ss
        # ctypes-backed liboqs
        if self._backend and self._backend.startswith("liboqs"):
            kem = self._kem.contents
            ct_len = int(kem.length_ciphertext)
            ss_len = int(kem.length_shared_secret)
            ct_buf = (ctypes.c_ubyte * ct_len)()
            ss_buf = (ctypes.c_ubyte * ss_len)()
            pub_buf = (ctypes.c_ubyte * len(public)).from_buffer_copy(public)
            rc = self._lib.OQS_KEM_encaps(self._kem_ptr, ctypes.byref(ct_buf), ctypes.byref(ss_buf), ctypes.byref(pub_buf))
            if rc != 0:
                raise RuntimeError("OQS_KEM_encaps failed")
            ct = bytes(bytearray(ct_buf))
            ss = bytes(bytearray(ss_buf))
            return ct, ss
        if self._backend == "oqs":
            kem = self._oqs.KEM(self.algorithm)
            ct, ss = kem.encapsulate(public)
            return ct, ss
        # Emulator: ciphertext is random, shared secret derived deterministically
        ct = os.urandom(80)
        ss = hashlib.sha256(ct + public).digest()
        return ct, ss

    def decapsulate(self, private: bytes, ciphertext: bytes) -> bytes:
        # cffi-backed path
        if getattr(self, "_ffi", None) is not None:
            ffi = self._ffi
            kem = self._kem
            ss_len = int(kem.length_shared_secret)
            ss_buf = ffi.new(f"uint8_t[{ss_len}]")
            ct_buf = ffi.new(f"uint8_t[{len(ciphertext)}]", ciphertext)
            sk_buf = ffi.new(f"uint8_t[{len(private)}]", private)
            rc = self._lib.OQS_KEM_decaps(self._kem_ptr, ss_buf, ct_buf, sk_buf)
            if rc != 0:
                raise RuntimeError("OQS_KEM_decaps failed (cffi)")
            ss = bytes(ffi.buffer(ss_buf, ss_len))
            return ss
        # ctypes-backed liboqs
        if self._backend and self._backend.startswith("liboqs"):
            kem = self._kem.contents
            ss_len = int(kem.length_shared_secret)
            ss_buf = (ctypes.c_ubyte * ss_len)()
            ct_buf = (ctypes.c_ubyte * len(ciphertext)).from_buffer_copy(ciphertext)
            sk_buf = (ctypes.c_ubyte * len(private)).from_buffer_copy(private)
            rc = self._lib.OQS_KEM_decaps(self._kem_ptr, ctypes.byref(ss_buf), ctypes.byref(ct_buf), ctypes.byref(sk_buf))
            if rc != 0:
                raise RuntimeError("OQS_KEM_decaps failed")
            ss = bytes(bytearray(ss_buf))
            return ss
        if self._backend == "oqs":
            kem = self._oqs.KEM(self.algorithm)
            ss = kem.decapsulate(private, ciphertext)
            return ss
        # Emulator must derive same shared secret as encapsulate
        pub = hashlib.sha256(private).digest()
        ss = hashlib.sha256(ciphertext + pub).digest()
        return ss

    def __del__(self):
        try:
            # free via cffi if used
            if getattr(self, "_ffi", None) is not None and getattr(self, "_lib", None) is not None and getattr(self, "_kem_ptr", None) is not None:
                try:
                    self._lib.OQS_KEM_free(self._kem_ptr)
                except Exception:
                    pass
            elif self._lib and self._kem_ptr:
                try:
                    self._lib.OQS_KEM_free(self._kem_ptr)
                except Exception:
                    pass
        except Exception:
            pass


__all__ = ["KyberKEM", "KeyPair"]
