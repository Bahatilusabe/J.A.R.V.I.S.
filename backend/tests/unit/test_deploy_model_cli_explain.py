import os
import tempfile


def test_cli_explain_upload(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        # create dummy model dir and explanation file
        mdl = os.path.join(td, "m")
        os.makedirs(mdl)
        open(os.path.join(mdl, "f.txt"), "w").write("x")
        expl = os.path.join(td, "expl.json")
        open(expl, "w").write('{"ex": 1}')

        called = {}

        def fake_example_flow(local_model_dir, obs_bucket, obs_prefix, job_name, dry_run=True, **kwargs):
            # accept new explain_* kwargs
            called["flow"] = True
            called["kwargs"] = kwargs
            return {"archive": "/tmp/fake.tar.gz", "obs": {"bucket": obs_bucket, "object_key": f"{obs_prefix}/fake.tar.gz"}, "job_name": job_name}

        monkeypatch.setattr("backend.integrations.huawei_modelarts.example_flow", fake_example_flow)

        from deployment.modelarts import deploy_model as cli

        rc = cli.main(["--local-dir", mdl, "--obs-bucket", "my-bucket", "--obs-prefix", "pfx", "--job-name", "j1", "--dry-run", "--explain-path", expl, "--explain-obs-prefix", "epfx"])
        assert rc == 0
        assert called.get("flow") is True
        # example_flow should have received explain args in kwargs
        assert called["kwargs"].get("explain_path") == expl
        assert called["kwargs"].get("explain_obs_prefix") == "epfx"
