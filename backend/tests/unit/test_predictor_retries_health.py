import importlib
import sys
import types
import time


class TransientClient:
    def __init__(self, fail_times=1):
        self.calls = 0
        self.fail_times = fail_times

    def predict(self, payload):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("transient")
        return {"score": 0.42}


class HealthClient:
    def __init__(self, ok=True):
        self.ok = ok

    def health(self):
        return self.ok


def _install_transient_mss(fail_times=1):
    mss = types.ModuleType("mindspore_serving.client")

    def Client(url=None):
        return TransientClient(fail_times=fail_times)

    mss.Client = Client
    # also ensure parent package exists
    pkg = types.ModuleType("mindspore_serving")
    sys.modules["mindspore_serving"] = pkg
    sys.modules["mindspore_serving.client"] = mss


def _install_health_mss(ok=True):
    mss = types.ModuleType("mindspore_serving.client")

    class Client:
        def __init__(self, url=None):
            self._c = HealthClient(ok)

        def health(self):
            return self._c.health()

    mss.Client = Client
    pkg = types.ModuleType("mindspore_serving")
    sys.modules["mindspore_serving"] = pkg
    sys.modules["mindspore_serving.client"] = mss


def test_predictor_retries_on_transient_error(monkeypatch):
    # configure retries low to speed test (set env before importing module)
    monkeypatch.setenv("JARVIS_SERVING_RETRIES", "3")
    monkeypatch.setenv("JARVIS_SERVING_TIMEOUT", "1.0")
    monkeypatch.setenv("JARVIS_SERVING_BACKOFF", "0.01")

    _install_transient_mss(fail_times=1)

    mod = importlib.import_module("backend.core.pasm.predictor")
    importlib.reload(mod)

    Pred = mod.Predictor
    p = Pred(serving_url="http://fake")
    graph = {"nodes": [{"id": 1, "features": [[0.1]]}]}
    res = p.predict(graph)
    assert isinstance(res, dict)
    assert res["score"] == 0.42

    del sys.modules["mindspore_serving.client"]


def test_predictor_health_check(monkeypatch):
    # make sure module reads any env (not required here but consistent)
    monkeypatch.setenv("JARVIS_SERVING_TIMEOUT", "1.0")
    _install_health_mss(ok=True)
    mod = importlib.import_module("backend.core.pasm.predictor")
    importlib.reload(mod)

    Pred = mod.Predictor
    p = Pred(serving_url="http://fake")
    ok = p.health_check(timeout=1.0)
    assert ok is True

    # negative case
    _install_health_mss(ok=False)
    importlib.reload(mod)
    p2 = Pred(serving_url="http://fake")
    ok2 = p2.health_check(timeout=1.0)
    assert ok2 is False

    del sys.modules["mindspore_serving.client"]
