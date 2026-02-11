import os
import tempfile


def test_non_dryrun_explain_upload_passes_creds(monkeypatch, tmp_path):
    # Prepare model dir and explanation file
    d = tmp_path / "m"
    d.mkdir()
    (d / "f.txt").write_text("x")
    expl = tmp_path / "expl.json"
    expl.write_text('{"a":1}')

    captured = {}

    def fake_upload_to_obs(archive_path, bucket, object_key, ak=None, sk=None, retries=3, backoff=1.0, content_type=None, **kwargs):
        # capture creds passed
        captured["ak"] = ak
        captured["sk"] = sk
        return {"bucket": bucket, "object_key": object_key}

    def fake_example_flow(local_model_dir, obs_bucket, obs_prefix, job_name, dry_run=True, **kwargs):
        # Simulate a job submission that would include the metadata key if provided
        captured["flow_called"] = True
        captured["kwargs"] = kwargs
        return {"archive": "/tmp/fake.tar.gz", "obs": {"bucket": obs_bucket, "object_key": f"{obs_prefix}/fake.tar.gz"}, "job_name": job_name}

    monkeypatch.setattr("backend.integrations.huawei_modelarts.upload_to_obs", fake_upload_to_obs)
    def fake_create_job(*a, **k):
        captured["flow_called"] = True
        captured["job_args"] = (a, k)
        return {"job_id": "j1"}

    monkeypatch.setattr("backend.integrations.huawei_modelarts.create_modelarts_training_job", fake_create_job)
    # Prevent register_explanation_metadata from calling real SDK
    monkeypatch.setattr("backend.integrations.huawei_modelarts.register_explanation_metadata", lambda metadata, bucket, key, ak=None, sk=None, dry_run=True: {"bucket": bucket, "object_key": key, "metadata": metadata})

    from deployment.modelarts import deploy_model as cli

    # Run CLI non-dry-run; pass creds via flags
    rc = cli.main(["--local-dir", str(d), "--obs-bucket", "b", "--obs-prefix", "pfx", "--job-name", "j", "--ak", "flag-ak", "--sk", "flag-sk", "--explain-path", str(expl)])
    assert rc == 0
    # upload_to_obs should have received creds from flags via upload_explanation_artifact
    assert captured.get("ak") == "flag-ak"
    assert captured.get("sk") == "flag-sk"
    assert captured.get("flow_called") is True
