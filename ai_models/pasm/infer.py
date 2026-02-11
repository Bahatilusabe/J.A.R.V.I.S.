"""PASM TGNN inference wrapper.

This module provides a small predictor that loads a MindSpore `.mindir`
model when MindSpore is available, and otherwise falls back to a
lightweight deterministic predictor so demos and tests run without
heavy native deps.

Usage:
	from ai_models.pasm.infer import PASMTGNNPredictor
	p = PASMTGNNPredictor()
	p.load()
	preds = p.predict([[0.1]*8, [0.9]*8])

The predictor accepts lists or numpy arrays for features and returns
probabilities in [0,1].
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Iterable, List

logger = logging.getLogger(__name__)


class PASMTGNNPredictor:
	"""Predictor for the pretrained `pasm_tgnn.mindir` model.

	The class is robust: if MindSpore is importable it will attempt to
	load the provided `.mindir`. If not, it falls back to a small
	deterministic logistic-style predictor.
	"""

	def __init__(self, model_path: str | None = None, feature_dim: int = 8, seed: int = 42):
		self.feature_dim = feature_dim
		self.seed = seed
		self._model = None
		self._ms = None
		self._backend = "fallback"

		# default pretrained path inside repository
		if model_path:
			self.model_path = Path(model_path)
		else:
			self.model_path = (
				Path(__file__).resolve().parents[1] / "pretrained" / "pasm_tgnn.mindir"
			)

		# try lazy import of MindSpore
		try:
			import mindspore as ms  # type: ignore

			self._ms = ms
		except Exception:
			self._ms = None

		# deterministic fallback weights
		try:
			import numpy as _np

			rng = _np.random.RandomState(seed)
			self._fallback_w = rng.rand(self.feature_dim).astype(_np.float32)
			self._fallback_b = float(rng.rand(1)[0])
		except Exception:
			# last-resort pure-python fallback
			self._fallback_w = [0.1] * self.feature_dim
			self._fallback_b = 0.1

	def load(self) -> None:
		"""Attempt to load the MindSpore mindir model if possible.

		If loading fails or MindSpore is not available, the predictor
		remains in fallback mode.
		"""
		if self._ms is None:
			logger.debug("MindSpore not available; using fallback predictor")
			self._backend = "fallback"
			return

		# If model file is missing, keep fallback
		if not self.model_path.exists():
			logger.warning("MindSpore model file not found at %s; using fallback", self.model_path)
			self._backend = "fallback"
			return

		ms = self._ms
		try:
			# Try common mindspore loading APIs defensively
			model_obj = None
			if hasattr(ms, "load"):
				try:
					model_obj = ms.load(str(self.model_path))
				except Exception:
					model_obj = None

			# If ms.load didn't work, try train.serialization.load_checkpoint
			if model_obj is None and hasattr(ms, "train"):
				try:
					loader = getattr(ms.train, "serialization", None)
					if loader and hasattr(loader, "load_checkpoint"):
						# load_checkpoint returns param dict for ckpt; mindir may not be supported
						params = loader.load_checkpoint(str(self.model_path))
						model_obj = params
				except Exception:
					model_obj = None

			if model_obj is not None:
				self._model = model_obj
				self._backend = "mindspore"
				logger.info("Loaded MindSpore PASM model from %s", self.model_path)
			else:
				logger.warning("Could not load MindSpore model via known APIs; using fallback")
				self._backend = "fallback"
		except Exception:
			logger.exception("Unexpected error while loading MindSpore model; using fallback")
			self._backend = "fallback"

	def predict(self, X: Iterable[Iterable[float]]) -> List[float]:
		"""Predict probabilities for each input feature vector.

		Returns a list of floats in [0,1].
		"""
		# normalize input to list of lists
		try:
			import numpy as _np

			X_np = _np.array(list(X), dtype=_np.float32)
		except Exception:
			# pure-python fallback: convert manually
			X_np = [list(row) for row in X]

		if self._backend == "mindspore" and self._model is not None:
			try:
				ms = self._ms
				# create tensor and call model if possible
				Tensor = getattr(ms, "Tensor", None)
				if Tensor is not None:
					x_tensor = Tensor(X_np)
					# Many MindSpore models implement call. Try both.
					if callable(self._model):
						out = self._model(x_tensor)
					elif hasattr(self._model, "predict"):
						out = self._model.predict(x_tensor)
					else:
						out = None

					# Try to convert output to numpy array
					if out is not None:
						try:
							# out might be a Tensor
							return list(getattr(out, "asnumpy", lambda: out)().ravel())
						except Exception:
							try:
								return list(out.ravel())
							except Exception:
								pass
			except Exception:
				logger.exception("MindSpore model inference failed; falling back to deterministic predictor")

		# Fallback deterministic logistic predictor
		probs: List[float] = []
		try:
			import numpy as _np

			for row in X_np:
				vec = _np.array(row, dtype=_np.float32)
				# pad/truncate to feature_dim
				if vec.size != self.feature_dim:
					if vec.size < self.feature_dim:
						vec = _np.pad(vec, (0, self.feature_dim - vec.size), mode="constant")
					else:
						vec = vec[: self.feature_dim]
				logit = float((_np.array(self._fallback_w) * vec).sum() + self._fallback_b)
				prob = 1.0 / (1.0 + _np.exp(-logit))
				probs.append(float(prob))
			return probs
		except Exception:
			# last-resort pure-python compute
			for row in X_np:
				s = 0.0
				for i, v in enumerate(row):
					w = self._fallback_w[i] if i < len(self._fallback_w) else 0.1
					s += float(v) * float(w)
				s += float(self._fallback_b)
				# sigmoid
				try:
					prob = 1.0 / (1.0 + (2.718281828459045 ** (-s)))
				except Exception:
					prob = 0.5
				probs.append(prob)
			return probs


		def predict_with_uncertainty(self, X: Iterable[Iterable[float]], n_samples: int = 8, noise_scale: float = 1e-3):
			"""Return (mean_probs, std_probs) using a Monte-Carlo wrapper.

			Uses the `mc_predict` helper which will call `predict` multiple times.
			"""
			try:
				from .uncertainty import mc_predict

				mean, std = mc_predict(lambda x: self.predict(x), X, n_samples=n_samples, noise_scale=noise_scale)
				return mean, std
			except Exception:
				logger.exception("Failed to run predict_with_uncertainty; falling back to deterministic predict")
				preds = self.predict(X)
				return preds, [0.0] * len(preds)


__all__ = ["PASMTGNNPredictor"]
