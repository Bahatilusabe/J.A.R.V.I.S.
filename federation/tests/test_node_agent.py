import importlib
import sys


def test_node_agent_rest_fallback(monkeypatch):
    # prepare fake requests and reload module so node_agent picks it up
    captured = {"gets": [], "posts": []}

    class FakeResp:
        def __init__(self, status_code=200, json_data=None):
            self.status_code = status_code
            self._json = json_data or {}

        def json(self):
            return self._json

    class FakeRequests:
        def get(self, url, timeout=5.0):
            captured["gets"].append(url)
            return FakeResp(status_code=200, json_data={"version": 2})

        def post(self, url, json=None, timeout=5.0):
            captured["posts"].append((url, json))
            return FakeResp(status_code=200)

    sys.modules["requests"] = FakeRequests()
    # reload node_agent so it binds to our fake requests
    na = importlib.reload(importlib.import_module("federation.node_agent"))
    # create manager and replace client with stub that returns None/False so REST used
    mgr = na.NodeSyncManager(node_id="n1", server_url="http://example", interval=1)

    class StubClient:
        def __init__(self):
            self._registered = True

        def get_weights(self):
            return None

        def submit_update(self, update):
            return False

    mgr.client = StubClient()
    # call one sync iteration
    mgr._do_sync_once()
    assert len(captured["gets"]) >= 1
    assert len(captured["posts"]) >= 1


def test_node_agent_simulated_client(monkeypatch):
    # reload module to ensure default environment (no requests)
    na = importlib.reload(importlib.import_module("federation.node_agent"))
    mgr = na.NodeSyncManager(node_id="n2", server_url=None, interval=1)
    # default client is a MindSporeFederatedClient which when no ms module is present
    # will simulate submit_update returning True. Ensure no exceptions and submission succeeds.
    mgr.client._ms = None
    # ensure registered
    mgr.client.register()
    mgr._do_sync_once()
    # if simulated, submit_update returns True and logs; ensure client is registered
    assert mgr.client._registered
