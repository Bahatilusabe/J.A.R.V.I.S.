import importlib
import sys
import types

import numpy as np


def _make_fake_mindspore():
    ms = types.ModuleType("mindspore")

    class FakeTensor:
        def __init__(self, data):
            self._a = np.asarray(data)

        def asnumpy(self):
            return self._a

        @property
        def shape(self):
            return self._a.shape

    class FakeNet:
        def __init__(self, *layers):
            self.layers = layers

        def __call__(self, x):
            # x may be FakeTensor or numpy
            arr = x.asnumpy() if hasattr(x, "asnumpy") else np.asarray(x)
            # return zeros with shape (n,1)
            return FakeTensor(np.zeros((arr.shape[0], 1), dtype=np.float32))

        def trainable_params(self):
            return []

    class FakeDense:
        def __init__(self, in_dim, out_dim):
            self.in_dim = in_dim
            self.out_dim = out_dim

    class FakeReLU:
        pass

    class FakeLossResult:
        def backward(self):
            return None

    class FakeMSELoss:
        def __call__(self, preds, ys):
            return FakeLossResult()

    class FakeOpt:
        def __init__(self, params, learning_rate=1e-3):
            pass

        def step(self):
            return None

        def clear_grad(self):
            return None

    class FakeDataset:
        def __init__(self, d, shuffle=False):
            self._data = d

        def create_tuple_iterator(self):
            # yield tuples (Xb, yb)
            X = np.asarray(self._data["data"])
            y = np.asarray(self._data["label"])
            for i in range(X.shape[0]):
                yield (FakeTensor(X[i:i+1]), FakeTensor(y[i:i+1]))

    ms.nn = types.SimpleNamespace(
        SequentialCell=FakeNet,
        Dense=FakeDense,
        ReLU=FakeReLU,
        MSELoss=FakeMSELoss,
        Adam=FakeOpt,
    )
    ms.Tensor = FakeTensor
    ms.dataset = types.SimpleNamespace(NumpySlicesDataset=FakeDataset)

    def save_checkpoint(net, path):
        with open(path, "wb") as f:
            f.write(b"ckpt")

    ms.save_checkpoint = save_checkpoint
    return ms


def _make_fake_dowhy():
    m = types.ModuleType("dowhy")
    # minimal placeholder
    m.__doc__ = "fake dowhy"
    return m


def test_hybrid_identify_and_fit(monkeypatch, tmp_path):
    # Inject fake modules
    monkeypatch.setitem(sys.modules, "dowhy", _make_fake_dowhy())
    monkeypatch.setitem(sys.modules, "mindspore", _make_fake_mindspore())

    # reload the module so it picks up the fakes
    mod = importlib.reload(importlib.import_module("backend.core.ced.causal_engine"))

    Engine = mod.DoWhyMindSporeCausalEngine
    e = Engine()

    # identification (dowhy fake)
    ident = e.identify("t", "y")
    assert ident["status"] == "identified"

    # prepare simple numpy data
    X = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    y = np.array([[1.0], [2.0]], dtype=np.float32)

    # fit a node
    e._parents["z"] = ()
    e.fit_node_with_mindspore("z", X, y, epochs=1, use_dataset=False, checkpoint_dir=str(tmp_path))

    assert "z" in e._ms_models
    # call the structural function; it should return a float
    val = e._nodes["z"]({})
    assert isinstance(val, float)
