"""Temporal GNN (TGNN) model for PASM.

This module provides a light wrapper `TGNNModel` which will use a
MindSpore-based neural network together with DGL for graph handling when
those libraries are available. In test/CI environments where those heavy
dependencies are not installed, the class falls back to a deterministic
placeholder implementation so the rest of the system and tests can run.

The implementation here is intentionally small: when both `mindspore` and
`dgl` are present we construct a tiny temporal encoder that averages node
features across time and passes them through a MindSpore MLP to produce a
per-graph risk score. This is a safe starting point you can extend to a
full TGNN with message passing and temporal recurrence.
"""

from __future__ import annotations

import logging
from typing import Any, Dict
import os

logger = logging.getLogger("jarvis.pasm.tgnn")


class TGNNModel:
    def __init__(self, device: str = "CPU"):
        """Attempt to initialize MindSpore + DGL model. If imports fail,
        keep a fallback mode active.
        """
        self._use_ms = False
        self._use_dgl = False
        self.device = device

        try:
            import mindspore as ms  # type: ignore[import]
            import mindspore.nn as msnn  # type: ignore[import]
            import mindspore.ops as msops  # type: ignore[import]

            self.ms = ms
            self.msnn = msnn
            self.msops = msops
            self._use_ms = True
        except Exception:
            logger.debug("MindSpore not available; TGNN will run in fallback mode")
            self.ms = None

        try:
            import dgl

            self.dgl = dgl
            self._use_dgl = True
        except Exception:
            logger.debug("DGL not available; TGNN will run in fallback mode")
            self.dgl = None

        # If both available, construct a small MindSpore MLP
        if self._use_ms and self._use_dgl:
            try:
                # simple 2-layer MLP
                class MLP(self.msnn.Cell):
                    def __init__(self, in_dim: int = 16, hidden: int = 32):
                        super().__init__()
                        self.fc1 = self.msnn.Dense(in_dim, hidden)
                        self.relu = self.msnn.ReLU()
                        self.fc2 = self.msnn.Dense(hidden, 1)

                    def construct(self, x):
                        x = self.fc1(x)
                        x = self.relu(x)
                        x = self.fc2(x)
                        return x

                # instantiate with default dims; we'll adapt at predict time
                self._mlp = MLP()
                try:
                    self.msg_rounds = int(os.environ.get("JARVIS_TGNN_MSG_ROUNDS", "2"))
                except Exception:
                    self.msg_rounds = 2
                # temporal encoder will be lazily instantiated when MindSpore is present
                self._use_temporal = True
                self._temporal_encoder = None
                try:
                    self._temporal_hidden = int(os.environ.get("JARVIS_TGNN_TEMPORAL_HIDDEN", "16"))
                except Exception:
                    self._temporal_hidden = 16
                self._initialized = True
            except Exception:
                logger.exception("failed to initialize MindSpore MLP; falling back")
                self._use_ms = False
                self._use_dgl = False

    def predict(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """Predict a risk score for the provided temporal graph.

        Expected graph format (lightweight):
          {
            "nodes": [{"id": ..., "features": [[t0_feat...], [t1_feat...], ...]}, ...],
            "edges": [[u,v], ...]
          }

        Returns a dict {"score": float, "details": {...}}
        """
        # If MindSpore+DGL available, run a minimal forward
        if self._use_ms and self._use_dgl:
            try:
                # Build node feature matrix by encoding temporal features per-node.
                # We compute a compact temporal encoding (mean, std, last, trend)
                # so the model receives information about recent dynamics. When
                # MindSpore is available we convert to tensors later; otherwise
                # the NumPy encoding is used and fed to the fallback MLP.
                import numpy as _np

                node_feats = []
                for n in graph.get("nodes", []):
                    feats = n.get("features") or []
                    if len(feats) == 0:
                        # empty node -> zeros for a small default feature size
                        node_feats.append(_np.zeros(8, dtype=float))
                        continue

                    arr = _np.array(feats, dtype=float)
                    # ensure 2D time x feature
                    if arr.ndim == 1:
                        arr = arr.reshape(1, -1)

                    # Attempt gated MindSpore temporal encoding (GRU) if available.
                    temporal_ok = False
                    if getattr(self, "_use_temporal", False) and getattr(self, "ms", None) is not None:
                        try:
                            # lazy-create temporal encoder
                            if getattr(self, "_temporal_encoder", None) is None:
                                input_size = arr.shape[1]
                                hidden = getattr(self, "_temporal_hidden", 16)
                                # Try multi-head temporal attention first (optional module)
                                try:
                                    from ai_models.pasm.temporal_attention import MultiHeadTemporalAttention

                                    head_dim = max(4, int(max(1, hidden) // max(1, 4)))
                                    self._temporal_encoder = MultiHeadTemporalAttention(input_dim=input_size, n_heads=4, head_dim=head_dim, ms_module=self.ms)
                                    # indicate module-like behaviour
                                    self._temporal_is_module = True
                                except Exception:
                                    try:
                                        # prefer nn.GRU module
                                        self._temporal_encoder = self.msnn.GRU(input_size, hidden, batch_first=True)
                                        self._temporal_is_module = True
                                    except Exception:
                                        # fallback to GRUCell if GRU module not present
                                        try:
                                            self._temporal_encoder = self.msnn.GRUCell(input_size, hidden)
                                            self._temporal_is_module = False
                                        except Exception:
                                            self._temporal_encoder = None

                            if getattr(self, "_temporal_encoder", None) is not None:
                                # prepare sequence tensor: (batch=1, seq_len, input_size)
                                # Prepare sequence tensor; many encoders expect (T, D)
                                try:
                                    seq = self.ms.Tensor(arr, dtype=self.ms.float32)
                                except Exception:
                                    seq = self.ms.Tensor(arr.reshape(1, arr.shape[0], arr.shape[1]), dtype=self.ms.float32)

                                if getattr(self, "_temporal_is_module", False):
                                    try:
                                        enc = self._temporal_encoder
                                        # If encoder exposes a `cell` (our MultiHeadTemporalAttention wrapper), use it with (T, D)
                                        if hasattr(enc, "cell"):
                                            out = enc.cell.construct(seq)
                                        else:
                                            # Other MindSpore modules often accept (batch, seq, feat)
                                            out = self._temporal_encoder(seq)

                                        # GRU module may return (output, h)
                                        if isinstance(out, (tuple, list)) and len(out) >= 2:
                                            h = out[1]
                                        else:
                                            h = out
                                        # try to convert to numpy
                                        try:
                                            h_np = h.asnumpy().reshape(-1)
                                        except Exception:
                                            # if h is a tensor-like sequence, attempt direct reshape
                                            try:
                                                import numpy as _np

                                                h_np = _np.asarray(h).reshape(-1)
                                            except Exception:
                                                raise

                                        node_feats.append(h_np)
                                        temporal_ok = True
                                    except Exception:
                                        temporal_ok = False
                                else:
                                    # GRUCell: manual unroll over sequence
                                    try:
                                        h_state = None
                                        for t in range(arr.shape[0]):
                                            x_t = self.ms.Tensor(arr[t].reshape(1, -1), dtype=self.ms.float32)
                                            if h_state is None:
                                                # initialize hidden state to zeros
                                                h_state = self.ms.ops.Zeros()((1, getattr(self, "_temporal_hidden", 16)), self.ms.float32)
                                            h_state = self._temporal_encoder(x_t, h_state)
                                        h_np = h_state.asnumpy().reshape(-1)
                                        node_feats.append(h_np)
                                        temporal_ok = True
                                    except Exception:
                                        temporal_ok = False
                        except Exception:
                            temporal_ok = False

                    if temporal_ok:
                        continue

                    # Fallback: temporal statistics (mean, std, last, trend)
                    mean = arr.mean(axis=0)
                    std = arr.std(axis=0)
                    last = arr[-1]
                    first = arr[0]
                    trend = last - first
                    enc = _np.concatenate([mean, std, last, trend], axis=0)
                    node_feats.append(enc)

                if len(node_feats) == 0:
                    return {"score": 0.0, "details": {"reason": "empty_graph"}}

                X = _np.vstack(node_feats)
                # convert to MindSpore tensor
                tensor = self.ms.Tensor(X, dtype=self.ms.float32)
                # if MLP input dim mismatches, recreate with proper dim
                in_dim = X.shape[1]
                try:
                    # Recreate _mlp if input dim changed
                    if getattr(self, "_mlp", None) is None or getattr(self._mlp.fc1, "in_channels", None) != in_dim:
                        class MLP(self.msnn.Cell):
                            def __init__(self, in_dim: int = in_dim, hidden: int = 32):
                                super().__init__()
                                self.fc1 = self.msnn.Dense(in_dim, hidden)
                                self.relu = self.msnn.ReLU()
                                self.fc2 = self.msnn.Dense(hidden, 1)

                            def construct(self, x):
                                x = self.fc1(x)
                                x = self.relu(x)
                                x = self.fc2(x)
                                return x

                        self._mlp = MLP()
                except Exception:
                    logger.debug("failed to adapt MLP input dim; proceeding with existing network")

                # Try to run DGL-based message passing before MLP-only forward
                try:
                    try:
                        # prefer MindSpore backend in DGL when available
                        self.dgl.backend.set_backend("mindspore")
                    except Exception:
                        pass

                    edges = graph.get("edges", [])
                    if len(edges) > 0:
                        u = [int(e[0]) for e in edges]
                        v = [int(e[1]) for e in edges]
                        g = self.dgl.graph((u, v))
                    else:
                        g = self.dgl.graph(([], []), num_nodes=len(node_feats))

                    # attach node features as MindSpore tensor
                    g.ndata["h"] = tensor

                    rounds = getattr(self, "msg_rounds", 2)
                    for _ in range(rounds):
                        try:
                            g.update_all(self.dgl.function.copy_u("h", "m"), self.dgl.function.mean("m", "h"))
                        except Exception:
                            # fallback to simple neighbor averaging using numpy
                            try:
                                h_np = g.ndata["h"].asnumpy()
                            except Exception:
                                h_np = tensor.asnumpy()

                            import numpy as _np

                            deg = _np.zeros((h_np.shape[0], 1), dtype=float)
                            acc = _np.zeros_like(h_np)
                            for (src, dst) in edges:
                                acc[int(dst)] += h_np[int(src)]
                                deg[int(dst)] += 1.0
                            deg[deg == 0] = 1.0
                            h_np = acc / deg
                            g.ndata["h"] = self.ms.Tensor(h_np, dtype=self.ms.float32)

                    out = self._mlp(g.ndata["h"])
                    vals = out.asnumpy().reshape(-1)
                    score = float(vals.mean())
                    return {"score": float(score), "details": {"nodes": len(node_feats)}}
                except Exception:
                    logger.exception("DGL message-passing failed; falling back to MLP-only path")
                    out = self._mlp(tensor)
                    vals = out.asnumpy().reshape(-1)
                    score = float(vals.mean())
                    return {"score": float(score), "details": {"nodes": len(node_feats)}}
            except Exception:
                logger.exception("TGNN predict failed; falling back to simple heuristic")

        # Fallback deterministic scorer: count nodes and edges and produce heuristic
        nodes = graph.get("nodes") or []
        edges = graph.get("edges") or []
        n = len(nodes)
        m = len(edges)
        # simple heuristic: more nodes and edges -> higher score, scaled
        score = min(1.0, (n * 0.1) + (m * 0.05))
        return {"score": float(score), "details": {"nodes": n, "edges": m}}

