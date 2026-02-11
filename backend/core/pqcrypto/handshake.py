"""Post-quantum TLS-like handshake implementation.

Implements a lightweight hybrid PQ/classical key agreement protocol with:
- ClientHello: ephemeral public keys + nonce
- ServerHello: encapsulated shared secrets + nonce
- Finished: master secret derivation and verification

Suitable for edge/cloud AI nodes requiring quantum-resistant key establishment.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Tuple, Optional, Dict, Any
import base64
import hashlib
import hmac
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class ClientHello:
    """Client-initiated handshake message with ephemeral public keys."""
    version: str = "1.0"
    client_id: str = ""
    timestamp: str = ""
    kyber_public: str = ""  # base64-encoded
    classical_public: str = ""  # base64-encoded (for hybrid)
    client_nonce: str = ""  # base64-encoded
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, data: str) -> ClientHello:
        d = json.loads(data)
        return cls(**d)


@dataclass
class ServerHello:
    """Server-initiated response with encapsulated shared secrets."""
    version: str = "1.0"
    server_id: str = ""
    timestamp: str = ""
    kyber_ciphertext: str = ""  # base64-encoded
    classical_ciphertext: str = ""  # base64-encoded (for hybrid)
    server_nonce: str = ""  # base64-encoded
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, data: str) -> ServerHello:
        d = json.loads(data)
        return cls(**d)


@dataclass
class Finished:
    """Final handshake message with master secret verification."""
    version: str = "1.0"
    client_id: str = ""
    verify_data: str = ""  # base64-encoded HMAC(master_secret, "handshake")
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, data: str) -> Finished:
        d = json.loads(data)
        return cls(**d)


def _b64_encode(data: bytes) -> str:
    """Encode bytes to base64 string."""
    return base64.b64encode(data).decode("ascii")


def _b64_decode(data: str) -> bytes:
    """Decode base64 string to bytes."""
    return base64.b64decode(data.encode("ascii"))


def _derive_master_secret(
    kyber_ss: bytes,
    classical_ss: bytes,
    client_nonce: bytes,
    server_nonce: bytes,
) -> bytes:
    """Derive master secret from two shared secrets and nonces."""
    # Simple KDF: HMAC(concat(ss), nonces)
    ikm = kyber_ss + classical_ss
    salt = client_nonce + server_nonce
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()
    # Single-block HKDF-expand for 32 bytes
    return hmac.new(prk, b"pqc-master\x01", hashlib.sha256).digest()


class PQCClientHandshake:
    """Client-side PQC handshake orchestration.
    
    Usage:
        from backend.core.pqcrypto.kyber import KyberKEM
        from backend.core.pqcrypto.hybrid_wrapper import HybridKEM
        from cryptography.hazmat.primitives.asymmetric import ec
        
        kyber = KyberKEM("Kyber768")
        classical_kem = ...  # e.g., ECDH wrapper
        hybrid = HybridKEM(kyber, classical_kem)
        
        client = PQCClientHandshake(hybrid, client_id="node-1")
        hello = client.generate_client_hello()
        
        # Send hello to server, receive server_hello
        master_secret = client.process_server_hello(server_hello)
        finished = client.generate_finished()
    """
    
    def __init__(self, hybrid_kem, client_id: str = "", classical_kem=None):
        """Initialize client handshake.
        
        Args:
            hybrid_kem: HybridKEM instance or raw KEM (Kyber)
            client_id: Client identifier
            classical_kem: Optional classical KEM for hybrid (if not in hybrid_kem)
        """
        self.hybrid_kem = hybrid_kem
        self.client_id = client_id or f"client-{os.urandom(4).hex()}"
        self.classical_kem = classical_kem
        
        self.client_nonce = os.urandom(32)
        self.kyber_public = None
        self.classical_public = None
        self.kyber_private = None
        self.classical_private = None
        self.master_secret = None
        self.server_nonce = None
        
    def generate_client_hello(self) -> ClientHello:
        """Generate ClientHello with ephemeral public keys and nonce."""
        # Generate keypairs
        kyber_kp = self.hybrid_kem.kem_a.generate_keypair() if hasattr(self.hybrid_kem, 'kem_a') else self.hybrid_kem.generate_keypair()
        
        if hasattr(self.hybrid_kem, 'kem_b') and self.hybrid_kem.kem_b:
            classical_kp = self.hybrid_kem.kem_b.generate_keypair()
            self.classical_public = classical_kp.public
            self.classical_private = classical_kp.private
        elif self.classical_kem:
            classical_kp = self.classical_kem.generate_keypair()
            self.classical_public = classical_kp.public
            self.classical_private = classical_kp.private
        
        self.kyber_public = kyber_kp.public
        self.kyber_private = kyber_kp.private
        
        hello = ClientHello(
            version="1.0",
            client_id=self.client_id,
            timestamp=datetime.utcnow().isoformat(),
            kyber_public=_b64_encode(self.kyber_public),
            classical_public=_b64_encode(self.classical_public) if self.classical_public else "",
            client_nonce=_b64_encode(self.client_nonce),
        )
        
        logger.info(f"Generated ClientHello for {self.client_id}")
        return hello
    
    def process_server_hello(self, server_hello: ServerHello) -> bytes:
        """Process ServerHello and derive master secret.
        
        Returns:
            master_secret (bytes): Derived master secret for secure communication
        """
        if not self.kyber_private:
            raise RuntimeError("ClientHello must be generated first")
        
        # Decode ciphertexts
        kyber_ct = _b64_decode(server_hello.kyber_ciphertext)
        self.server_nonce = _b64_decode(server_hello.server_nonce)
        
        # Decapsulate
        kyber_ss = self.hybrid_kem.kem_a.decapsulate(self.kyber_private, kyber_ct) if hasattr(self.hybrid_kem, 'kem_a') else self.hybrid_kem.decapsulate(self.kyber_private, kyber_ct)
        
        classical_ss = b""
        if server_hello.classical_ciphertext and self.classical_private:
            classical_ct = _b64_decode(server_hello.classical_ciphertext)
            if hasattr(self.hybrid_kem, 'kem_b') and self.hybrid_kem.kem_b:
                classical_ss = self.hybrid_kem.kem_b.decapsulate(self.classical_private, classical_ct)
            elif self.classical_kem:
                classical_ss = self.classical_kem.decapsulate(self.classical_private, classical_ct)
        
        # Derive master secret
        self.master_secret = _derive_master_secret(
            kyber_ss,
            classical_ss,
            self.client_nonce,
            self.server_nonce,
        )
        
        logger.info(f"Derived master secret for {self.client_id}")
        return self.master_secret
    
    def generate_finished(self) -> Finished:
        """Generate Finished message with master secret verification."""
        if not self.master_secret:
            raise RuntimeError("Server hello must be processed first")
        
        # Create verify data: HMAC(master_secret, "handshake")
        verify_data = hmac.new(self.master_secret, b"handshake", hashlib.sha256).digest()
        
        finished = Finished(
            version="1.0",
            client_id=self.client_id,
            verify_data=_b64_encode(verify_data),
        )
        
        logger.info(f"Generated Finished for {self.client_id}")
        return finished


class PQCServerHandshake:
    """Server-side PQC handshake orchestration.
    
    Usage:
        from backend.core.pqcrypto.kyber import KyberKEM
        from backend.core.pqcrypto.hybrid_wrapper import HybridKEM
        
        kyber = KyberKEM("Kyber768")
        hybrid = HybridKEM(kyber, classical_kem)
        
        server = PQCServerHandshake(hybrid, server_id="node-0")
        server_kp = server.generate_keypair()  # Pre-generate server keypair
        
        # Receive client_hello
        master_secret = server.process_client_hello(client_hello, server_kp)
        server_hello = server.generate_server_hello()
    """
    
    def __init__(self, hybrid_kem, server_id: str = "", classical_kem=None):
        """Initialize server handshake.
        
        Args:
            hybrid_kem: HybridKEM instance
            server_id: Server identifier
            classical_kem: Optional classical KEM
        """
        self.hybrid_kem = hybrid_kem
        self.server_id = server_id or f"server-{os.urandom(4).hex()}"
        self.classical_kem = classical_kem
        
        self.server_nonce = os.urandom(32)
        self.server_kyber_public = None
        self.server_kyber_private = None
        self.server_classical_public = None
        self.server_classical_private = None
        
        self.client_nonce = None
        self.master_secret = None
        
    def generate_keypair(self) -> Tuple[Tuple[bytes, bytes], Tuple[bytes, bytes]]:
        """Generate server's long-term keypair (pre-generated)."""
        kyber_kp = self.hybrid_kem.kem_a.generate_keypair() if hasattr(self.hybrid_kem, 'kem_a') else self.hybrid_kem.generate_keypair()
        self.server_kyber_public = kyber_kp.public
        self.server_kyber_private = kyber_kp.private
        
        if hasattr(self.hybrid_kem, 'kem_b') and self.hybrid_kem.kem_b:
            classical_kp = self.hybrid_kem.kem_b.generate_keypair()
            self.server_classical_public = classical_kp.public
            self.server_classical_private = classical_kp.private
        elif self.classical_kem:
            classical_kp = self.classical_kem.generate_keypair()
            self.server_classical_public = classical_kp.public
            self.server_classical_private = classical_kp.private
        
        logger.info(f"Generated server keypair for {self.server_id}")
        return ((self.server_kyber_public, self.server_classical_public), 
                (self.server_kyber_private, self.server_classical_private))
    
    def process_client_hello(self, client_hello: ClientHello) -> bytes:
        """Process ClientHello and derive master secret.
        
        Returns:
            master_secret (bytes): Derived master secret
        """
        if not self.server_kyber_private:
            raise RuntimeError("Server keypair must be generated first")
        
        # Extract client public keys and nonce
        client_kyber_public = _b64_decode(client_hello.kyber_public)
        self.client_nonce = _b64_decode(client_hello.client_nonce)
        client_classical_public = None
        if client_hello.classical_public:
            client_classical_public = _b64_decode(client_hello.classical_public)
        
        # Encapsulate to client's public keys
        kyber_ct, kyber_ss = self.hybrid_kem.kem_a.encapsulate(client_kyber_public) if hasattr(self.hybrid_kem, 'kem_a') else self.hybrid_kem.encapsulate(client_kyber_public)
        
        classical_ct = b""
        classical_ss = b""
        if client_classical_public:
            if hasattr(self.hybrid_kem, 'kem_b') and self.hybrid_kem.kem_b:
                classical_ct, classical_ss = self.hybrid_kem.kem_b.encapsulate(client_classical_public)
            elif self.classical_kem:
                classical_ct, classical_ss = self.classical_kem.encapsulate(client_classical_public)
        
        self._kyber_ct = kyber_ct
        self._classical_ct = classical_ct
        
        # Derive master secret
        self.master_secret = _derive_master_secret(
            kyber_ss,
            classical_ss,
            self.client_nonce,
            self.server_nonce,
        )
        
        logger.info(f"Processed ClientHello and derived master secret for {client_hello.client_id}")
        return self.master_secret
    
    def generate_server_hello(self) -> ServerHello:
        """Generate ServerHello with encapsulated shared secrets."""
        if not self.master_secret:
            raise RuntimeError("Client hello must be processed first")
        
        hello = ServerHello(
            version="1.0",
            server_id=self.server_id,
            timestamp=datetime.utcnow().isoformat(),
            kyber_ciphertext=_b64_encode(self._kyber_ct),
            classical_ciphertext=_b64_encode(self._classical_ct) if self._classical_ct else "",
            server_nonce=_b64_encode(self.server_nonce),
        )
        
        logger.info(f"Generated ServerHello for {self.server_id}")
        return hello
    
    def verify_finished(self, finished: Finished) -> bool:
        """Verify Finished message from client.
        
        Returns:
            bool: True if verify_data matches derived master secret
        """
        if not self.master_secret:
            raise RuntimeError("ClientHello must be processed first")
        
        expected_verify_data = hmac.new(self.master_secret, b"handshake", hashlib.sha256).digest()
        received_verify_data = _b64_decode(finished.verify_data)
        
        is_valid = hmac.compare_digest(expected_verify_data, received_verify_data)
        logger.info(f"Finished verification for {finished.client_id}: {'PASS' if is_valid else 'FAIL'}")
        return is_valid


__all__ = [
    "ClientHello",
    "ServerHello", 
    "Finished",
    "PQCClientHandshake",
    "PQCServerHandshake",
]
