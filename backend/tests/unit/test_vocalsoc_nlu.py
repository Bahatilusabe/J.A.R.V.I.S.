import pytest

from backend.core.vocalsoc import nlu_processor as nlu
from backend.core.vocalsoc.nlu_processor import ParseResult


def test_rule_based_open_vpn():
    text = "Please open VPN connection to node 5"
    res = nlu.parse_intent(text)
    assert isinstance(res, ParseResult)
    assert res.text == text
    assert "name" in res.intent
    assert res.intent["name"] == "open_vpn"
    # node id should be extracted
    assert any(e.get("entity") == "node_id" and e.get("value") == "5" for e in res.entities)


def test_rule_based_ip_entity():
    text = "Check status of node 3 at 10.0.0.5"
    res = nlu.parse_intent(text)
    assert res.intent["name"] in ("check_status", "unknown")
    assert any(e.get("entity") == "ip_address" and e.get("value") == "10.0.0.5" for e in res.entities)
