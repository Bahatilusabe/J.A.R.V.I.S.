"""
Utilities for FL+Blockchain module

Helper functions for serialization, hashing, signing, and monitoring.
"""

import hashlib
import hmac
import json
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger("jarvis.fl_blockchain.utils")


def compute_gradient_hash(gradient: np.ndarray) -> str:
    """
    Compute SHA-256 hash of gradient
    
    Args:
        gradient: Gradient array
    
    Returns:
        Hex string of SHA-256 hash
    """
    gradient_bytes = gradient.tobytes()
    return hashlib.sha256(gradient_bytes).hexdigest()


def sign_gradient(
    gradient: np.ndarray,
    secret_key: str,
) -> str:
    """
    Sign gradient using HMAC
    
    Args:
        gradient: Gradient to sign
        secret_key: Secret key for HMAC
    
    Returns:
        HMAC signature hex string
    """
    gradient_hash = compute_gradient_hash(gradient)
    signature = hmac.new(
        secret_key.encode('utf-8'),
        gradient_hash.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature


def verify_signature(
    gradient_hash: str,
    signature: str,
    public_key: str,
) -> bool:
    """
    Verify gradient signature
    
    Args:
        gradient_hash: SHA-256 hash of gradient
        signature: Provided signature
        public_key: Public key for verification
    
    Returns:
        True if signature is valid
    """
    # In production: use public key cryptography (Ed25519, etc.)
    # For now: verify using HMAC
    expected_signature = hmac.new(
        public_key.encode('utf-8'),
        gradient_hash.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


def serialize_gradient(gradient: np.ndarray) -> str:
    """Serialize gradient to base64 for transmission"""
    import base64
    return base64.b64encode(gradient.tobytes()).decode('utf-8')


def deserialize_gradient(
    serialized: str,
    shape: tuple,
    dtype: np.dtype = np.float32,
) -> np.ndarray:
    """Deserialize gradient from base64"""
    import base64
    gradient_bytes = base64.b64decode(serialized)
    return np.frombuffer(gradient_bytes, dtype=dtype).reshape(shape)


def get_privacy_metrics(
    epsilon: float,
    delta: float,
    clipping_norm: float,
) -> Dict[str, Any]:
    """
    Get privacy metrics for configuration
    
    Args:
        epsilon: Privacy budget
        delta: Failure probability
        clipping_norm: Gradient clipping norm
    
    Returns:
        Dict with privacy properties
    """
    return {
        "differential_privacy_guarantee": f"({epsilon:.2f}, {delta:.2e})-DP",
        "epsilon_budget": epsilon,
        "delta_budget": delta,
        "gradient_clipping_norm": clipping_norm,
        "privacy_level": (
            "very_high" if epsilon < 0.5 else
            "high" if epsilon < 1.0 else
            "moderate" if epsilon < 5.0 else
            "low"
        ),
    }


def get_model_metrics(
    norm_difference: float,
    gradient_norm: float,
    aggregation_quality: float,
) -> Dict[str, float]:
    """
    Get model convergence metrics
    
    Args:
        norm_difference: ||w_new - w_old||
        gradient_norm: ||aggregated_gradient||
        aggregation_quality: Quality score (0.0-1.0)
    
    Returns:
        Dict with convergence metrics
    """
    return {
        "norm_difference": norm_difference,
        "gradient_norm": gradient_norm,
        "aggregation_quality": aggregation_quality,
        "convergence_rate": (
            "excellent" if norm_difference < 1e-4 else
            "good" if norm_difference < 1e-3 else
            "moderate" if norm_difference < 0.01 else
            "slow"
        ),
    }
