import os
import tempfile

import pytest


def test_cli_input_validation_nonexistent_dir():
    from deployment.modelarts import deploy_model as cli

    # Path that doesn't exist should yield exit code 1
    rc = cli.main(["--local-dir", "/tmp/definitely-not-exist-xyz", "--obs-bucket", "b", "--job-name", "j", "--dry-run"])
    assert rc == 1


def test_cli_creds_flag_overrides_env(monkeypatch, tmp_path):
    # Setup a small directory with content
    d = tmp_path / "m"
    d.mkdir()
    (d / "f.txt").write_text("x")

    # ensure env has some values
    os.environ["HUAWEI_AK"] = "env-ak"
    os.environ["HUAWEI_SK"] = "env-sk"

    called = {}

    def fake_example_flow(local_model_dir, obs_bucket, obs_prefix, job_name, dry_run=True, **kwargs):
        # accept new explain_* kwargs
        called["env_ak"] = os.environ.get("HUAWEI_AK")
        called["env_sk"] = os.environ.get("HUAWEI_SK")
        called["args"] = (local_model_dir, obs_bucket, obs_prefix, job_name, dry_run)
        called["kwargs"] = kwargs
        return {"ok": True}

    monkeypatch.setattr("backend.integrations.huawei_modelarts.example_flow", fake_example_flow)

    from deployment.modelarts import deploy_model as cli

    # Pass flags that should override env
    rc = cli.main(["--local-dir", str(d), "--obs-bucket", "b", "--job-name", "j", "--ak", "flag-ak", "--sk", "flag-sk"])
    assert rc == 0
    assert called["env_ak"] == "flag-ak"
    assert called["env_sk"] == "flag-sk"
