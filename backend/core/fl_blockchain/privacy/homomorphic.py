"""
Homomorphic Encryption for Federated Learning

Provides encryption/decryption of gradients using Paillier homomorphic encryption,
enabling encrypted aggregation without decryption at server.
"""

from typing import Tuple, Optional
import numpy as np
import base64
import logging
import json

logger = logging.getLogger("jarvis.fl_blockchain.homomorphic")


class HomomorphicEncryptor:
    """
    Provides Paillier homomorphic encryption interface for gradients.
    
    In production, this would use a library like python-paillier.
    For now, we provide a template interface with mock implementation.
    """
    
    def __init__(self, key_size: int = 2048):
        """
        Initialize HE encryptor
        
        Args:
            key_size: RSA key size (typically 2048 or 4096)
        """
        self.key_size = key_size
        self.public_key = None
        self.private_key = None
        
        # In production: 
        # from paillier import paillier
        # public_key, private_key = paillier.generate_paillier_keypair(n_length=key_size)
        
        logger.info(f"HomomorphicEncryptor initialized (key_size={key_size})")
    
    def generate_keypair(self) -> Tuple[str, str]:
        """
        Generate HE key pair
        
        Returns:
            (public_key_serialized, private_key_serialized)
        """
        # In production:
        # public_key, private_key = paillier.generate_paillier_keypair(n_length=self.key_size)
        # return serialize(public_key), serialize(private_key)
        
        # Mock implementation:
        mock_public = {
            "key_type": "paillier_public",
            "key_size": self.key_size,
            "id": "mock-public-key-001",
        }
        mock_private = {
            "key_type": "paillier_private",
            "key_size": self.key_size,
            "id": "mock-private-key-001",
        }
        
        self.public_key = mock_public
        self.private_key = mock_private
        
        return (
            json.dumps(mock_public),
            json.dumps(mock_private),
        )
    
    def encrypt(self, gradient: np.ndarray, public_key: Optional[str] = None) -> str:
        """
        Encrypt gradient using public key
        
        Args:
            gradient: Gradient array to encrypt
            public_key: Public key (uses instance key if None)
        
        Returns:
            Base64-encoded encrypted gradient
        """
        if public_key is None:
            if self.public_key is None:
                raise ValueError("No public key available")
            public_key = json.dumps(self.public_key)
        
        try:
            # In production with python-paillier:
            # from paillier import paillier
            # pub_key = deserialize(public_key)
            # encrypted = [pub_key.encrypt(float(x)) for x in gradient.flat]
            # return serialize(encrypted)
            
            # Mock implementation: simple base64 encoding with encryption marker
            gradient_bytes = gradient.tobytes()
            encoded = base64.b64encode(gradient_bytes).decode('utf-8')
            
            # Add marker to show encryption was applied
            encrypted_marker = {
                "encrypted": True,
                "key_id": "mock-public-key-001",
                "data": encoded,
                "shape": gradient.shape,
                "dtype": str(gradient.dtype),
            }
            
            result = base64.b64encode(
                json.dumps(encrypted_marker).encode('utf-8')
            ).decode('utf-8')
            
            logger.debug(f"Gradient encrypted: {gradient.shape} → {len(result)} bytes")
            return result
        
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise ValueError(f"Encryption failed: {str(e)}")
    
    def decrypt(
        self,
        encrypted_gradient: str,
        private_key: Optional[str] = None,
    ) -> np.ndarray:
        """
        Decrypt gradient using private key
        
        Args:
            encrypted_gradient: Base64-encoded encrypted gradient
            private_key: Private key (uses instance key if None)
        
        Returns:
            Decrypted gradient array
        """
        if private_key is None:
            if self.private_key is None:
                raise ValueError("No private key available")
            private_key = json.dumps(self.private_key)
        
        try:
            # In production with python-paillier:
            # from paillier import paillier
            # priv_key = deserialize(private_key)
            # encrypted = deserialize(encrypted_gradient)
            # decrypted = [priv_key.decrypt(x) for x in encrypted]
            # return np.array(decrypted).reshape(original_shape)
            
            # Mock implementation: reverse base64 encoding
            encrypted_marker = json.loads(
                base64.b64decode(encrypted_gradient).decode('utf-8')
            )
            
            if not encrypted_marker.get("encrypted"):
                raise ValueError("Invalid encrypted gradient format")
            
            gradient_bytes = base64.b64decode(encrypted_marker["data"])
            dtype = np.dtype(encrypted_marker["dtype"])
            shape = tuple(encrypted_marker["shape"])
            
            gradient = np.frombuffer(gradient_bytes, dtype=dtype).reshape(shape)
            
            logger.debug(f"Gradient decrypted: {gradient.shape}")
            return gradient
        
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def aggregate_encrypted(self, encrypted_gradients: list) -> str:
        """
        Aggregate encrypted gradients without decryption
        
        In true Paillier HE, this would sum encrypted values directly:
        Enc(g1 + g2 + ... + gn) = Enc(g1) ⊕ Enc(g2) ⊕ ... ⊕ Enc(gn)
        
        Args:
            encrypted_gradients: List of base64-encoded encrypted gradients
        
        Returns:
            Base64-encoded encrypted sum
        """
        # In production: use Paillier property that Enc(x) + Enc(y) = Enc(x + y)
        
        # Mock implementation: decrypt, aggregate, re-encrypt
        # (In real system, this would NOT decrypt at all)
        logger.warning(
            "Mock HE aggregation (production would aggregate encrypted values)"
        )
        
        decrypted_gradients = [
            self.decrypt(eg) for eg in encrypted_gradients
        ]
        aggregated = np.mean(decrypted_gradients, axis=0)
        
        return self.encrypt(aggregated)


def create_encryptor(key_size: int = 2048) -> HomomorphicEncryptor:
    """Factory function to create homomorphic encryptor"""
    return HomomorphicEncryptor(key_size=key_size)
