import importlib
import os
import sys


def test_local_replication_writes_jsonl(tmp_path, monkeypatch):
    # ensure module uses our cwd
    cwd = tmp_path
    monkeypatch.chdir(cwd)
    m = importlib.import_module("federation.ledger_sync")
    client = m.FabricClient()
    client.connect()
    replicator = m.LedgerReplicator(client, target_url=None)
    blocks = list(replicator.replicate("mychannel", start_block=0, end_block=2, poll_interval=0.01))
    assert len(blocks) == 3
    fname = cwd / "replicated_ledger_mychannel.jsonl"
    assert fname.exists()
    # check file has 3 lines
    with open(fname, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    assert len(lines) == 3


def test_replication_posts_to_requests(monkeypatch, tmp_path):
    # inject fake requests module before reloading ledger_sync
    class FakeResp:
        def __init__(self, status_code=200, json_data=None):
            self.status_code = status_code
            self._json = json_data or {}

        def json(self):
            return self._json

    captured = {"posts": [], "gets": []}

    class FakeRequests:
        def get(self, url, timeout=5.0):
            captured["gets"].append(url)
            return FakeResp(status_code=200, json_data={"version": 1})

        def post(self, url, json=None, timeout=5.0):
            captured["posts"].append((url, json))
            return FakeResp(status_code=200)

    sys.modules["requests"] = FakeRequests()
    importlib.reload(importlib.import_module("federation.ledger_sync"))
    m = importlib.import_module("federation.ledger_sync")
    client = m.FabricClient()
    client.connect()
    replicator = m.LedgerReplicator(client, target_url="http://example")
    # replicate a single block
    blocks = list(replicator.replicate("mychannel", start_block=0, end_block=0, poll_interval=0.01))
    assert len(blocks) == 1
    assert len(captured["posts"]) == 1
