import importlib
import os
import sys
import tempfile
from pathlib import Path

import pytest


def _inject_fake_obs_and_modelarts(monkeypatch):
    """Create lightweight fake `obs` and `modelarts` modules in sys.modules.

    These fakes implement the minimal API our wrapper calls so we can test
    upload and job creation without the real SDK or network.
    """
    class FakeObsClient:
        def __init__(self, access_key_id=None, secret_access_key=None):
            self.ak = access_key_id
            self.sk = secret_access_key

        def putContent(self, bucketName, objectKey, content):
            # Return a simple dict-like object
            return {"bucket": bucketName, "object_key": objectKey, "size": len(content)}

    fake_obs_mod = type(sys)("obs")
    fake_obs_mod.ObsClient = FakeObsClient

    class FakeModelArts:
        @staticmethod
        def create_training_job(req):
            return {"job": req}

        @staticmethod
        def create_inference_service(req):
            return {"service": req}

    fake_modelarts_mod = type(sys)("modelarts")
    fake_modelarts_mod.create_training_job = FakeModelArts.create_training_job
    fake_modelarts_mod.create_inference_service = FakeModelArts.create_inference_service

    monkeypatch.setitem(sys.modules, "obs", fake_obs_mod)
    monkeypatch.setitem(sys.modules, "modelarts", fake_modelarts_mod)


def test_package_and_example_dry_run(tmp_path):
    # create a small dummy model dir
    model_dir = tmp_path / "mymodel"
    model_dir.mkdir()
    (model_dir / "weights.bin").write_bytes(b"abcd")

    from backend.integrations import huawei_modelarts as ha

    archive = ha.package_model(str(model_dir))
    assert Path(archive).exists()

    res = ha.example_flow(str(model_dir), "my-bucket", "prefix", "job-1", dry_run=True)
    assert res["job_name"] == "job-1"
    assert "archive" in res


def test_upload_and_create_job_with_fakes(monkeypatch, tmp_path):
    # Inject fake SDK modules then import the integration module fresh.
    _inject_fake_obs_and_modelarts(monkeypatch)

    # reload module under test so it picks up the fake modules
    import importlib

    ha = importlib.reload(importlib.import_module("backend.integrations.huawei_modelarts"))

    # prepare a small archive
    model_dir = tmp_path / "mymodel"
    model_dir.mkdir()
    (model_dir / "weights.bin").write_bytes(b"abcd")
    archive = ha.package_model(str(model_dir))

    # upload should use the fake ObsClient and return our dict-like response
    up = ha.upload_to_obs(archive, "bucket-x", "obj-key", ak="ak", sk="sk", retries=1)
    assert up["bucket"] == "bucket-x"
    assert up["object_key"] == "obj-key"
    assert isinstance(up["response"], dict)

    # create job should call our fake modelarts
    jr = ha.create_modelarts_training_job("bucket-x", "obj-key", "job-1", job_spec={"image": "ms"})
    assert "job_name" in jr["job"]


def test_errors_when_no_sdk(monkeypatch, tmp_path):
    # Ensure the module raises helpful errors when SDK missing
    # Remove any fake modules
    monkeypatch.setitem(sys.modules, "obs", None)
    monkeypatch.setitem(sys.modules, "modelarts", None)

    import importlib

    ha = importlib.reload(importlib.import_module("backend.integrations.huawei_modelarts"))

    model_dir = tmp_path / "mymodel"
    model_dir.mkdir()
    (model_dir / "weights.bin").write_bytes(b"abcd")
    archive = ha.package_model(str(model_dir))

    with pytest.raises(RuntimeError):
        ha.upload_to_obs(archive, "b", "k")

    with pytest.raises(RuntimeError):
        ha.create_modelarts_training_job("b", "k", "j")
