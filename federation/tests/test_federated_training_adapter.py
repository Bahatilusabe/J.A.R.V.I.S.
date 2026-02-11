import importlib
import sys


def test_mindspore_adapter_basic():
    """Mock a minimal MindSpore federated SDK and validate adapter binding."""
    # create a fake module with Client class
    class FakeClient:
        def __init__(self, *args, **kwargs):
            self._registered = False

        def register(self):
            self._registered = True

        def get_weights(self, *a, **k):
            return {"w": [1, 2, 3]}

        def submit_update(self, payload):
            # echo back to indicate reception
            return {"ok": True, "payload": payload}

    fake_mod = type(sys)("mindspore_federated")
    setattr(fake_mod, "Client", FakeClient)
    sys.modules["mindspore_federated"] = fake_mod

    # import factory and create adapter
    m = importlib.import_module("federation.federated_training")
    adapter = m.make_mindspore_server_from_sdk()
    assert adapter is not None
    # register should not raise
    adapter.register()
    got = adapter.get_weights()
    assert isinstance(got, dict) and "w" in got
    res = adapter.submit_update({"delta": 1})
    assert res.get("ok") is True
