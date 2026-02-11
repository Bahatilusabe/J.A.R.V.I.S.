import os
import tempfile
import numpy as np

from backend.core.vocalsoc.voice_auth import VoiceAuthenticator, TPMClientInterface


class DummyTPM(TPMClientInterface):
    def __init__(self):
        self.store = {}

    def seal(self, key_name: str, data: bytes) -> bytes:
        # store raw bytes and return a fake sealed blob (base64-like)
        blob = b"SEALED:" + data
        self.store[key_name] = blob
        return blob

    def unseal(self, sealed_blob: bytes) -> bytes:
        if sealed_blob in self.store.values():
            # reverse transform
            return sealed_blob.replace(b"SEALED:", b"")
        # if not exact match, try to find by value
        for v in self.store.values():
            if v == sealed_blob:
                return v.replace(b"SEALED:", b"")
        raise RuntimeError("sealed blob not found")


def test_enroll_and_verify_software_fallback(tmp_path):
    db = tmp_path / "voice_auth_db"
    os.makedirs(db, exist_ok=True)

    auth = VoiceAuthenticator(storage_path=str(db), dry_run=True)

    # make a deterministic pseudo-audio bytes
    audio = b"test-audio-bytes-123"

    meta = auth.enroll("alice", audio)
    assert meta["user_id"] == "alice"
    assert os.path.exists(meta["file"])

    res = auth.verify("alice", audio)
    assert res["matched"] is True
    assert res["score"] > 0.0


def test_tpm_enroll_and_verify(tmp_path):
    db = tmp_path / "voice_auth_db"
    os.makedirs(db, exist_ok=True)

    tpm = DummyTPM()
    auth = VoiceAuthenticator(storage_path=str(db), tpm_client=tpm, dry_run=True)

    audio = b"other-audio-456"
    meta = auth.enroll("bob", audio)
    assert meta["user_id"] == "bob"

    # verify using same audio
    res = auth.verify("bob", audio)
    assert res["matched"] is True
