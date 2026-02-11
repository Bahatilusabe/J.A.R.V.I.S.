"""Evaluation utilities for PASM TGNN: Precision@k and simple harness.

Provides a small evaluation harness to compute Precision@k on a list of
graphs and binary labels using a provided predictor.
"""
from __future__ import annotations

from typing import Callable, Iterable, List, Tuple
import logging

logger = logging.getLogger(__name__)


def precision_at_k(labels: List[int], scores: List[float], k: int = 5) -> float:
    """Compute global Precision@k across the dataset.

    Args:
      labels: list of 0/1 ground-truth labels (1 = positive/high-risk)
      scores: predicted scores (higher means more likely positive)
      k: number of top items to consider

    Returns:
      precision@k (float between 0 and 1)
    """
    if len(labels) == 0:
        return 0.0
    # sort by scores desc
    paired = list(zip(labels, scores))
    paired.sort(key=lambda x: x[1], reverse=True)
    topk = paired[:max(1, min(k, len(paired)))]
    if len(topk) == 0:
        return 0.0
    tp = sum(int(l) for l, _ in topk)
    return float(tp) / float(len(topk))


def evaluate_predictor(predict_fn: Callable[[Iterable], List[float]], graphs: Iterable, labels: List[int], k: int = 5) -> Tuple[float, List[float]]:
    """Run predictor on graphs and compute precision@k.

    Returns (precision_at_k, scores)
    """
    graphs = list(graphs)
    if len(graphs) != len(labels):
        raise ValueError("graphs and labels must have the same length")

    scores = []
    for g in graphs:
        try:
            res = predict_fn(g)
            # predict_fn may return a dict or single float/list; normalize
            if isinstance(res, dict) and "score" in res:
                scores.append(float(res["score"]))
            elif isinstance(res, (list, tuple)):
                # assume first element or single score per graph
                scores.append(float(res[0]))
            else:
                scores.append(float(res))
        except Exception:
            logger.exception("predict_fn failed on a graph; using score 0.0")
            scores.append(0.0)

    p_at_k = precision_at_k(labels, scores, k=k)
    return p_at_k, scores


__all__ = ["precision_at_k", "evaluate_predictor"]
