"""Lightweight integration helpers for Huawei ModelArts training and deployment.

This module provides a small, defensive wrapper to interact with Huawei
Cloud ModelArts and OBS for packaging, submitting training jobs and
deploying inference services on Ascend 910. The code is intentionally
gated: it will only attempt to import heavy Huawei SDKs when present and
falls back to raising informative errors (or performing dry-run logging)
when not available. Use these helpers from CI or deployment scripts.

NOTE: This module does not perform privileged cloud operations by
default. You must provide credentials (AK/SK) and proper IAM permissions
to use ModelArts/OBS. See docs/MODELARTS.md for environment variables
and required roles.
"""

from __future__ import annotations

import json
import logging
import os
import tarfile
import tempfile
import time
from pathlib import Path
from typing import Dict, Optional, Any

logger = logging.getLogger("jarvis.integrations.modelarts")

# Try optional Huawei SDK imports; keep these imports lazy/optional so tests and
# developer environments without the SDK still work.
_huaweicloud_sdk_available = False
try:
    import obs  # type: ignore
    import modelarts  # type: ignore

    _huaweicloud_sdk_available = True
except Exception:
    obs = None  # type: ignore
    modelarts = None  # type: ignore


def _resolve_credentials(ak: Optional[str], sk: Optional[str]) -> Dict[str, Optional[str]]:
    """Resolve AK/SK credentials from parameters or environment.

    Prefer explicit args, then environment variables HUAWEI_AK / HUAWEI_SK.
    """
    return {"ak": ak or os.environ.get("HUAWEI_AK"), "sk": sk or os.environ.get("HUAWEI_SK")}


def package_model(source_dir: str, output_path: Optional[str] = None) -> str:
    """Create a tar.gz archive of the model directory suitable for upload to OBS.

    Returns the absolute path to the created archive.
    """
    src = Path(source_dir)
    if not src.exists():
        raise FileNotFoundError(f"source_dir {source_dir} not found")

    out = Path(output_path) if output_path is not None else None
    if out is None:
        tmp = tempfile.NamedTemporaryFile(prefix="jarvis-model-", suffix=".tar.gz", delete=False)
        out = Path(tmp.name)
        tmp.close()

    logger.info("Packaging model directory %s -> %s", src, out)

    with tarfile.open(out, "w:gz") as tf:
        tf.add(src, arcname="package")

    return str(out)


def upload_to_obs(archive_path: str, bucket: str, object_key: str, ak: Optional[str] = None, sk: Optional[str] = None, retries: int = 3, backoff: float = 1.0, content_type: Optional[str] = None) -> Dict[str, Any]:
    """Upload local archive to OBS (Huawei Object Storage).

    If the Huawei OBS SDK is unavailable, raise a helpful RuntimeError so
    calling code can fall back or mock. Returns a dict with OBS location
    information on success.
    """
    creds = _resolve_credentials(ak, sk)
    if not _huaweicloud_sdk_available or obs is None:
        raise RuntimeError("Huawei OBS SDK not available in this environment; install the SDK or run in dry-run mode")

    # Construct client using resolved credentials; real deployments should
    # support endpoints, region and credential chaining.
    client = obs.ObsClient(access_key_id=creds["ak"], secret_access_key=creds["sk"])  # type: ignore

    attempt = 0
    last_exc: Optional[Exception] = None
    with open(archive_path, "rb") as f:
        data = f.read()

    while attempt < retries:
        try:
            logger.debug("Uploading %s to OBS bucket=%s object=%s (attempt=%d)", archive_path, bucket, object_key, attempt + 1)
            # Prefer SDK content-type support when available. Many SDKs accept an
            # optional contentType/content_type argument; attempt to pass it and
            # gracefully fallback if not supported.
            try:
                if content_type is not None:
                    resp = client.putContent(bucketName=bucket, objectKey=object_key, content=data, contentType=content_type)  # type: ignore
                else:
                    resp = client.putContent(bucketName=bucket, objectKey=object_key, content=data)  # type: ignore
            except TypeError:
                # Some SDKs may not accept contentType kwarg; fall back
                resp = client.putContent(bucketName=bucket, objectKey=object_key, content=data)  # type: ignore
            return {"bucket": bucket, "object_key": object_key, "response": resp}
        except Exception as e:  # pragma: no cover - SDK network errors
            last_exc = e
            logger.warning("OBS upload attempt %d failed: %s", attempt + 1, e)
            time.sleep(backoff * (2 ** attempt))
            attempt += 1

    raise RuntimeError("Failed to upload to OBS after retries") from last_exc


