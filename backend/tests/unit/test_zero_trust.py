import time
from unittest.mock import patch

import pytest

from backend.core.tds import zero_trust


def test_attest_device_with_tpm(monkeypatch):
    # Mock tpm_attestation.attest to return a positive attestation
    fake_att = {"attested": True, "device_key": "dev-xyz", "device_id": "dev-xyz"}

    class FakeTPM:
        @staticmethod
        def attest():
            return fake_att

    # Ensure a fake hardware_integration package exists with tpm_attestation attribute
    import types, sys
    hw = types.ModuleType("hardware_integration")
    hw.tpm_attestation = FakeTPM
    monkeypatch.setitem(sys.modules, "hardware_integration", hw)

    device_info = {"device_id": "dev-xyz"}
    res = zero_trust.attest_device(device_info)
    assert res["attested"] is True
    assert res["score"] == 1.0
    assert res["device_id"] == "dev-xyz"


def test_attest_device_fallback(monkeypatch):
    # Ensure tpm_attestation is not present
    if "hardware_integration.tpm_attestation" in __import__("sys").modules:
        del __import__("sys").modules["hardware_integration.tpm_attestation"]

    # Device with secure_boot and recent patch age -> should be attested via fallback
    di = {"device_id": "dev-fb", "secure_boot": True, "patch_age_days": 5}
    res = zero_trust.attest_device(di)
    assert res["attested"] is True
    assert res["score"] >= 0.6
    assert res["device_id"] == "dev-fb"


def test_enforce_microsegmentation_allow(tmp_path):
    meta = {"role": "user", "allowed_cidrs": ["10.0.0.0/8"]}
    out = zero_trust.enforce_microsegmentation(meta, "10.1.2.3")
    assert out["allowed"] is True
    assert out["reason"] == "cidr_allowed"


def test_enforce_microsegmentation_deny(tmp_path):
    meta = {"role": "user", "allowed_cidrs": ["10.0.0.0/8"]}
    out = zero_trust.enforce_microsegmentation(meta, "192.168.1.5")
    assert out["allowed"] is False
    assert out["reason"] == "cidr_denied"
