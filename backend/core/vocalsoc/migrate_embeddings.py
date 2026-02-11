"""Migration utility for voice embeddings storage.

This script can:
- Encrypt existing `.npz` embedding files using AES-GCM (requires `cryptography`).
- Seal embeddings using a TPM client that implements the `TPMClientInterface`.

It operates on the same `index.json` used by `voice_auth.py` (default: the
`voice_auth_db` folder next to this module) and updates index flags to mark
entries as encrypted or sealed. It performs backups by default.

Usage examples:
    python -m backend.core.vocalsoc.migrate_embeddings --db-path /path/to/voice_auth_db --key-file ./mykey.bin
    python -m backend.core.vocalsoc.migrate_embeddings --db-path ./backend/core/vocalsoc/voice_auth_db --use-tpm --tpm-prefer pytss

Note: This script is safe to run in dry-run mode (no files changed).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import sys
from typing import Optional

import numpy as np

from . import tpm_wrapper
from . import encryption


def _load_index(db_path: str) -> dict:
    idx_file = os.path.join(db_path, "index.json")
    if not os.path.exists(idx_file):
        raise FileNotFoundError(f"index.json not found in {db_path}")
    with open(idx_file, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_index(db_path: str, idx: dict) -> None:
    idx_file = os.path.join(db_path, "index.json")
    with open(idx_file, "w", encoding="utf-8") as f:
        json.dump(idx, f, indent=2)


def migrate(db_path: str, key: Optional[bytes], use_tpm: bool, tpm_prefer: Optional[str], dry_run: bool = True) -> None:
    idx = _load_index(db_path)
    tpm_client = None
    if use_tpm:
        tpm_client = tpm_wrapper.detect_client(prefer=tpm_prefer)

    changed = False
    for user_id, entry in idx.items():
        fname = entry.get("file")
        if not fname:
            print(f"Skipping {user_id}: no file entry")
            continue
        npz_path = os.path.join(db_path, fname)
        if not os.path.exists(npz_path):
            print(f"Skipping {user_id}: file missing {npz_path}")
            continue

        print(f"Processing {user_id} -> {npz_path}")
        # load embedding
        data = np.load(npz_path)
        emb = data.get("embedding")
        if emb is None:
            print(f"  No embedding found in {npz_path}; skipping")
            continue

        # backup
        bak = npz_path + ".bak"
        if not dry_run:
            shutil.copy2(npz_path, bak)
            print(f"  Backed up to {bak}")
        else:
            print("  Dry-run: would back up file")

        if use_tpm and tpm_client is not None:
            try:
                sealed = tpm_client.seal(user_id, emb.tobytes())
                sealed_path = npz_path + ".sealed"
                if not dry_run:
                    with open(sealed_path, "wb") as f:
                        f.write(sealed)
                print(f"  Sealed blob written to {sealed_path} (dry_run={dry_run})")
                entry["sealed"] = True
                changed = True
            except Exception as e:
                print(f"  TPM seal failed for {user_id}: {e}")
        elif key is not None:
            try:
                ct = encryption.encrypt(emb.tobytes(), key)
                enc_path = npz_path + ".enc"
                if not dry_run:
                    with open(enc_path, "wb") as f:
                        f.write(ct)
                    # Optionally remove original embedding file or keep backup
                    os.remove(npz_path)
                print(f"  Encrypted blob written to {enc_path} (dry_run={dry_run})")
                entry["encrypted"] = True
                entry["enc_file"] = os.path.basename(enc_path)
                changed = True
            except Exception as e:
                print(f"  Encryption failed for {user_id}: {e}")
        else:
            print("  No action taken (no key and no TPM client)")

    if changed and not dry_run:
        _write_index(db_path, idx)
        print("Index updated")
    elif changed and dry_run:
        print("Dry-run: index would be updated")
    else:
        print("No changes made")


def main(argv=None):
    p = argparse.ArgumentParser(description="Migrate voice_auth embeddings: encrypt or TPM-seal")
    p.add_argument("--db-path", default=os.path.join(os.path.dirname(__file__), "voice_auth_db"))
    p.add_argument("--key-file", help="Path to AES-256 key file (32 bytes) to encrypt embeddings")
    p.add_argument("--key-hex", help="AES key as hex string")
    p.add_argument("--use-tpm", action="store_true", help="Seal embeddings using TPM instead of symmetric encryption")
    p.add_argument("--tpm-prefer", choices=("pytss", "tools"), help="Prefer a specific TPM client")
    p.add_argument("--dry-run", action="store_true", default=False, help="Do not write files; just show actions")

    args = p.parse_args(argv)
    key = None
    if args.key_file:
        with open(args.key_file, "rb") as f:
            key = f.read()
    elif args.key_hex:
        key = bytes.fromhex(args.key_hex)

    if key is not None and len(key) != 32:
        print("Key must be 32 bytes (256-bit)")
        sys.exit(2)

    if not args.use_tpm and key is None:
        print("Either --key-file/--key-hex or --use-tpm must be provided")
        sys.exit(2)

    try:
        migrate(args.db_path, key, args.use_tpm, args.tpm_prefer, dry_run=args.dry_run)
    except Exception as e:
        print("Migration failed:", e)
        raise


if __name__ == "__main__":
    main()
