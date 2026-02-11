"""Small CLI for exporting/importing OfflineSpeechCache with tar+checksum and atomic apply.

Commands:
- export-pack: export cache to a staging dir, create tar.gz and sha256.
- import-verify: verify tarball checksum and extract to staging dir.
- apply: atomically swap the extracted cache into place (optionally backup existing).

This automates the air-gapped cache transfer workflow.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import tarfile
import tempfile
from typing import Optional

from .offline_cache import OfflineSpeechCache


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def export_pack(cache_dir: str, out_tar: str) -> str:
    """Copy cache_dir to a temp staging dir and create a tar.gz at out_tar; return checksum."""
    if os.path.exists(out_tar):
        raise FileExistsError(out_tar)
    with tempfile.TemporaryDirectory() as td:
        staging = os.path.join(td, "offline_cache_export")
        shutil.copytree(cache_dir, staging)
        with tarfile.open(out_tar, "w:gz") as tar:
            tar.add(staging, arcname=os.path.basename(staging))
    checksum = sha256_file(out_tar)
    with open(out_tar + ".sha256", "w", encoding="utf-8") as f:
        f.write(checksum + "  " + os.path.basename(out_tar) + "\n")
    return checksum


def import_verify(tar_path: str, sha_path: Optional[str], extract_to: str) -> bool:
    if sha_path:
        with open(sha_path, "r", encoding="utf-8") as f:
            provided = f.read().strip().split()[0]
        actual = sha256_file(tar_path)
        if provided != actual:
            raise RuntimeError(f"Checksum mismatch: expected {provided} got {actual}")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=extract_to)
    return True


def atomic_apply(staging_dir: str, live_dir: str, backup_dir: Optional[str] = None) -> None:
    """Atomically replace live_dir with staging_dir contents. Optionally backup existing live_dir to backup_dir."""
    # staging_dir is the parent folder that contains the extracted export folder
    # find the single child
    children = [os.path.join(staging_dir, p) for p in os.listdir(staging_dir)]
    if len(children) != 1:
        raise RuntimeError("Staging dir must contain exactly one export folder")
    new_cache = children[0]
    if backup_dir:
        if os.path.exists(backup_dir):
            raise FileExistsError(backup_dir)
        if os.path.exists(live_dir):
            shutil.move(live_dir, backup_dir)
    # move new_cache into live_dir atomically by using os.replace on directory rename
    tmp_target = live_dir + ".tmp"
    if os.path.exists(tmp_target):
        shutil.rmtree(tmp_target)
    shutil.move(new_cache, tmp_target)
    # after move, replace
    if os.path.exists(live_dir):
        shutil.rmtree(live_dir)
    os.replace(tmp_target, live_dir)


def main(argv=None):
    p = argparse.ArgumentParser(description="OfflineSpeechCache transfer tool")
    sp = p.add_subparsers(dest="cmd")

    ep = sp.add_parser("export-pack")
    ep.add_argument("--cache-dir", help="Path to existing cache dir", required=False)
    ep.add_argument("--out-tar", help="Output tar.gz path", required=True)

    ip = sp.add_parser("import-verify")
    ip.add_argument("--tar", required=True)
    ip.add_argument("--sha", required=False)
    ip.add_argument("--extract-to", required=True)

    ap = sp.add_parser("apply")
    ap.add_argument("--staging-dir", required=True)
    ap.add_argument("--live-dir", required=True)
    ap.add_argument("--backup-dir", required=False)

    args = p.parse_args(argv)

    if args.cmd == "export-pack":
        cache_dir = args.cache_dir or os.path.join(os.path.dirname(__file__), "offline_cache_db")
        chksum = export_pack(cache_dir, args.out_tar)
        print("Wrote", args.out_tar)
        print("SHA256:", chksum)
        return 0

    if args.cmd == "import-verify":
        import_verify(args.tar, args.sha, args.extract_to)
        print("Extracted to", args.extract_to)
        return 0

    if args.cmd == "apply":
        atomic_apply(args.staging_dir, args.live_dir, backup_dir=args.backup_dir)
        print("Applied staging -> live")
        return 0

    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
