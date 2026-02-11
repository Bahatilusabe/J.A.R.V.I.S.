import os
import sys
import types
import time

import pytest

from backend.core.tds import zero_trust


def test_attest_device_with_opa_allows(monkeypatch):
    # force OPA path
    monkeypatch.setenv("JARVIS_OPA_URL", "http://opa.local:8181")

    # stub _evaluate_opa_policy to return a positive decision
    def fake_eval(url, path, input_data):
        assert "device" in input_data
        return {"allowed": True, "score": 0.95, "reasons": ["policy_ok"], "claims": {"from": "opa"}}

    monkeypatch.setattr(zero_trust, "_evaluate_opa_policy", fake_eval)

    res = zero_trust.attest_device({"device_id": "dev-1"})
    assert res["attested"] is True
    assert abs(res["score"] - 0.95) < 1e-6
    assert "policy_ok" in res.get("reasons", [])


def test_attest_device_with_opa_denies(monkeypatch):
    monkeypatch.setenv("JARVIS_OPA_URL", "http://opa.local:8181")

    def fake_eval(url, path, input_data):
        return {"allowed": False, "score": 0.0, "reasons": ["policy_block"], "claims": {}}

    monkeypatch.setattr(zero_trust, "_evaluate_opa_policy", fake_eval)

    res = zero_trust.attest_device({"device_id": "dev-2"})
    assert res["attested"] is False
    assert res["score"] == 0.0
    assert "policy_block" in res.get("reasons", [])


def test_attest_device_with_huawei_enrichment(monkeypatch):
    # ensure OPA not consulted
    monkeypatch.delenv("JARVIS_OPA_URL", raising=False)

    # inject a fake hardware_integration.huawei_iam module
    fake_mod = types.SimpleNamespace()

    def fake_get_device_attributes(device_id):
        return {"vendor": "trustedco", "secure_boot": True}

    fake_mod.get_device_attributes = fake_get_device_attributes

    sys.modules.setdefault("hardware_integration", types.ModuleType("hardware_integration"))
    sys.modules["hardware_integration"].huawei_iam = fake_mod

    # Provide device_info missing vendor so enrichment is visible
    res = zero_trust.attest_device({"device_id": "dev-3", "patch_age_days": 5})
    assert res["attested"] is True
    assert res["score"] >= 0.6
    # Ensure enrichment merged vendor/secure_boot into claims/raw
    assert res["claims"].get("secure_boot") is True or res["raw"].get("secure_boot") is True


def test_enforce_microsegmentation_opa_decision(monkeypatch):
    monkeypatch.setenv("JARVIS_OPA_URL", "http://opa.local:8181")

    def fake_eval(url, path, input_data):
        # simulate OPA allowing traffic
        return {"allowed": True, "reason": "opa_allow"}

    monkeypatch.setattr(zero_trust, "_evaluate_opa_policy", fake_eval)

    allowed = zero_trust.enforce_microsegmentation({"role": "user"}, "10.0.0.5", proto="tcp")
    assert allowed["allowed"] is True
    assert allowed.get("reason") == "opa_allow"
