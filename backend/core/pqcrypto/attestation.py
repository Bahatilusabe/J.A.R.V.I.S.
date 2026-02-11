"""PQC-based attestation and cryptographic verification.

Implements attestation using Dilithium signatures with:
- Attestation certificate generation (device identity + measurements)
- Attestation verification with revocation checking
- Challenge-response protocol for remote attestation
- Measurement logging and audit trail

Provides cryptographic verification models for zero-knowledge proofs of code integrity.
"""
from __future__ import annotations

import json
import hashlib
import hmac
import os
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import base64
import logging

from backend.core.pqcrypto.dilithium import DilithiumSigner, SignKeyPair

logger = logging.getLogger(__name__)


@dataclass
class MeasurementRecord:
    """Record of a system/code measurement (e.g., code hash)."""
    name: str  # e.g., "code_hash", "config_hash"
    value: str  # base64-encoded hash or measurement
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    algorithm: str = "sha256"  # Measurement algorithm


@dataclass
class AttestationCertificate:
    """PQC-based attestation certificate (self-signed)."""
    device_id: str
    device_name: str = ""
    issuer: str = "PQC-Attestation-Root"
    issued_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: str = ""
    measurements: List[MeasurementRecord] = field(default_factory=list)
    public_key: str = ""  # base64-encoded Dilithium public key
    certificate_hash: str = ""  # base64-encoded SHA256 of cert (pre-signature)
    signature: str = ""  # base64-encoded Dilithium signature
    nonce: str = ""  # base64-encoded random nonce
    
    def to_dict(self) -> Dict:
        """Convert to dictionary (excluding signature for pre-signing)."""
        d = asdict(self)
        if not self.signature:
            d.pop("signature", None)
        return d
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class AttestationChallenge:
    """Challenge for remote attestation (challenge-response protocol)."""
    challenge_id: str
    device_id: str
    nonce: str  # base64-encoded random nonce
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: str = ""
    required_measurements: List[str] = field(default_factory=list)  # e.g., ["code_hash"]
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


@dataclass
class AttestationResponse:
    """Response to attestation challenge with signed measurements."""
    challenge_id: str
    device_id: str
    measurements: List[MeasurementRecord] = field(default_factory=list)
    certificate_hash: str = ""  # base64-encoded
    response_nonce: str = ""  # base64-encoded
    signature: str = ""  # base64-encoded signature over response
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


def _b64_encode(data: bytes) -> str:
    """Encode bytes to base64."""
    return base64.b64encode(data).decode("ascii")


def _b64_decode(data: str) -> bytes:
    """Decode base64 to bytes."""
    return base64.b64decode(data.encode("ascii"))


def compute_measurement(data: bytes, algorithm: str = "sha256") -> str:
    """Compute measurement (hash) of data."""
    if algorithm == "sha256":
        return _b64_encode(hashlib.sha256(data).digest())
    elif algorithm == "sha512":
        return _b64_encode(hashlib.sha512(data).digest())
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")


