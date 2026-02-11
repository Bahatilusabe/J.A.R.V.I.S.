"""Self-healing Snapshot Rollback manager.

This module provides a RecoveryManager that can use a Huawei Cloud Backup & DR
client (gated import) to create/list/restore snapshots and orchestrate a
rollback when an attack or policy-violation is detected. When the Huawei SDK
is not available, a lightweight local emulator is used which stores directory
snapshots as timestamped tarballs under a `.backups/` folder in the working
directory. The emulator allows safe local testing without cloud access.

Design contract (simple):
- Inputs: resource identifier (for cloud) or a local path (for emulator), a
  detector callable that returns True when rollback is required.
- Outputs: Snapshot metadata objects and boolean success indicators.
- Error modes: raises RuntimeError on disallowed operations or when
  the underlying client fails; getter methods return empty lists on missing
  resources.

This file intentionally avoids heavy third-party imports at module import time.
"""
from __future__ import annotations

import dataclasses
import datetime
import logging
import os
import shutil
import tarfile
import tempfile
import json
from typing import Callable, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)
_BACKUP_DIR = ".backups"


@dataclasses.dataclass
class SnapshotMetadata:
    id: str
    resource: str
    created_at: datetime.datetime
    size_bytes: Optional[int] = None
    notes: Optional[str] = None


class BaseBackupClient:
    """Abstract small interface for a backup client used by RecoveryManager."""

    def create_snapshot(self, resource: str, notes: Optional[str] = None) -> SnapshotMetadata:
        raise NotImplementedError()

    def list_snapshots(self, resource: str) -> List[SnapshotMetadata]:
        raise NotImplementedError()

    def restore_snapshot(self, snapshot_id: str, target: str) -> bool:
        raise NotImplementedError()

    def delete_snapshot(self, snapshot_id: str) -> bool:
        raise NotImplementedError()


class LocalEmulatorBackup(BaseBackupClient):
    """Simple local filesystem backup emulator.

    - create_snapshot: tar.gz the provided `resource` path into .backups/<id>.tar.gz
    - list_snapshots: list tarballs for resource
    - restore_snapshot: extract tarball into target path (overwrites by default)
    """

    def __init__(self, backup_dir: str = _BACKUP_DIR):
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)

    def _history_path(self) -> str:
        return os.path.join(self.backup_dir, "history.json")

    def _append_history(self, entry: Dict) -> None:
        path = self._history_path()
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
            else:
                data = []
        except Exception:
            data = []
        data.append(entry)
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, default=str)
        except Exception:
            logger.exception("failed to write backup history")

    def _snapshot_path(self, snapshot_id: str) -> str:
        return os.path.join(self.backup_dir, f"{snapshot_id}.tar.gz")

    def create_snapshot(self, resource: str, notes: Optional[str] = None) -> SnapshotMetadata:
        if not os.path.exists(resource):
            raise RuntimeError(f"resource path does not exist: {resource}")
        ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        snapshot_id = f"local-{os.path.basename(resource)}-{ts}"
        target_path = self._snapshot_path(snapshot_id)
        logger.info("Creating local snapshot %s -> %s", resource, target_path)
        with tarfile.open(target_path, "w:gz") as tar:
            tar.add(resource, arcname=os.path.basename(resource))
        size = os.path.getsize(target_path)
        meta = SnapshotMetadata(id=snapshot_id, resource=resource, created_at=datetime.datetime.utcnow(), size_bytes=size, notes=notes)
        logger.debug("Snapshot created: %s", meta)
        # append to history
        try:
            self._append_history({
                "event": "snapshot_created",
                "snapshot_id": meta.id,
                "resource": resource,
                "created_at": meta.created_at.isoformat() + "Z",
                "size_bytes": meta.size_bytes,
                "notes": meta.notes,
            })
        except Exception:
            logger.exception("failed to append snapshot history")
        return meta

    def list_snapshots(self, resource: str) -> List[SnapshotMetadata]:
        out: List[SnapshotMetadata] = []
        prefix = f"local-{os.path.basename(resource)}-"
        for fname in os.listdir(self.backup_dir):
            if not fname.endswith(".tar.gz"):
                continue
            if not fname.startswith(prefix):
                continue
            snapshot_id = fname[:-7]
            path = os.path.join(self.backup_dir, fname)
            try:
                created_at = datetime.datetime.utcfromtimestamp(os.path.getmtime(path))
            except Exception:
                created_at = datetime.datetime.utcnow()
            size = os.path.getsize(path)
            out.append(SnapshotMetadata(id=snapshot_id, resource=resource, created_at=created_at, size_bytes=size))
        out.sort(key=lambda x: x.created_at, reverse=True)
        return out

    def restore_snapshot(self, snapshot_id: str, target: str) -> bool:
        path = self._snapshot_path(snapshot_id)
        if not os.path.exists(path):
            raise RuntimeError(f"snapshot not found: {snapshot_id}")
        logger.info("Restoring snapshot %s into %s", snapshot_id, target)
        # Extract into a temp dir first, then move into place to avoid partial writes
        with tempfile.TemporaryDirectory() as td:
            with tarfile.open(path, "r:gz") as tar:
                tar.extractall(path=td)
            # we expect the tarball to contain a single top-level entry with the resource basename
            entries = os.listdir(td)
            if not entries:
                raise RuntimeError("snapshot archive empty")
            src = os.path.join(td, entries[0])
            # remove target (if exists) then move
            if os.path.exists(target):
                if os.path.isdir(target):
                    shutil.rmtree(target)
                else:
                    os.remove(target)
            shutil.move(src, target)
        logger.info("Restore complete")
        try:
            self._append_history({
                "event": "snapshot_restored",
                "snapshot_id": snapshot_id,
                "resource": target,
                "restored_at": datetime.datetime.utcnow().isoformat() + "Z",
            })
        except Exception:
            logger.exception("failed to append restore history")
        return True

    def delete_snapshot(self, snapshot_id: str) -> bool:
        path = self._snapshot_path(snapshot_id)
        if os.path.exists(path):
            os.remove(path)
            try:
                self._append_history({
                    "event": "snapshot_deleted",
                    "snapshot_id": snapshot_id,
                    "deleted_at": datetime.datetime.utcnow().isoformat() + "Z",
                })
            except Exception:
                logger.exception("failed to append delete history")
            return True
        return False


