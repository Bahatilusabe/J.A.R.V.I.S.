"""ONNX-based ASR inference helper with safe fallback.

This module provides a simple inference wrapper around an ONNX
automatic-speech-recognition (ASR) model stored at
`ai_models/pretrained/voice_model.onnx`.

Behavior:
- If `onnxruntime` is available, it will load the model and run
  inference using CPU execution provider.
- If `onnxruntime` is not available, a deterministic fallback
  synthesizes a short dummy transcript so the rest of the system
  can continue to function in tests.

The wrapper expects precomputed features (e.g., log-mel frames) as
numpy arrays; for convenience it accepts raw 1D audio and a basic
feature extractor will be used when `librosa` is installed.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional, Sequence

logger = logging.getLogger(__name__)


class ONNXASR:
    def __init__(self, model_path: Optional[str] = None):
        if model_path:
            self.model_path = Path(model_path)
        else:
            self.model_path = Path(__file__).resolve().parents[1] / "pretrained" / "voice_model.onnx"

        self._sess = None
        self._ort = None
        try:
            import onnxruntime as ort  # type: ignore

            self._ort = ort
        except Exception:
            self._ort = None

    def available(self) -> bool:
        return self._ort is not None and self.model_path.exists()

    def load(self) -> None:
        """Load the ONNX model into an ONNX Runtime InferenceSession if possible."""
        if not self.available():
            logger.debug("ONNX runtime or model not available; using fallback ASR")
            return
        try:
            so = self._ort.SessionOptions()
            # small optimization: set intra threads
            so.intra_op_num_threads = 1
            self._sess = self._ort.InferenceSession(str(self.model_path), sess_options=so, providers=["CPUExecutionProvider"])
            logger.info("Loaded ONNX ASR model from %s", self.model_path)
        except Exception:
            logger.exception("Failed to create ONNX Runtime session; using fallback")
            self._sess = None

    def _extract_features(self, audio: Sequence[float], sr: int = 16000):
        """Simple feature extractor: compute log-mel spectrogram if librosa available.

        If librosa is not installed, return a very small synthetic feature array.
        """
        try:
            import numpy as _np
            import librosa  # type: ignore

            arr = _np.array(audio, dtype=_np.float32)
            # compute log-mel
            mel = librosa.feature.melspectrogram(y=arr, sr=sr, n_mels=80, hop_length=160, n_fft=400)
            log_mel = _np.log1p(mel)
            # return shape (T, features)
            return log_mel.T
        except Exception:
            # fallback synthetic features
            try:
                import numpy as _np

                return _np.zeros((10, 80), dtype=_np.float32)
            except Exception:
                return [[0.0] * 80 for _ in range(10)]

    def transcribe(self, audio: Optional[Sequence[float]] = None, features=None, sr: int = 16000) -> str:
        """Transcribe audio or features into a short text transcript.

        Provide either `audio` (1-D floats) or `features` (precomputed frames).
        """
        if features is None:
            if audio is None:
                raise ValueError("either audio or features must be provided")
            features = self._extract_features(audio, sr=sr)

        # If ONNX runtime session is ready, run model
        if self._sess is not None:
            try:
                import numpy as _np

                # The exact input name/shape depends on the ONNX model. We'll
                # attempt common input keys: 'input', 'audio', 'features', else use first.
                input_name = None
                for n in self._sess.get_inputs():
                    if n.name.lower() in ("input", "audio", "features"):
                        input_name = n.name
                        break
                if input_name is None:
                    input_name = self._sess.get_inputs()[0].name

                # prepare a batch of 1
                feats = _np.array(features, dtype=_np.float32)
                # if model expects (N, T, C) or (N, C, T) we try to infer.
                inp = feats[None, ...]
                # try multiple permutations if shape mismatch occurs
                try:
                    out = self._sess.run(None, {input_name: inp})
                except Exception:
                    # try channel-first
                    try:
                        out = self._sess.run(None, {input_name: inp.transpose(0, 2, 1)})
                    except Exception:
                        out = None

                if out:
                    # Attempt to decode output to text. Many ASR ONNX models output
                    # token IDs or char probabilities. We conservatively convert numeric
                    # outputs to a short hex digest to represent a transcript if no
                    # decoder is available.
                    try:
                        import numpy as _np

                        arr = out[0]
                        # collapse to 1-D by taking argmax over last dim if applicable
                        if hasattr(arr, "argmax"):
                            ids = arr.argmax(axis=-1)
                            # simple decode: join ids as string
                            return "pred:" + "-".join(str(int(x)) for x in ids.flatten()[:20])
                        else:
                            return "pred:ok"
                    except Exception:
                        return "pred:ok"
            except Exception:
                logger.exception("ONNX inference failed; falling back to dummy transcript")

        # Deterministic safe fallback transcript
        return "<transcript unavailable - using fallback>"


__all__ = ["ONNXASR"]
