from backend.api import server
import asyncio


def test_health():
    resp = server.health()
    # support both sync and async health() implementations
    if asyncio.iscoroutine(resp):
        resp = asyncio.run(resp)
    assert isinstance(resp, dict)
    assert resp.get("status") == "ok"
