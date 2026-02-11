import os
import json
import types

import pytest

from backend.integrations.huawei_lts import HuaweiLTSClient


def test_client_no_endpoint(monkeypatch):
    monkeypatch.delenv("HUAWEI_LTS_ENDPOINT", raising=False)
    c = HuaweiLTSClient()
    assert not c.enabled()
    r = c.send_log({"a": 1})
    assert r["ok"] is False


def test_client_post(monkeypatch):
    # provide fake endpoint and monkeypatch requests.post
    monkeypatch.setenv("HUAWEI_LTS_ENDPOINT", "http://example.local/api")
    calls = {}

    class FakeResp:
        def __init__(self):
            self.status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"stored": True}

    def fake_post(url, data=None, headers=None, timeout=None):
        calls['url'] = url
        calls['data'] = data
        calls['headers'] = headers
        return FakeResp()

    # monkeypatch the top-level requests module used by the client
    import sys
    sys.modules["requests"] = types.SimpleNamespace(post=fake_post)

    c = HuaweiLTSClient()
    res = c.send_log({"k": "v"})
    assert res["ok"] is True
    assert "result" in res
