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

        def __array__(self):
            return self._a

    class FakeGrads(FakeTensor):
        pass

    class FakeNet:
        def __call__(self, x):
            # return a tensor of shape (batch, 1)
            arr = x.asnumpy() if hasattr(x, "asnumpy") else np.asarray(x)
            return FakeTensor(np.sum(arr, axis=1, keepdims=True))

    class FakeGradOp:
        def __init__(self, get_all=False, get_by_list=False):
            pass

        def __call__(self, fn):
            # return a function that given input returns grads (ones)
            def _inner(x):
                arr = x.asnumpy() if hasattr(x, "asnumpy") else np.asarray(x)
                grads = np.ones_like(arr)
                return FakeGrads(grads)

            return _inner

    ms.Tensor = FakeTensor
    ms.GradOperation = FakeGradOp
    ms.nn = types.SimpleNamespace(SequentialCell=FakeNet)
    return ms


def test_compute_saliency_with_mindspore(monkeypatch):
    monkeypatch.setitem(sys.modules, "mindspore", _make_fake_mindspore())

    eb = importlib.reload(importlib.import_module("backend.core.ced.explanation_builder"))
    DashBuilder = eb.DashExplanationBuilder

    b = DashBuilder()

    # fake model that expects numpy and returns array
    def model(x):
        a = np.asarray(x)
        # return sum over features along axis 1 as (batch,1)
        return a.sum(axis=1, keepdims=True)

    x = np.array([[1.0, 2.0, 3.0]], dtype=float)
    sal = b.compute_saliency(model, x)
    # expect three features
    assert len(sal) == 3
    for v in sal.values():
        assert isinstance(v, float)


def test_compute_saliency_finite_difference(monkeypatch):
    # Ensure MindSpore not present
    monkeypatch.setitem(sys.modules, "mindspore", None)
    eb = importlib.reload(importlib.import_module("backend.core.ced.explanation_builder"))
    DashBuilder = eb.DashExplanationBuilder
    b = DashBuilder()

    def model(x):
        a = np.asarray(x)
        return a.sum(axis=1, keepdims=True)

    x = np.array([[1.0, 2.0, 3.0]], dtype=float)
    sal = b.compute_saliency(model, x)
    assert len(sal) == 3
    for v in sal.values():
        assert v >= 0.0
