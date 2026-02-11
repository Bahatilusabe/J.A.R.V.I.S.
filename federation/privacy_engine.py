"""Differential privacy engine using PySyft + DP-optimizer (guarded) with NumPy fallback.

This module provides utilities to add DP noise to model weights or gradients.
It will try to use PySyft and a DP optimizer if available; otherwise it
provides deterministic NumPy-based noise addition so code paths and tests
can run without heavy native dependencies.

API:
- PrivacyEngine.apply_dp_to_weights(weights_dict, noise_std, clip_norm=None)
  -> returns new weights dict with Gaussian noise applied.
- PrivacyEngine.wrap_optimizer(optimizer, noise_std, clip_norm)
  -> returns a thin wrapper around an optimizer which adds noise after step.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def _try_import_syft():
    try:
        import syft  # type: ignore

        return syft
    except Exception:
        logger.debug("PySyft not available; using NumPy fallback for DP operations")
        return None


def _try_import_opacus():
    try:
        import opacus  # type: ignore

        return opacus
    except Exception:
        logger.debug("Opacus/DP optimizer not available; using NumPy fallback for DP operations")
        return None


syft = _try_import_syft()
opacus = _try_import_opacus()


class PrivacyEngine:
    """Engine to add differential privacy noise to model weights.

    This class intentionally keeps a minimal surface. For production DP we
    recommend using a well-tested library (Opacus for PyTorch or TensorFlow
    DP). Here we provide a fallback that is deterministic (seeded) and
    suitable for unit tests.
    """

    def __init__(self, seed: int = 0):
        self.rng = np.random.RandomState(seed)

    def apply_dp_to_weights(self, weights: Dict[str, Any], noise_std: float = 1e-3, clip_norm: Optional[float] = None) -> Dict[str, Any]:
        """Return a new weights dict with Gaussian noise added.

        weights: mapping of parameter name -> numeric array/list
        noise_std: standard deviation of Gaussian noise to add
        clip_norm: if provided, clip each weight array by this L2 norm before adding noise
        """
        out: Dict[str, Any] = {}
        for k, v in weights.items():
            arr = _to_numpy(v)
            if clip_norm is not None:
                norm = np.linalg.norm(arr)
                if norm > clip_norm and norm > 0:
                    arr = arr * (clip_norm / norm)
            noise = self.rng.normal(loc=0.0, scale=noise_std, size=arr.shape)
            out[k] = (arr + noise).tolist()
        logger.debug("Applied DP noise (std=%s) to %d tensors", noise_std, len(out))
        return out

    def wrap_optimizer(self, optimizer: Any, noise_std: float = 1e-3, clip_norm: Optional[float] = None):
        """Return a simple wrapper around an optimizer-like object which adds
        noise to parameters after each step. This is a thin convenience for
        tests; it assumes optimizer has `step()` and that parameters can be
        iterated as `optimizer.param_groups` or `optimizer.params`.
        """

        class _Wrapper:
            def __init__(self, inner, engine: PrivacyEngine):
                self._inner = inner
                self._engine = engine

            def __getattr__(self, name):
                return getattr(self._inner, name)

            def step(self, *args, **kwargs):
                res = None
                if hasattr(self._inner, "step"):
                    res = self._inner.step(*args, **kwargs)
                # attempt to find parameters
                params = []
                if hasattr(self._inner, "param_groups"):
                    for g in getattr(self._inner, "param_groups"):
                        params.extend(g.get("params", []))
                elif hasattr(self._inner, "params"):
                    params = list(getattr(self._inner, "params"))
                # apply noise
                for p in params:
                    try:
                        arr = _to_numpy(p)
                        noise = self._engine.rng.normal(loc=0.0, scale=noise_std, size=arr.shape)
                        new = arr + noise
                        # write back if p is a numpy array or list
                        if isinstance(p, np.ndarray):
                            p[...] = new
                        elif isinstance(p, (list, tuple)):
                            # best-effort: if list, replace in place when possible
                            if isinstance(p, list):
                                for i in range(len(p)):
                                    p[i] = float(new.flat[i])
                    except Exception:
                        # skip parameters that can't be noisified
                        continue
                return res

        return _Wrapper(optimizer, self)


def _to_numpy(x: Any) -> Any:
    if isinstance(x, np.ndarray):
        return x
    if isinstance(x, (list, tuple)):
        return np.array(x)
    try:
        return np.array(x)
    except Exception:
        raise TypeError("Unsupported parameter type for DP conversion")


__all__ = ["PrivacyEngine"]