class HuaweiBackupClient(BaseBackupClient):
    """Wrapper for Huawei Cloud Backup & DR SDK.

    This is a gated integration: we attempt to import the Huawei Cloud SDK when
    available. The implementation here is intentionally minimal: real projects
    should expand error handling, authentication, paging, and rate-limit handling.
    """

    def __init__(self, region: Optional[str] = None, **auth_kwargs):
        # Lazy import to avoid hard dependency at package import time.
        try:
            # Placeholder import - adapt to the actual Huawei SDK package and
            # client classes used in your environment if/when available.
            from huaweicloudsdkbbr.v1 import BbrClient  # type: ignore
        except Exception as exc:  # pragma: no cover - requires actual SDK
            raise RuntimeError("Huawei SDK not available: %s" % exc)
        # In a real integration we would authenticate and create the client here.
        self._client = None
        self.region = region

    def create_snapshot(self, resource: str, notes: Optional[str] = None) -> SnapshotMetadata:
        raise RuntimeError("HuaweiBackupClient.create_snapshot not implemented in emulator wrapper")

    def list_snapshots(self, resource: str) -> List[SnapshotMetadata]:
        raise RuntimeError("HuaweiBackupClient.list_snapshots not implemented in emulator wrapper")

    def restore_snapshot(self, snapshot_id: str, target: str) -> bool:
        raise RuntimeError("HuaweiBackupClient.restore_snapshot not implemented in emulator wrapper")

    def delete_snapshot(self, snapshot_id: str) -> bool:
        raise RuntimeError("HuaweiBackupClient.delete_snapshot not implemented in emulator wrapper")


