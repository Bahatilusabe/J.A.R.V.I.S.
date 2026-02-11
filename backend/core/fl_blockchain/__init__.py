"""
Federated Learning + Blockchain XDR Module

Complete implementation of federated learning with blockchain-verified
model provenance for global threat intelligence sharing.

Core Components:
- Federation: Orchestrator, aggregation (FedAvg/FedProx), client management
- Privacy: Differential privacy, homomorphic encryption, gradient sanitization
- Models: Federated TGNN, Federated RL
- Blockchain: Immutable ledger, model provenance, verification
- Config: Centralized configuration management
"""

from .config import get_fl_config, set_fl_config, FLBlockchainConfig
from .exceptions import (
    FLBlockchainException,
    FederationException,
    PrivacyException,
    BlockchainException,
    ModelException,
)

from .federation import (
    FederationOrchestrator,
    get_federation_orchestrator,
    TrainingRoundState,
    RoundPhase,
    FederatedAggregator,
    RobustAggregator,
)

from .privacy import (
    DifferentialPrivacyMechanism,
    PrivacyBudgetManager,
    GradientSanitizer,
    HomomorphicEncryptor,
    SecureAggregationProtocol,
)

from .models import (
    FederatedTGNNModel,
    FederatedRLPolicy,
    FederatedModelState,
)

from .blockchain import (
    BlockchainLedger,
    get_blockchain_ledger,
    Block,
    BlockProvenance,
)

__all__ = [
    # Config
    "get_fl_config",
    "set_fl_config",
    "FLBlockchainConfig",
    
    # Exceptions
    "FLBlockchainException",
    "FederationException",
    "PrivacyException",
    "BlockchainException",
    "ModelException",
    
    # Federation
    "FederationOrchestrator",
    "get_federation_orchestrator",
    "TrainingRoundState",
    "RoundPhase",
    "FederatedAggregator",
    "RobustAggregator",
    
    # Privacy
    "DifferentialPrivacyMechanism",
    "PrivacyBudgetManager",
    "GradientSanitizer",
    "HomomorphicEncryptor",
    "SecureAggregationProtocol",
    
    # Models
    "FederatedTGNNModel",
    "FederatedRLPolicy",
    "FederatedModelState",
    
    # Blockchain
    "BlockchainLedger",
    "get_blockchain_ledger",
    "Block",
    "BlockProvenance",
]
