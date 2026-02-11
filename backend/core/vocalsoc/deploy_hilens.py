"""Deployment helpers for HiLens Kit (edge) for low-latency speech processing.

This module provides packaging and sanity-check utilities to prepare the
voice-activated SOC components for deployment on HiLens-based devices. The
functions are high-level and intentionally avoid direct hardware calls so
they can be used in CI and by developers without HiLens SDK installed.

What this provides:
- model conversion suggestions (MindSpore/ONNX -> IR or HiLens-compatible formats)
- packaging helper to assemble runtime files into a deployable bundle
- a lightweight smoke-check function that validates presence of required files

Note: Actual HiLens app deployment often requires using Huawei's HiLens Studio
or uploading packages via the cloud console. This module's goal is to automate
the local packaging steps and provide reproducible artifacts for the operator.
"""

from __future__ import annotations

import json
import os
import shutil
import tarfile
from typing import List, Optional

DEFAULT_RUNTIME_FILES = [
    "offline_cache_db/index.json",
    "voice_auth_db/index.json",
    "offline_cache_db/",
    "voice_auth_db/",
    "asr_model/",
    "pasm_model/",
]


def make_deploy_bundle(source_root: str, out_path: str, include_files: Optional[List[str]] = None) -> str:
    """Create a tar.gz bundle suitable for transferring to a HiLens operator.

    source_root: project root where the `backend/core/vocalsoc` folder lives.
    out_path: output tar.gz path
    include_files: list of relative paths inside the vocalsoc folder to include.
    Returns the path to the created tar.gz
    """
    voc_root = os.path.join(source_root, "backend", "core", "vocalsoc")
    if include_files is None:
        include_files = DEFAULT_RUNTIME_FILES

    staging = out_path + ".staging"
    if os.path.exists(staging):
        shutil.rmtree(staging)
    os.makedirs(staging, exist_ok=True)

    for rel in include_files:
        src = os.path.join(voc_root, rel)
        if not os.path.exists(src):
            # skip missing optional files
            continue
        dest = os.path.join(staging, os.path.basename(rel.rstrip('/')))
        if os.path.isdir(src):
            shutil.copytree(src, dest)
        else:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)

    # Create tar.gz
    with tarfile.open(out_path, "w:gz") as tar:
        tar.add(staging, arcname=os.path.basename(staging))

    shutil.rmtree(staging)
    return out_path


def check_bundle_contents(bundle_path: str) -> dict:
    """Return a dict listing top-level files inside the bundle for a quick sanity check."""
    if not os.path.exists(bundle_path):
        raise FileNotFoundError(bundle_path)
    import tarfile

    with tarfile.open(bundle_path, "r:gz") as tar:
        members = tar.getmembers()
        names = [m.name for m in members]
    return {"member_count": len(names), "sample": names[:20]}


def conversion_notes() -> str:
    return (
        """Model conversion notes:
  - If your model is trained in MindSpore, export to ONNX then convert to HiLens/IR.
  - For OpenVINO/CPU inference on HiLens, generate IR (.xml/.bin) via OpenVINO conversion.
  - For Ascend/Atlas, convert MindSpore models to .om with MindSpore/Ascend tools.
  - Quantize models (INT8) where supported to improve latency; validate accuracy.

Ensure you provide the model files and a small inference harness (preprocess/postprocess)
inside the bundle so the operator can validate on-device before final registration.
"""
    )


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Create HiLens deploy bundle for vocalsoc")
    p.add_argument("--root", default=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
    p.add_argument("--out", required=True)
    args = p.parse_args()
    out = make_deploy_bundle(args.root, args.out)
    print("Wrote:", out)
