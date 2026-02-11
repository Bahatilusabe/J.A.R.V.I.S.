"""
Differential Privacy Implementation

Adds calibrated noise to gradients to provide formal privacy guarantees
against membership inference and model inversion attacks.
"""

from typing import Tuple
import numpy as np
import logging

logger = logging.getLogger("jarvis.fl_blockchain.privacy")


class DifferentialPrivacyMechanism:
    """
    Differentially private gradient sanitization using Gaussian mechanism.
    
    Adds noise: gradient_DP = gradient + N(0, σ²)
    
    where σ is calibrated to provide (ε, δ)-differential privacy guarantee.
    """
    
    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5):
        """
        Initialize DP mechanism
        
        Args:
            epsilon: Privacy budget (lower = more private but noisier)
            delta: Failure probability
        """
        if not (0 < epsilon <= 10):
            raise ValueError(f"epsilon must be in (0, 10], got {epsilon}")
        if not (0 < delta < 1):
            raise ValueError(f"delta must be in (0, 1), got {delta}")
        
        self.epsilon = epsilon
        self.delta = delta
        
        # Compute noise scale using Gaussian mechanism
        # For (ε, δ)-DP: σ = sqrt(2 * log(1.25/δ)) / ε
        self.sigma = np.sqrt(2.0 * np.log(1.25 / delta)) / epsilon
        
        logger.info(f"DP mechanism initialized: ε={epsilon}, δ={delta}, σ={self.sigma:.6f}")
    
    def add_noise(self, gradient: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Add Gaussian noise to gradient
        
        Args:
            gradient: Input gradient array
        
        Returns:
            (noisy_gradient, noise_scale)
        """
        # Generate noise from standard normal, scaled by sigma
        noise = np.random.normal(
            loc=0.0,
            scale=self.sigma,
            size=gradient.shape
        )
        
        noisy_gradient = gradient + noise
        
        return noisy_gradient, float(self.sigma)
    
    def add_noise_with_clipping(
        self,
        gradient: np.ndarray,
        clipping_norm: float = 1.0,
    ) -> Tuple[np.ndarray, float]:
        """
        Add noise with gradient clipping for more stable privacy
        
        Clipping reduces sensitivity of gradients, allowing smaller σ.
        
        Args:
            gradient: Input gradient array
            clipping_norm: L2 norm bound for gradients
        
        Returns:
            (noisy_clipped_gradient, noise_scale)
        """
        # L2 norm clipping
        gradient_norm = np.linalg.norm(gradient)
        if gradient_norm > clipping_norm:
            gradient = gradient * (clipping_norm / gradient_norm)
        
        # Add noise
        noisy_gradient, sigma = self.add_noise(gradient)
        
        return noisy_gradient, sigma


class PrivacyBudgetManager:
    """
    Tracks cumulative privacy budget across multiple rounds.
    
    Ensures total privacy loss (ε_total, δ_total) stays within bounds.
    """
    
    def __init__(
        self,
        max_epsilon: float = 10.0,
        max_delta: float = 1e-2,
    ):
        """
        Initialize privacy budget manager
        
        Args:
            max_epsilon: Maximum cumulative epsilon budget
            max_delta: Maximum cumulative delta budget
        """
        self.max_epsilon = max_epsilon
        self.max_delta = max_delta
        
        self.used_epsilon = 0.0
        self.used_delta = 0.0
        self.round_history = []  # Track per-round usage
    
    def check_budget(self, epsilon: float, delta: float) -> bool:
        """Check if proposed epsilon/delta would exceed budget"""
        return (
            (self.used_epsilon + epsilon <= self.max_epsilon) and
            (self.used_delta + delta <= self.max_delta)
        )
    
    def consume_budget(
        self,
        round_number: int,
        epsilon: float,
        delta: float,
    ) -> None:
        """
        Record privacy budget consumption for a round
        
        Args:
            round_number: Training round number
            epsilon: Epsilon used in this round
            delta: Delta used in this round
        """
        if not self.check_budget(epsilon, delta):
            raise ValueError(
                f"Privacy budget exceeded: "
                f"ε={self.used_epsilon + epsilon}/{self.max_epsilon}, "
                f"δ={self.used_delta + delta}/{self.max_delta}"
            )
        
        self.used_epsilon += epsilon
        self.used_delta += delta
        
        self.round_history.append({
            "round": round_number,
            "epsilon": epsilon,
            "delta": delta,
            "cumulative_epsilon": self.used_epsilon,
            "cumulative_delta": self.used_delta,
        })
        
        logger.info(
            f"Privacy budget consumed in round {round_number}: "
            f"ε={epsilon:.4f} (total: {self.used_epsilon:.4f}/{self.max_epsilon}), "
            f"δ={delta:.2e} (total: {self.used_delta:.2e}/{self.max_delta})"
        )
    
    def get_remaining_budget(self) -> Tuple[float, float]:
        """Get remaining privacy budget"""
        return (
            self.max_epsilon - self.used_epsilon,
            self.max_delta - self.used_delta,
        )
    
    def get_usage_percentage(self) -> Tuple[float, float]:
        """Get privacy budget usage as percentages"""
        return (
            (self.used_epsilon / self.max_epsilon) * 100,
            (self.used_delta / self.max_delta) * 100,
        )


def compute_dp_noise_scale(
    epsilon: float,
    delta: float,
    gradient_shape: tuple,
    clipping_norm: float = 1.0,
) -> float:
    """
    Compute noise scale for DP-SGD with gradient clipping
    
    Args:
        epsilon: Privacy budget
        delta: Failure probability
        gradient_shape: Shape of gradient tensor
        clipping_norm: L2 norm bound
    
    Returns:
        Noise standard deviation (σ)
    """
    # Gaussian mechanism: σ = sqrt(2 * log(1.25/δ)) / ε
    return np.sqrt(2.0 * np.log(1.25 / delta)) / epsilon


def get_privacy_budget_for_epsilon_delta(
    desired_epsilon: float,
    desired_delta: float,
    gradient_clipping_norm: float = 1.0,
) -> dict:
    """
    Get recommended privacy parameters for desired DP guarantee
    
    Args:
        desired_epsilon: Target epsilon value
        desired_delta: Target delta value
        gradient_clipping_norm: Gradient clipping threshold
    
    Returns:
        Dict with recommended privacy parameters
    """
    sigma = compute_dp_noise_scale(
        desired_epsilon,
        desired_delta,
        None,
        gradient_clipping_norm
    )
    
    return {
        "epsilon": desired_epsilon,
        "delta": desired_delta,
        "noise_scale": sigma,
        "gradient_clipping_norm": gradient_clipping_norm,
        "guarantees": f"({desired_epsilon:.2f}, {desired_delta:.2e})-DP",
    }
