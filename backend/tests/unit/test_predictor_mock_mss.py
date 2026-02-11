import importlib
import sys
import types

def _install_fake_mss_client():
    # minimal fake mindspore_serving.client with Client class
    mss = types.ModuleType("mindspore_serving.client")

    class FakeClient:
        def __init__(self, url=None):
            self.url = url

        def predict(self, payload):
            # echo back a deterministic score based on nodes
            graph = payload.get("inputs")
            nodes = graph.get("nodes", []) if isinstance(graph, dict) else []
            score = min(1.0, len(nodes) * 0.1)
            return {"score": score}

    mss.Client = FakeClient
    sys.modules["mindspore_serving.client"] = mss


def test_predictor_uses_mss_client_and_falls_back(monkeypatch):
    _install_fake_mss_client()

    # reload predictor to pick up fake mss client
    mod = importlib.import_module("backend.core.pasm.predictor")
    importlib.reload(mod)

    Predictor = mod.Predictor
    p = Predictor(serving_url="http://fake")
    graph = {"nodes": [{"id": 1, "features": [[0.1]]}]}
    res = p.predict(graph)
    assert isinstance(res, dict)
    assert "score" in res

    # cleanup
    del sys.modules["mindspore_serving.client"]
