"""PASM TGNN model definition and helpers.

This module provides a tiny MLP that can be instantiated in MindSpore
when available. It also exposes a fallback pure-Python callable that
mimics a trained model for environments without MindSpore.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from .gnn_ops import GraphSAGE, GAT

logger = logging.getLogger(__name__)


def get_mindspore_model(ms=None, input_dim: int = 8, hidden: int = 64, use_gat: bool = False, out_feats: int = 2):
    """Return a graph-based model either as a MindSpore Cell (when `ms` is
    provided and MindSpore is importable) or as a NumPy-backed fallback when
    `ms` is None.

    This function favors GraphSAGE by default; set `use_gat=True` to get a
    GAT-style cell instead. The returned MindSpore object (when `ms` present)
    exposes a `construct(X, A)` method. The fallback path returns a small
    wrapper that exposes `predict_proba(X, A=None)` for compatibility with
    existing tests and code.
    """
    # MindSpore path: build a graph operator cell
    try:
        if ms is not None:
            if use_gat:
                cell = GAT(in_feats=input_dim, out_feats=out_feats, ms_module=ms)
            else:
                cell = GraphSAGE(in_feats=input_dim, out_feats=out_feats, hidden=hidden, ms_module=ms)
            # the gnn_ops classes keep the built MindSpore cell under `.cell`
            return getattr(cell, "cell", cell)
        # Fallback path: return a wrapper that is compatible with previous
        # `FallbackModel.predict_proba(X)` semantics.
        return GraphFallbackModel(input_dim=input_dim, hidden=hidden, use_gat=use_gat, out_feats=out_feats)
    except Exception:
        logger.exception("Failed to build graph model")
        raise


class GraphFallbackModel:
    """Wrap GraphSAGE/GAT NumPy fallback to provide `predict_proba`.

    The wrapper will create a trivial adjacency (self-loops) if none is
    provided. After running the GNN operator it applies a tiny logistic head
    to produce two-class probabilities.
    """

    def __init__(self, input_dim: int = 8, hidden: int = 64, use_gat: bool = False, out_feats: int = 2):
        self.input_dim = input_dim
        self.hidden = hidden
        self.use_gat = use_gat
        self.out_feats = out_feats
        if use_gat:
            self.op = GAT(in_feats=input_dim, out_feats=out_feats, ms_module=None)
        else:
            self.op = GraphSAGE(in_feats=input_dim, out_feats=out_feats, hidden=hidden, ms_module=None)
        # small linear head weights
        import numpy as _np

        self.np = _np
        self.w_head = self.np.ones((out_feats, 1)) * 0.1
        self.bias = 0.0

    def predict_proba(self, X, A=None):
        X = self.np.asarray(X)
        N = X.shape[0]
        if A is None:
            A = self.np.eye(N, dtype=float)
        h = self.op(X, A)  # (N, out_feats)
        logits = (h @ self.w_head).reshape((N,)) + float(self.bias)
        # sigmoid
        probs = 1.0 / (1.0 + self.np.exp(-logits))
        out = self.np.stack([1 - probs, probs], axis=1)
        return out


class FallbackModel:
    """A tiny deterministic model used when MindSpore isn't available.

    It stores weights and provides a `predict_proba` method returning
    probabilities for binary classification.
    """

    def __init__(self, weights=None, bias: float = 0.0):
        if weights is None:
            # simple default weights
            self.weights = [0.1] * 8
        else:
            self.weights = list(weights)
        self.bias = float(bias)

    def predict_proba(self, X):
        # X: iterable of feature iterables
        out = []
        for row in X:
            s = self.bias
            for i, v in enumerate(row):
                w = self.weights[i] if i < len(self.weights) else 0.1
                s += float(v) * float(w)
            # sigmoid
            try:
                p = 1.0 / (1.0 + 2.718281828459045 ** (-s))
            except Exception:
                p = 0.5
            out.append([1 - p, p])
        return out


__all__ = ["get_mindspore_model", "FallbackModel"]
