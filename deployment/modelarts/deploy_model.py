"""CLI for packaging and submitting ModelArts training jobs (dry-run capable).

This script wraps `backend.integrations.huawei_modelarts.example_flow` and
provides a small CLI for CI and developer use. It defaults to dry-run so it is
safe to invoke in CI without credentials.

Usage examples:
  python -m deployment.modelarts.deploy_model --local-dir ./model --obs-bucket my-bucket --obs-prefix jarvis/models --job-name test-job --dry-run

The module exposes a `main` function for programmatic invocation (useful in
unit tests).
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Optional

from backend.integrations import huawei_modelarts as modelarts

logger = logging.getLogger("jarvis.deploy.modelarts")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Package and submit a ModelArts training job (dry-run by default)")
    p.add_argument("--local-dir", required=True, help="Local directory containing the model to package")
    p.add_argument("--obs-bucket", required=True, help="Target OBS bucket (e.g., my-bucket)")
    p.add_argument("--obs-prefix", default="jarvis/models", help="OBS prefix/path under the bucket")
    p.add_argument("--job-name", required=True, help="ModelArts training job name")
    p.add_argument("--dry-run", action="store_true", help="Only log actions, do not call cloud APIs")
    p.add_argument("--explain-path", help="Optional local explanation artifact to upload (JSON/HTML/image)")
    p.add_argument("--explain-obs-prefix", default="jarvis/explanations", help="OBS prefix for explanation artifacts")
    p.add_argument("--explain-format", choices=["json", "html", "png", "jpg"], help="Optional format/mime hint for the explanation artifact")
    p.add_argument("--ak", help="Optional Huawei AK (will set HUAWEI_AK for the process)")
    p.add_argument("--sk", help="Optional Huawei SK (will set HUAWEI_SK for the process)")
    p.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    # Input validation
    if not args.local_dir or not os.path.exists(args.local_dir):
        logger.error("Local model directory does not exist: %s", args.local_dir)
        return 1
    if not os.path.isdir(args.local_dir):
        logger.error("Local model path is not a directory: %s", args.local_dir)
        return 1
    # ensure directory is non-empty
    try:
        if not any(os.scandir(args.local_dir)):
            logger.error("Local model directory is empty: %s", args.local_dir)
            return 1
    except PermissionError:
        logger.exception("Permission denied checking local model directory: %s", args.local_dir)
        return 1

    if not args.obs_bucket:
        logger.error("OBS bucket name must be provided")
        return 1
    if not args.job_name:
        logger.error("Job name must be provided")
        return 1

    # Apply AK/SK flags to environment so downstream code can rely on them
    if args.ak:
        os.environ["HUAWEI_AK"] = args.ak
        logger.debug("Set HUAWEI_AK from CLI flag")
    if args.sk:
        os.environ["HUAWEI_SK"] = args.sk
        logger.debug("Set HUAWEI_SK from CLI flag")

    # If not dry-run, ensure credentials exist
    if not args.dry_run:
        ak = os.environ.get("HUAWEI_AK")
        sk = os.environ.get("HUAWEI_SK")
        if not ak or not sk:
            logger.error("HUAWEI_AK and HUAWEI_SK must be set for non-dry-run submissions")
            return 3

    try:
        # Delegate to example_flow which supports explanation upload and
        # metadata registration; it will perform all actions and return a
        # summary describing uploads and the created job.
        summary = modelarts.example_flow(
            args.local_dir,
            args.obs_bucket,
            args.obs_prefix,
            args.job_name,
            dry_run=args.dry_run,
            explain_path=args.explain_path,
            explain_obs_prefix=args.explain_obs_prefix,
            explain_format=args.explain_format,
        )

        logger.info("ModelArts flow result: %s", summary)
        return 0
    except Exception as e:
        logger.exception("ModelArts flow failed: %s", e)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
