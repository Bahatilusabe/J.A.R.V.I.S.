"""PQC configuration and key management system.

Centralized management of:
- Kyber and Dilithium algorithm selection
- Key generation, rotation, and backup
- Environment variable based configuration
- Hardware security module (HSM) simulation
- Key versioning and audit trail
"""
from __future__ import annotations

import os
import json
import base64
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class KeyEncapsulationMechanism(Enum):
    """Supported KEM algorithms."""
    KYBER512 = "Kyber512"
    KYBER768 = "Kyber768"
    KYBER1024 = "Kyber1024"


class DigitalSignatureAlgorithm(Enum):
    """Supported signature algorithms."""
    DILITHIUM2 = "Dilithium2"
    DILITHIUM3 = "Dilithium3"
    DILITHIUM5 = "Dilithium5"


@dataclass
class PQCPrivateKey:
    """Represents a private key with metadata."""
    key_bytes: bytes
    algorithm: str
    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: Optional[str] = None
    key_id: str = ""  # Unique identifier
    
    def to_dict(self) -> Dict:
        """Convert to dictionary (sensitive - use with care)."""
        return {
            "key_bytes": base64.b64encode(self.key_bytes).decode(),
            "algorithm": self.algorithm,
            "version": self.version,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "key_id": self.key_id,
        }


@dataclass
class PQCPublicKey:
    """Represents a public key with metadata."""
    key_bytes: bytes
    algorithm: str
    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: Optional[str] = None
    key_id: str = ""
    parent_key_id: Optional[str] = None  # For key rotation tracking
    
    def to_dict(self) -> Dict:
        return asdict(self) | {"key_bytes": base64.b64encode(self.key_bytes).decode()}
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, data: str) -> PQCPublicKey:
        d = json.loads(data)
        d["key_bytes"] = base64.b64decode(d["key_bytes"])
        return cls(**d)


@dataclass
class PQCKeyRotationAudit:
    """Audit trail for key rotation."""
    key_id: str
    old_key_id: Optional[str]
    new_key_id: str
    algorithm: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    reason: str = ""
    performed_by: str = ""
    status: str = "completed"  # completed, pending, failed


class PQCConfig:
    """Centralized PQC configuration.
    
    Configuration can come from:
    1. Environment variables (PQC_*)
    2. Config file (pqc_config.json)
    3. Defaults
    
    Priority: env vars > config file > defaults
    """
    
    # Default algorithms
    DEFAULT_KEM = KeyEncapsulationMechanism.KYBER768
    DEFAULT_SIG = DigitalSignatureAlgorithm.DILITHIUM3
    
    # Default key validity
    DEFAULT_KEY_VALIDITY_DAYS = 365
    DEFAULT_KEY_ROTATION_DAYS = 180
    
    def __init__(self):
        """Initialize PQC configuration from environment."""
        # Algorithm selection
        self.kem_algorithm = os.environ.get("PQC_KEM", self.DEFAULT_KEM.value)
        self.sig_algorithm = os.environ.get("PQC_SIG", self.DEFAULT_SIG.value)
        
        # Key management - use temp directory if /var/lib/jarvis is not accessible
        default_backup_dir = "/var/lib/jarvis/pqc_keys"
        if not os.path.exists("/var/lib/jarvis"):
            # Fallback to home directory for dev/test environments
            import tempfile
            default_backup_dir = os.path.join(tempfile.gettempdir(), "jarvis_pqc_keys")
        
        self.key_backup_dir = os.environ.get("PQC_KEY_BACKUP_DIR", default_backup_dir)
        self.key_rotation_days = int(os.environ.get("PQC_KEY_ROTATION_DAYS", str(self.DEFAULT_KEY_ROTATION_DAYS)))
        self.key_validity_days = int(os.environ.get("PQC_KEY_VALIDITY_DAYS", str(self.DEFAULT_KEY_VALIDITY_DAYS)))
        
        # HSM configuration
        self.use_hsm = os.environ.get("PQC_USE_HSM", "false").lower() == "true"
        self.hsm_module = os.environ.get("PQC_HSM_MODULE", "")
        self.hsm_slot = int(os.environ.get("PQC_HSM_SLOT", "0"))
        self.hsm_pin = os.environ.get("PQC_HSM_PIN", "")
        
        # Handshake configuration
        self.handshake_timeout_seconds = int(os.environ.get("PQC_HANDSHAKE_TIMEOUT", "30"))
        self.support_hybrid = os.environ.get("PQC_SUPPORT_HYBRID", "true").lower() == "true"
        
        # Attestation configuration
        self.attestation_enabled = os.environ.get("PQC_ATTESTATION_ENABLED", "true").lower() == "true"
        self.attestation_cert_validity_days = int(os.environ.get("PQC_ATTESTATION_CERT_VALIDITY_DAYS", "365"))
        
        # CANN configuration
        self.use_cann = os.environ.get("PQC_USE_CANN", "true").lower() == "true"
        self.gradient_compression_ratio = float(os.environ.get("PQC_GRADIENT_COMPRESSION_RATIO", "0.1"))
        
        # Logging
        self.log_level = os.environ.get("PQC_LOG_LEVEL", "INFO")
        self.audit_log_enabled = os.environ.get("PQC_AUDIT_LOG_ENABLED", "true").lower() == "true"
        
        logger.info(f"Initialized PQC config: KEM={self.kem_algorithm}, SIG={self.sig_algorithm}")
    
    def to_dict(self) -> Dict:
        """Export configuration (excludes sensitive HSM PIN)."""
        return {
            "kem_algorithm": self.kem_algorithm,
            "sig_algorithm": self.sig_algorithm,
            "key_backup_dir": self.key_backup_dir,
            "key_rotation_days": self.key_rotation_days,
            "key_validity_days": self.key_validity_days,
            "use_hsm": self.use_hsm,
            "hsm_module": self.hsm_module,
            "hsm_slot": self.hsm_slot,
            "handshake_timeout_seconds": self.handshake_timeout_seconds,
            "support_hybrid": self.support_hybrid,
            "attestation_enabled": self.attestation_enabled,
            "attestation_cert_validity_days": self.attestation_cert_validity_days,
            "use_cann": self.use_cann,
            "gradient_compression_ratio": self.gradient_compression_ratio,
            "log_level": self.log_level,
            "audit_log_enabled": self.audit_log_enabled,
        }


