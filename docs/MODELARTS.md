# ModelArts integration (overview)

This document describes how to use the lightweight ModelArts helpers in this
repository. The code in `backend/integrations/huawei_modelarts.py` is defensive
and supports a dry-run mode so CI and developers can exercise packaging and
submission flows without requiring Huawei credentials or SDKs.

Environment variables

- `HUAWEI_AK` / `HUAWEI_SK` - Access key / secret for OBS and ModelArts (optional
  for dry-run). You can also pass `--ak`/`--sk` to the CLI which sets these in
  the process environment.

OBS

- Create an OBS bucket and ensure the IAM role/user has permission to put
  objects into the bucket. ModelArts training jobs will reference the OBS
  object path `obs://<bucket>/<object>`.

ModelArts

- The lightweight wrapper expects ModelArts/OBS SDKs to be installed if you
  want to run the real submission flow. For CI and local development, prefer
  `--dry-run` which only logs planned actions.

MindSpore / Ascend

- Training on Ascend 910 requires MindSpore and appropriate drivers on the
  training host. This repository intentionally keeps those dependencies gated so
  unit tests run without them. See the Dockerfile in `deployment/modelarts` for
  a starting point.

CLI

- Use the CLI at `deployment/modelarts/deploy_model.py`.

Example (dry-run):

```bash
python -m deployment.modelarts.deploy_model \
  --local-dir ./my_model \
  --obs-bucket my-bucket \
  --obs-prefix jarvis/models \
  --job-name my-test-job \
  --dry-run
```

Next steps and CI

- For full CI that runs training or ModelArts submissions you will need to set
  up a self-hosted runner or hosted image with MindSpore and Ascend support.
  The provided GitHub Actions workflow is a dry-run smoke test that runs the
  CLI unit test.
# ModelArts integration (overview)

This document describes how to use the lightweight ModelArts helpers in this
repository. The code in `backend/integrations/huawei_modelarts.py` is defensive
and supports a dry-run mode so CI and developers can exercise packaging and
submission flows without requiring Huawei credentials or SDKs.

Environment variables

- `HUAWEI_AK` / `HUAWEI_SK` - Access key / secret for OBS and ModelArts (optional
  for dry-run). You can also pass `--ak`/`--sk` to the CLI which sets these in
  the process environment.

OBS

- Create an OBS bucket and ensure the IAM role/user has permission to put
  objects into the bucket. ModelArts training jobs will reference the OBS
  object path `obs://<bucket>/<object>`.

ModelArts

- The lightweight wrapper expects ModelArts/OBS SDKs to be installed if you
  want to run the real submission flow. For CI and local development, prefer
  `--dry-run` which only logs planned actions.

MindSpore / Ascend

- Training on Ascend 910 requires MindSpore and appropriate drivers on the
  training host. This repository intentionally keeps those dependencies gated so
  unit tests run without them. See the Dockerfile in `deployment/modelarts` for
  a starting point.

CLI

- Use the CLI at `deployment/modelarts/deploy_model.py`.

Example (dry-run):

```bash
python -m deployment.modelarts.deploy_model \
  --local-dir ./my_model \
  --obs-bucket my-bucket \
  --obs-prefix jarvis/models \
  --job-name my-test-job \
  --dry-run
```

Next steps and CI

- For full CI that runs training or ModelArts submissions you will need to set
  up a self-hosted runner or hosted image with MindSpore and Ascend support.
  The provided GitHub Actions workflow is a dry-run smoke test that runs the
  CLI unit test.
# ModelArts integration (overview)

This document describes how to use the lightweight ModelArts helpers in this
repository. The code in `backend/integrations/huawei_modelarts.py` is defensive
and supports a dry-run mode so CI and developers can exercise packaging and
submission flows without requiring Huawei credentials or SDKs.

Environment variables
- `HUAWEI_AK` / `HUAWEI_SK` - Access key / secret for OBS and ModelArts (optional
  for dry-run). You can also pass `--ak`/`--sk` to the CLI which sets these in
  the process environment.

OBS
- Create an OBS bucket and ensure the IAM role/user has permission to put
  objects into the bucket. ModelArts training jobs will reference the OBS
  object path `obs://<bucket>/<object>`.

ModelArts
- The lightweight wrapper expects ModelArts/OBS SDKs to be installed if you
  want to run the real submission flow. For CI and local development, prefer
  `--dry-run` which only logs planned actions.

MindSpore / Ascend
- Training on Ascend 910 requires MindSpore and appropriate drivers on the
  training host. This repository intentionally keeps those dependencies gated so
  unit tests run without them. See the Dockerfile in `deployment/modelarts` for
  a starting point.

CLI
- Use the CLI at `deployment/modelarts/deploy_model.py`.

Example (dry-run):

```bash
python -m deployment.modelarts.deploy_model \
  --local-dir ./my_model \
  --obs-bucket my-bucket \
  --obs-prefix jarvis/models \
  --job-name my-test-job \
  --dry-run
```

Next steps and CI
- For full CI that runs training or ModelArts submissions you will need to set
  up a self-hosted runner or hosted image with MindSpore and Ascend support.
  The provided GitHub Actions workflow is a dry-run smoke test that runs the
  CLI unit test.
