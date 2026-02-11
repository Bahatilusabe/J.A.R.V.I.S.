import importlib
import sys
import types
from pathlib import Path

from backend.core.pasm.dataset_loader import create_mindspore_dataset


def _install_fake_ms_and_dgl():
    import numpy as _np
    ms = types.ModuleType("mindspore")

    class FakeTensor:
        def __init__(self, arr):
            import numpy as _np

            self._a = _np.array(arr)

        def asnumpy(self):
            return self._a

    ms.Tensor = lambda arr, dtype=None: FakeTensor(arr)
    ms.float32 = _np.float32

    ops = types.SimpleNamespace()
    ops.Zeros = lambda shape, dtype: ms.Tensor(_np.zeros(tuple(shape), dtype=_np.float32))
    ms.ops = ops

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
            summed = a.mean(axis=-1, keepdims=True)
            out = _np.tile(summed, (1, self.out_dim))
            return ms.Tensor(out)

    class ReLU:
        def __call__(self, x):
            import numpy as _np

            return ms.Tensor(_np.maximum(0, x.asnumpy()))

    class GRU:
        def __init__(self, input_size, hidden, batch_first=True):
            self.input_size = input_size
            self.hidden = hidden

        def __call__(self, seq):
            a = seq.asnumpy()
            h = a.mean(axis=1)
            h2 = _np.tile(h, (1, self.hidden)) if h.ndim == 2 else _np.tile(h, (self.hidden,))
            return (ms.Tensor(a), ms.Tensor(h2))

    msnn.Cell = Cell
    msnn.Dense = Dense
    msnn.ReLU = ReLU
    msnn.GRU = GRU

    sys.modules["mindspore"] = ms
    sys.modules["mindspore.nn"] = msnn
    sys.modules["mindspore.ops"] = types.SimpleNamespace(Zeros=ops.Zeros)

    dgl = types.ModuleType("dgl")
    dgl.graph = lambda uv, num_nodes=None: types.SimpleNamespace(ndata={}, update_all=lambda *a, **k: None)
    dgl.function = types.SimpleNamespace(copy_u=lambda *a, **k: None, mean=lambda *a, **k: None)
    dgl.backend = types.SimpleNamespace(set_backend=lambda b: None)
    sys.modules["dgl"] = dgl


def test_dataset_loader_and_mocked_tgnn_forward(tmp_path: Path):
    # prepare CSV and use dataset loader
    node_csv = tmp_path / "nodes.csv"
    node_csv.write_text("asset_id,timestamp,f1,f2\n1,2025-11-11T12:00:00,0.1,0.2\n1,2025-11-11T12:01:00,0.2,0.3\n")

    ds = create_mindspore_dataset(str(node_csv), window_size=2, stride=1, batch_size=1)
    # get a graph dict
    if hasattr(ds, "create_dict_iterator"):
        it = ds.create_dict_iterator(output_numpy=False)
        graph = next(it)["graph"]
    else:
        graph = next(iter(ds))

    # install fake MindSpore + DGL and reload tgnn module to pick them up
    _install_fake_ms_and_dgl()
    tgnn_mod = importlib.import_module("backend.core.pasm.tgnn_model")
    importlib.reload(tgnn_mod)
    TGNNModel = tgnn_mod.TGNNModel

    model = TGNNModel()
    res = model.predict(graph)
    assert isinstance(res, dict)
    assert "score" in res

    # cleanup
    for k in ["mindspore", "mindspore.nn", "mindspore.ops", "dgl"]:
        if k in sys.modules:
            del sys.modules[k]