def create_modelarts_training_job(obs_bucket: str, obs_object: str, job_name: str, region: str = "cn-north-4", job_spec: Optional[Dict] = None) -> Dict[str, Any]:
    """Submit a ModelArts training job that uses the provided OBS artifact.

    This is a thin wrapper that expects the ModelArts SDK. In environments
    without the SDK a RuntimeError is raised so calling code can implement
    an alternative submission path.
    """
    if not _huaweicloud_sdk_available or modelarts is None:
        raise RuntimeError("Huawei ModelArts SDK not available in this environment; cannot submit training job")

    spec = job_spec or {}
    logger.info("Creating ModelArts job %s using obs://%s/%s", job_name, obs_bucket, obs_object)

    job_req = {
        "job_name": job_name,
        "region": region,
        "input": {"obs_bucket": obs_bucket, "obs_object": obs_object},
        "spec": spec,
    }

    # Attach job_spec if provided (SDKs may expect different shapes; pass
    # through under 'spec' so callers can adapt as needed).
    if job_spec:
        job_req["spec"].update(job_spec)

    resp = modelarts.create_training_job(job_req)  # type: ignore
    return resp


def register_explanation_metadata(metadata: Dict[str, Any], bucket: str, metadata_key: str, ak: Optional[str] = None, sk: Optional[str] = None, dry_run: bool = True) -> Dict[str, Any]:
    """Write explanation metadata JSON to OBS under `metadata_key`.

    The metadata should include references to the model artifact and the
    explanation artifact. When `dry_run` is True the function only logs the
    intended action and returns the metadata that would be written.
    """
    import json as _json

    if dry_run:
        logger.info("Dry-run: would write metadata to obs://%s/%s: %s", bucket, metadata_key, metadata)
        return {"bucket": bucket, "object_key": metadata_key, "metadata": metadata}

    # Ensure SDK available
    creds = _resolve_credentials(ak, sk)
    if not _huaweicloud_sdk_available or obs is None:
        raise RuntimeError("Huawei OBS SDK not available; cannot write metadata to OBS")

    data = _json.dumps(metadata).encode("utf-8")

    client = obs.ObsClient(access_key_id=creds.get("ak"), secret_access_key=creds.get("sk"))  # type: ignore
    # Use putContent to write small JSON metadata
    resp = client.putContent(bucketName=bucket, objectKey=metadata_key, content=data)  # type: ignore
    return {"bucket": bucket, "object_key": metadata_key, "response": resp}


def deploy_model_to_serving(model_id: str, service_name: str, device_type: str = "Ascend-910", replicas: int = 1) -> Dict[str, Any]:
    """Deploy a trained model to a ModelArts inference service on Ascend.

    This wrapper calls ModelArts deployment APIs and will raise when the
    SDK is missing.
    """
    if not _huaweicloud_sdk_available or modelarts is None:
        raise RuntimeError("Huawei ModelArts SDK not available; cannot deploy model")

    logger.info("Deploying model %s to service %s on device %s", model_id, service_name, device_type)
    req = {"model_id": model_id, "service_name": service_name, "device_type": device_type, "replicas": replicas}
    resp = modelarts.create_inference_service(req)  # type: ignore
    return resp


