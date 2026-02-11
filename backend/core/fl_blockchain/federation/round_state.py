"""
Federated Training Round State Management

Tracks the lifecycle of each federated training round:
registration → local training → aggregation → verification → completion.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime
from enum import Enum
import json
import logging

logger = logging.getLogger("jarvis.fl_blockchain.round_state")


class RoundPhase(str, Enum):
    """Training round lifecycle phases"""
    INITIALIZED = "initialized"  # Round created, awaiting client start
    IN_PROGRESS = "in_progress"  # Clients training locally
    AGGREGATING = "aggregating"  # Collecting & aggregating gradients
    VERIFYING = "verifying"  # Blockchain verification
    COMPLETED = "completed"  # Round finished successfully
    FAILED = "failed"  # Round terminated with error


class OrgPhase(str, Enum):
    """Organization participation phase in round"""
    PENDING = "pending"  # Awaiting gradient submission
    SUBMITTED = "submitted"  # Gradient received
    VERIFIED = "verified"  # Signature verified
    AGGREGATED = "aggregated"  # Included in aggregation
    FAILED = "failed"  # Error in submission/verification


@dataclass
class OrgGradient:
    """Organization's gradient submission for a round"""
    org_id: str
    timestamp: datetime
    gradient_hash: str  # SHA-256 of encrypted gradient
    encrypted_gradient: str  # Base64-encoded encrypted gradient
    signature: str  # HMAC signature
    phase: OrgPhase = OrgPhase.PENDING
    error_message: Optional[str] = None
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class ConvergenceMetrics:
    """Training convergence metrics for a round"""
    norm_difference: float = 0.0  # ||w_new - w_old||
    gradient_norm: float = 0.0  # ||aggregated_gradient||
    loss_value: Optional[float] = None
    accuracy: Optional[float] = None
    privacy_epsilon_used: float = 0.0
    privacy_delta_used: float = 0.0
    aggregation_quality: float = 1.0  # 0.0 = poor, 1.0 = excellent
    

@dataclass
class BlockchainRecord:
    """Blockchain record metadata for round completion"""
    block_height: int = 0
    block_hash: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    model_hash: str = ""
    org_signatures: Dict[str, str] = field(default_factory=dict)
    provenance: Dict[str, any] = field(default_factory=dict)
    verified: bool = False


