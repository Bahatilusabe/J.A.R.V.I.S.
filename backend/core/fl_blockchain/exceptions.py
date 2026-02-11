"""
FL+Blockchain Custom Exceptions

Specific exception hierarchy for federated learning and blockchain operations.
"""


class FLBlockchainException(Exception):
    """Base exception for FL+Blockchain module"""
    pass


# Federation Exceptions
class FederationException(FLBlockchainException):
    """Base federation exception"""
    pass


class OrganizationNotRegistered(FederationException):
    """Organization not found in registry"""
    pass


class RoundAlreadyActive(FederationException):
    """Training round already in progress"""
    pass


class RoundTimeout(FederationException):
    """Training round timed out waiting for gradients"""
    pass


class InsufficientParticipants(FederationException):
    """Not enough organizations to start round"""
    pass


class AggregationFailed(FederationException):
    """Gradient aggregation failed"""
    pass


# Privacy Exceptions
class PrivacyException(FLBlockchainException):
    """Base privacy exception"""
    pass


class PrivacyBudgetExhausted(PrivacyException):
    """Differential privacy budget exhausted"""
    pass


class SanitizationFailed(PrivacyException):
    """Gradient sanitization failed"""
    pass


class EncryptionFailed(PrivacyException):
    """Homomorphic encryption/decryption failed"""
    pass


class InvalidGradient(PrivacyException):
    """Gradient does not meet validation criteria"""
    pass


# Blockchain Exceptions
class BlockchainException(FLBlockchainException):
    """Base blockchain exception"""
    pass


class InvalidBlock(BlockchainException):
    """Block does not meet validity criteria"""
    pass


class InvalidSignature(BlockchainException):
    """Block signature verification failed"""
    pass


class InsufficientSignatures(BlockchainException):
    """Block does not have required multi-signatures"""
    pass


class ProvenanceCheckFailed(BlockchainException):
    """Model provenance verification failed"""
    pass


class LedgerCorruption(BlockchainException):
    """Blockchain ledger integrity check failed"""
    pass


# Model Exceptions
class ModelException(FLBlockchainException):
    """Base model exception"""
    pass


class InvalidModelState(ModelException):
    """Model state is invalid or corrupted"""
    pass


class ModelConvergenceFailed(ModelException):
    """Model failed to converge"""
    pass


# Configuration Exceptions
class ConfigurationException(FLBlockchainException):
    """Configuration error"""
    pass


class InvalidPrivacyBudget(ConfigurationException):
    """Privacy budget parameters invalid"""
    pass