def example_flow(local_model_dir: str, obs_bucket: str, obs_prefix: str, job_name: str, dry_run: bool = True, explain_path: Optional[str] = None, explain_obs_prefix: Optional[str] = None, explain_format: Optional[str] = None, job_spec: Optional[Dict] = None) -> Dict[str, Any]:
    """High-level example: package, upload, submit a training job and (optionally) attach explanation metadata.

    When `dry_run` is True the function will only log actions instead of
    calling cloud APIs. If `explain_path` is provided the explanation artifact
    is uploaded and a small metadata JSON is registered in OBS; the metadata
    location is attached to the `job_spec` under the key `explanation_metadata`.
    Returns a summary dict of planned or executed actions.
    """
    tar = package_model(local_model_dir)
    object_key = f"{obs_prefix}/{Path(tar).name}"
    if dry_run:
        logger.info("Dry-run: would upload %s -> obs://%s/%s", tar, obs_bucket, object_key)
        logger.info("Dry-run: would submit ModelArts job %s", job_name)
        # Include explain hints in dry-run return
        summary = {"archive": tar, "obs": {"bucket": obs_bucket, "object_key": object_key}, "job_name": job_name}
        if explain_path:
            expl_key = f"{(explain_obs_prefix or 'jarvis/explanations')}/{Path(explain_path).name}"
            summary["explain"] = {"artifact": explain_path, "obs": {"bucket": obs_bucket, "object_key": expl_key}}
        return summary

    upload_resp = upload_to_obs(tar, obs_bucket, object_key)

    # If an explanation artifact is provided, upload it, register metadata,
    # and attach the metadata path to the job_spec so training jobs can find it.
    spec = job_spec or {}
    if explain_path:
        expl_prefix = explain_obs_prefix or "jarvis/explanations"
        expl_obj = f"{expl_prefix}/{Path(explain_path).name}"
        # map explain_format to content-type if provided
        content_type = None
        if explain_format:
            mapping = {"json": "application/json", "html": "text/html", "png": "image/png", "jpg": "image/jpeg"}
            content_type = mapping.get(explain_format.lower())

        upload_explanation_artifact(explain_path, obs_bucket, expl_obj, dry_run=False, content_type=content_type)
        # register small metadata JSON under a stable key
        meta_key = f"{expl_prefix}/{job_name}.explanation.meta.json"
        metadata = {"model_obs": {"bucket": obs_bucket, "object_key": object_key}, "explanation_obs": {"bucket": obs_bucket, "object_key": expl_obj}}
        register_explanation_metadata(metadata, obs_bucket, meta_key, dry_run=False)
        spec = spec.copy()
        spec["explanation_metadata"] = {"bucket": obs_bucket, "object_key": meta_key}

    job_resp = create_modelarts_training_job(obs_bucket, object_key, job_name, job_spec=spec)
    return {"upload": upload_resp, "job": job_resp}


def upload_explanation_artifact(artifact_path: str, bucket: str, object_key: str, ak: Optional[str] = None, sk: Optional[str] = None, dry_run: bool = True, content_type: Optional[str] = None) -> Dict[str, Any]:
    """Upload an explanation artifact (JSON, HTML, image, etc.) to OBS.

    This helper is dry-run friendly. When `dry_run` is True the function will
    only log the intended action. When False it delegates to `upload_to_obs`.
    Returns a dict describing the observed or planned upload.
    """
    p = Path(artifact_path)
    if not p.exists():
        raise FileNotFoundError(f"artifact_path {artifact_path} not found")

    creds = _resolve_credentials(ak, sk)
    object_key = object_key

    if dry_run:
        logger.info("Dry-run: would upload explanation artifact %s -> obs://%s/%s", artifact_path, bucket, object_key)
        return {"artifact": str(artifact_path), "obs": {"bucket": bucket, "object_key": object_key}}

    # Delegate to upload_to_obs for actual upload behaviour and retries
    return upload_to_obs(str(artifact_path), bucket, object_key, ak=creds.get("ak"), sk=creds.get("sk"), content_type=content_type)
