"""
Global Federated Learning Orchestrator

Coordinates training rounds across all organizations:
- Round initialization & coordination
- Gradient collection & aggregation
- Blockchain verification
- Model distribution

This is the central hub of the federation.
"""

from typing import Dict, List, Optional, Set
from datetime import datetime
import json
import logging
import asyncio
from dataclasses import dataclass

from .round_state import TrainingRoundState, RoundPhase, ConvergenceMetrics
from .aggregator import FederatedAggregator, RobustAggregator, create_aggregator
from ..config import get_fl_config, FLBlockchainConfig
from ..exceptions import (
    FederationException,
    RoundAlreadyActive,
    InsufficientParticipants,
    AggregationFailed,
)
import numpy as np

logger = logging.getLogger("jarvis.fl_blockchain.orchestrator")


@dataclass
class FederationStats:
    """Global federation statistics"""
    total_rounds: int = 0
    completed_rounds: int = 0
    failed_rounds: int = 0
    total_organizations: int = 0
    active_organizations: int = 0
    global_model_hash: str = ""
    global_model_version: str = ""
    total_privacy_epsilon_used: float = 0.0
    total_privacy_delta_used: float = 0.0
    avg_convergence_norm: float = 0.0


class FederationOrchestrator:
    """
    Central coordinator for federated learning training.
    
    Manages:
    - Organization registry
    - Round lifecycle coordination
    - Gradient aggregation
    - Blockchain verification
    - Global model distribution
    """
    
    def __init__(self, config: Optional[FLBlockchainConfig] = None):
        """
        Initialize federation orchestrator
        
        Args:
            config: FLBlockchainConfig instance (uses global if None)
        """
        self.config = config or get_fl_config()
        
        # Organization registry
        self.organizations: Dict[str, Dict] = {}  # org_id → org_info
        
        # Round management
        self.rounds: Dict[int, TrainingRoundState] = {}  # round_number → state
        self.current_round_number = self.config.federation.initial_round
        self.active_round: Optional[TrainingRoundState] = None
        
        # Global model
        self.global_weights: Optional[np.ndarray] = None
        self.global_model_hash: str = ""
        self.global_model_version: str = f"v1.0-round-{self.current_round_number}"
        
        # Statistics
        self.stats = FederationStats(
            total_organizations=0,
            global_model_version=self.global_model_version,
        )
        
        # Aggregator
        self._aggregator = None
        self._robust_aggregator = None
        
        logger.info(f"FederationOrchestrator initialized (round {self.current_round_number})")
    
    # === Organization Management ===
    
    def register_organization(
        self,
        org_id: str,
        public_key: str,
        endpoint: str,
        capabilities: Dict[str, bool],
    ) -> Dict[str, any]:
        """
        Register new organization for federation
        
        Args:
            org_id: Unique organization ID
            public_key: Public key for signature verification
            endpoint: Organization's API endpoint
            capabilities: {"federated_tgnn": bool, "federated_rl": bool, ...}
        
        Returns:
            Registration confirmation with token
        """
        if org_id in self.organizations:
            raise FederationException(f"Organization {org_id} already registered")
        
        self.organizations[org_id] = {
            "org_id": org_id,
            "public_key": public_key,
            "endpoint": endpoint,
            "capabilities": capabilities,
            "registered_at": datetime.utcnow().isoformat(),
            "last_submission": None,
            "reputation_score": 1.0,  # Start with perfect reputation
            "submission_count": 0,
            "failure_count": 0,
        }
        
        self.stats.total_organizations += 1
        self.stats.active_organizations += 1
        
        logger.info(f"Registered organization: {org_id}")
        
        return {
            "org_id": org_id,
            "status": "registered",
            "registration_token": f"token-{org_id}",
            "global_config": {
                "aggregation_method": self.config.aggregation.method,
                "privacy_epsilon": self.config.privacy.epsilon,
                "privacy_delta": self.config.privacy.delta,
                "clipping_norm": self.config.privacy.clipping_norm,
            }
        }
    
    def get_registered_organizations(self) -> List[str]:
        """Get list of registered organization IDs"""
        return list(self.organizations.keys())
    
    # === Round Management ===
    
    def start_training_round(self, round_number: Optional[int] = None) -> Dict[str, any]:
        """
        Initiate new federated training round
        
        Args:
            round_number: Round number (auto-increment if None)
        
        Returns:
            Round info: {round_id, deadline, privacy_params, global_weights_hash}
        """
        if self.active_round is not None:
            raise RoundAlreadyActive(
                f"Round {self.active_round.round_number} still active"
            )
        
        if round_number is None:
            round_number = self.current_round_number + 1
        
        # Create round state
        deadline = self.config.aggregation.client_timeout_seconds
        round_state = TrainingRoundState(
            round_number=round_number,
            global_model_hash=self.global_model_hash,
            deadline_seconds=deadline,
            min_clients=self.config.aggregation.min_clients_per_round,
        )
        
        # Register all active organizations
        for org_id in self.get_registered_organizations():
            round_state.register_organization(org_id)
        
        # Transition to IN_PROGRESS
        round_state.start_round()
        
        # Store round
        self.rounds[round_number] = round_state
        self.active_round = round_state
        self.current_round_number = round_number
        
        # Update stats
        self.stats.total_rounds += 1
        
        logger.info(
            f"Started training round {round_number} "
            f"({len(round_state.participating_orgs)} organizations)"
        )
        
        return {
            "round_id": round_number,
            "status": "active",
            "deadline_seconds": deadline,
            "global_model_hash": self.global_model_hash,
            "privacy_params": {
                "epsilon": self.config.privacy.epsilon,
                "delta": self.config.privacy.delta,
                "clipping_norm": self.config.privacy.clipping_norm,
            },
            "aggregation_method": self.config.aggregation.method,
        }
    
    def submit_gradient(
        self,
        round_number: int,
        org_id: str,
        gradient_hash: str,
        encrypted_gradient: str,
        signature: str,
        metadata: Optional[Dict[str, any]] = None,
    ) -> Dict[str, any]:
        """
        Receive gradient submission from organization
        
        Args:
            round_number: Training round number
            org_id: Submitting organization
            gradient_hash: SHA-256 hash of encrypted gradient
            encrypted_gradient: Base64-encoded encrypted gradient
            signature: HMAC signature
            metadata: Optional submission metadata
        
        Returns:
            Submission acknowledgment
        """
        if round_number not in self.rounds:
            raise FederationException(f"Round {round_number} not found")
        
        round_state = self.rounds[round_number]
        if round_state.phase != RoundPhase.IN_PROGRESS:
            raise FederationException(
                f"Round {round_number} not accepting submissions (phase: {round_state.phase})"
            )
        
        if org_id not in self.organizations:
            raise FederationException(f"Organization {org_id} not registered")
        
        # Record gradient submission
        round_state.submit_gradient(
            org_id=org_id,
            gradient_hash=gradient_hash,
            encrypted_gradient=encrypted_gradient,
            signature=signature,
            metadata=metadata,
        )
        
        # Update organization stats
        org = self.organizations[org_id]
        org["last_submission"] = datetime.utcnow().isoformat()
        org["submission_count"] += 1
        
        logger.info(f"Gradient received from {org_id} for round {round_number}")
        
        return {
            "status": "received",
            "round_id": round_number,
            "org_id": org_id,
            "gradient_hash": gradient_hash,
        }
    
    async def aggregate_round(
        self,
        round_number: int,
        decrypted_gradients: Dict[str, np.ndarray],
        sample_counts: Dict[str, int],
    ) -> Dict[str, any]:
        """
        Aggregate gradients after decryption and privacy processing
        
        Args:
            round_number: Training round number
            decrypted_gradients: org_id → decrypted gradient array
            sample_counts: org_id → number of local samples
        
        Returns:
            Aggregation result with metrics
        """
        if round_number not in self.rounds:
            raise FederationException(f"Round {round_number} not found")
        
        round_state = self.rounds[round_number]
        
        # Transition to aggregation phase
        try:
            round_state.start_aggregation()
        except RuntimeError as e:
            raise AggregationFailed(str(e))
        
        try:
            # Get aggregator
            aggregator = self._get_aggregator()
            
            # Run aggregation
            logger.info(
                f"Aggregating gradients from {len(decrypted_gradients)} organizations"
            )
            
            result = aggregator.aggregate(
                org_weights=decrypted_gradients,
                org_sample_counts=sample_counts,
                global_weights_prev=self.global_weights,
                learning_rate=self.config.aggregation.learning_rate,
            )
            
            # Update global model
            self.global_weights = result.aggregated_weights.copy()
            self.global_model_version = f"v{self._get_model_version()}-round-{round_number}"
            
            # Create convergence metrics
            metrics = ConvergenceMetrics(
                norm_difference=result.norm_difference,
                gradient_norm=result.gradient_norm,
                privacy_epsilon_used=self.config.privacy.epsilon,
                privacy_delta_used=self.config.privacy.delta,
                aggregation_quality=result.aggregation_quality,
            )
            
            # Record aggregation result
            round_state.set_aggregation_result(
                aggregated_weights=str(self.global_weights.tolist()),
                method=result.aggregation_method,
                metrics=metrics,
            )
            
            # Update statistics
            self.stats.avg_convergence_norm = metrics.norm_difference
            self.stats.total_privacy_epsilon_used += metrics.privacy_epsilon_used
            self.stats.total_privacy_delta_used += metrics.privacy_delta_used
            
            logger.info(
                f"Round {round_number} aggregation complete: "
                f"norm_diff={metrics.norm_difference:.6f}, "
                f"quality={result.aggregation_quality:.2f}"
            )
            
            return {
                "round_id": round_number,
                "status": "aggregated",
                "aggregation_method": result.aggregation_method,
                "num_participants": result.num_participants,
                "metrics": {
                    "norm_difference": metrics.norm_difference,
                    "gradient_norm": metrics.gradient_norm,
                    "aggregation_quality": metrics.aggregation_quality,
                },
            }
        
        except Exception as e:
            round_state.fail_round(f"Aggregation failed: {str(e)}")
            raise AggregationFailed(f"Round {round_number} aggregation failed: {str(e)}")
    
    def complete_round(self, round_number: int) -> Dict[str, any]:
        """
        Mark round as complete after blockchain verification
        
        Args:
            round_number: Training round number
        
        Returns:
            Round completion info
        """
        if round_number not in self.rounds:
            raise FederationException(f"Round {round_number} not found")
        
        round_state = self.rounds[round_number]
        round_state.complete_round()
        
        self.stats.completed_rounds += 1
        
        logger.info(f"Round {round_number} completed successfully")
        
        return {
            "round_id": round_number,
            "status": "completed",
            "global_model_version": self.global_model_version,
            "global_model_hash": self.global_model_hash,
        }
    
    # === Query Methods ===
    
    def get_round_status(self, round_number: int) -> Dict[str, any]:
        """Get status of specific round"""
        if round_number not in self.rounds:
            raise FederationException(f"Round {round_number} not found")
        
        return self.rounds[round_number].get_status_dict()
    
    def get_federation_status(self) -> Dict[str, any]:
        """Get overall federation status"""
        return {
            "current_round": self.current_round_number,
            "active_round": self.active_round.round_number if self.active_round else None,
            "global_model_version": self.global_model_version,
            "global_model_hash": self.global_model_hash,
            "stats": {
                "total_rounds": self.stats.total_rounds,
                "completed_rounds": self.stats.completed_rounds,
                "failed_rounds": self.stats.failed_rounds,
                "total_organizations": self.stats.total_organizations,
                "active_organizations": self.stats.active_organizations,
                "avg_convergence_norm": self.stats.avg_convergence_norm,
                "total_privacy_epsilon_used": self.stats.total_privacy_epsilon_used,
                "total_privacy_delta_used": self.stats.total_privacy_delta_used,
            }
        }
    
    # === Private Helper Methods ===
    
    def _get_aggregator(self):
        """Get or create aggregator instance"""
        if self._aggregator is None:
            self._aggregator = create_aggregator(
                method=self.config.aggregation.method,
                robust=self.config.aggregation.enable_robust_aggregation,
                fedprox_lambda=self.config.aggregation.fedprox_lambda,
                trimmed_percentage=self.config.aggregation.trimmed_percentage,
            )
        return self._aggregator
    
    def _get_model_version(self) -> str:
        """Generate next model version string"""
        parts = self.global_model_version.split('-')
        if len(parts) >= 2 and parts[0].startswith('v'):
            # Extract version number and increment
            try:
                version_num = float(parts[0][1:])
                return f"{version_num + 0.1:.1f}"
            except:
                pass
        return "1.0"


def get_federation_orchestrator(
    config: Optional[FLBlockchainConfig] = None
) -> FederationOrchestrator:
    """
    Get or create global federation orchestrator singleton
    
    Args:
        config: Optional FLBlockchainConfig (uses global if None)
    
    Returns:
        FederationOrchestrator instance
    """
    if not hasattr(get_federation_orchestrator, "_instance"):
        get_federation_orchestrator._instance = FederationOrchestrator(config)
    return get_federation_orchestrator._instance
