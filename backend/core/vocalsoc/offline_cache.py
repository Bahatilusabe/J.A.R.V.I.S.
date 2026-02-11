"""Offline speech recognition cache using OpenVINO (gated) for air-gapped nodes.

This module provides a simple, persistent cache for speech-to-text
transcriptions. It is designed for air-gapped or offline nodes and will
use the OpenVINO runtime when available to run a supplied ASR model. The
implementation is intentionally generic so you can plug in different
preprocess/postprocess functions for your specific model.

Key features:
- Persistent cache (JSON index + per-entry text files) keyed by audio SHA256.
- Gated OpenVINO use: module imports OpenVINO at runtime; if unavailable the
  code falls back to a deterministic software-only transcription stub (useful
  for testing and air-gapped dry-runs).
- APIs: preload_model(), transcribe(audio_bytes|path), clear_cache(), export_cache(), import_cache().

Usage sketch:
    cache = OfflineSpeechCache(model_xml="asr.xml", model_bin="asr.bin", device="CPU")
    cache.preload_model(preprocess_fn=my_preprocess, postprocess_fn=my_postprocess)
    text = cache.transcribe(wav_bytes)

Note: real ASR models require model-specific preprocessing (feature extraction)
and postprocessing (CTC decoding, language model rescoring). Provide those
functions when calling `preload_model`.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)
_LOCK = threading.RLock()


class OpenVINOUnavailable(Exception):
    pass


class OfflineSpeechCache:
    """Persistent speech-to-text cache with optional OpenVINO inference.

    Parameters
    - model_xml/model_bin: paths to an OpenVINO IR model (optional).
    - device: OpenVINO device name (default 'CPU').
    - cache_dir: folder to persist cache; defaults to `offline_cache_db` next to this file.
    - max_age_seconds: optional TTL for cached entries (None = never expire).
    """

    def __init__(
        self,
        model_xml: Optional[str] = None,
        model_bin: Optional[str] = None,
        device: str = "CPU",
        cache_dir: Optional[str] = None,
        max_age_seconds: Optional[int] = None,
    ) -> None:
        self.model_xml = model_xml
        self.model_bin = model_bin
        self.device = device
        self.max_age_seconds = max_age_seconds
        base = cache_dir or os.path.join(os.path.dirname(__file__), "offline_cache_db")
        self.cache_dir = os.path.abspath(base)
        self.index_file = os.path.join(self.cache_dir, "index.json")
        self._ensure_cache_dir()

        # OpenVINO runtime objects
        self._ov_core = None
        self._compiled_model = None
        self._infer_request = None
        self._preprocess_fn: Optional[Callable[[bytes], Dict]] = None
        self._postprocess_fn: Optional[Callable[[Dict], str]] = None
        self._ov_available = None

    def _ensure_cache_dir(self) -> None:
        with _LOCK:
            os.makedirs(self.cache_dir, exist_ok=True)
            if not os.path.exists(self.index_file):
                with open(self.index_file, "w", encoding="utf-8") as f:
                    json.dump({}, f)

    def _read_index(self) -> Dict[str, Dict]:
        with _LOCK:
            with open(self.index_file, "r", encoding="utf-8") as f:
                return json.load(f)

    def _write_index(self, idx: Dict[str, Dict]) -> None:
        with _LOCK:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(idx, f, indent=2)

    # -- OpenVINO integration -------------------------------------------
    def _detect_openvino(self) -> bool:
        if self._ov_available is not None:
            return self._ov_available
        try:
            import openvino.runtime as ov  # type: ignore

            self._ov_available = True
        except Exception:
            self._ov_available = False
        return self._ov_available

    def preload_model(self, preprocess_fn: Optional[Callable[[bytes], Dict]] = None, postprocess_fn: Optional[Callable[[Dict], str]] = None) -> None:
        """Load/compile the OpenVINO model and register preprocess/postprocess.

        preprocess_fn: callable that accepts raw audio bytes and returns a dict
          of input_name->numpy array expected by the model.
        postprocess_fn: callable that accepts raw model outputs and returns text.

        If OpenVINO is unavailable this method sets the preprocess/postprocess
        functions if provided; otherwise a software stub is used.
        """
        self._preprocess_fn = preprocess_fn
        self._postprocess_fn = postprocess_fn

        if not self._detect_openvino():
            logger.info("OpenVINO runtime not available; using software fallback")
            return

        try:
            import openvino.runtime as ov  # type: ignore

            self._ov_core = ov.Core()
            if self.model_xml is None and self.model_bin is None:
                logger.warning("No model files specified; OpenVINO available but no model loaded")
                return
            model = self._ov_core.read_model(self.model_xml, self.model_bin) if self.model_bin else self._ov_core.read_model(self.model_xml)
            self._compiled_model = self._ov_core.compile_model(model, self.device)
            # Note: infer request usage depends on model I/O; we create requests lazily
            logger.info("OpenVINO model compiled for device %s", self.device)
        except Exception as e:
            logger.exception("Failed to load/compile OpenVINO model: %s", e)
            self._ov_available = False

    # -- Cache helpers --------------------------------------------------
    def _audio_key(self, audio: bytes) -> str:
        return hashlib.sha256(audio).hexdigest()

    def _cache_text_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.txt")

    def transcribe(self, audio: bytes | str) -> str:
        """Transcribe audio bytes or path; returns cached value when available.

        If `audio` is a string it is treated as a filesystem path and its
        raw bytes are read.
        """
        if isinstance(audio, str):
            if not os.path.exists(audio):
                raise ValueError("Audio path not found: %s" % audio)
            with open(audio, "rb") as f:
                audio_bytes = f.read()
        else:
            audio_bytes = audio

        key = self._audio_key(audio_bytes)
        idx = self._read_index()

        # TTL check
        if key in idx:
            entry = idx[key]
            if self.max_age_seconds is None or (time.time() - entry.get("ts", 0)) <= (self.max_age_seconds or 0):
                text_path = self._cache_text_path(key)
                if os.path.exists(text_path):
                    with open(text_path, "r", encoding="utf-8") as f:
                        return f.read()
            # expired or missing file -> fall through to re-run

        # Not cached: attempt to run model if available
        text = None
        if self._detect_openvino() and self._compiled_model is not None and self._preprocess_fn and self._postprocess_fn:
            try:
                # prepare model input
                inputs = self._preprocess_fn(audio_bytes)
                # compiled_model expects a mapping of input->value
                result = self._compiled_model.infer(inputs)
                text = self._postprocess_fn(result)
            except Exception as e:
                logger.exception("OpenVINO inference failed: %s", e)
                text = None

        if text is None:
            # fallback deterministic transcription stub: human-readable hash fragment
            h = hashlib.sha256(audio_bytes).hexdigest()
            text = f"[offline_stub]{h[:12]}"

        # persist
        text_path = self._cache_text_path(key)
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)
        idx[key] = {"ts": time.time(), "model": self.model_xml or "fallback"}
        self._write_index(idx)
        return text

    # -- Maintenance ----------------------------------------------------
    def clear_cache(self) -> None:
        """Remove all cached entries and reset the index."""
        with _LOCK:
            for fname in os.listdir(self.cache_dir):
                path = os.path.join(self.cache_dir, fname)
                try:
                    os.remove(path)
                except Exception:
                    logger.debug("Failed to remove cache file %s", path)
            # recreate empty index
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def export_cache(self, out_path: str) -> None:
        """Export the cache directory as a tarball (simple copy here).

        For air-gapped transfer you might prefer creating a tar/zip. This
        function simply copies the directory for convenience.
        """
        import shutil

        shutil.copytree(self.cache_dir, out_path, dirs_exist_ok=True)

    def import_cache(self, src_path: str, merge: bool = True) -> None:
        """Import cache contents from another folder. If merge=False replaces current cache."""
        import shutil

        if not merge:
            self.clear_cache()
        shutil.copytree(src_path, self.cache_dir, dirs_exist_ok=True)


__all__ = ["OfflineSpeechCache", "OpenVINOUnavailable"]
