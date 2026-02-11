"""
Federated Learning + Blockchain Configuration

Centralizes all FL+Blockchain parameters: aggregation strategy, privacy budgets,
cryptographic settings, and training hyperparameters.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal
import os
from datetime import timedelta


@dataclass
class PrivacyConfig:
    """Differential Privacy and Encryption Parameters"""
    
    # Differential Privacy budget
    epsilon: float = float(os.getenv("FL_PRIVACY_EPSILON", "1.0"))  # Privacy budget
    delta: float = float(os.getenv("FL_PRIVACY_DELTA", "1e-5"))  # Failure probability
    
    # Gradient Clipping
    clipping_norm: float = 1.0  # L2 norm bound for gradients
    
    # Homomorphic Encryption
    enable_homomorphic_encryption: bool = True  # Encrypt gradients before aggregation
    he_key_size: int = 2048  # Bits for HE key
    
    # Secure Aggregation
    enable_secure_aggregation: bool = True
    
    # Sanitization
    enable_gradient_sanitization: bool = True
    sanitization_rules: Dict[str, str] = field(default_factory=lambda: {
        "remove_pii": "true",
        "normalize_categories": "true",
        "anonymize_embeddings": "true",
    })


@dataclass
class AggregationConfig:
    """Federated Aggregation Strategy Configuration"""
    
    # Aggregation method
    method: Literal["fedavg", "fedprox", "secagg"] = "fedprox"  # FedProx better for non-IID
    
    # FedProx proximal term coefficient
    fedprox_lambda: float = 0.01
    
    # Learning rate
    learning_rate: float = 0.01
    
    # Minimum clients required for round
    min_clients_per_round: int = int(os.getenv("FL_MIN_CLIENTS", "2"))
    
    # Timeout for waiting client gradients
    client_timeout_seconds: int = 300  # 5 minutes
    
    # Robust aggregation (Byzantine resilience)
    enable_robust_aggregation: bool = True
    robust_method: Literal["median", "trimmed_mean", "krum"] = "trimmed_mean"
    trimmed_percentage: float = 0.1  # Trim 10% from both tails


@dataclass
class BlockchainConfig:
    """Blockchain Ledger Configuration"""
    
    # Block creation
    create_block_every_n_rounds: int = 1  # Create block after each round
    
    # Signature algorithm
    signature_algorithm: Literal["hmac-sha256", "ed25519"] = "hmac-sha256"
    
    # Multi-signature requirement
    require_multisig: bool = True
    min_signatures: int = 2  # Minimum orgs required to sign block
    
    # Provenance tracking
    track_provenance: bool = True
    max_provenance_depth: int = 100  # Maintain lineage for last N models
    
    # Ledger storage
    ledger_db_path: str = os.getenv("FL_LEDGER_DB_PATH", "var/fl_blockchain_ledger.db")
    

@dataclass
class TrainingConfig:
    """Federated Training Configuration"""
    
    # Model type
    model_type: Literal["tgnn", "rl", "combined"] = "combined"
    
    # Training parameters
    num_epochs_local: int = 1  # Local training epochs per round
    batch_size: int = 32
    
    # Convergence criteria
    convergence_threshold: float = 1e-4  # Stop if ||w_new - w_old|| < threshold
    max_rounds: int = 100  # Maximum training rounds
    
    # Model checkpointing
    checkpoint_every_n_rounds: int = 10
    checkpoint_dir: str = os.getenv("FL_CHECKPOINT_DIR", "var/fl_checkpoints")


@dataclass
class FederationConfig:
    """Global Federation Configuration"""
    
    # Orchestration
    orchestrator_id: str = os.getenv("FL_ORCHESTRATOR_ID", "global-orchestrator")
    orchestrator_port: int = int(os.getenv("FL_ORCHESTRATOR_PORT", "8001"))
    
    # Organization registry
    org_registry_file: str = os.getenv("FL_ORG_REGISTRY", "var/fl_orgs.json")
    
    # State management
    state_db_path: str = os.getenv("FL_STATE_DB", "var/fl_state.db")
    
    # Federation rounds
    initial_round: int = 0
    round_interval_minutes: int = 60  # Time between rounds
    
    # Failure handling
    enable_Byzantine_detection: bool = True
    reputation_window_size: int = 10  # Last N rounds for reputation
    


@dataclass
class FLBlockchainConfig:
    """Master FL+Blockchain Configuration"""
    
    # Sub-configs
    privacy: PrivacyConfig = field(default_factory=PrivacyConfig)
    aggregation: AggregationConfig = field(default_factory=AggregationConfig)
    blockchain: BlockchainConfig = field(default_factory=BlockchainConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    federation: FederationConfig = field(default_factory=FederationConfig)
    
    # Debugging & Logging
    debug_mode: bool = bool(os.getenv("FL_DEBUG", "false").lower() == "true")
    log_level: str = os.getenv("FL_LOG_LEVEL", "INFO")
    
    # Timeouts
    request_timeout_seconds: int = 30
    aggregation_timeout_seconds: int = 600  # 10 minutes
    
    @classmethod
    def from_env(cls) -> "FLBlockchainConfig":
        """Load config from environment variables"""
        return cls(
            privacy=PrivacyConfig(),
            aggregation=AggregationConfig(),
            blockchain=BlockchainConfig(),
            training=TrainingConfig(),
            federation=FederationConfig(),
            debug_mode=bool(os.getenv("FL_DEBUG", "false").lower() == "true"),
            log_level=os.getenv("FL_LOG_LEVEL", "INFO"),
        )


# Global singleton config instance
_config: Optional[FLBlockchainConfig] = None


def get_fl_config() -> FLBlockchainConfig:
    """Get or create global FL+Blockchain configuration"""
    global _config
    if _config is None:
        _config = FLBlockchainConfig.from_env()
    return _config


def set_fl_config(config: FLBlockchainConfig) -> None:
    """Override global FL+Blockchain configuration"""
    global _config
    _config = config
