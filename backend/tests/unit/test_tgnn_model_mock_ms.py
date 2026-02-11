import importlib
import sys
import types
import numpy as _np


def _make_fake_mindspore():
    ms = types.ModuleType("mindspore")

    class FakeTensor:
        def __init__(self, arr):
            self._a = _np.array(arr)

        def asnumpy(self):
            return self._a

        def reshape(self, *args):
            return FakeTensor(self._a.reshape(*args))

        def __repr__(self):
            return f"FakeTensor(shape={self._a.shape})"

    ms.Tensor = lambda arr, dtype=None: FakeTensor(arr)
    ms.float32 = _np.float32

    ops = types.SimpleNamespace()
    ops.Zeros = lambda shape, dtype: FakeTensor(_np.zeros(tuple(shape), dtype=_np.float32))
    ms.ops = ops

    # nn submodule
    msnn = types.ModuleType("mindspore.nn")

    class Cell:
        def __call__(self, x):
            return self.construct(x)

    class Dense:
        def __init__(self, in_dim, out_dim):
            self.in_dim = in_dim
            self.out_dim = out_dim

        def __call__(self, x):
            a = x.asnumpy()
            # simple linear: sum features then expand
            summed = a.mean(axis=-1, keepdims=True)
            out = _np.tile(summed, (1, self.out_dim))
            return ms.Tensor(out)

    class ReLU:
        def __call__(self, x):
            return ms.Tensor(_np.maximum(0, x.asnumpy()))

    class GRU:
        def __init__(self, input_size, hidden, batch_first=True):
            self.input_size = input_size
            self.hidden = hidden

        def __call__(self, seq):
            # seq: FakeTensor shape (1, seq_len, input_size)
            a = seq.asnumpy()
            # compute simple reduced hidden: mean over time then tile
            h = a.mean(axis=1)
            h2 = _np.tile(h, (1, self.hidden)) if h.ndim == 2 else _np.tile(h, (self.hidden,))
            return (ms.Tensor(a), ms.Tensor(h2))

    class GRUCell:
        def __init__(self, input_size, hidden):
            self.input_size = input_size
            self.hidden = hidden

        def __call__(self, x, h):
            # x: (1, input_size), h: FakeTensor
            a = x.asnumpy()
            # simple update: new h is mean of x tiled
            newh = _np.tile(a.mean(axis=-1, keepdims=True), (1, self.hidden))
            return ms.Tensor(newh)

    msnn.Cell = Cell
    msnn.Dense = Dense
    msnn.ReLU = ReLU
    msnn.GRU = GRU
    msnn.GRUCell = GRUCell

    # expose submodules
    sys.modules["mindspore"] = ms
    sys.modules["mindspore.nn"] = msnn
    sys.modules["mindspore.ops"] = types.SimpleNamespace(Zeros=ops.Zeros)


def _make_fake_dgl():
    dgl = types.ModuleType("dgl")

    class FakeGraph:
        def __init__(self, uv, num_nodes=None):
            self._ndata = {}
            self._uv = uv
            self._num = num_nodes if num_nodes is not None else (max([max(u) for u in uv]) + 1 if len(uv) > 0 else 0)

        @property
        def ndata(self):
            return self._ndata

        def update_all(self, copy_u, reducer):
            # no-op for tests (we rely on MLP)
            return

    def graph(u_v):
        return FakeGraph(u_v[0])

    dgl.graph = lambda uv, num_nodes=None: FakeGraph(list(zip(uv[0], uv[1])) if isinstance(uv, tuple) else [], num_nodes=num_nodes)
    dgl.function = types.SimpleNamespace(copy_u=lambda *a, **k: None, mean=lambda *a, **k: None)
    dgl.backend = types.SimpleNamespace(set_backend=lambda b: None)

    sys.modules["dgl"] = dgl


def test_tgnn_temporal_encoder_with_mocked_mindspore(monkeypatch):
    # Install fake mindspore and dgl into sys.modules before importing module
    _make_fake_mindspore()
    _make_fake_dgl()

    # reload the module so it picks up the fake packages
    import importlib

    mod = importlib.import_module("backend.core.pasm.tgnn_model")
    importlib.reload(mod)

    TGNNModel = mod.TGNNModel

    m = TGNNModel()
    # small graph with two time steps
    graph = {"nodes": [{"id": 1, "features": [[0.1, 0.2], [0.2, 0.3]]}], "edges": []}
    res = m.predict(graph)
    assert isinstance(res, dict)
    assert "score" in res

    # cleanup mocks
    for k in ["mindspore", "mindspore.nn", "mindspore.ops", "dgl"]:
        if k in sys.modules:
            del sys.modules[k]
