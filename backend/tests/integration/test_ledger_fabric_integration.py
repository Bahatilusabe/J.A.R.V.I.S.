"""Integration test for LedgerManager with Hyperledger Fabric.

This test is gated and will be skipped unless both:
- the Fabric SDK is available (ledger_manager.FABRIC_AVAILABLE == True)
- the environment variable RUN_FABRIC_INTEGRATION is set to "1"

To run locally against a Fabric test network set the following environment
variables (example):

export RUN_FABRIC_INTEGRATION=1
export FABRIC_NET_PROFILE=/path/to/network.json
export FABRIC_ORG=Org1
export FABRIC_USER=Admin
export FABRIC_CHANNEL=mychannel

IMPORTANT: This test will attempt to invoke chaincode on the provided
network profile. Only enable it in CI when a test Fabric network is
available and configured.
"""

import os
import pytest

from backend.core.blockchain_xdr import ledger_manager

RUN_ENABLED = os.getenv("RUN_FABRIC_INTEGRATION") == "1" and getattr(ledger_manager, "FABRIC_AVAILABLE", False)

pytestmark = pytest.mark.skipif(not RUN_ENABLED, reason="Fabric SDK or RUN_FABRIC_INTEGRATION not available")


def test_store_signed_threat_on_fabric_smoke():
    # This is a smoke test that simply verifies a txid is returned by the
    # submission path when a real Fabric network is present. It intentionally
    # omits signature verification to reduce certificate handling complexity.
    profile = os.getenv("FABRIC_NET_PROFILE")
    org = os.getenv("FABRIC_ORG")
    user = os.getenv("FABRIC_USER")
    channel = os.getenv("FABRIC_CHANNEL", "mychannel")

    lm = ledger_manager.LedgerManager(fabric_profile=profile, channel_name=channel, org=org, user=user, dry_run=False)
    lm.connect(org=org, user=user)

    threat = {"id": "int-test-001", "severity": "high", "desc": "integration smoke test"}

    txid = lm.store_signed_threat(chaincode_name="threatcc", threat=threat, signature=b"", signer_cert_pem=None)
    assert isinstance(txid, str) and len(txid) > 0
