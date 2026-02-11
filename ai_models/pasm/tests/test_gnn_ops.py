import numpy as np

from ai_models.pasm.gnn_ops import GraphSAGE, GAT


def make_toy_graph(n=4, feat=6):
    rng = np.random.RandomState(0)
    X = rng.randn(n, feat).astype(float)
    # simple adjacency: chain + self loops
    A = np.zeros((n, n), dtype=float)
    for i in range(n):
        A[i, i] = 1.0
        if i + 1 < n:
            A[i, i + 1] = 1.0
            A[i + 1, i] = 1.0
    return X, A


def test_graphsage_shapes_and_values():
    X, A = make_toy_graph(5, 4)
    sage = GraphSAGE(in_feats=4, out_feats=3, hidden=5, ms_module=None)
    out = sage(X, A)
    assert out.shape == (5, 3)
    # deterministic fallback: check value ranges
    assert np.all(np.isfinite(out))
    assert np.abs(out).sum() > 0


def test_gat_shapes_and_attention():
    X, A = make_toy_graph(5, 4)
    gat = GAT(in_feats=4, out_feats=3, ms_module=None)
    out = gat(X, A)
    assert out.shape == (5, 3)
    # rows with single neighbor (edge case) should be finite
    assert np.all(np.isfinite(out))
