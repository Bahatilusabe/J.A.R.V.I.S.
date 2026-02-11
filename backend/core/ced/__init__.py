"""
Causal Explainable Defense (CED) Module

This module provides explainable AI for security threats through structural
causal modeling (SCM). It answers:

1. **WHY** did this threat occur? (Root cause analysis)
2. **HOW** could we prevent it? (Minimal interventions)
3. **WHAT IF** we take action X? (Counterfactual simulation)

Key components:
- causal_engine: Structural causal models for attack chains
- explanation_builder: Natural language explanations with security context
- attack_models: Pre-built MITRE ATT&CK attack chain DAGs
- pasm_integration: Data flow from PASM predictions to CED explanations

Architecture:
    PASM Prediction
         ↓
    Extract threat scores
         ↓
    Build causal DAG
         ↓
    Infer root causes
         ↓
    Generate explanation
         ↓
    Rank interventions
         ↓
    CED Explanation Response

Example usage:
    from backend.core.ced import get_ced_engine
    
    engine = get_ced_engine()
    explanation = engine.explain_threat(
        prediction_id="pred-001",
        threat_data={"privilege_escalation": 0.92, ...}
    )
    print(explanation.root_causes)
    print(explanation.minimal_interventions)
"""

from __future__ import annotations

from .causal_engine import CausalEngine, get_causal_engine
from .explanation_builder import ExplanationBuilder, get_explanation_builder
from .attack_models import (
    get_attack_chain_dag,
    MITRE_ATTACK_CHAINS,
    AttackChain,
    AttackNode,
    AttackEdge,
    get_all_chain_types,
    find_attack_path,
)
from .dashboard_models import (
    DashboardExplanation,
    DashboardSimulationResult,
    DashboardIncidentDetail,
    DashboardMetrics,
)

__version__ = "1.0.0"
__all__ = [
    "CausalEngine",
    "get_causal_engine",
    "ExplanationBuilder",
    "get_explanation_builder",
    "get_attack_chain_dag",
    "get_all_chain_types",
    "find_attack_path",
    "MITRE_ATTACK_CHAINS",
    "AttackChain",
    "AttackNode",
    "AttackEdge",
    "DashboardExplanation",
    "DashboardSimulationResult",
    "DashboardIncidentDetail",
    "DashboardMetrics",
]