class TrainingRoundState:
    """
    Manages the state of a single federated training round.
    
    Tracks:
    - Organization participation
    - Gradient collection
    - Aggregation progress
    - Blockchain verification
    - Convergence metrics
    """
    
    def __init__(
        self,
        round_number: int,
        global_model_hash: str,
        deadline_seconds: int = 300,
        min_clients: int = 2,
    ):
        self.round_number = round_number
        self.global_model_hash = global_model_hash
        self.deadline_seconds = deadline_seconds
        self.min_clients = min_clients
        
        # Lifecycle
        self.phase = RoundPhase.INITIALIZED
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
        # Organization tracking
        self.org_gradients: Dict[str, OrgGradient] = {}  # org_id → OrgGradient
        self.participating_orgs: Set[str] = set()
        
        # Aggregation state
        self.aggregated_weights: Optional[str] = None  # Base64 encoded
        self.aggregation_method: str = "fedprox"
        self.convergence_metrics: Optional[ConvergenceMetrics] = None
        
        # Blockchain
        self.blockchain_record: Optional[BlockchainRecord] = None
        
        # Errors
        self.errors: List[str] = []
    
    # === Round Lifecycle ===
    
    def start_round(self) -> None:
        """Transition to IN_PROGRESS phase"""
        if self.phase != RoundPhase.INITIALIZED:
            raise RuntimeError(f"Cannot start round in {self.phase} phase")
        self.started_at = datetime.utcnow()
        self.phase = RoundPhase.IN_PROGRESS
        logger.info(f"Round {self.round_number} started")
    
    def start_aggregation(self) -> None:
        """Transition to AGGREGATING phase"""
        if self.phase != RoundPhase.IN_PROGRESS:
            raise RuntimeError(f"Cannot aggregate in {self.phase} phase")
        self.phase = RoundPhase.AGGREGATING
        logger.info(f"Round {self.round_number} aggregating gradients")
    
    def start_verification(self) -> None:
        """Transition to VERIFYING phase"""
        if self.phase != RoundPhase.AGGREGATING:
            raise RuntimeError(f"Cannot verify in {self.phase} phase")
        self.phase = RoundPhase.VERIFYING
        logger.info(f"Round {self.round_number} verifying blockchain")
    
    def complete_round(self) -> None:
        """Transition to COMPLETED phase"""
        if self.phase != RoundPhase.VERIFYING:
            raise RuntimeError(f"Cannot complete in {self.phase} phase")
        self.completed_at = datetime.utcnow()
        self.phase = RoundPhase.COMPLETED
        logger.info(f"Round {self.round_number} completed successfully")
    
    def fail_round(self, error_message: str) -> None:
        """Transition to FAILED phase"""
        self.phase = RoundPhase.FAILED
        self.errors.append(error_message)
        logger.error(f"Round {self.round_number} failed: {error_message}")
    
    # === Gradient Management ===
    
    def register_organization(self, org_id: str) -> None:
        """Register organization as participant"""
        self.participating_orgs.add(org_id)
        logger.debug(f"Registered org {org_id} for round {self.round_number}")
    
    def submit_gradient(
        self,
        org_id: str,
        gradient_hash: str,
        encrypted_gradient: str,
        signature: str,
        metadata: Optional[Dict[str, any]] = None,
    ) -> None:
        """Record gradient submission from organization"""
        if org_id not in self.participating_orgs:
            raise RuntimeError(f"Organization {org_id} not registered")
        
        if org_id in self.org_gradients:
            raise RuntimeError(f"Org {org_id} already submitted gradient")
        
        gradient = OrgGradient(
            org_id=org_id,
            timestamp=datetime.utcnow(),
            gradient_hash=gradient_hash,
            encrypted_gradient=encrypted_gradient,
            signature=signature,
            phase=OrgPhase.SUBMITTED,
            metadata=metadata or {}
        )
        self.org_gradients[org_id] = gradient
        logger.info(f"Gradient submitted by {org_id} (hash: {gradient_hash[:16]}...)")
    
    def verify_gradient(self, org_id: str, signature_valid: bool) -> None:
        """Mark gradient as verified"""
        if org_id not in self.org_gradients:
            raise RuntimeError(f"No gradient from {org_id}")
        
        gradient = self.org_gradients[org_id]
        if signature_valid:
            gradient.phase = OrgPhase.VERIFIED
            logger.debug(f"Gradient from {org_id} verified")
        else:
            gradient.phase = OrgPhase.FAILED
            gradient.error_message = "Signature verification failed"
            logger.warning(f"Gradient from {org_id} failed verification")
    
    def mark_gradient_aggregated(self, org_id: str) -> None:
        """Mark gradient as included in aggregation"""
        if org_id not in self.org_gradients:
            raise RuntimeError(f"No gradient from {org_id}")
        self.org_gradients[org_id].phase = OrgPhase.AGGREGATED
    
    # === Aggregation Results ===
    
    def set_aggregation_result(
        self,
        aggregated_weights: str,
        method: str,
        metrics: ConvergenceMetrics,
    ) -> None:
        """Record aggregation result"""
        self.aggregated_weights = aggregated_weights
        self.aggregation_method = method
        self.convergence_metrics = metrics
        logger.info(
            f"Round {self.round_number} aggregation complete "
            f"(norm_diff: {metrics.norm_difference:.6f}, "
            f"epsilon_used: {metrics.privacy_epsilon_used:.4f})"
        )
    
    # === Blockchain Integration ===
    
    def set_blockchain_record(self, record: BlockchainRecord) -> None:
        """Record blockchain verification result"""
        self.blockchain_record = record
        logger.info(
            f"Round {self.round_number} recorded on blockchain "
            f"(block_height: {record.block_height}, hash: {record.block_hash[:16]}...)"
        )
    
    # === Query Methods ===
    
    def get_phase(self) -> str:
        """Get current round phase"""
        return self.phase.value
    
    def num_gradients_received(self) -> int:
        """Count gradients submitted"""
        return len(self.org_gradients)
    
    def num_gradients_verified(self) -> int:
        """Count verified gradients"""
        return sum(
            1 for g in self.org_gradients.values()
            if g.phase in (OrgPhase.VERIFIED, OrgPhase.AGGREGATED)
        )
    
    def has_min_participants(self) -> bool:
        """Check if minimum participants requirement met"""
        return self.num_gradients_verified() >= self.min_clients
    
    def is_deadline_passed(self) -> bool:
        """Check if deadline exceeded"""
        if self.started_at is None:
            return False
        elapsed = (datetime.utcnow() - self.started_at).total_seconds()
        return elapsed > self.deadline_seconds
    
    def get_status_dict(self) -> Dict[str, any]:
        """Get round status as dictionary"""
        return {
            "round_number": self.round_number,
            "phase": self.phase.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "participating_orgs": len(self.participating_orgs),
            "gradients_received": self.num_gradients_received(),
            "gradients_verified": self.num_gradients_verified(),
            "aggregation_method": self.aggregation_method,
            "convergence_metrics": {
                "norm_difference": self.convergence_metrics.norm_difference if self.convergence_metrics else None,
                "gradient_norm": self.convergence_metrics.gradient_norm if self.convergence_metrics else None,
                "privacy_epsilon_used": self.convergence_metrics.privacy_epsilon_used if self.convergence_metrics else None,
                "privacy_delta_used": self.convergence_metrics.privacy_delta_used if self.convergence_metrics else None,
            } if self.convergence_metrics else None,
            "blockchain_verified": self.blockchain_record.verified if self.blockchain_record else False,
            "errors": self.errors,
        }
    
    def to_json(self) -> str:
        """Serialize round state to JSON"""
        return json.dumps(self.get_status_dict(), indent=2)
