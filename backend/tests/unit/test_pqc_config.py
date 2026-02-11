"""Unit tests for PQC configuration and key management.

Tests:
- PQCConfig initialization from environment variables
- PQCKeyManager key generation, rotation, and backup
- Key serialization and restoration
- Audit trail tracking
"""
import os
import pytest
import json
import tempfile
from datetime import datetime, timedelta

from backend.core.pqcrypto.config import (
    PQCConfig,
    PQCKeyManager,
    PQCPrivateKey,
    PQCPublicKey,
    KeyEncapsulationMechanism,
    DigitalSignatureAlgorithm,
    get_pqc_config,
    get_key_manager,
)


class TestPQCConfig:
    """Test PQCConfig initialization and environment handling."""

    def test_default_algorithms(self):
        """Test default algorithm selection."""
        config = PQCConfig()
        assert config.kem_algorithm in ["Kyber512", "Kyber768", "Kyber1024"]
        assert config.sig_algorithm in ["Dilithium2", "Dilithium3", "Dilithium5"]

    def test_env_var_override(self, monkeypatch):
        """Test environment variable overrides."""
        monkeypatch.setenv("PQC_KEM", "Kyber512")
        monkeypatch.setenv("PQC_SIG", "Dilithium2")

        config = PQCConfig()
        assert config.kem_algorithm == "Kyber512"
        assert config.sig_algorithm == "Dilithium2"

    def test_key_rotation_days_config(self, monkeypatch):
        """Test key rotation configuration."""
        monkeypatch.setenv("PQC_KEY_ROTATION_DAYS", "90")
        monkeypatch.setenv("PQC_KEY_VALIDITY_DAYS", "180")

        config = PQCConfig()
        assert config.key_rotation_days == 90
        assert config.key_validity_days == 180

    def test_hsm_configuration(self, monkeypatch):
        """Test HSM configuration."""
        monkeypatch.setenv("PQC_USE_HSM", "true")
        monkeypatch.setenv("PQC_HSM_MODULE", "/usr/lib/softhsm/libsofthsm2.so")
        monkeypatch.setenv("PQC_HSM_SLOT", "1")

        config = PQCConfig()
        assert config.use_hsm is True
        assert config.hsm_module == "/usr/lib/softhsm/libsofthsm2.so"
        assert config.hsm_slot == 1

    def test_handshake_timeout_config(self, monkeypatch):
        """Test handshake timeout configuration."""
        monkeypatch.setenv("PQC_HANDSHAKE_TIMEOUT", "60")

        config = PQCConfig()
        assert config.handshake_timeout_seconds == 60

    def test_attestation_config(self, monkeypatch):
        """Test attestation configuration."""
        monkeypatch.setenv("PQC_ATTESTATION_ENABLED", "true")
        monkeypatch.setenv("PQC_ATTESTATION_CERT_VALIDITY_DAYS", "730")

        config = PQCConfig()
        assert config.attestation_enabled is True
        assert config.attestation_cert_validity_days == 730

    def test_cann_configuration(self, monkeypatch):
        """Test CANN/gradient compression configuration."""
        monkeypatch.setenv("PQC_USE_CANN", "false")
        monkeypatch.setenv("PQC_GRADIENT_COMPRESSION_RATIO", "0.05")

        config = PQCConfig()
        assert config.use_cann is False
        assert config.gradient_compression_ratio == 0.05

    def test_to_dict(self):
        """Test exporting config to dictionary."""
        config = PQCConfig()
        config_dict = config.to_dict()

        assert "kem_algorithm" in config_dict
        assert "sig_algorithm" in config_dict
        assert "key_rotation_days" in config_dict
        assert "use_hsm" in config_dict
        # HSM PIN should not be exposed
        assert "hsm_pin" not in config_dict


