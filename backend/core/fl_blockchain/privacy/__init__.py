"""
Privacy & Security Layer for Federated Learning

Implements differential privacy, homomorphic encryption, gradient sanitization,
and secure aggregation protocols.
"""

from .differential_privacy import (
    DifferentialPrivacyMechanism,
    PrivacyBudgetManager,
    compute_dp_noise_scale,
    get_privacy_budget_for_epsilon_delta,
)
from .gradient_sanitizer import (
    GradientSanitizer,
    SecureGradientValidator,
    create_sanitizer,
)
from .homomorphic import (
    HomomorphicEncryptor,
    create_encryptor,
)
from .secure_aggregation import (
    SecureAggregationProtocol,
    SecAggMaskManager,
)

__all__ = [
    "DifferentialPrivacyMechanism",
    "PrivacyBudgetManager",
    "compute_dp_noise_scale",
    "get_privacy_budget_for_epsilon_delta",
    "GradientSanitizer",
    "SecureGradientValidator",
    "create_sanitizer",
    "HomomorphicEncryptor",
    "create_encryptor",
    "SecureAggregationProtocol",
    "SecAggMaskManager",
]
