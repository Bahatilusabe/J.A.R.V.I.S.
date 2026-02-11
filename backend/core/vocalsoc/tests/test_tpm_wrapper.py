"""Unit tests for the TPM wrapper emulation and selection logic."""
from __future__ import annotations

import os
import sys

import pytest

import pytest

# Skip these tests if the cryptography package isn't available in the environment.
pytest.importorskip("cryptography")

from backend.core.vocalsoc import tpm_client as tw


def test_get_tpm_client_emulator_by_default():
    client = tw.get_tpm_client(prefer="emulator")
    assert client is not None
    # Test that seal/unseal round-trips
    payload = b"hello-tpm"
    blob = client.seal(payload)
    assert isinstance(blob, (bytes, bytearray))
    out = client.unseal(blob)
    assert out == payload


def test_sign_verify_emulator():
    client = tw.get_tpm_client(prefer="emulator")
    data = b"message-to-sign"
    sig = client.sign(data)
    assert isinstance(sig, bytes)
    assert client.verify(data, sig)


def test_factory_prefers_pytss_when_available(monkeypatch):
    # Simulate pytss available by monkeypatching the flag and class
    class DummyPytss:
        def __init__(self):
            pass

        def seal(self, data: bytes) -> bytes:
            return b"pytss-sealed"

        def unseal(self, blob: bytes) -> bytes:
            return b"pytss-unsealed"

        def sign(self, data: bytes) -> bytes:
            return b"sig"

        def verify(self, data: bytes, signature: bytes, pubkey_pem=None) -> bool:
            return True

    monkeypatch.setattr(tw, "HAS_PYTSS", True)
    monkeypatch.setattr(tw, "PytssTPMClient", lambda: DummyPytss())
    client = tw.get_tpm_client(prefer="pytss")
    assert hasattr(client, "seal")
