"""Dilithium signature wrapper with gated pyOQS usage and emulator fallback.

Provides a minimal sign/verify API. The emulator is INSECURE and only for
local tests where real PQ libs are not available.
"""
from __future__ import annotations

import ctypes
import hashlib
import logging
import os
from dataclasses import dataclass
from typing import Tuple

logger = logging.getLogger(__name__)


@dataclass
class SignKeyPair:
    public: bytes
    private: bytes


class _OQSSigStruct(ctypes.Structure):
    _fields_ = [
        ("method_name", ctypes.c_char_p),
        ("alg_version", ctypes.c_char_p),
        ("claimed_nist_level", ctypes.c_uint8),
        ("length_public_key", ctypes.c_size_t),
        ("length_secret_key", ctypes.c_size_t),
        ("length_signature", ctypes.c_size_t),
    ]


class DilithiumSigner:
    """Dilithium signer using liboqs C binding when available.

    Falls back to pyOQS Python binding, then to an insecure emulator.
    """

    def __init__(self, algorithm: str = "Dilithium2"):
        self.algorithm = algorithm
        self._backend = "emulator"
        self._lib = None
        self._sig_ptr = None
        try:
            # try loading liboqs C shared library
            candidates = [
                "liboqs.so",
                "liboqs.dylib",
                "/usr/local/lib/liboqs.dylib",
                "/opt/homebrew/lib/liboqs.dylib",
                "/usr/lib/liboqs.so",
            ]
            lib = None
            for c in candidates:
                try:
                    lib = ctypes.CDLL(c)
                    logger.debug("Loaded liboqs from %s", c)
                    break
                except Exception:
                    lib = None
            if lib is not None:
                self._lib = lib
                # init function prototypes
                lib.OQS_SIG_new.argtypes = [ctypes.c_char_p]
                lib.OQS_SIG_new.restype = ctypes.c_void_p
                lib.OQS_SIG_free.argtypes = [ctypes.c_void_p]
                lib.OQS_SIG_free.restype = None
                lib.OQS_SIG_keypair.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
                lib.OQS_SIG_keypair.restype = ctypes.c_int
                lib.OQS_SIG_sign.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p]
                lib.OQS_SIG_sign.restype = ctypes.c_int
                lib.OQS_SIG_verify.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p]
                lib.OQS_SIG_verify.restype = ctypes.c_int
                self._sig_ptr = lib.OQS_SIG_new(self.algorithm.encode("ascii"))
                if not self._sig_ptr:
                    raise RuntimeError("OQS_SIG_new returned NULL")
                self._sig = ctypes.cast(self._sig_ptr, ctypes.POINTER(_OQSSigStruct))
                _ = int(self._sig.contents.length_public_key)
                self._backend = "liboqs"
        except Exception as exc:  # pragma: no cover - gated
            logger.debug("liboqs C binding not available: %s", exc)
            self._lib = None
            self._sig_ptr = None
            try:
                import oqs  # type: ignore

                self._oqs = oqs
                self._backend = "oqs"
            except Exception:
                self._oqs = None
                self._backend = "emulator"
                logger.debug("pyOQS not available; using Dilithium emulator")

    def generate_keypair(self) -> SignKeyPair:
        if self._backend == "liboqs":
            sig = self._sig.contents
            pk_len = int(sig.length_public_key)
            sk_len = int(sig.length_secret_key)
            pk_buf = (ctypes.c_ubyte * pk_len)()
            sk_buf = (ctypes.c_ubyte * sk_len)()
            rc = self._lib.OQS_SIG_keypair(self._sig_ptr, ctypes.byref(pk_buf), ctypes.byref(sk_buf))
            if rc != 0:
                raise RuntimeError("OQS_SIG_keypair failed")
            pk = bytes(bytearray(pk_buf))
            sk = bytes(bytearray(sk_buf))
            return SignKeyPair(public=pk, private=sk)
        if self._backend == "oqs":
            sign = self._oqs.Sign(self.algorithm)
            pub, priv = sign.generate_keypair()
            return SignKeyPair(public=pub, private=priv)
        # Emulator: make public == private for easy verify (INSECURE)
        sk = os.urandom(32)
        pk = sk
        return SignKeyPair(public=pk, private=sk)

    def sign(self, private: bytes, message: bytes) -> bytes:
        if self._backend == "liboqs":
            sig = self._sig.contents
            sig_len = int(sig.length_signature)
            sig_buf = (ctypes.c_ubyte * sig_len)()
            sig_len_c = ctypes.c_size_t(sig_len)
            msg_buf = (ctypes.c_ubyte * len(message)).from_buffer_copy(message)
            sk_buf = (ctypes.c_ubyte * len(private)).from_buffer_copy(private)
            rc = self._lib.OQS_SIG_sign(self._sig_ptr, ctypes.byref(sig_buf), ctypes.byref(sig_len_c), ctypes.byref(msg_buf), ctypes.c_size_t(len(message)), ctypes.byref(sk_buf))
            if rc != 0:
                raise RuntimeError("OQS_SIG_sign failed")
            return bytes(bytearray(sig_buf))[:sig_len_c.value]
        if self._backend == "oqs":
            sign = self._oqs.Sign(self.algorithm)
            return sign.sign(message, private)
        # Emulator: naive digest-based signature (INSECURE)
        return hashlib.sha256(private + message).digest()

    def verify(self, public: bytes, message: bytes, signature: bytes) -> bool:
        if self._backend == "liboqs":
            msg_buf = (ctypes.c_ubyte * len(message)).from_buffer_copy(message)
            sig_buf = (ctypes.c_ubyte * len(signature)).from_buffer_copy(signature)
            pk_buf = (ctypes.c_ubyte * len(public)).from_buffer_copy(public)
            rc = self._lib.OQS_SIG_verify(self._sig_ptr, ctypes.byref(msg_buf), ctypes.c_size_t(len(message)), ctypes.byref(sig_buf), ctypes.c_size_t(len(signature)), ctypes.byref(pk_buf))
            return rc == 0
        if self._backend == "oqs":
            sign = self._oqs.Sign(self.algorithm)
            return sign.verify(message, signature, public)
        expected = hashlib.sha256(public + message).digest()
        return expected == signature

    def __del__(self):
        try:
            if self._lib and self._sig_ptr:
                self._lib.OQS_SIG_free(self._sig_ptr)
        except Exception:
            pass


__all__ = ["DilithiumSigner", "SignKeyPair"]
