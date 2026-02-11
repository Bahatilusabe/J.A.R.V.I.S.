import os
import tempfile

import pytest


def test_cli_dry_run_monkeypatch(monkeypatch):
    # Create a tiny directory to act as the model directory
    with tempfile.TemporaryDirectory() as td:
        # create a dummy file
        open(os.path.join(td, "dummy.txt"), "w").write("ok")

        called = {}

        def fake_example_flow(local_model_dir, obs_bucket, obs_prefix, job_name, dry_run=True, **kwargs):
            # accept new explain_* kwargs added to example_flow
            called["args"] = (local_model_dir, obs_bucket, obs_prefix, job_name, dry_run)
            called["kwargs"] = kwargs
            return {"archive": "/tmp/fake.tar.gz", "obs": {"bucket": obs_bucket, "object_key": f"{obs_prefix}/fake.tar.gz"}, "job_name": job_name}

        # Patch the integration function
        monkeypatch.setattr("backend.integrations.huawei_modelarts.example_flow", fake_example_flow)

        # Import the CLI main and call it
        from deployment.modelarts import deploy_model as cli

        rc = cli.main(["--local-dir", td, "--obs-bucket", "my-bucket", "--obs-prefix", "pfx", "--job-name", "j1", "--dry-run"])
        assert rc == 0
        assert "args" in called
        assert called["args"][1] == "my-bucket"
        assert called["args"][2] == "pfx"
        assert called["args"][3] == "j1"
        assert called["args"][4] is True