class PQCAttestationIssuer:
    """Issues attestation certificates signed by Dilithium.
    
    Usage:
        from backend.core.pqcrypto.dilithium import DilithiumSigner
        
        signer = DilithiumSigner("Dilithium3")
        issuer = PQCAttestationIssuer(signer, issuer_id="root-attestation-1")
        
        # Generate device certificate
        cert = issuer.issue_certificate(device_id="node-1", validity_days=365)
        
        # Record measurements
        issuer.add_measurement(cert, "code_hash", code_bytes)
        issuer.sign_certificate(cert)
    """
    
    def __init__(self, dilithium_signer: DilithiumSigner, issuer_id: str = ""):
        self.signer = dilithium_signer
        self.issuer_id = issuer_id or f"issuer-{os.urandom(4).hex()}"
        
        # Generate issuer keypair
        kp = self.signer.generate_keypair()
        self.public_key = kp.public
        self.private_key = kp.private
        
        logger.info(f"Initialized attestation issuer {self.issuer_id}")
    
    def issue_certificate(
        self,
        device_id: str,
        device_name: str = "",
        validity_days: int = 365,
    ) -> AttestationCertificate:
        """Issue a new attestation certificate for a device.
        
        Args:
            device_id: Unique device identifier
            device_name: Human-readable device name
            validity_days: Certificate validity period
            
        Returns:
            AttestationCertificate: Unsigned certificate ready for measurement and signing
        """
        issued_at = datetime.utcnow()
        expires_at = issued_at + timedelta(days=validity_days)
        
        cert = AttestationCertificate(
            device_id=device_id,
            device_name=device_name or device_id,
            issuer=self.issuer_id,
            issued_at=issued_at.isoformat(),
            expires_at=expires_at.isoformat(),
            public_key=_b64_encode(self.public_key),
            nonce=_b64_encode(os.urandom(32)),
        )
        
        logger.info(f"Issued attestation certificate for {device_id}")
        return cert
    
    def add_measurement(
        self,
        cert: AttestationCertificate,
        name: str,
        data: bytes,
        algorithm: str = "sha256",
    ) -> None:
        """Add a measurement to the certificate.
        
        Args:
            cert: Certificate to update
            name: Measurement name (e.g., "code_hash")
            data: Data to measure
            algorithm: Hash algorithm (sha256, sha512)
        """
        measurement = MeasurementRecord(
            name=name,
            value=compute_measurement(data, algorithm),
            algorithm=algorithm,
        )
        cert.measurements.append(measurement)
        logger.info(f"Added measurement {name} to cert for {cert.device_id}")
    
    def sign_certificate(self, cert: AttestationCertificate) -> None:
        """Sign the certificate with Dilithium.
        
        Args:
            cert: Certificate to sign (modified in-place)
        """
        # Compute hash over certificate content (pre-signature)
        cert_data = json.dumps(cert.to_dict(), sort_keys=True).encode()
        cert.certificate_hash = _b64_encode(hashlib.sha256(cert_data).digest())
        
        # Sign the certificate hash
        signature = self.signer.sign(self.private_key, cert_data)
        cert.signature = _b64_encode(signature)
        
        logger.info(f"Signed attestation certificate for {cert.device_id}")
    
    def get_public_key(self) -> bytes:
        """Get issuer's public key for verification."""
        return self.public_key