class RecoveryManager:
    """Orchestrates detection and snapshot rollback.

    Typical usage:
      client = LocalEmulatorBackup()  # or HuaweiBackupClient(...)
      manager = RecoveryManager(client)
      # create a snapshot before risky operations
      manager.backup_client.create_snapshot('/srv/app', notes='pre-deploy')
      # later: detect attack and rollback
      manager.monitor_and_rollback(detect_fn=my_detector, resource='/srv/app')
    """

    def __init__(self, backup_client: Optional[BaseBackupClient] = None):
        self.backup_client: BaseBackupClient = backup_client or LocalEmulatorBackup()

    def create_checkpoint(self, resource: str, notes: Optional[str] = None) -> SnapshotMetadata:
        """Create a snapshot/checkpoint for the given resource (path or id)."""
        logger.debug("Creating checkpoint for %s", resource)
        return self.backup_client.create_snapshot(resource, notes=notes)

    def list_checkpoints(self, resource: str) -> List[SnapshotMetadata]:
        return self.backup_client.list_snapshots(resource)

    def perform_rollback(self, snapshot_id: str, target: str, dry_run: bool = False) -> bool:
        """Restore a snapshot into the given target. If dry_run, only validate.

        Returns True on success.
        """
        logger.info("Requested rollback: snapshot=%s target=%s dry_run=%s", snapshot_id, target, dry_run)
        if dry_run:
            # simple validation: snapshot exists
            snaps = self.backup_client.list_snapshots(target)
            exists = any(s.id == snapshot_id for s in snaps)
            logger.info("Dry-run validation: exists=%s", exists)
            return exists
        return self.backup_client.restore_snapshot(snapshot_id, target)

    def monitor_and_rollback(self, detect_fn: Callable[[], bool], resource: str, max_lookback: Optional[int] = 10, dry_run: bool = False) -> Dict[str, str]:
        """Monitor via a detector callable and rollback to the most recent snapshot if detector returns True.

        - detect_fn: callable that returns True when rollback is required.
        - resource: resource id (cloud) or local path (emulator) to restore.
        - max_lookback: how many snapshots to try (most recent first).
        - dry_run: if True, don't actually restore.

        Returns a dict with outcome details.
        """
        logger.debug("monitor_and_rollback called for resource=%s", resource)
        if not callable(detect_fn):
            raise ValueError("detect_fn must be callable")

        if not detect_fn():
            return {"status": "no_action", "reason": "detector returned False"}

        snaps = self.backup_client.list_snapshots(resource)
        if not snaps:
            return {"status": "failed", "reason": "no_snapshots_available"}

        tried = 0
        for snap in snaps:
            if tried >= (max_lookback or 10):
                break
            tried += 1
            try:
                ok = self.perform_rollback(snap.id, resource, dry_run=dry_run)
                if ok:
                    return {"status": "rolled_back", "snapshot_id": snap.id}
            except Exception as exc:  # keep trying older snapshots
                logger.warning("rollback attempt failed for %s: %s", snap.id, exc)
                continue

        return {"status": "failed", "reason": "all_restore_attempts_failed"}


def _demo_detector_factory(trigger_file: str) -> Callable[[], bool]:
    """Return a detector that signals True when `trigger_file` exists.

    This is a tiny helper for local testing: create the file to simulate an
    attack/trigger and delete to resolve.
    """

    def detect() -> bool:
        return os.path.exists(trigger_file)

    return detect


def monitor_with_policy(decision_supplier: Callable[[], dict], engine=None) -> Callable[[], bool]:
    """Return a detector callable that evaluates a decision via a policy engine.

    The returned callable takes no arguments and returns True when the
    policy engine indicates a rollback is required (verdict == 'unsafe').

    - decision_supplier: callable returning a decision dict used for evaluation
    - engine: optional BaseEthicsEngine; if None, will use policy_engine.get_default_engine()
    """
    try:
        from . import policy_engine
    except Exception:
        # import relative fallback
        import backend.core.self_healing.policy_engine as policy_engine  # type: ignore

    if engine is None:
        engine = policy_engine.get_default_engine()

    def detector() -> bool:
        try:
            decision = decision_supplier()
            outcome = engine.evaluate(decision, context={})
            # Only trigger rollback for explicit 'unsafe' verdicts in this helper
            return outcome.verdict == "unsafe"
        except Exception:
            logger.exception("policy-based detector failed; conservatively signaling no rollback")
            return False

    return detector


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RecoveryManager demo (local emulator)")
    parser.add_argument("resource", help="Local path to snapshot (directory) to protect/rollback")
    parser.add_argument("--trigger-file", default="/tmp/recovery.trigger", help="file whose presence simulates an attack")
    parser.add_argument("--create", action="store_true", help="create a snapshot now")
    parser.add_argument("--restore", action="store_true", help="attempt restore if trigger exists")
    parser.add_argument("--list", action="store_true", help="list snapshots")
    parser.add_argument("--dry-run", action="store_true", help="dry-run the restore")
    args = parser.parse_args()

    rm = RecoveryManager(LocalEmulatorBackup())
    if args.create:
        meta = rm.create_checkpoint(args.resource, notes="demo checkpoint")
        print("created:", meta)
    if args.list:
        for s in rm.list_checkpoints(args.resource):
            print(s)
    if args.restore:
        det = _demo_detector_factory(args.trigger_file)
        out = rm.monitor_and_rollback(det, args.resource, dry_run=args.dry_run)
        print(out)
