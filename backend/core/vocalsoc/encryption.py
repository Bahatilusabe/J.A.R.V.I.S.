"""AES-GCM encryption helpers for embedding encryption.

This module uses the `cryptography` package when available. If the
package is not installed, functions will raise a clear RuntimeError so
callers can choose to fall back to a different strategy.

API:
- generate_key() -> bytes (32 bytes)
- encrypt(plaintext: bytes, key: bytes, associated_data: bytes=b'') -> bytes
- decrypt(ciphertext: bytes, key: bytes, associated_data: bytes=b'') -> bytes

The ciphertext format is: nonce (12 bytes) || ciphertext || tag (16 bytes)
as returned by AESGCM.encrypt.
"""

from __future__ import annotations

import os
from typing import Optional


def _get_aesgcm():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore

        return AESGCM
    except Exception as e:
        raise RuntimeError(
            "cryptography package is required for AES-GCM support: %s" % e
        )


def generate_key() -> bytes:
    """Generate a random 256-bit AES key."""
    return os.urandom(32)


def encrypt(plaintext: bytes, key: bytes, associated_data: Optional[bytes] = None) -> bytes:
    """Encrypt plaintext with AES-GCM and return nonce||ciphertext.

    Returns the raw bytes containing nonce (12 bytes) + ciphertext+tag.
    """
    AESGCM = _get_aesgcm()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    aad = associated_data or b""
    ct = aesgcm.encrypt(nonce, plaintext, aad)
    return nonce + ct


def decrypt(ciphertext: bytes, key: bytes, associated_data: Optional[bytes] = None) -> bytes:
    """Decrypt a blob produced by `encrypt` and return the plaintext."""
    AESGCM = _get_aesgcm()
    if len(ciphertext) < 13:
        raise ValueError("ciphertext too short")
    nonce = ciphertext[:12]
    ct = ciphertext[12:]
    aesgcm = AESGCM(key)
    aad = associated_data or b""
    return aesgcm.decrypt(nonce, ct, aad)


__all__ = ["generate_key", "encrypt", "decrypt"]
