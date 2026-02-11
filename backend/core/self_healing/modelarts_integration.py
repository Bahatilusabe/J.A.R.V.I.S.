"""Huawei ModelArts integration helpers for RL training.

This module provides a thin, gated wrapper around Huawei's ModelArts training
service for submitting reinforcement-learning training jobs. The real client
requires the Huawei Cloud SDK (e.g. huaweicloudsdkcore / huaweicloudsdkmodelarts)
and credentials; when the SDK is not available we expose a lightweight
emulator suitable for local development and unit tests.

Design contract (small):
- Inputs: training package (local path) or S3/OBS path, job config dict
- Outputs: job id string, methods to query status or cancel
- Error modes: raises RuntimeError for unrecoverable errors, or returns
  emulator-safe values when running locally.

This file intentionally avoids hard imports of heavy SDKs at module import
time. Use gated imports inside the concrete client implementation.
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class TrainingJobInfo:
    job_id: str
    status: str
    created_at: float
    raw: Dict


class BaseModelArtsClient:
    """Abstract interface for ModelArts training client."""

    def submit_training_job(self, package_path: str, config: Dict) -> TrainingJobInfo:
        raise NotImplementedError()

    def get_job_status(self, job_id: str) -> TrainingJobInfo:
        raise NotImplementedError()

    def cancel_job(self, job_id: str) -> bool:
        raise NotImplementedError()


class ModelArtsEmulator(BaseModelArtsClient):
    """A safe, local emulator for training jobs.

    It doesn't call any network services. Instead it records metadata to a
    file under `.modelarts_emulator/` inside the repository and simulates
    state transitions (PENDING -> RUNNING -> SUCCEEDED) over a short time.
    Useful for unit tests and local dev when the real SDK is unavailable.
    """

    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = workspace_root or os.getcwd()
        self.storage_dir = os.path.join(self.workspace_root, ".modelarts_emulator")
        os.makedirs(self.storage_dir, exist_ok=True)
        self._jobs: Dict[str, TrainingJobInfo] = {}

    def _make_job_id(self) -> str:
        return f"emul-{int(time.time() * 1000)}"

    def submit_training_job(self, package_path: str, config: Dict) -> TrainingJobInfo:
        job_id = self._make_job_id()
        info = TrainingJobInfo(job_id=job_id, status="PENDING", created_at=time.time(), raw={"package": package_path, "config": config})
        self._jobs[job_id] = info
        # write metadata for inspection
        meta_path = os.path.join(self.storage_dir, f"{job_id}.meta")
        with open(meta_path, "w", encoding="utf-8") as fh:
            fh.write(str(info.raw))
        logger.info("[ModelArtsEmulator] submitted job %s (package=%s)", job_id, package_path)
        return info

    def get_job_status(self, job_id: str) -> TrainingJobInfo:
        info = self._jobs.get(job_id)
        if not info:
            raise RuntimeError(f"job {job_id} not found in emulator")
        # simulate simple progression
        now = time.time()
        age = now - info.created_at
        if age > 5 and info.status == "PENDING":
            info.status = "RUNNING"
        if age > 15 and info.status == "RUNNING":
            info.status = "SUCCEEDED"
        return info

    def cancel_job(self, job_id: str) -> bool:
        info = self._jobs.get(job_id)
        if not info:
            return False
        info.status = "CANCELLED"
        logger.info("[ModelArtsEmulator] cancelled job %s", job_id)
        return True


class ModelArtsClient(BaseModelArtsClient):
    """A thin wrapper around Huawei ModelArts SDK.

    This is intentionally minimal: it assumes the presence of the Huawei
    ModelArts client libraries and credentials in the environment. The
    implementation only imports the SDK when an instance is created.

    NOTE: to fully implement this you will need to install the official
    Huawei SDK packages and supply authentication (AK/SK or appropriate
    IAM token). This implementation raises RuntimeError if the SDK is
    unavailable.
    """

    def __init__(self, region: Optional[str] = None):
        try:
            # Example: gated import. The actual package names and API calls
            # may differ depending on the SDK version. Keep this gated so
            # the module can be imported in environments without the SDK.
            from huaweicloudsdkcore.auth.credentials import BasicCredentials  # type: ignore
            from huaweicloudsdkmodelarts.v1 import ModelArtsClient as _MAC  # type: ignore
        except Exception as exc:  # pragma: no cover - gated
            raise RuntimeError("Huawei ModelArts SDK not available") from exc

        # Real client construction goes here (requires region and credentials)
        self.region = region
        # Placeholder: we do not implement concrete auth here because it
        # requires credentials and environment setup.
        self._client = None

    def submit_training_job(self, package_path: str, config: Dict) -> TrainingJobInfo:
        raise RuntimeError("ModelArtsClient.submit_training_job not implemented - SDK stub")

    def get_job_status(self, job_id: str) -> TrainingJobInfo:
        raise RuntimeError("ModelArtsClient.get_job_status not implemented - SDK stub")

    def cancel_job(self, job_id: str) -> bool:
        raise RuntimeError("ModelArtsClient.cancel_job not implemented - SDK stub")


def get_modelarts_client(prefer_emulator: bool = False, workspace_root: Optional[str] = None) -> BaseModelArtsClient:
    """Factory: return a usable client. Prefer the real SDK unless prefer_emulator
    is True or the SDK isn't installed.
    """
    if prefer_emulator:
        return ModelArtsEmulator(workspace_root=workspace_root)

    try:
        # Attempt to create a real client; if the SDK is missing, fall back
        # to the emulator.
        client = ModelArtsClient()
        return client
    except Exception:
        logger.info("ModelArts SDK not available, using emulator")
        return ModelArtsEmulator(workspace_root=workspace_root)


__all__ = [
    "BaseModelArtsClient",
    "ModelArtsEmulator",
    "ModelArtsClient",
    "get_modelarts_client",
    "TrainingJobInfo",
]