class TestPQCKeyManager:
    """Test PQCKeyManager key operations."""

    def test_initialization(self):
        """Test key manager initialization."""
        km = PQCKeyManager()
        assert km.current_kem_key is None
        assert km.current_sig_key is None
        assert km.kem_key_id == ""
        assert len(km.rotation_audit_log) == 0

    def test_generate_kem_keypair(self):
        """Test Kyber keypair generation."""
        km = PQCKeyManager()
        pub, priv = km.generate_kem_keypair()

        assert pub is not None
        assert priv is not None
        assert len(pub) > 0
        assert len(priv) > 0
        assert km.kem_key_id != ""
        assert km.current_kem_key == (pub, priv)

    def test_generate_sig_keypair(self):
        """Test Dilithium keypair generation."""
        km = PQCKeyManager()
        pub, priv = km.generate_sig_keypair()

        assert pub is not None
        assert priv is not None
        assert len(pub) > 0
        assert len(priv) > 0
        assert km.sig_key_id != ""
        assert km.current_sig_key == (pub, priv)

    def test_rotate_kem_key(self):
        """Test Kyber key rotation."""
        km = PQCKeyManager()
        km.generate_kem_keypair()
        old_key_id = km.kem_key_id

        # Rotate
        new_pub, new_priv = km.rotate_kem_key(reason="test rotation", performed_by="test_user")

        assert km.kem_key_id != old_key_id
        assert km.current_kem_key == (new_pub, new_priv)
        assert len(km.rotation_audit_log) == 1

        audit = km.rotation_audit_log[0]
        assert audit.old_key_id == old_key_id
        assert audit.new_key_id == km.kem_key_id
        assert audit.reason == "test rotation"
        assert audit.performed_by == "test_user"
        assert audit.status == "completed"

    def test_rotate_sig_key(self):
        """Test Dilithium key rotation."""
        km = PQCKeyManager()
        km.generate_sig_keypair()
        old_key_id = km.sig_key_id

        # Rotate
        new_pub, new_priv = km.rotate_sig_key(reason="test rotation")

        assert km.sig_key_id != old_key_id
        assert km.current_sig_key == (new_pub, new_priv)
        assert len(km.rotation_audit_log) == 1

    def test_backup_and_restore_keys(self):
        """Test key backup and restoration."""
        km = PQCKeyManager()
        km.generate_kem_keypair()
        km.generate_sig_keypair()

        # Backup
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_path = os.path.join(tmpdir, "backup.json")
            km.config.key_backup_dir = tmpdir
            km.backup_keys(backup_path)

            assert os.path.exists(backup_path)

            # Verify file is restricted (if on Unix)
            try:
                stat_info = os.stat(backup_path)
                # Check that only user can read (0o600)
                assert stat_info.st_mode & 0o077 == 0
            except (OSError, AttributeError):
                # Windows or unsupported system
                pass

            # Create new manager and restore
            km2 = PQCKeyManager()
            km2.restore_keys(backup_path)

            assert km2.current_kem_key == km.current_kem_key
            assert km2.current_sig_key == km.current_sig_key
            assert km2.kem_key_id == km.kem_key_id
            assert km2.sig_key_id == km.sig_key_id

    def test_get_rotation_audit_log(self):
        """Test retrieving audit log."""
        km = PQCKeyManager()
        km.generate_kem_keypair()

        # Perform multiple rotations
        km.rotate_kem_key(reason="rotation 1")
        km.rotate_kem_key(reason="rotation 2")
        km.generate_sig_keypair()
        km.rotate_sig_key(reason="rotation 3")

        log = km.get_rotation_audit_log()
        assert len(log) >= 3

        # All entries should have timestamp
        for entry in log:
            assert entry.timestamp != ""
            assert datetime.fromisoformat(entry.timestamp) is not None

    def test_export_public_keys(self):
        """Test exporting public keys for distribution."""
        km = PQCKeyManager()
        km.generate_kem_keypair()
        km.generate_sig_keypair()

        exported = km.export_public_keys()

        assert "kem_public" in exported
        assert "sig_public" in exported
        assert "kem_key_id" in exported
        assert "sig_key_id" in exported
        assert "kem_algorithm" in exported
        assert "sig_algorithm" in exported

        # Exported keys should be base64-encoded strings
        assert isinstance(exported["kem_public"], str)
        assert isinstance(exported["sig_public"], str)


class TestPQCPrivateKey:
    """Test PQCPrivateKey dataclass."""

    def test_creation(self):
        """Test private key creation."""
        key_bytes = b"secret_key_data"
        priv = PQCPrivateKey(key_bytes=key_bytes, algorithm="Kyber768")

        assert priv.key_bytes == key_bytes
        assert priv.algorithm == "Kyber768"
        assert priv.version == 1
        assert priv.key_id == ""

    def test_to_dict(self):
        """Test converting to dictionary."""
        key_bytes = b"secret"
        priv = PQCPrivateKey(key_bytes=key_bytes, algorithm="Dilithium3", key_id="key-123")

        d = priv.to_dict()
        assert "key_bytes" in d
        assert "algorithm" in d
        assert "version" in d
        assert d["algorithm"] == "Dilithium3"
        assert d["key_id"] == "key-123"


class TestPQCPublicKey:
    """Test PQCPublicKey dataclass."""

    def test_creation(self):
        """Test public key creation."""
        key_bytes = b"public_key_data"
        pub = PQCPublicKey(key_bytes=key_bytes, algorithm="Kyber768")

        assert pub.key_bytes == key_bytes
        assert pub.algorithm == "Kyber768"

    def test_json_serialization(self):
        """Test JSON serialization."""
        key_bytes = b"public_key"
        pub = PQCPublicKey(key_bytes=key_bytes, algorithm="Dilithium3", key_id="pub-456")

        # Serialize
        json_str = pub.to_json()
        assert isinstance(json_str, str)

        # Deserialize
        pub2 = PQCPublicKey.from_json(json_str)
        assert pub2.key_bytes == pub.key_bytes
        assert pub2.algorithm == pub.algorithm
        assert pub2.key_id == pub.key_id


class TestSingletons:
    """Test singleton getters."""

    def test_get_pqc_config_singleton(self):
        """Test PQCConfig singleton."""
        config1 = get_pqc_config()
        config2 = get_pqc_config()
        assert config1 is config2

    def test_get_key_manager_singleton(self):
        """Test PQCKeyManager singleton."""
        km1 = get_key_manager()
        km2 = get_key_manager()
        assert km1 is km2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