def get_pqc_config() -> PQCConfig:
    """Lazy getter for PQC config singleton."""
    if not hasattr(get_pqc_config, "_instance"):
        get_pqc_config._instance = PQCConfig()
    return get_pqc_config._instance


class PQCKeyManager:
    """Manages PQC key generation, storage, rotation, and backup.
    
    Usage:
        from backend.core.pqcrypto.config import PQCKeyManager
        
        km = PQCKeyManager()
        kem_kp = km.generate_kem_keypair()
        sig_kp = km.generate_sig_keypair()
        
        # Rotate keys
        new_kem_kp = km.rotate_kem_key(reason="scheduled rotation")
        
        # Backup
        km.backup_keys()
    """
    
    def __init__(self, config: Optional[PQCConfig] = None):
        self.config = config or get_pqc_config()
        self.current_kem_key: Optional[Tuple[bytes, bytes]] = None
        self.current_sig_key: Optional[Tuple[bytes, bytes]] = None
        self.kem_key_id = ""
        self.sig_key_id = ""
        self.rotation_audit_log: List[PQCKeyRotationAudit] = []
        
        # Ensure backup directory exists
        os.makedirs(self.config.key_backup_dir, exist_ok=True)
        
        logger.info("Initialized PQC key manager")
    
    def generate_kem_keypair(self) -> Tuple[bytes, bytes]:
        """Generate a new Kyber keypair.
        
        Returns:
            Tuple of (public_key, private_key)
        """
        from backend.core.pqcrypto.kyber import KyberKEM
        
        kem = KyberKEM(self.config.kem_algorithm)
        kp = kem.generate_keypair()
        
        self.current_kem_key = (kp.public, kp.private)
        self.kem_key_id = f"kem-{os.urandom(8).hex()}"
        
        logger.info(f"Generated new Kyber keypair: {self.kem_key_id}")
        return self.current_kem_key
    
    def generate_sig_keypair(self) -> Tuple[bytes, bytes]:
        """Generate a new Dilithium keypair.
        
        Returns:
            Tuple of (public_key, private_key)
        """
        from backend.core.pqcrypto.dilithium import DilithiumSigner
        
        signer = DilithiumSigner(self.config.sig_algorithm)
        kp = signer.generate_keypair()
        
        self.current_sig_key = (kp.public, kp.private)
        self.sig_key_id = f"sig-{os.urandom(8).hex()}"
        
        logger.info(f"Generated new Dilithium keypair: {self.sig_key_id}")
        return self.current_sig_key
    
    def rotate_kem_key(self, reason: str = "scheduled rotation", performed_by: str = "system") -> Tuple[bytes, bytes]:
        """Rotate Kyber keypair.
        
        Args:
            reason: Reason for rotation
            performed_by: User/system performing rotation
            
        Returns:
            New public and private keys
        """
        old_key_id = self.kem_key_id
        new_pub, new_priv = self.generate_kem_keypair()
        
        # Record in audit log
        audit = PQCKeyRotationAudit(
            key_id=self.kem_key_id,
            old_key_id=old_key_id,
            new_key_id=self.kem_key_id,
            algorithm=self.config.kem_algorithm,
            reason=reason,
            performed_by=performed_by,
        )
        self.rotation_audit_log.append(audit)
        
        logger.warning(f"Rotated Kyber key: {old_key_id} -> {self.kem_key_id}")
        return new_pub, new_priv
    
    def rotate_sig_key(self, reason: str = "scheduled rotation", performed_by: str = "system") -> Tuple[bytes, bytes]:
        """Rotate Dilithium keypair.
        
        Args:
            reason: Reason for rotation
            performed_by: User/system performing rotation
            
        Returns:
            New public and private keys
        """
        old_key_id = self.sig_key_id
        new_pub, new_priv = self.generate_sig_keypair()
        
        # Record in audit log
        audit = PQCKeyRotationAudit(
            key_id=self.sig_key_id,
            old_key_id=old_key_id,
            new_key_id=self.sig_key_id,
            algorithm=self.config.sig_algorithm,
            reason=reason,
            performed_by=performed_by,
        )
        self.rotation_audit_log.append(audit)
        
        logger.warning(f"Rotated Dilithium key: {old_key_id} -> {self.sig_key_id}")
        return new_pub, new_priv
    
    def backup_keys(self, backup_path: Optional[str] = None) -> str:
        """Backup current keys to file (SENSITIVE - protect this file).
        
        Args:
            backup_path: Custom backup path (defaults to config.key_backup_dir)
            
        Returns:
            Path where keys were backed up
        """
        if backup_path is None:
            backup_path = os.path.join(
                self.config.key_backup_dir,
                f"pqc_keys_backup_{datetime.utcnow().isoformat()}.json"
            )
        
        backup_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "kem_key_id": self.kem_key_id,
            "sig_key_id": self.sig_key_id,
            "kem_public": base64.b64encode(self.current_kem_key[0]).decode() if self.current_kem_key else None,
            "kem_private": base64.b64encode(self.current_kem_key[1]).decode() if self.current_kem_key else None,
            "sig_public": base64.b64encode(self.current_sig_key[0]).decode() if self.current_sig_key else None,
            "sig_private": base64.b64encode(self.current_sig_key[1]).decode() if self.current_sig_key else None,
            "rotation_audit": [asdict(a) for a in self.rotation_audit_log],
        }
        
        with open(backup_path, "w") as f:
            json.dump(backup_data, f, indent=2)
        
        # Restrict permissions (if on Unix)
        try:
            os.chmod(backup_path, 0o600)
        except Exception as e:
            logger.warning(f"Could not restrict backup file permissions: {e}")
        
        logger.warning(f"Backed up PQC keys to {backup_path}")
        return backup_path
    
    def restore_keys(self, backup_path: str) -> None:
        """Restore keys from backup file.
        
        Args:
            backup_path: Path to backup file
        """
        with open(backup_path, "r") as f:
            backup_data = json.load(f)
        
        if backup_data.get("kem_public"):
            kem_pub = base64.b64decode(backup_data["kem_public"])
            kem_priv = base64.b64decode(backup_data["kem_private"])
            self.current_kem_key = (kem_pub, kem_priv)
            self.kem_key_id = backup_data["kem_key_id"]
        
        if backup_data.get("sig_public"):
            sig_pub = base64.b64decode(backup_data["sig_public"])
            sig_priv = base64.b64decode(backup_data["sig_private"])
            self.current_sig_key = (sig_pub, sig_priv)
            self.sig_key_id = backup_data["sig_key_id"]
        
        logger.warning(f"Restored PQC keys from {backup_path}")
    
    def get_rotation_audit_log(self) -> List[PQCKeyRotationAudit]:
        """Get key rotation audit trail.
        
        Returns:
            List of rotation audit records
        """
        return self.rotation_audit_log.copy()
    
    def export_public_keys(self) -> Dict[str, str]:
        """Export public keys for distribution.
        
        Returns:
            Dict with base64-encoded public keys
        """
        return {
            "kem_public": base64.b64encode(self.current_kem_key[0]).decode() if self.current_kem_key else None,
            "kem_key_id": self.kem_key_id,
            "sig_public": base64.b64encode(self.current_sig_key[0]).decode() if self.current_sig_key else None,
            "sig_key_id": self.sig_key_id,
            "kem_algorithm": self.config.kem_algorithm,
            "sig_algorithm": self.config.sig_algorithm,
        }


def get_key_manager() -> PQCKeyManager:
    """Lazy getter for key manager singleton."""
    if not hasattr(get_key_manager, "_instance"):
        get_key_manager._instance = PQCKeyManager()
    return get_key_manager._instance


__all__ = [
    "PQCConfig",
    "PQCKeyManager",
    "PQCPrivateKey",
    "PQCPublicKey",
    "PQCKeyRotationAudit",
    "KeyEncapsulationMechanism",
    "DigitalSignatureAlgorithm",
    "get_pqc_config",
    "get_key_manager",
]
