"""Graph neural network operator implementations: GraphSAGE and (single-head) GAT.

This module provides lightweight implementations using MindSpore primitives when
MindSpore is available, and NumPy fallbacks for environments without MindSpore.

APIs:
 - GraphSAGE(in_feats, out_feats, hidden=None, ms=None)
 - GAT(in_feats, out_feats, num_heads=1, ms=None)

Both classes expose a `Cell`-like callable interface for MindSpore (ms.nn.Cell)
and a plain Python `__call__(X, A)` for NumPy fallback where X is (N, F) and A is
an adjacency matrix (N, N) with 0/1 or weights. The implementations are kept
simple and deterministic so tests can run without heavy dependencies.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _try_import_mindspore():
    try:
        import mindspore as ms

        return ms
    except Exception:
        return None


ms = _try_import_mindspore()


class GraphSAGE:
    """Simple GraphSAGE-style aggregator.

    MindSpore usage: instantiate with ms provided (or autodetected) and the
    returned object will be an `ms.nn.Cell`-like object with a `construct(X, A)`
    method.

    NumPy fallback: calling the instance as a function `callable(X, A)` returns
    a new feature matrix of shape (N, out_feats).
    """

    def __init__(self, in_feats: int, out_feats: int, hidden: Optional[int] = None, ms_module=None):
        self.in_feats = in_feats
        self.out_feats = out_feats
        self.hidden = hidden or max(in_feats, out_feats)
        self.ms = ms_module or ms

        if self.ms is not None:
            # build MindSpore cell
            import mindspore.nn as nn
            import mindspore.ops as ops

            class _SageCell(self.ms.nn.Cell):
                def __init__(self, in_f, hid, out_f):
                    super().__init__()
                    self.fc_neigh = nn.Dense(in_f, hid)
                    self.fc_self = nn.Dense(in_f, hid)
                    self.act = nn.ReLU()
                    self.fc_out = nn.Dense(hid * 2, out_f)
                    self.matmul = ops.MatMul()
                    self.reduce_sum = ops.ReduceSum(keep_dims=True)

                def construct(self, X, A):
                    # X: (N, F), A: (N, N)
                    deg = self.reduce_sum(A, 1) + 1e-6
                    neigh = self.matmul(A, X) / deg
                    h_neigh = self.fc_neigh(neigh)
                    h_self = self.fc_self(X)
                    h = ops.Concat(1)((h_self, h_neigh))
                    h = self.act(self.fc_out(h))
                    return h

            self.cell = _SageCell(self.in_feats, self.hidden, self.out_feats)
        else:
            # NumPy fallback: store simple linear weights
            import numpy as _np

            self.np = _np
            self.w_self = self.np.ones((self.in_feats, self.hidden)) * 0.1
            self.w_neigh = self.np.ones((self.in_feats, self.hidden)) * 0.1
            self.w_out = self.np.ones((self.hidden * 2, self.out_feats)) * 0.1

    def __call__(self, X, A):
        if self.ms is not None:
            # MindSpore path expects tensors; delegate to cell.construct
            return self.cell.construct(X, A)
        # NumPy fallback
        X = self.np.asarray(X)
        A = self.np.asarray(A)
        deg = A.sum(axis=1, keepdims=True) + 1e-6
        neigh = (A @ X) / deg
        h_self = X @ self.w_self
        h_neigh = neigh @ self.w_neigh
        h = self.np.concatenate([h_self, h_neigh], axis=1)
        # ReLU
        h = self.np.maximum(h @ self.w_out, 0.0)
        return h


class GAT:
    """Single-head Graph Attention (GAT) lightweight implementation.

    Notes: This is a simplified single-head GAT for clarity and testability. The
    attention uses a learnable vector `a` applied after a linear transform W.
    """

    def __init__(self, in_feats: int, out_feats: int, num_heads: int = 1, ms_module=None):
        self.in_feats = in_feats
        self.out_feats = out_feats
        self.ms = ms_module or ms
        self.num_heads = num_heads

        if self.ms is not None:
            import mindspore.nn as nn
            import mindspore.ops as ops

            class _GATCell(self.ms.nn.Cell):
                def __init__(self, in_f, out_f):
                    super().__init__()
                    self.W = nn.Dense(in_f, out_f, has_bias=False)
                    self.a = nn.Dense(out_f * 2, 1, has_bias=False)
                    self.leaky = nn.LeakyReLU(alpha=0.2)
                    self.softmax = ops.Softmax(axis=1)
                    self.matmul = ops.MatMul()

                def construct(self, X, A):
                    # X: (N, F) ; A: (N, N)
                    h = self.W(X)  # (N, out_f)
                    N = h.shape[0]
                    # compute pairwise concat [h_i || h_j] -> (N, N, 2*out_f)
                    h_i = ops.ExpandDims()(h, 1)  # (N,1,out_f)
                    h_j = ops.ExpandDims()(h, 0)  # (1,N,out_f)
                    h_cat = ops.Concat(2)((h_i.broadcast_to((N, N, h.shape[1])),
                                           h_j.broadcast_to((N, N, h.shape[1]))))
                    e = self.a(h_cat.reshape((-1, h_cat.shape[2])))
                    e = e.reshape((N, N))
                    e = self.leaky(e)
                    # mask with adjacency: set -1e9 for non-edges
                    mask = (A > 0).astype(e.dtype)
                    neg_inf = ms.Tensor(-1e9, dtype=e.dtype)
                    e = e * mask + (1 - mask) * neg_inf
                    alpha = self.softmax(e)
                    out = alpha @ h
                    return out

            self.cell = _GATCell(self.in_feats, self.out_feats)
        else:
            import numpy as _np

            self.np = _np
            # deterministic small weights
            self.W = self.np.ones((self.in_feats, self.out_feats)) * 0.1
            self.a = self.np.ones((self.out_feats * 2, 1)) * 0.1

    def __call__(self, X, A):
        if self.ms is not None:
            return self.cell.construct(X, A)
        X = self.np.asarray(X)
        A = self.np.asarray(A)
        h = X @ self.W  # (N, out_f)
        N = h.shape[0]
        # compute pairwise concat
        h_i = _broadcast_axis(h, 1)
        h_j = _broadcast_axis(h, 0)
        h_cat = self.np.concatenate([h_i, h_j], axis=2)  # (N, N, 2*out_f)
        e = h_cat.reshape((-1, h_cat.shape[2])) @ self.a
        e = e.reshape((N, N))
        # leaky relu
        e = self.np.where(e > 0, e, 0.2 * e)
        # mask
        mask = (A > 0).astype(float)
        neg_inf = -1e9
        e = e * mask + (1 - mask) * neg_inf
        # softmax over neighbors
        exp = self.np.exp(e - e.max(axis=1, keepdims=True)) * mask
        alpha = exp / (exp.sum(axis=1, keepdims=True) + 1e-9)
        out = alpha @ h
        return out


def _broadcast_axis(arr, axis):
    """Helper to expand array for pairwise concatenation.

    arr: (N, F)
    axis: 0 or 1
    returns: (N, N, F)
    """
    import numpy as _np

    if axis == 0:
        return _np.expand_dims(arr, 0).repeat(arr.shape[0], axis=0)
    return _np.expand_dims(arr, 1).repeat(arr.shape[0], axis=1)


__all__ = ["GraphSAGE", "GAT"]
