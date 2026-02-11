import os
import tempfile
import json
import numpy as np

from backend.core.vocalsoc import migrate_embeddings, encryption


def test_migrate_encrypt_dryrun(tmp_path, monkeypatch):
    db = tmp_path / "voice_auth_db"
    os.makedirs(db, exist_ok=True)
    # create a fake index and .npz files
    idx = {"carol": {"file": "carol.npz"}}
    with open(os.path.join(db, "index.json"), "w", encoding="utf-8") as f:
        json.dump(idx, f)

    arr = np.arange(10, dtype=np.float32)
    np.savez_compressed(os.path.join(db, "carol.npz"), embedding=arr)

    key = encryption.generate_key()

    # dry-run should not modify files
    migrate_embeddings.migrate(str(db), key, use_tpm=False, tpm_prefer=None, dry_run=True)

    # ensure original file still exists
    assert os.path.exists(os.path.join(db, "carol.npz"))
