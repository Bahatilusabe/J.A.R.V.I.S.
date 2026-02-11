"""Multi-head temporal attention encoder (MindSpore + NumPy fallback).

Provides a compact MultiHeadTemporalAttention class exposing an
`encode(sequence)` method where `sequence` is shape (T, D) and the return
is a 1D embedding vector for the sequence.

This implementation is intentionally lightweight to be testable in CI and
to provide a MindSpore-compatible Cell when MindSpore is available.
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


class MultiHeadTemporalAttention:
    def __init__(self, input_dim: int = 8, n_heads: int = 4, head_dim: int = 8, ms_module=None):
        self.input_dim = input_dim
        self.n_heads = n_heads
        self.head_dim = head_dim
        self.out_dim = n_heads * head_dim
        self.ms = ms_module or ms

        if self.ms is not None:
            # MindSpore cell implementation
            import mindspore.nn as nn
            import mindspore.ops as ops

            class _MHTCell(self.ms.nn.Cell):
                def __init__(self, in_dim, heads, hdim, out_dim):
                    super().__init__()
                    self.heads = heads
                    self.hdim = hdim
                    self.q_proj = nn.Dense(in_dim, heads * hdim)
                    self.k_proj = nn.Dense(in_dim, heads * hdim)
                    self.v_proj = nn.Dense(in_dim, heads * hdim)
                    self.out_proj = nn.Dense(heads * hdim, out_dim)
                    self.matmul = ops.MatMul()
                    self.softmax = ops.Softmax(axis=-1)

                def construct(self, X):
                    # X: (T, D)
                    # project
                    Q = self.q_proj(X)  # (T, H*hd)
                    K = self.k_proj(X)
                    V = self.v_proj(X)

                    T = Q.shape[0]
                    H = self.heads
                    hd = self.hdim

                    # reshape to (H, T, hd)
                    Qh = Q.reshape((T, H, hd)).transpose((1, 0, 2))
                    Kh = K.reshape((T, H, hd)).transpose((1, 0, 2))
                    Vh = V.reshape((T, H, hd)).transpose((1, 0, 2))

                    # scaled dot-product attention per head
                    scores = self.matmul(Qh, Kh.transpose((0, 2, 1))) / (hd ** 0.5)
                    att = self.softmax(scores)
                    context = self.matmul(att, Vh)  # (H, T, hd)

                    # aggregate across time by averaging
                    agg = context.mean(axis=1)
                    # concat heads -> (H*hd,)
                    flat = agg.reshape((H * hd,))
                    out = self.out_proj(flat)
                    return out

            self.cell = _MHTCell(self.input_dim, self.n_heads, self.head_dim, self.out_dim)
        else:
            # NumPy fallback
            import numpy as _np

            self.np = _np
            # small deterministic weights
            self.w_q = self.np.ones((self.input_dim, self.out_dim)) * 0.1
            self.w_k = self.np.ones((self.input_dim, self.out_dim)) * 0.1
            self.w_v = self.np.ones((self.input_dim, self.out_dim)) * 0.1
            self.w_out = self.np.ones((self.out_dim, self.out_dim)) * 0.1

    def encode(self, seq):
        """Encode a temporal sequence (T x D) into a vector of size out_dim.

        seq: array-like shape (T, D)
        returns: 1D array length out_dim
        """
        if self.ms is not None:
            # delegate to MindSpore cell
            try:
                return self.cell.construct(self.ms.Tensor(seq))
            except Exception:
                logger.exception("MindSpore temporal attention failed; falling back to numpy path")

        # numpy fallback
        X = self.np.asarray(seq, dtype=float)
        T = X.shape[0]
        Q = X @ self.w_q
        K = X @ self.w_k
        V = X @ self.w_v

        H = self.n_heads
        hd = self.head_dim
        # reshape (T, H, hd)
        Qh = Q.reshape((T, H, hd))
        Kh = K.reshape((T, H, hd))
        Vh = V.reshape((T, H, hd))

        # attention per head
        contexts = []
        for h in range(H):
            q = Qh[:, h, :]
            k = Kh[:, h, :]
            v = Vh[:, h, :]
            scores = q @ k.T / (hd ** 0.5)
            # softmax
            ex = self.np.exp(scores - scores.max(axis=1, keepdims=True))
            att = ex / (ex.sum(axis=1, keepdims=True) + 1e-9)
            context = att @ v
            contexts.append(context.mean(axis=0))

        flat = self.np.concatenate(contexts, axis=0)
        out = flat @ self.w_out
        return out


__all__ = ["MultiHeadTemporalAttention"]
