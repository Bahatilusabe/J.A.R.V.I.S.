"""Simple uncertainty helpers (MC-dropout style wrapper).

Provides a lightweight Monte-Carlo wrapper that calls a predictor multiple
times and returns mean and std of predictions. For deterministic predictors
this wrapper will add tiny input noise to produce a bootstrap-like spread.
"""
from __future__ import annotations

import logging
from typing import Callable, Iterable, List, Tuple

logger = logging.getLogger(__name__)


def mc_predict(predict_fn: Callable[[Iterable], List[float]], X: Iterable, n_samples: int = 8, noise_scale: float = 1e-3):
    """Run `predict_fn` multiple times and return (mean_list, std_list).

    - predict_fn: callable accepting an iterable of feature rows and returning
      a list of floats (scores).
    - X: iterable of feature rows.
    - n_samples: number of Monte Carlo runs.
    - noise_scale: std dev of Gaussian noise added to inputs for deterministic models.
    """
    try:
        import numpy as _np
    except Exception:
        _np = None

    # Convert X to list for repeated sampling
    X_list = list(X)
    N = len(X_list)
    all_preds: List[List[float]] = []

    for i in range(max(1, int(n_samples))):
        X_pert = X_list
        if _np is not None and noise_scale and noise_scale > 0:
            # add tiny noise per-run
            X_pert = [(_np.asarray(row, dtype=float) + _np.random.normal(scale=noise_scale, size=len(row))).tolist() for row in X_list]

        try:
            preds = list(predict_fn(X_pert))
        except Exception:
            logger.exception("predict_fn failed during mc sampling")
            preds = [0.0] * N

        # ensure length N
        if len(preds) != N:
            # try to pad/truncate
            preds = (preds + [0.0] * N)[:N]

        all_preds.append(preds)

    # aggregate
    if _np is not None:
        arr = _np.array(all_preds)
        mean = arr.mean(axis=0).tolist()
        std = arr.std(axis=0).tolist()
    else:
        # fallback pure-Python
        mean = [sum(col) / len(col) for col in zip(*all_preds)]
        import math

        std = [math.sqrt(sum((v - m) ** 2 for v in col) / max(1, len(col))) for col, m in zip(zip(*all_preds), mean)]

    return mean, std


__all__ = ["mc_predict"]
