"""Unit tests for forensics API (backend/api/routes/forensics.py).

Tests cover:
- Pydantic models (ForensicsRecord, ForensicArtifact, etc.)
- LedgerManager integration
- HTTP endpoints for storing and retrieving forensics records
- Signature verification
- Multi-backend support (Ledger, Web3, Fabric)
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import models and router
from backend.api.routes.forensics import (
    ForensicArtifact,
    ForensicsRecord,
    ForensicsStoreRequest,
    router,
)


@pytest.fixture
def forensics_app():
    """Create a test FastAPI app with forensics router."""
    app = FastAPI()
    app.include_router(router, prefix="/forensics")
    return app


@pytest.fixture
def client(forensics_app):
    """FastAPI test client."""
    return TestClient(forensics_app)


# ======================== Pydantic Model Tests ========================

def test_forensic_artifact_creation():
    """Test ForensicArtifact model."""
    artifact = ForensicArtifact(
        artifact_type="file",
        name="malware.exe",
        path="/evidence/malware.exe",
        content_hash="abc123",
        size_bytes=1024,
    )
    assert artifact.artifact_type == "file"
    assert artifact.name == "malware.exe"
    assert artifact.artifact_id is not None
    assert artifact.collected_at is not None


def test_forensic_artifact_defaults():
    """Test ForensicArtifact with defaults."""
    artifact = ForensicArtifact(
        artifact_type="log",
        name="system.log",
    )
    assert artifact.artifact_id is not None
    assert artifact.path is None
    assert artifact.metadata == {}


def test_forensics_record_creation():
    """Test ForensicsRecord model."""
    incident_start = datetime.utcnow()
    record = ForensicsRecord(
        incident_id="INC-2024-001",
        threat_id="THR-123",
        case_number="CASE-2024-001",
        incident_start=incident_start,
        investigator_notes="Initial investigation findings",
        severity="high",
    )
    assert record.incident_id == "INC-2024-001"
    assert record.record_id is not None
    assert record.status == "open"
    assert record.severity == "high"
    assert record.labels == []


def test_forensics_record_with_artifacts():
    """Test ForensicsRecord with artifacts."""
    incident_start = datetime.utcnow()
    artifact = ForensicArtifact(
        artifact_type="file",
        name="evidence.bin",
    )
    record = ForensicsRecord(
        incident_id="INC-2024-002",
        incident_start=incident_start,
        artifacts=[artifact],
        labels=["malware", "ransomware"],
    )
    assert len(record.artifacts) == 1
    assert record.artifacts[0].name == "evidence.bin"
    assert "malware" in record.labels


def test_forensics_record_serialization():
    """Test ForensicsRecord can be serialized to/from dict."""
    incident_start = datetime.utcnow()
    record = ForensicsRecord(
        incident_id="INC-2024-003",
        incident_start=incident_start,
        investigator_notes="Test notes",
    )
    record_dict = record.dict()
    assert "incident_id" in record_dict
    assert "record_id" in record_dict
    assert record_dict["investigator_notes"] == "Test notes"

    # Reconstruct from dict
    reconstructed = ForensicsRecord(**record_dict)
    assert reconstructed.incident_id == record.incident_id


def test_forensics_store_request():
    """Test ForensicsStoreRequest model."""
    incident_start = datetime.utcnow()
    record = ForensicsRecord(
        incident_id="INC-2024-004",
        incident_start=incident_start,
    )
    request = ForensicsStoreRequest(
        record=record,
        signature="deadbeef",
        signer_cert_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
    )
    assert request.record.incident_id == "INC-2024-004"
    assert request.signature == "deadbeef"


# ======================== Ledger Manager Mock Tests ========================

@pytest.fixture
def mock_ledger_manager():
    """Create a mock LedgerManager."""
    manager = Mock()
    manager.ledgers = {"forensics": {"transactions": [], "created": 1000.0}}
    manager.create_ledger = Mock()
    manager.get_transactions = Mock(return_value=[])
    manager.store_signed_threat = Mock(return_value="mock_txid_12345")
    return manager


def test_store_forensics_with_ledger(client, mock_ledger_manager):
    """Test storing forensics record via API with mocked LedgerManager."""
    incident_start = datetime.utcnow()
    record = ForensicsRecord(
        incident_id="INC-2024-005",
        incident_start=incident_start,
        investigator_notes="API test",
    )
    record_dict = record.dict(exclude_unset=False)
    # Convert datetime fields to ISO format strings
    record_dict["incident_start"] = record_dict["incident_start"].isoformat() if isinstance(record_dict["incident_start"], datetime) else record_dict["incident_start"]
    if record_dict.get("incident_end"):
        record_dict["incident_end"] = record_dict["incident_end"].isoformat() if isinstance(record_dict["incident_end"], datetime) else record_dict["incident_end"]
    record_dict["investigation_opened"] = record_dict["investigation_opened"].isoformat() if isinstance(record_dict["investigation_opened"], datetime) else record_dict["investigation_opened"]
    
    request_payload = {
        "record": record_dict,
        "signature": "abcd1234",
        "signer_cert_pem": None,
    }

    # Patch the ledger manager
    with patch("backend.api.routes.forensics._ledger_manager", mock_ledger_manager):
        with patch("backend.api.routes.forensics._ledger_enabled", True):
            response = client.post("/forensics/store", json=request_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stored"
    assert "record_id" in data
    assert "txid" in data
    assert data["txid"] == "mock_txid_12345"


def test_store_forensics_ledger_disabled(client):
    """Test storing forensics when ledger is disabled."""
    incident_start = datetime.utcnow()
    record = ForensicsRecord(
        incident_id="INC-2024-006",
        incident_start=incident_start,
    )
    record_dict = record.dict(exclude_unset=False)
    # Convert datetime fields to ISO format strings
    record_dict["incident_start"] = record_dict["incident_start"].isoformat() if isinstance(record_dict["incident_start"], datetime) else record_dict["incident_start"]
    record_dict["investigation_opened"] = record_dict["investigation_opened"].isoformat() if isinstance(record_dict["investigation_opened"], datetime) else record_dict["investigation_opened"]
    
    request_payload = {"record": record_dict}

    with patch("backend.api.routes.forensics._ledger_enabled", False):
        response = client.post("/forensics/store", json=request_payload)

    assert response.status_code == 503
    data = response.json()
    assert "Ledger manager not initialized" in data["detail"]


# ======================== Endpoint Tests ========================

def test_health_endpoint(client):
    """Test /forensics/health endpoint."""
    with patch("backend.api.routes.forensics._ledger_enabled", True):
        with patch("backend.api.routes.forensics._web3_enabled", False):
            with patch("backend.api.routes.forensics._fabric_enabled", False):
                response = client.get("/forensics/health")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["ledger"] is True
    assert data["web3"] is False
    assert data["fabric"] is False
    assert "timestamp" in data


def test_get_forensics_record(client, mock_ledger_manager):
    """Test GET /forensics/records/{record_id}."""
    incident_start = datetime.utcnow()
    record = ForensicsRecord(
        incident_id="INC-2024-007",
        incident_start=incident_start,
    )
    record_id = record.record_id

    # Mock ledger returns transaction with record
    mock_txid = "txid_test_123"
    mock_ledger_manager.get_transactions.return_value = [
        {
            "txid": mock_txid,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": record.dict(),
        }
    ]

    with patch("backend.api.routes.forensics._ledger_manager", mock_ledger_manager):
        with patch("backend.api.routes.forensics._ledger_enabled", True):
            response = client.get(f"/forensics/records/{record_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "found"
    assert data["source"] == "ledger"
    assert data["record"]["incident_id"] == "INC-2024-007"
    assert data["txid"] == mock_txid


def test_get_forensics_record_not_found(client, mock_ledger_manager):
    """Test GET /forensics/records/{record_id} when not found."""
    mock_ledger_manager.get_transactions.return_value = []

    with patch("backend.api.routes.forensics._ledger_manager", mock_ledger_manager):
        with patch("backend.api.routes.forensics._ledger_enabled", True):
            response = client.get("/forensics/records/nonexistent_record_id")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"]


def test_list_forensics_for_incident(client, mock_ledger_manager):
    """Test GET /forensics/incidents/{incident_id}/forensics."""
    incident_id = "INC-2024-008"
    incident_start = datetime.utcnow()

    # Create multiple records for same incident
    record1 = ForensicsRecord(
        incident_id=incident_id,
        incident_start=incident_start,
        status="open",
    )
    record2 = ForensicsRecord(
        incident_id=incident_id,
        incident_start=incident_start,
        status="closed",
    )

    mock_ledger_manager.get_transactions.return_value = [
        {
            "txid": "txid_1",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": record1.dict(),
        },
        {
            "txid": "txid_2",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": record2.dict(),
        },
    ]

    with patch("backend.api.routes.forensics._ledger_manager", mock_ledger_manager):
        with patch("backend.api.routes.forensics._ledger_enabled", True):
            response = client.get(f"/forensics/incidents/{incident_id}/forensics")

    assert response.status_code == 200
    data = response.json()
    assert data["incident_id"] == incident_id
    assert data["count"] == 2
    assert len(data["records"]) == 2


def test_list_forensics_with_status_filter(client, mock_ledger_manager):
    """Test GET /forensics/incidents/{incident_id}/forensics with status filter."""
    incident_id = "INC-2024-009"
    incident_start = datetime.utcnow()

    record1 = ForensicsRecord(
        incident_id=incident_id,
        incident_start=incident_start,
        status="open",
    )
    record2 = ForensicsRecord(
        incident_id=incident_id,
        incident_start=incident_start,
        status="closed",
    )

    mock_ledger_manager.get_transactions.return_value = [
        {"txid": "txid_1", "timestamp": datetime.utcnow().isoformat(), "payload": record1.dict()},
        {"txid": "txid_2", "timestamp": datetime.utcnow().isoformat(), "payload": record2.dict()},
    ]

    with patch("backend.api.routes.forensics._ledger_manager", mock_ledger_manager):
        with patch("backend.api.routes.forensics._ledger_enabled", True):
            response = client.get(f"/forensics/incidents/{incident_id}/forensics?status=open")

    assert response.status_code == 200
    data = response.json()
    assert data["status_filter"] == "open"
    assert data["count"] == 1
    assert data["records"][0]["record"]["status"] == "open"


def test_get_forensics_logs_endpoint(client, mock_ledger_manager):
    """Test GET /forensics/logs/{txid} with multiple backends."""
    txid = "test_txid_789"
    incident_start = datetime.utcnow()
    record = ForensicsRecord(
        incident_id="INC-2024-010",
        incident_start=incident_start,
    )

    # Mock ledger has the record
    mock_ledger_manager.get_transactions.return_value = [
        {
            "txid": txid,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": record.dict(),
        }
    ]

    with patch("backend.api.routes.forensics._ledger_manager", mock_ledger_manager):
        with patch("backend.api.routes.forensics._ledger_enabled", True):
            with patch("backend.api.routes.forensics._web3_enabled", False):
                with patch("backend.api.routes.forensics._fabric_enabled", False):
                    response = client.get(f"/forensics/logs/{txid}")

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "ledger"
    assert data["txid"] == txid


def test_get_forensics_logs_not_found(client, mock_ledger_manager):
    """Test GET /forensics/logs/{txid} when not found in any backend."""
    txid = "nonexistent_txid"
    mock_ledger_manager.get_transactions.return_value = []

    with patch("backend.api.routes.forensics._ledger_manager", mock_ledger_manager):
        with patch("backend.api.routes.forensics._ledger_enabled", True):
            with patch("backend.api.routes.forensics._web3_enabled", False):
                with patch("backend.api.routes.forensics._fabric_enabled", False):
                    response = client.get(f"/forensics/logs/{txid}")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"]


# ======================== Signature & Crypto Tests ========================

def test_store_with_signature():
    """Test storing forensics record with signature."""
    incident_start = datetime.utcnow()
    record = ForensicsRecord(
        incident_id="INC-2024-011",
        incident_start=incident_start,
        investigator_notes="Signed record",
    )

    # Simulate hex-encoded signature
    signature_hex = "deadbeefcafebabe1234567890abcdef"
    signature_bytes = bytes.fromhex(signature_hex)
    assert len(signature_bytes) == 16

    request = ForensicsStoreRequest(
        record=record,
        signature=signature_hex,
        signer_cert_pem="-----BEGIN CERTIFICATE-----\nMIIC...\n-----END CERTIFICATE-----",
    )

    assert request.signature == signature_hex
    assert request.signer_cert_pem is not None


# ======================== Error Handling Tests ========================

def test_store_forensics_ledger_error(client, mock_ledger_manager):
    """Test error handling when ledger store fails."""
    incident_start = datetime.utcnow()
    record = ForensicsRecord(
        incident_id="INC-2024-012",
        incident_start=incident_start,
    )
    record_dict = record.dict(exclude_unset=False)
    # Convert datetime fields to ISO format strings
    record_dict["incident_start"] = record_dict["incident_start"].isoformat() if isinstance(record_dict["incident_start"], datetime) else record_dict["incident_start"]
    record_dict["investigation_opened"] = record_dict["investigation_opened"].isoformat() if isinstance(record_dict["investigation_opened"], datetime) else record_dict["investigation_opened"]
    
    request_payload = {"record": record_dict}

    # Mock ledger raises exception
    mock_ledger_manager.store_signed_threat.side_effect = Exception("Ledger write failed")

    with patch("backend.api.routes.forensics._ledger_manager", mock_ledger_manager):
        with patch("backend.api.routes.forensics._ledger_enabled", True):
            response = client.post("/forensics/store", json=request_payload)

    assert response.status_code == 500
    data = response.json()
    assert "failed to store" in data["detail"]


def test_list_forensics_ledger_error(client, mock_ledger_manager):
    """Test error handling when querying ledger fails."""
    incident_id = "INC-2024-013"

    # Mock ledger raises exception
    mock_ledger_manager.get_transactions.side_effect = Exception("Ledger query failed")

    with patch("backend.api.routes.forensics._ledger_manager", mock_ledger_manager):
        with patch("backend.api.routes.forensics._ledger_enabled", True):
            response = client.get(f"/forensics/incidents/{incident_id}/forensics")

    assert response.status_code == 500
    data = response.json()
    assert "failed to list" in data["detail"]


# ======================== Integration-style Tests ========================

def test_full_forensics_workflow(client, mock_ledger_manager):
    """Test complete forensics workflow: create, store, retrieve."""
    incident_id = "INC-2024-014"
    incident_start = datetime.utcnow()
    incident_end = incident_start + timedelta(hours=2)

    # Step 1: Create forensics record with artifacts
    artifact1 = ForensicArtifact(
        artifact_type="file",
        name="malware_sample.exe",
        path="/evidence/malware.exe",
        content_hash="e5fa44f2b31c1fb553b6021e7aab6b74",
        size_bytes=2048,
    )
    artifact2 = ForensicArtifact(
        artifact_type="log",
        name="syslog.txt",
        path="/var/log/syslog",
        size_bytes=10240,
    )

    record = ForensicsRecord(
        incident_id=incident_id,
        threat_id="THR-456",
        case_number="CASE-2024-014",
        incident_start=incident_start,
        incident_end=incident_end,
        artifacts=[artifact1, artifact2],
        investigator_notes="Malware detected during morning scan",
        severity="critical",
        labels=["malware", "backdoor"],
    )

    record_id = record.record_id

    # Convert record dict for JSON serialization
    record_dict = record.dict(exclude_unset=False)
    record_dict["incident_start"] = record_dict["incident_start"].isoformat() if isinstance(record_dict["incident_start"], datetime) else record_dict["incident_start"]
    if record_dict.get("incident_end"):
        record_dict["incident_end"] = record_dict["incident_end"].isoformat() if isinstance(record_dict["incident_end"], datetime) else record_dict["incident_end"]
    record_dict["investigation_opened"] = record_dict["investigation_opened"].isoformat() if isinstance(record_dict["investigation_opened"], datetime) else record_dict["investigation_opened"]
    
    # Recursively convert datetime in artifacts
    for artifact in record_dict.get("artifacts", []):
        if "collected_at" in artifact and isinstance(artifact["collected_at"], datetime):
            artifact["collected_at"] = artifact["collected_at"].isoformat()

    # Mock ledger for storage
    mock_ledger_manager.store_signed_threat.return_value = "txid_stored_001"
    mock_ledger_manager.get_transactions.return_value = []

    request_payload = {"record": record_dict}

    # Step 2: Store record
    with patch("backend.api.routes.forensics._ledger_manager", mock_ledger_manager):
        with patch("backend.api.routes.forensics._ledger_enabled", True):
            store_response = client.post("/forensics/store", json=request_payload)

    assert store_response.status_code == 200
    store_data = store_response.json()
    assert store_data["status"] == "stored"

    # Step 3: Mock retrieval
    mock_ledger_manager.get_transactions.return_value = [
        {
            "txid": "txid_stored_001",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": record.dict(),
        }
    ]

    # Step 4: Retrieve record
    with patch("backend.api.routes.forensics._ledger_manager", mock_ledger_manager):
        with patch("backend.api.routes.forensics._ledger_enabled", True):
            retrieve_response = client.get(f"/forensics/records/{record_id}")

    assert retrieve_response.status_code == 200
    retrieve_data = retrieve_response.json()
    assert retrieve_data["status"] == "found"
    assert retrieve_data["record"]["incident_id"] == incident_id
    assert len(retrieve_data["record"]["artifacts"]) == 2

    # Step 5: List all records for incident
    with patch("backend.api.routes.forensics._ledger_manager", mock_ledger_manager):
        with patch("backend.api.routes.forensics._ledger_enabled", True):
            list_response = client.get(f"/forensics/incidents/{incident_id}/forensics")

    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["count"] == 1
    assert list_data["records"][0]["record"]["severity"] == "critical"


def test_verify_endpoint_with_txid(client, mock_ledger_manager):
    """Test POST /forensics/verify for a txid that exists on the ledger.

    We mock the fetch and the internal verification helper to avoid crypto
    dependencies and focus on routing/argument handling.
    """
    txid = "verify_tx_001"
    threat = {"record_id": "r-verify-1", "incident_id": "INC-V-1"}
    threat_json = json.dumps(threat, sort_keys=True, separators=(",", ":"))
    # ledger stores chaincode wrapper with args
    mock_ledger_manager.get_transactions.return_value = [
        {"txid": txid, "timestamp": datetime.utcnow().isoformat(), "payload": {"args": [threat_json, "cafebabe", "-----BEGIN CERT-----\n..\n-----END CERT-----"]}}
    ]

    with patch("backend.api.routes.forensics._ledger_manager", mock_ledger_manager):
        with patch("backend.api.routes.forensics._ledger_enabled", True):
            # patch the verifier to return a positive result
            with patch("backend.api.routes.forensics._verify_signature", return_value={"verified": True, "reason": "verified", "signer": "CN=Test"}):
                response = client.post("/forensics/verify", json={"txid": txid})

    assert response.status_code == 200
    data = response.json()
    assert data["verified"] is True
    assert data["reason"] == "verified"
    assert data["signer"] == "CN=Test"
    assert data["txid"] == txid


def test_verify_endpoint_missing(client):
    """POST /forensics/verify with no data returns 400."""
    response = client.post("/forensics/verify", json={})
    assert response.status_code == 400
    data = response.json()
    assert "no record or txid provided" in data["detail"]
