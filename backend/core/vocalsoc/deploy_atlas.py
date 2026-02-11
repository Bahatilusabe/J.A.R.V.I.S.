"""Deployment helpers for Atlas Edge 500 (Ascend) for low-latency speech processing.

This module outlines steps to convert MindSpore/onnx models to Ascend .om
artifacts, package runtime files, and provides a helper to create a bundle
that operators can deploy to Atlas Edge devices.

Note: actual conversion to .om requires Ascend toolchain and is not executed
here. The helper emits a reproducible checklist and packages files for transport.
"""

from __future__ import annotations

import os
import shutil
import tarfile
from typing import List, Optional

DEFAULT_ATLAS_FILES = [
    "offline_cache_db/",
    "voice_auth_db/",
    "asr_model_om/",
    "pasm_model_om/",
]


def make_atlas_bundle(source_root: str, out_path: str, include_files: Optional[List[str]] = None) -> str:
    voc_root = os.path.join(source_root, "backend", "core", "vocalsoc")
    if include_files is None:
        include_files = DEFAULT_ATLAS_FILES

    staging = out_path + ".staging"
    if os.path.exists(staging):
        shutil.rmtree(staging)
    os.makedirs(staging, exist_ok=True)

    for rel in include_files:
        src = os.path.join(voc_root, rel)
        if not os.path.exists(src):
            continue
        dest = os.path.join(staging, os.path.basename(rel.rstrip('/')))
        if os.path.isdir(src):
            shutil.copytree(src, dest)
        else:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)

    with tarfile.open(out_path, "w:gz") as tar:
        tar.add(staging, arcname=os.path.basename(staging))

    shutil.rmtree(staging)
    return out_path


def conversion_checklist() -> str:
    return (
        """Ascend deployment checklist:
  - Install Ascend toolchain and set environment (source setenv.sh from Ascend package).
  - Convert MindSpore/ONNX models to .om using ATC:
      atc --framework=5 --model=model.onnx --output=model_ascend --soc_version=Ascend310
  - Verify .om artifacts with a small inference harness on the target board.
  - Optimize for batch size=1 and enable precision tuning (quantization) if needed.

Include the .om files and a small inference harness (preprocess/postprocess) in the bundle.
"""
    )


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Create Atlas Edge deploy bundle for vocalsoc")
    p.add_argument("--root", default=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
    p.add_argument("--out", required=True)
    args = p.parse_args()
    out = make_atlas_bundle(args.root, args.out)
    print("Wrote:", out)
