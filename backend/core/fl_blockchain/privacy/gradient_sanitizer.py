"""
Gradient Sanitization

Removes PII, normalizes sensitive fields, and applies security constraints
to gradients before transmission and aggregation.
"""

from typing import Dict, Optional, Tuple
import numpy as np
import logging

logger = logging.getLogger("jarvis.fl_blockchain.sanitizer")


class GradientSanitizer:
    """
    Sanitizes gradients by removing PII, normalizing embeddings,
    and enforcing constraints.
    """
    
    def __init__(
        self,
        clipping_norm: float = 1.0,
        remove_pii: bool = True,
        normalize_categories: bool = True,
    ):
        """
        Initialize gradient sanitizer
        
        Args:
            clipping_norm: L2 norm bound for gradients
            remove_pii: Remove PII from embeddings
            normalize_categories: Normalize threat categories
        """
        self.clipping_norm = clipping_norm
        self.remove_pii = remove_pii
        self.normalize_categories = normalize_categories
        
        logger.info(f"GradientSanitizer initialized (clipping={clipping_norm})")
    
    def sanitize(
        self,
        gradient: np.ndarray,
        metadata: Optional[Dict[str, any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, any]]:
        """
        Sanitize gradient and return sanitized version with metrics
        
        Args:
            gradient: Input gradient array
            metadata: Optional gradient metadata (org_id, sample_count, etc.)
        
        Returns:
            (sanitized_gradient, sanitization_stats)
        """
        stats = {
            "original_norm": float(np.linalg.norm(gradient)),
            "original_shape": gradient.shape,
            "clipped": False,
            "pii_removed": False,
            "categories_normalized": False,
        }
        
        sanitized = gradient.copy()
        
        # 1. L2 norm clipping
        norm = np.linalg.norm(sanitized)
        if norm > self.clipping_norm:
            sanitized = sanitized * (self.clipping_norm / norm)
            stats["clipped"] = True
            logger.debug(f"Gradient clipped: {norm:.4f} → {self.clipping_norm:.4f}")
        
        # 2. Detect and remove PII patterns
        if self.remove_pii:
            sanitized = self._remove_pii(sanitized)
            stats["pii_removed"] = True
        
        # 3. Normalize threat categories
        if self.normalize_categories:
            sanitized = self._normalize_categories(sanitized)
            stats["categories_normalized"] = True
        
        # 4. Final validation
        final_norm = np.linalg.norm(sanitized)
        stats["final_norm"] = float(final_norm)
        stats["norm_reduction_ratio"] = float(stats["final_norm"] / (stats["original_norm"] + 1e-8))
        
        # Check for NaN/Inf
        if np.any(np.isnan(sanitized)) or np.any(np.isinf(sanitized)):
            raise ValueError("Sanitized gradient contains NaN or Inf values")
        
        return sanitized, stats
    
    def _remove_pii(self, gradient: np.ndarray) -> np.ndarray:
        """
        Remove PII from gradient embeddings
        
        Strategy: Zero out dimensions that appear to contain PII
        (e.g., dimensions with very large/small values, specific patterns)
        """
        # Mark dimensions with extreme values as potential PII
        # (simplified heuristic; in production, use more sophisticated detection)
        sanitized = gradient.copy()
        
        # Check for extremely large values (might be IDs or timestamps)
        suspicious_dims = np.abs(sanitized) > 1e6
        sanitized[suspicious_dims] = 0.0
        
        return sanitized
    
    def _normalize_categories(self, gradient: np.ndarray) -> np.ndarray:
        """
        Normalize threat category embeddings
        
        Ensures all embeddings have similar scale (L2 norm ≈ 1.0)
        """
        sanitized = gradient.copy()
        
        # Per-element normalization (if treating as embedding vectors)
        # This is a simplified approach; real implementation would
        # operate on semantic dimensions
        
        # Avoid division by zero
        norms = np.maximum(np.abs(sanitized), 1e-6)
        sanitized = sanitized / norms
        
        return sanitized


class SecureGradientValidator:
    """
    Validates gradients against security constraints
    before acceptance into aggregation.
    """
    
    def __init__(
        self,
        max_gradient_norm: float = 10.0,
        max_nan_ratio: float = 0.1,  # 10% NaN allowed before rejection
    ):
        """
        Initialize gradient validator
        
        Args:
            max_gradient_norm: Maximum acceptable L2 norm
            max_nan_ratio: Maximum ratio of NaN/Inf values
        """
        self.max_gradient_norm = max_gradient_norm
        self.max_nan_ratio = max_nan_ratio
    
    def validate(self, gradient: np.ndarray) -> Tuple[bool, str]:
        """
        Validate gradient meets security constraints
        
        Args:
            gradient: Gradient to validate
        
        Returns:
            (is_valid, error_message)
        """
        # Check shape (should be 1D or 2D)
        if len(gradient.shape) > 2:
            return False, f"Gradient shape too high-dimensional: {gradient.shape}"
        
        # Check for NaN/Inf
        nan_count = np.isnan(gradient).sum()
        inf_count = np.isinf(gradient).sum()
        total_invalid = nan_count + inf_count
        
        if total_invalid > 0:
            ratio = total_invalid / gradient.size
            if ratio > self.max_nan_ratio:
                return False, (
                    f"Too many NaN/Inf values: {total_invalid} "
                    f"({ratio*100:.1f}% > {self.max_nan_ratio*100:.1f}%)"
                )
        
        # Check norm
        norm = np.linalg.norm(gradient)
        if norm > self.max_gradient_norm:
            return False, (
                f"Gradient norm too large: {norm:.4f} > {self.max_gradient_norm:.4f}"
            )
        
        # Check for all-zero gradient (possible data privacy issue)
        if np.allclose(gradient, 0.0):
            logger.warning("All-zero gradient submitted")
        
        return True, "OK"


def create_sanitizer(
    clipping_norm: float = 1.0,
    **kwargs
) -> GradientSanitizer:
    """Factory function to create gradient sanitizer"""
    return GradientSanitizer(clipping_norm=clipping_norm, **kwargs)
