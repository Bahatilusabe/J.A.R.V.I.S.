import importlib
import sys


def test_mindspore_adapter_variant_names():
    """Mock an SDK with alternative method names and ensure adapter finds them."""
    class AltClient:
        def __init__(self, *a, **k):
            pass

        def get_parameters(self):
            return {"p": [7, 8, 9]}

        def push_update(self, payload):
            return {"ok": True, "received": payload}

    fake_mod = type(sys)("mindspore.federated")
    setattr(fake_mod, "Client", AltClient)
    sys.modules["mindspore.federated"] = fake_mod

    m = importlib.import_module("federation.federated_training")
    adapter = m.make_mindspore_server_from_sdk()
    assert adapter is not None
    got = adapter.get_weights()
    assert isinstance(got, dict) and "p" in got
    res = adapter.submit_update({"delta": 2})
    assert res.get("ok") is True
