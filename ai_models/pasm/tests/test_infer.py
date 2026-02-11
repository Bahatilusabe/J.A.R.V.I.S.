"""Unit test for PASM TGNN inference wrapper.

The test asserts that predictions are returned and are probabilities.
It is written to work without MindSpore installed (uses fallback).
"""
from __future__ import annotations

import os
from ai_models.pasm.infer import PASMTGNNPredictor


def test_pasm_predictor_basic():
    # Instantiate predictor and ensure load() is safe
    p = PASMTGNNPredictor()
    p.load()

    # Two simple rows of features
    X = [[0.1] * p.feature_dim, [0.9] * p.feature_dim]
    preds = p.predict(X)

    assert len(preds) == 2
    for v in preds:
        assert isinstance(v, float)
        assert 0.0 <= v <= 1.0


def test_pasm_predictor_shape_mismatch():
    p = PASMTGNNPredictor()
    p.load()
    # shorter and longer inputs should be padded/truncated
    X = [[0.2] * (p.feature_dim - 2), [0.5] * (p.feature_dim + 3)]
    preds = p.predict(X)
    assert len(preds) == 2
    for v in preds:
        assert 0.0 <= v <= 1.0
