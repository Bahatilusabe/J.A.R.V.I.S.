import os
import time
import json
import hmac
import hashlib
import base64
import tempfile
import threading
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _generate_rsa_keypair():
    """Generate a simple RSA keypair for testing (requires cryptography)."""
    try:
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend

        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("utf-8")

        return private_pem, public_pem, private_key, public_key
    except Exception:
        pytest.skip("cryptography not available for RS256 test")


def create_rs256_token(payload: dict, private_key) -> str:
    """Create an RS256 token using cryptography library."""
    try:
        import jwt as _pyjwt

        return _pyjwt.encode(payload, private_key, algorithm="RS256")
    except Exception:
        pytest.skip("PyJWT not available for RS256 test")


def create_hs256_token(payload: dict, secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_b = _b64url_encode(json.dumps(header).encode("utf-8"))
    payload_b = _b64url_encode(json.dumps(payload).encode("utf-8"))
    signing_input = f"{header_b}.{payload_b}".encode("ascii")
    sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b = _b64url_encode(sig)
    return f"{header_b}.{payload_b}.{sig_b}"


@pytest.fixture(autouse=True)
def env_setup(monkeypatch, tmp_path):
    # Set audit path for test verification
    audit_file = tmp_path / "audit.log"
    monkeypatch.setenv("AUDIT_LOG_PATH", str(audit_file))
    # Set a JWT secret for HS256 tests
    monkeypatch.setenv("JARVIS_JWT_SECRET", "testsecret")
    # For tests, allow insecure storage (file-based keystore without encryption)
    # This simulates the dev environment where TEE/TPM are not available
    monkeypatch.setenv("JARVIS_ALLOW_INSECURE_STORAGE", "1")
    yield


def test_create_session_and_audit_hs256(tmp_path):
    from backend.api.server import app
    from backend.api.routes import vpn as vpn_routes

    # Use a temporary directory for the keystore
    keystore_dir = tmp_path / "keystore"
    os.environ["KEYSTORE_DIR"] = str(keystore_dir)

    client = TestClient(app)

    # create a token with role 'user'
    now = int(time.time())
    token = create_hs256_token({"role": "user", "exp": now + 60}, "testsecret")

    headers = {"Authorization": f"Bearer {token}"}

    # create session via API
    r = client.post("/vpn/session?session_id=s-int-1", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["session_id"] == "s-int-1"

    # check audit file includes create_session
    path = os.environ.get("AUDIT_LOG_PATH")
    with open(path, "r") as f:
        lines = [json.loads(l) for l in f.readlines() if l.strip()]
    actions = [l.get("action") for l in lines]
    assert "create_session" in actions


def test_create_session_and_audit_rs256(tmp_path):
    """Test RS256 token flow with JARVIS_JWT_PUBLIC_KEY."""
    from backend.api.server import app
    from backend.api.routes import vpn as vpn_routes

    private_pem, public_pem, private_key, public_key = _generate_rsa_keypair()

    # Use a temporary directory for the keystore
    keystore_dir = tmp_path / "keystore_rs256"
    os.environ["KEYSTORE_DIR"] = str(keystore_dir)

    client = TestClient(app)

    # Set RS256 public key
    os.environ["JARVIS_JWT_PUBLIC_KEY"] = public_pem
    now = int(time.time())
    token = create_rs256_token({"role": "user", "exp": now + 60}, private_key)

    headers = {"Authorization": f"Bearer {token}"}

    # Create session via API with RS256 token
    r = client.post("/vpn/session?session_id=s-rs256-1", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["session_id"] == "s-rs256-1"


def test_process_incoming_and_audit(tmp_path):
    from backend.api.server import app
    from backend.api.routes import vpn as vpn_routes

    # Use a temporary directory for the keystore
    keystore_dir = tmp_path / "keystore_process"
    os.environ["KEYSTORE_DIR"] = str(keystore_dir)

    client = TestClient(app)

    # admin token for rekey/close operations
    now = int(time.time())
    admin_token = create_hs256_token({"role": "admin", "exp": now + 60}, "testsecret")
    user_token = create_hs256_token({"role": "user", "exp": now + 60}, "testsecret")

    # create session using admin or user
    r = client.post("/vpn/session?session_id=s-int-2", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 200

    # prepare a plaintext and encrypt it using the in-memory gateway for realistic blob
    gw = vpn_routes.gw
    # ensure session exists in gw
    assert "s-int-2" in gw.sessions
    pt = b"hello-integration"
    blob = gw.encrypt_for_session("s-int-2", pt)
    b64 = base64.b64encode(blob).decode("ascii")

    # send to process endpoint
    r2 = client.post(f"/vpn/session/s-int-2/process", headers={"Authorization": f"Bearer {user_token}"}, json={"blob": b64})
    assert r2.status_code == 200
    res = r2.json()
    assert "plaintext_b64" in res
    assert base64.b64decode(res["plaintext_b64"]) == pt

    # check audit file has process_incoming entry
    path = os.environ.get("AUDIT_LOG_PATH")
    with open(path, "r") as f:
        lines = [json.loads(l) for l in f.readlines() if l.strip()]
    actions = [l.get("action") for l in lines]
    assert "process_incoming" in actions


def test_jwks_endpoint_mock(tmp_path):
    """Test JWKS endpoint mocking with PyJWT's PyJWKClient."""
    try:
        import jwt as _pyjwt
        from jwt import PyJWKClient
    except Exception:
        pytest.skip("PyJWT not available")

    from backend.api.server import app
    from backend.api.routes import vpn as vpn_routes

    private_pem, public_pem, private_key, public_key = _generate_rsa_keypair()

    # Use a temporary directory for the keystore
    keystore_dir = tmp_path / "keystore_jwks"
    os.environ["KEYSTORE_DIR"] = str(keystore_dir)

    # Create a mock JWKS endpoint that returns the public key
    def mock_get_signing_key_from_jwt(token):
        # Return a mock key object with .key property
        mock_key = MagicMock()
        mock_key.key = public_pem
        return mock_key

    # Mock PyJWKClient to return our test key
    with patch("jwt.PyJWKClient") as mock_jwks_client_class:
        mock_jwks = MagicMock()
        mock_jwks.get_signing_key_from_jwt = mock_get_signing_key_from_jwt
        mock_jwks_client_class.return_value = mock_jwks

        os.environ["JARVIS_JWKS_URL"] = "http://localhost:8080/.well-known/jwks.json"
        os.environ["JARVIS_JWT_SECRET"] = ""  # unset so JWKS is tried

        client = TestClient(app)

        now = int(time.time())
        token = create_rs256_token({"role": "user", "exp": now + 60}, private_key)

        headers = {"Authorization": f"Bearer {token}"}

        # Create session via API using JWKS-verified token
        r = client.post("/vpn/session?session_id=s-jwks-1", headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert body["session_id"] == "s-jwks-1"


def test_create_session_with_enforced_attestation_success(tmp_path, monkeypatch):
    """When enforcement is enabled and TPM attests, session creation succeeds."""
    from backend.api.server import app

    # ensure enforce is enabled
    monkeypatch.setenv("JARVIS_ENFORCE_ATTESTATION", "1")

    # provide a fake hardware_integration.tpm_attestation that returns attested
    import types, sys

    class FakeTPM:
        @staticmethod
        def attest():
            return {"attested": True, "device_key": "dev-e2e", "device_id": "dev-e2e"}

    hw = types.ModuleType("hardware_integration")
    hw.tpm_attestation = FakeTPM
    monkeypatch.setitem(sys.modules, "hardware_integration", hw)

    # Use a temp keystore dir
    keystore_dir = tmp_path / "keystore_att_ok"
    monkeypatch.setenv("KEYSTORE_DIR", str(keystore_dir))

    client = TestClient(app)
    # ensure JWT auth is accepted by endpoint
    monkeypatch.setenv("JARVIS_JWT_SECRET", "testsecret")
    now = int(time.time())
    token = create_hs256_token({"role": "user", "exp": now + 60}, "testsecret")

    device_info = {"device_id": "dev-e2e", "secure_boot": True, "patch_age_days": 1}
    r = client.post("/vpn/session?session_id=s-e2e-ok", json={"device_info": device_info}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json().get("session_id") == "s-e2e-ok"


def test_create_session_with_enforced_attestation_fail(tmp_path, monkeypatch):
    """When enforcement is enabled and TPM attestation fails, session creation is rejected."""
    from backend.api.server import app

    monkeypatch.setenv("JARVIS_ENFORCE_ATTESTATION", "1")

    # fake TPM that returns not attested
    import types, sys

    class FakeTPMFail:
        @staticmethod
        def attest():
            return {"attested": False, "reason": "bad_quote"}

    hw = types.ModuleType("hardware_integration")
    hw.tpm_attestation = FakeTPMFail
    monkeypatch.setitem(sys.modules, "hardware_integration", hw)

    keystore_dir = tmp_path / "keystore_att_bad"
    monkeypatch.setenv("KEYSTORE_DIR", str(keystore_dir))

    client = TestClient(app)
    # ensure JWT auth is accepted by endpoint
    monkeypatch.setenv("JARVIS_JWT_SECRET", "testsecret")
    now = int(time.time())
    token = create_hs256_token({"role": "user", "exp": now + 60}, "testsecret")

    device_info = {"device_id": "dev-e2e-bad", "secure_boot": False, "patch_age_days": 400}
    r = client.post("/vpn/session?session_id=s-e2e-bad", json={"device_info": device_info}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    body = r.json()
    # ensure attestation failure reason is present in response body
    assert body.get("detail") and body["detail"].get("reason") == "attestation_failed"
