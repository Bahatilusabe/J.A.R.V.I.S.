"""
Federated Learning Core Module

Coordinates federated training across organizations with secure
aggregation, privacy preservation, and blockchain verification.
"""

from .orchestrator import FederationOrchestrator, get_federation_orchestrator
from .round_state import TrainingRoundState, RoundPhase, OrgPhase, ConvergenceMetrics
from .aggregator import FederatedAggregator, RobustAggregator, create_aggregator

__all__ = [
    "FederationOrchestrator",
    "get_federation_orchestrator",
    "TrainingRoundState",
    "RoundPhase",
    "OrgPhase",
    "ConvergenceMetrics",
    "FederatedAggregator",
    "RobustAggregator",
    "create_aggregator",
]
