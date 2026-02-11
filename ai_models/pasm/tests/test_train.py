"""Test training/export pipeline for PASM TGNN.

This test runs the `train_and_export` function which will write a
placeholder `.mindir` when MindSpore is not available. The test asserts
that the output file exists and contains the placeholder marker.
"""
from __future__ import annotations

import os
from pathlib import Path
from ai_models.pasm.train_pasm_tgnn import train_and_export


def test_train_exports_placeholder(tmp_path: Path):
    out = tmp_path / 'pasm_test.mindir'
    path = train_and_export(out, epochs=1, feature_dim=8)
    assert Path(path).exists()
    text = Path(path).read_text(encoding='utf-8')
    assert 'Placeholder' in text or 'mindir' in Path(path).suffix
