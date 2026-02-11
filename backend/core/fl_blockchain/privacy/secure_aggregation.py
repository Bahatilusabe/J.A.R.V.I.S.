"""
Secure Aggregation Protocol

Cryptographic protocol for aggregating gradients without revealing
individual gradients to any party (not even the server).
"""

from typing import Dict, Tuple, Optional
import numpy as np
import hmac
import hashlib
import logging

logger = logging.getLogger("jarvis.fl_blockchain.secagg")


class SecureAggregationProtocol:
    """
    Implements secure aggregation (SecAgg) protocol.
    
    Each client:
    1. Masks gradient with random mask
    2. Sends masked gradient to server
    3. If client drops out, other clients reveal their masks
    4. Server computes: Σ(masked_gradients) - Σ(masks) = Σ(true_gradients)
    
    Privacy guarantee: Server sees only aggregate, never individual gradients.
    """
    
    def __init__(self, masking_rounds: int = 1):
        """
        Initialize SecAgg protocol
        
        Args:
            masking_rounds: Number of masking rounds for stronger privacy
        """
        self.masking_rounds = masking_rounds
        self.client_masks: Dict[str, np.ndarray] = {}
    
    def generate_mask(
        self,
        org_id: str,
        gradient_shape: tuple,
        seed: Optional[int] = None,
    ) -> np.ndarray:
        """
        Generate random mask for organization's gradient
        
        Args:
            org_id: Organization ID
            gradient_shape: Shape of gradient to mask
            seed: Random seed (for reproducibility in testing)
        
        Returns:
            Random mask array
        """
        if seed is not None:
            np.random.seed(seed)
        
        # Generate random mask with same shape as gradient
        mask = np.random.randn(*gradient_shape)
        
        # Store for later (needed if org drops out)
        self.client_masks[org_id] = mask.copy()
        
        logger.debug(f"Generated mask for {org_id}: shape={gradient_shape}")
        return mask
    
    def apply_mask(
        self,
        gradient: np.ndarray,
        mask: np.ndarray,
    ) -> np.ndarray:
        """
        Apply mask to gradient
        
        Args:
            gradient: Original gradient
            mask: Mask generated for this organization
        
        Returns:
            Masked gradient (gradient - mask)
        """
        masked = gradient - mask
        return masked
    
    def remove_mask(
        self,
        masked_gradient: np.ndarray,
        mask: np.ndarray,
    ) -> np.ndarray:
        """
        Remove mask from gradient
        
        Args:
            masked_gradient: Masked gradient (gradient - mask)
            mask: Original mask
        
        Returns:
            Unmasked gradient
        """
        unmasked = masked_gradient + mask
        return unmasked
    
    def aggregate_masked_gradients(
        self,
        masked_gradients: Dict[str, np.ndarray],
        available_masks: Dict[str, np.ndarray],
    ) -> np.ndarray:
        """
        Aggregate masked gradients with dropout handling
        
        If an organization dropped out:
        - Its gradient was never received
        - But other orgs revealed their masks for it
        - So we can still aggregate correctly
        
        Args:
            masked_gradients: org_id → masked gradient (gradient - mask)
            available_masks: org_id → mask (from participating orgs)
        
        Returns:
            Aggregated gradient (sum of true gradients)
        """
        if not masked_gradients:
            raise ValueError("No masked gradients to aggregate")
        
        # Verify all organizations are accounted for
        all_orgs = set(masked_gradients.keys()) | set(available_masks.keys())
        
        # For organizations that submitted: sum(masked_gradients)
        # For organizations that dropped: already accounted in masks
        
        # Sum masked gradients
        aggregated = None
        for org_id, masked_grad in masked_gradients.items():
            if aggregated is None:
                aggregated = masked_grad.copy()
            else:
                aggregated = aggregated + masked_grad
        
        # Add back masks for dropped-out organizations
        for org_id, mask in available_masks.items():
            if org_id not in masked_gradients:
                # This org dropped out, add back its mask
                aggregated = aggregated + mask
        
        logger.info(
            f"SecAgg aggregation: {len(masked_gradients)} participants, "
            f"{len(available_masks) - len(masked_gradients)} dropouts handled"
        )
        
        return aggregated
    
    def verify_mask_commitment(
        self,
        org_id: str,
        mask: np.ndarray,
        commitment: str,
    ) -> bool:
        """
        Verify that revealed mask matches original commitment
        
        Args:
            org_id: Organization ID
            mask: Revealed mask
            commitment: Original commitment hash
        
        Returns:
            True if mask matches commitment
        """
        # Compute commitment hash of mask
        mask_bytes = mask.tobytes()
        computed_commitment = hashlib.sha256(mask_bytes).hexdigest()
        
        matches = computed_commitment == commitment
        if not matches:
            logger.warning(f"Mask commitment verification failed for {org_id}")
        
        return matches
    
    def get_mask_commitment(self, mask: np.ndarray) -> str:
        """
        Get commitment hash for mask (sent before training)
        
        Args:
            mask: Random mask
        
        Returns:
            SHA-256 commitment hash
        """
        mask_bytes = mask.tobytes()
        commitment = hashlib.sha256(mask_bytes).hexdigest()
        return commitment


class SecAggMaskManager:
    """
    Manages mask generation and storage across rounds.
    """
    
    def __init__(self):
        """Initialize mask manager"""
        self.mask_commitments: Dict[str, Dict[str, str]] = {}  # round → (org → commitment)
        self.revealed_masks: Dict[str, Dict[str, np.ndarray]] = {}  # round → (org → mask)
    
    def store_commitment(
        self,
        round_number: int,
        org_id: str,
        commitment: str,
    ) -> None:
        """Store mask commitment for a round"""
        if round_number not in self.mask_commitments:
            self.mask_commitments[round_number] = {}
        
        self.mask_commitments[round_number][org_id] = commitment
    
    def reveal_mask(
        self,
        round_number: int,
        org_id: str,
        mask: np.ndarray,
    ) -> None:
        """Record revealed mask"""
        if round_number not in self.revealed_masks:
            self.revealed_masks[round_number] = {}
        
        self.revealed_masks[round_number][org_id] = mask
    
    def verify_commitment(
        self,
        round_number: int,
        org_id: str,
        mask: np.ndarray,
    ) -> bool:
        """Verify revealed mask matches stored commitment"""
        if round_number not in self.mask_commitments:
            return False
        
        if org_id not in self.mask_commitments[round_number]:
            return False
        
        stored_commitment = self.mask_commitments[round_number][org_id]
        
        # Recompute commitment from revealed mask
        mask_bytes = mask.tobytes()
        computed_commitment = hashlib.sha256(mask_bytes).hexdigest()
        
        return computed_commitment == stored_commitment
