"""TPM client helpers: emulator + detection scaffolds.

This module is a clean, single-copy TPM helper used by unit tests and the
voice-auth stack. It intentionally provides a SimpleTPMEmulator for testing,
and lightweight detection stubs for real TPM bindings/CLI tools.
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import threading
from typing import Optional, Protocol

try:
    import tpm2_pytss  # type: ignore
    HAS_PYTSS = True
except Exception:
    HAS_PYTSS = False

try:
    from cryptography.hazmat.primitives import hashes  # type: ignore
    from cryptography.hazmat.primitives.asymmetric import padding, rsa  # type: ignore
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
    HAS_CRYPTO = True
except Exception:
    HAS_CRYPTO = False


class TPMClientInterface(Protocol):
    def seal(self, data: bytes) -> bytes: ...

    def unseal(self, blob: bytes) -> bytes: ...

    def sign(self, data: bytes) -> bytes: ...

    def verify(self, data: bytes, signature: bytes, pubkey_pem: Optional[bytes] = None) -> bool: ...


class SimpleTPMEmulator:
    def __init__(self) -> None:
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography is required for the TPM emulator")
        self._lock = threading.RLock()
        self._aes_key = AESGCM.generate_key(bit_length=256)
        self._rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def seal(self, data: bytes) -> bytes:
        with self._lock:
            aesgcm = AESGCM(self._aes_key)
            nonce = os.urandom(12)
            ct = aesgcm.encrypt(nonce, data, None)
            payload = {"nonce": base64.b64encode(nonce).decode(), "ct": base64.b64encode(ct).decode()}
            return json.dumps(payload).encode()

    def unseal(self, blob: bytes) -> bytes:
        with self._lock:
            payload = json.loads(blob.decode())
            nonce = base64.b64decode(payload["nonce"])
            ct = base64.b64decode(payload["ct"])
            aesgcm = AESGCM(self._aes_key)
            return aesgcm.decrypt(nonce, ct, None)

    def sign(self, data: bytes) -> bytes:
        with self._lock:
            return self._rsa_key.sign(data, padding.PKCS1v15(), hashes.SHA256())

    def verify(self, data: bytes, signature: bytes, pubkey_pem: Optional[bytes] = None) -> bool:
        with self._lock:
            pub = self._rsa_key.public_key()
            try:
                pub.verify(signature, data, padding.PKCS1v15(), hashes.SHA256())
                return True
            except Exception:
                return False


class Tpm2ToolsClient:
    def __init__(self) -> None:
        required = ["tpm2_create", "tpm2_load", "tpm2_unseal", "tpm2_sign"]
        for cmd in required:
            if shutil.which(cmd) is None:
                raise FileNotFoundError("tpm2-tools not found")

    def seal(self, data: bytes) -> bytes:
        """Seal arbitrary bytes using the system `tpm2-tools`.

        The implementation uses an ephemeral primary key and creates a sealed
        object. The returned bytes are an opaque tarball containing the
        artifacts required to unseal on the same TPM (primary context, public
        and private blobs). This keeps the wrapper free of persistent
        handle management and is intended for portability; callers should
        treat the returned bytes as opaque.
        """
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            data_path = os.path.join(td, "data.bin")
            with open(data_path, "wb") as f:
                f.write(data)

            prim_ctx = os.path.join(td, "prim.ctx")
            pub = os.path.join(td, "key.pub")
            priv = os.path.join(td, "key.priv")

            # Create a primary key (owner hierarchy)
            subprocess.run(["tpm2_createprimary", "-C", "o", "-g", "sha256", "-G", "rsa", "-c", prim_ctx], check=True)

            # Create a sealed object under the primary key using the input file
            subprocess.run(["tpm2_create", "-C", prim_ctx, "-i", data_path, "-u", pub, "-r", priv], check=True)

            # Package the files into a single blob to return
            import tarfile, io

            buf = io.BytesIO()
            with tarfile.open(fileobj=buf, mode="w:gz") as tar:
                tar.add(prim_ctx, arcname="prim.ctx")
                tar.add(pub, arcname="key.pub")
                tar.add(priv, arcname="key.priv")
            return buf.getvalue()

    def unseal(self, blob: bytes) -> bytes:
        """Unseal a blob produced by `seal` using `tpm2-tools`.

        The blob is expected to be the tarball returned by `seal`.
        """
        import tempfile, tarfile, io

        with tempfile.TemporaryDirectory() as td:
            buf = io.BytesIO(blob)
            with tarfile.open(fileobj=buf, mode="r:gz") as tar:
                tar.extractall(path=td)

            prim_ctx = os.path.join(td, "prim.ctx")
            pub = os.path.join(td, "key.pub")
            priv = os.path.join(td, "key.priv")
            # Load the object and unseal
            key_ctx = os.path.join(td, "key.ctx")
            subprocess.run(["tpm2_load", "-C", prim_ctx, "-u", pub, "-r", priv, "-c", key_ctx], check=True)

            out = subprocess.check_output(["tpm2_unseal", "-c", key_ctx])
            return out

    def sign(self, data: bytes) -> bytes:
        """Create a transient signing key, sign `data`, and return the signature.

        The created key material is kept ephemeral and not persisted. The
        implementation mirrors the create/load/sign sequence used for sealed
        objects.
        """
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            data_path = os.path.join(td, "data.bin")
            with open(data_path, "wb") as f:
                f.write(data)

            prim_ctx = os.path.join(td, "prim.ctx")
            pub = os.path.join(td, "sign.pub")
            priv = os.path.join(td, "sign.priv")
            key_ctx = os.path.join(td, "sign.ctx")
            sig_path = os.path.join(td, "sig.bin")

            subprocess.run(["tpm2_createprimary", "-C", "o", "-g", "sha256", "-G", "rsa", "-c", prim_ctx], check=True)
            # Create an RSA signing key (template may be adapted)
            subprocess.run(["tpm2_create", "-C", prim_ctx, "-i", data_path, "-u", pub, "-r", priv, "-G", "rsa"], check=True)
            subprocess.run(["tpm2_load", "-C", prim_ctx, "-u", pub, "-r", priv, "-c", key_ctx], check=True)

            # Sign using the loaded key
            subprocess.run(["tpm2_sign", "-c", key_ctx, "-o", sig_path, data_path], check=True)
            with open(sig_path, "rb") as f:
                return f.read()

    def verify(self, data: bytes, signature: bytes, pubkey_pem: Optional[bytes] = None) -> bool:
        """Verify a signature. If `pubkey_pem` is provided use cryptography to
        validate it. Otherwise this wrapper attempts to use a public key blob
        that may have been produced by the TPM.
        """
        if pubkey_pem is not None:
            try:
                from cryptography.hazmat.primitives import hashes
                from cryptography.hazmat.primitives.asymmetric import padding
                from cryptography.hazmat.primitives.serialization import load_pem_public_key

                pub = load_pem_public_key(pubkey_pem)
                pub.verify(signature, data, padding.PKCS1v15(), hashes.SHA256())
                return True
            except Exception:
                return False

        # No public key provided — cannot verify without a key. Caller should
        # provide the public key or verify via the TPM.
        raise NotImplementedError("verify without pubkey_pem is not implemented for tpm2-tools client")


class PytssTPMClient:
    def __init__(self) -> None:
        if not HAS_PYTSS:
            raise RuntimeError("tpm2-pytss not available")

    def seal(self, data: bytes) -> bytes:
        raise NotImplementedError

    def unseal(self, blob: bytes) -> bytes:
        raise NotImplementedError

    def sign(self, data: bytes) -> bytes:
        raise NotImplementedError

    def verify(self, data: bytes, signature: bytes, pubkey_pem: Optional[bytes] = None) -> bool:
        raise NotImplementedError


def get_tpm_client(prefer: str = "auto") -> TPMClientInterface:
    if prefer in ("auto", "pytss") and HAS_PYTSS:
        try:
            return PytssTPMClient()
        except Exception:
            pass
    if prefer in ("auto", "tools"):
        try:
            return Tpm2ToolsClient()
        except Exception:
            pass
    return SimpleTPMEmulator()


__all__ = ["get_tpm_client", "SimpleTPMEmulator", "Tpm2ToolsClient", "PytssTPMClient"]
