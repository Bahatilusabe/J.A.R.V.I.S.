"""Tests for ONNX ASR inference wrapper (fallback-friendly)."""
from __future__ import annotations

from ai_models.asr.onnx_infer import ONNXASR


def test_onnx_fallback_transcribe():
    asr = ONNXASR()
    # don't load (onnxruntime likely missing), use fallback
    text = asr.transcribe(features=[[0.0]*80 for _ in range(5)])
    assert isinstance(text, str)
    assert 'fallback' in text or text.startswith('<transcript')
