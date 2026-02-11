"""Homomorphic-layer adapter with optional SEAL/Pyfhel and PALISADE support.

This module exposes a small, stable surface used by the federation and
ledger code: an object that can encrypt numeric model data, perform a
homomorphic addition of ciphertexts, and decrypt results. For practical
development we provide three modes:

- "pyfhel": Use the Pyfhel wrapper around Microsoft SEAL (CKKS scheme).
- "palisade": Placeholder scaffold for PALISADE bindings (not implemented).
- "emulated": Deterministic, dependency-free serializer used for CI and
  environments without HE libraries.

The CKKS implementation encrypts vectors of floats (suitable for model
weights). The API serializes ciphertexts to bytes so they can be transported
or stored in the ledger.
"""

from typing import Any, Dict, List, Optional, Sequence
import json
import struct
import tempfile
import os
import ctypes

HAS_PYFHEL = False
try:
    # Pyfhel provides a friendly Python wrapper over SEAL (CKKS/BFV)
    from Pyfhel import Pyfhel, PyCtxt  # type: ignore
    HAS_PYFHEL = True
except Exception:
    HAS_PYFHEL = False


class HomomorphicLayer:
    """Adapter that supports emulated and Pyfhel (SEAL) backends.

    Args:
        backend: one of 'emulated'|'pyfhel'|'palisade'
        ckks_scale: scale to use for CKKS (only for pyfhel backend)
    """

    def __init__(self, backend: str = "emulated", ckks_scale: float = 2 ** 40) -> None:
        backend = backend or "emulated"
        if backend not in ("emulated", "pyfhel", "palisade"):
            raise ValueError("unsupported backend")
        if backend == "pyfhel" and not HAS_PYFHEL:
            raise RuntimeError("Pyfhel (SEAL) backend requested but Pyfhel is not installed")

        self.backend = backend
        self._ckks_scale = ckks_scale

        # Pyfhel context and key objects (when used)
        self._pyfhel: Optional[Pyfhel] = None
        if self.backend == "pyfhel":
            self._init_pyfhel()

    # ---------------------- Pyfhel (SEAL) implementation ------------------
    def _init_pyfhel(self) -> None:
        assert HAS_PYFHEL
        self._pyfhel = Pyfhel()
        # CKKS params: n=2^14 or 2^15 depending on precision requirements
        self._pyfhel.contextGen(scheme="CKKS", n=2 ** 14, scale=self._ckks_scale)
        self._pyfhel.keyGen()
        # Generate relinearization & rotation keys only if needed in future

    def pyfhel_encrypt_vector(self, values: Sequence[float]) -> bytes:
        """Encrypt a vector of floats with CKKS and return serialized bytes."""
        assert self._pyfhel is not None
        ctxt: PyCtxt = self._pyfhel.encryptFrac(values)
        return ctxt.to_bytes()

    def pyfhel_decrypt_vector(self, ctxt_bytes: bytes) -> List[float]:
        assert self._pyfhel is not None
        ctxt = PyCtxt(pyfhel=self._pyfhel, bytestring=ctxt_bytes)
        return self._pyfhel.decryptFrac(ctxt)

    def pyfhel_add(self, a_bytes: bytes, b_bytes: bytes) -> bytes:
        assert self._pyfhel is not None
        a = PyCtxt(pyfhel=self._pyfhel, bytestring=a_bytes)
        b = PyCtxt(pyfhel=self._pyfhel, bytestring=b_bytes)
        c = a + b
        return c.to_bytes()

    # ---------------------- Pyfhel key serialization --------------------
    def export_keys(self) -> Dict[str, bytes]:
        """Export the Pyfhel context and keys as raw bytes.

        Returns a dict with keys: 'context', 'public_key', 'secret_key'.
        These bytes can be transported to other parties and re-imported with
        :meth:`from_keys` to create a compatible Pyfhel instance.
        """
        if self.backend != "pyfhel":
            raise RuntimeError("export_keys is only available for pyfhel backend")
        assert self._pyfhel is not None
        py = self._pyfhel

        def _get_bytes(to_bytes_name: str, save_name: str) -> bytes:
            # Prefer to_bytes_* API when available, otherwise fall back to
            # saving to a temp file and reading the bytes back.
            fn = getattr(py, to_bytes_name, None)
            if callable(fn):
                try:
                    return fn()
                except Exception:
                    pass

            # fallback via file save
            save_fn = getattr(py, save_name, None)
            if callable(save_fn):
                tmp = tempfile.NamedTemporaryFile(delete=False)
                tmp_path = tmp.name
                tmp.close()
                save_fn(tmp_path)
                try:
                    data = open(tmp_path, "rb").read()
                finally:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
                return data

            raise NotImplementedError(f"Pyfhel does not expose {to_bytes_name} or {save_name}")

        return {
            "context": _get_bytes("to_bytes_context", "save_context"),
            "public_key": _get_bytes("to_bytes_public_key", "save_public_key"),
            "secret_key": _get_bytes("to_bytes_secret_key", "save_secret_key"),
        }

    @classmethod
    def from_keys(cls, keys: Dict[str, bytes], ckks_scale: float = 2 ** 40) -> "HomomorphicLayer":
        """Construct a Pyfhel-backed HomomorphicLayer from serialized keys.

        The `keys` dict must contain the byte values returned by :meth:`export_keys`.
        """
        if not HAS_PYFHEL:
            raise RuntimeError("Pyfhel not installed")

        # Create layer and replace the internal pyro instance
        inst = cls(backend="pyfhel", ckks_scale=ckks_scale)
        py = inst._pyfhel
        assert py is not None

        def _load_bytes(from_bytes_name: str, load_name: str, data: bytes) -> None:
            fn = getattr(py, from_bytes_name, None)
            if callable(fn):
                try:
                    fn(data)
                    return
                except Exception:
                    pass

            # fallback: write to temp file and call a file-based loader
            tmp = tempfile.NamedTemporaryFile(delete=False)
            tmp_path = tmp.name
            tmp.close()
            try:
                open(tmp_path, "wb").write(data)
                load_fn = getattr(py, load_name, None)
                if callable(load_fn):
                    load_fn(tmp_path)
                    return
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

            raise NotImplementedError(f"Pyfhel does not expose {from_bytes_name} or {load_name}")

        _load_bytes("from_bytes_context", "contextLoad", keys["context"])
        _load_bytes("from_bytes_public_key", "publicKeyLoad", keys["public_key"])
        _load_bytes("from_bytes_secret_key", "secretKeyLoad", keys["secret_key"])

        return inst

    # ---------------------- PALISADE scaffold ------------------------------
    def _palisade_notimpl(self, *args, **kwargs):
        raise NotImplementedError("PALISADE backend is not implemented in Python; please integrate native bindings or use Pyfhel/SEAL")

    # ---------------------- PALISADE ctypes scaffold ---------------------
    class _PalisadeLib:
        """Lightweight loader for a PALISADE C library exposing a small C API.

        This class attempts to load a shared library (path provided by the
        PALISADE_LIB_PATH environment variable or explicit path) and wraps a
        minimal C API. The actual PALISADE project does not ship a stable
        C ABI by default; this scaffold requires a custom C wrapper that
        exposes `palisade_encrypt`, `palisade_add`, `palisade_decrypt` symbols
        with the ABI documented below.

        ABI expectations (example):
          // allocate result and return 0 on success
          int palisade_encrypt(const uint8_t* in, size_t in_len, uint8_t** out, size_t* out_len);
          int palisade_add(const uint8_t* a, size_t a_len, const uint8_t* b, size_t b_len, uint8_t** out, size_t* out_len);
          int palisade_decrypt(const uint8_t* in, size_t in_len, uint8_t** out, size_t* out_len);

        If your PALISADE build exposes these symbols, set PALISADE_LIB_PATH to
        the shared library path and this wrapper will call through to it.
        """

        def __init__(self, path: Optional[str] = None):
            path = path or os.environ.get("PALISADE_LIB_PATH")
            if not path:
                raise RuntimeError("PALISADE_LIB_PATH not set and no path provided")
            self._lib = ctypes.CDLL(path)

            # helper to wrap functions that return (int) status and produce
            # an allocated output buffer via out pointer/length.
            def _wrap_fn(name):
                fn = getattr(self._lib, name)
                fn.restype = ctypes.c_int
                fn.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                               ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)), ctypes.POINTER(ctypes.c_size_t)]
                return fn

            try:
                self._encrypt = _wrap_fn("palisade_encrypt")
                # palisade_add expected different signature (two inputs)
                add_fn = getattr(self._lib, "palisade_add")
                add_fn.restype = ctypes.c_int
                add_fn.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                                    ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                                    ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)), ctypes.POINTER(ctypes.c_size_t)]
                self._add = add_fn
                self._decrypt = _wrap_fn("palisade_decrypt")
            except AttributeError as ex:
                raise RuntimeError(f"PALISADE library missing expected symbols: {ex}")

        def _call_allocating(self, fn, data: bytes, extra: Optional[bytes] = None) -> bytes:
            # prepare input buffer(s)
            buf = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            out_pp = ctypes.POINTER(ctypes.c_uint8)()
            out_len = ctypes.c_size_t(0)
            if extra is None:
                status = fn(buf, ctypes.c_size_t(len(data)), ctypes.byref(out_pp), ctypes.byref(out_len))
            else:
                # extra is second input (for add)
                extra_buf = (ctypes.c_uint8 * len(extra)).from_buffer_copy(extra)
                status = fn(buf, ctypes.c_size_t(len(data)), extra_buf, ctypes.c_size_t(len(extra)), ctypes.byref(out_pp), ctypes.byref(out_len))

            if status != 0:
                raise RuntimeError(f"PALISADE call failed with status {status}")

            # copy result bytes
            out_len_val = int(out_len.value)
            out_buf = ctypes.cast(out_pp, ctypes.POINTER(ctypes.c_uint8 * out_len_val)).contents
            data_out = bytes(bytearray(out_buf))
            # assume library allocated with malloc; free symbol optional
            free_fn = getattr(self._lib, "palisade_free", None)
            if free_fn is not None:
                free_fn.argtypes = [ctypes.POINTER(ctypes.c_uint8)]
                free_fn(out_pp)
            return data_out

        def encrypt(self, data: bytes) -> bytes:
            return self._call_allocating(self._encrypt, data)

        def add(self, a: bytes, b: bytes) -> bytes:
            return self._call_allocating(self._add, a, extra=b)

        def decrypt(self, data: bytes) -> bytes:
            return self._call_allocating(self._decrypt, data)


    # ---------------------- Emulated fallback -----------------------------
    def _encode_emulated(self, values: Sequence[float]) -> bytes:
        # deterministic JSON serialization of vector of floats
        return json.dumps(list(values), separators=(",", ":")).encode("utf-8")

    def _decode_emulated(self, blob: bytes) -> List[float]:
        return json.loads(blob.decode("utf-8"))

    # ---------------------- Public API -----------------------------------
    def encrypt_vector(self, values: Sequence[float]) -> bytes:
        """Encrypt a vector of floats and return an opaque ciphertext blob.

        The returned type is bytes so it can be stored/transported in the
        ledger. For the emulated backend this is a JSON-serialized vector.
        For Pyfhel it is the native ciphertext bytes from SEAL.
        """
        if self.backend == "emulated":
            return self._encode_emulated(values)
        if self.backend == "pyfhel":
            return self.pyfhel_encrypt_vector(values)
        return self._palisade_notimpl(values)

    def add(self, ctxt_a: bytes, ctxt_b: bytes) -> bytes:
        """Homomorphically add two ciphertext blobs and return a new blob."""
        if self.backend == "emulated":
            a = self._decode_emulated(ctxt_a)
            b = self._decode_emulated(ctxt_b)
            if len(a) != len(b):
                raise ValueError("vector length mismatch")
            return self._encode_emulated([x + y for x, y in zip(a, b)])
        if self.backend == "pyfhel":
            return self.pyfhel_add(ctxt_a, ctxt_b)
        return self._palisade_notimpl(ctxt_a, ctxt_b)

    def decrypt_vector(self, ctxt: bytes) -> List[float]:
        """Decrypt a ciphertext blob and return the clear vector of floats."""
        if self.backend == "emulated":
            return self._decode_emulated(ctxt)
        if self.backend == "pyfhel":
            return self.pyfhel_decrypt_vector(ctxt)
        return self._palisade_notimpl(ctxt)

    # Convenience single-value helpers (for small integers / scalars)
    def encrypt(self, value: float) -> bytes:
        return self.encrypt_vector([float(value)])

    def decrypt(self, ctxt: bytes) -> float:
        v = self.decrypt_vector(ctxt)
        return float(v[0])