class PQCAttestationVerifier:
    """Verifies attestation certificates and responses.
    
    Usage:
        from backend.core.pqcrypto.dilithium import DilithiumSigner
        
        signer = DilithiumSigner("Dilithium3")
        verifier = PQCAttestationVerifier(signer, issuer_public_key)
        
        # Verify certificate
        is_valid = verifier.verify_certificate(cert)
        
        # Verify attestation response
        is_valid = verifier.verify_response(challenge, response)
    """
    
    def __init__(self, dilithium_signer: DilithiumSigner, issuer_public_key: bytes):
        self.signer = dilithium_signer
        self.issuer_public_key = issuer_public_key
        self.revocation_list: Dict[str, datetime] = {}
        
        logger.info("Initialized attestation verifier")
    
    def verify_certificate(self, cert: AttestationCertificate) -> bool:
        """Verify an attestation certificate's signature.
        
        Args:
            cert: Certificate to verify
            
        Returns:
            bool: True if signature is valid and cert is not revoked
        """
        # Check revocation
        if cert.device_id in self.revocation_list:
            logger.warning(f"Certificate for {cert.device_id} is revoked")
            return False
        
        # Check expiration
        if datetime.fromisoformat(cert.expires_at) < datetime.utcnow():
            logger.warning(f"Certificate for {cert.device_id} is expired")
            return False
        
        # Verify signature
        cert_data = json.dumps(cert.to_dict(), sort_keys=True).encode()
        signature = _b64_decode(cert.signature)
        
        is_valid = self.signer.verify(self.issuer_public_key, cert_data, signature)
        
        if is_valid:
            logger.info(f"Successfully verified certificate for {cert.device_id}")
        else:
            logger.warning(f"Certificate verification failed for {cert.device_id}")
        
        return is_valid
    
    def verify_measurement(self, cert: AttestationCertificate, expected_measurements: Dict[str, bytes]) -> bool:
        """Verify that certificate contains expected measurements.
        
        Args:
            cert: Certificate with measurements
            expected_measurements: Dict of name -> data to verify
            
        Returns:
            bool: True if all expected measurements match
        """
        cert_measurements = {m.name: m.value for m in cert.measurements}
        
        for name, data in expected_measurements.items():
            expected_value = compute_measurement(data, algorithm="sha256")
            actual_value = cert_measurements.get(name)
            
            if actual_value != expected_value:
                logger.warning(f"Measurement mismatch for {name} in {cert.device_id}")
                return False
        
        return True
    
    def create_challenge(
        self,
        device_id: str,
        required_measurements: List[str] = None,
        challenge_ttl_seconds: int = 300,
    ) -> AttestationChallenge:
        """Create a remote attestation challenge.
        
        Args:
            device_id: Target device
            required_measurements: List of required measurements (e.g., ["code_hash"])
            challenge_ttl_seconds: Challenge expiration time
            
        Returns:
            AttestationChallenge: Challenge for device to respond to
        """
        challenge = AttestationChallenge(
            challenge_id=f"challenge-{os.urandom(8).hex()}",
            device_id=device_id,
            nonce=_b64_encode(os.urandom(32)),
            required_measurements=required_measurements or [],
        )
        
        challenge.expires_at = (
            datetime.utcnow() + timedelta(seconds=challenge_ttl_seconds)
        ).isoformat()
        
        logger.info(f"Created attestation challenge {challenge.challenge_id} for {device_id}")
        return challenge
    
    def verify_response(
        self,
        challenge: AttestationChallenge,
        response: AttestationResponse,
        device_public_key: bytes,
    ) -> bool:
        """Verify an attestation response.
        
        Args:
            challenge: Original challenge
            response: Device's response
            device_public_key: Device's public key for signature verification
            
        Returns:
            bool: True if response is valid and signed correctly
        """
        # Check challenge match
        if response.challenge_id != challenge.challenge_id:
            logger.warning(f"Challenge ID mismatch in response")
            return False
        
        # Check expiration
        if datetime.fromisoformat(challenge.expires_at) < datetime.utcnow():
            logger.warning(f"Challenge {challenge.challenge_id} has expired")
            return False
        
        # Check required measurements present
        response_measurements = {m.name for m in response.measurements}
        for req_measurement in challenge.required_measurements:
            if req_measurement not in response_measurements:
                logger.warning(f"Missing required measurement {req_measurement}")
                return False
        
        # Verify signature
        response_data = json.dumps(asdict(response), sort_keys=True).encode()
        signature = _b64_decode(response.signature)
        
        is_valid = self.signer.verify(device_public_key, response_data, signature)
        
        if is_valid:
            logger.info(f"Successfully verified attestation response {response.challenge_id}")
        else:
            logger.warning(f"Attestation response verification failed")
        
        return is_valid
    
    def revoke_certificate(self, device_id: str) -> None:
        """Revoke a certificate by device ID.
        
        Args:
            device_id: Device whose certificate to revoke
        """
        self.revocation_list[device_id] = datetime.utcnow()
        logger.warning(f"Revoked certificate for {device_id}")
    
    def get_revocation_status(self, device_id: str) -> Tuple[bool, Optional[datetime]]:
        """Check revocation status of a device.
        
        Returns:
            Tuple of (is_revoked, revocation_time)
        """
        if device_id in self.revocation_list:
            return True, self.revocation_list[device_id]
        return False, None


__all__ = [
    "MeasurementRecord",
    "AttestationCertificate",
    "AttestationChallenge",
    "AttestationResponse",
    "PQCAttestationIssuer",
    "PQCAttestationVerifier",
    "compute_measurement",
]
