"""
CED Dashboard Integration Module

Provides REST API endpoints for integrating CED with the SOC dashboard.
Enables:
- Real-time threat explanations in incident view
- Intervention recommendation and simulation
- Attack chain visualization
- Historical audit and compliance
"""

from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Dashboard Data Models
# ============================================================================

class DashboardThreatSummary(BaseModel):
    """Summary of a threat for dashboard display."""
    incident_id: str = Field(..., description="Unique incident ID")
    prediction_id: str = Field(..., description="PASM prediction ID")
    threat_name: str = Field(..., description="Human-readable threat name")
    threat_type: str = Field(..., description="Type: ransomware, lateral_movement, etc.")
    severity: str = Field(..., description="CRITICAL, HIGH, MEDIUM, LOW, INFO")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Overall risk (0-1)")
    detected_at: str = Field(..., description="ISO 8601 timestamp")
    status: str = Field(..., description="new, investigating, mitigating, resolved")
    root_cause: Optional[str] = Field(default=None, description="Root cause analysis")
    affected_assets: List[str] = Field(default_factory=list, description="IPs, hosts, users")
    mitre_techniques: List[str] = Field(default_factory=list, description="MITRE ATT&CK IDs")


class DashboardCausalGraph(BaseModel):
    """Causal graph optimized for dashboard visualization."""
    nodes: List[Dict[str, Any]] = Field(..., description="Graph nodes with position, color, etc.")
    edges: List[Dict[str, Any]] = Field(..., description="Graph edges with labels")
    title: str = Field(..., description="Graph title")
    description: str = Field(..., description="Graph description")


class DashboardIntervention(BaseModel):
    """Intervention recommendation for dashboard."""
    id: str = Field(..., description="Unique intervention ID")
    name: str = Field(..., description="Intervention name")
    description: str = Field(..., description="What this intervention does")
    effectiveness: float = Field(..., ge=0.0, le=1.0, description="Effectiveness score")
    estimated_duration_minutes: int = Field(..., description="Implementation time")
    disruption_level: str = Field(..., description="None, Low, Medium, High, Critical")
    priority: str = Field(..., description="Critical, High, Medium, Low")
    requires_approval: bool = Field(default=False, description="Needs admin approval")
    one_click_deploy: bool = Field(default=False, description="Can be deployed immediately")


class DashboardExplanation(BaseModel):
    """Complete threat explanation for dashboard."""
    incident_id: str = Field(..., description="Incident ID")
    prediction_id: str = Field(..., description="PASM prediction ID")
    threat_summary: DashboardThreatSummary
    causal_graph: DashboardCausalGraph
    natural_language_explanation: str = Field(..., description="Human-readable explanation")
    attack_chain: List[str] = Field(..., description="Attack chain phases")
    root_causes: List[str] = Field(..., description="Root causes of the attack")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Explanation confidence")
    recommended_interventions: List[DashboardIntervention]
    timestamp: str = Field(..., description="When explanation was generated")


class DashboardSimulationResult(BaseModel):
    """Result of what-if intervention simulation."""
    simulation_id: str = Field(..., description="Unique simulation ID")
    incident_id: str = Field(..., description="Incident being simulated")
    scenario_name: str = Field(..., description="Name of scenario")
    interventions_applied: List[str] = Field(..., description="Intervention IDs applied")
    risk_reduction: float = Field(..., ge=0.0, le=1.0, description="Risk reduction percentage")
    time_to_resolution_hours: float = Field(..., description="Estimated hours to resolve")
    operational_impact: str = Field(..., description="None, Low, Medium, High")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Simulation confidence")
    success_probability: float = Field(..., ge=0.0, le=1.0, description="Probability of success")
    explanation: str = Field(..., description="Why this scenario works")
    timestamp: str = Field(..., description="When simulation was run")


class DashboardIncidentDetail(BaseModel):
    """Complete incident detail for dashboard."""
    incident_id: str
    prediction_id: str
    status: str
    threat_summary: DashboardThreatSummary
    explanation: Optional[DashboardExplanation] = None
    active_simulations: List[DashboardSimulationResult] = Field(default_factory=list)
    recommended_action: str = Field(default="", description="Recommended next step")
    approval_required: bool = Field(default=False)


class DashboardMetrics(BaseModel):
    """CED metrics for dashboard."""
    total_incidents_analyzed: int
    incidents_resolved: int
    avg_time_to_resolution_hours: float
    avg_risk_reduction_percentage: float
    most_common_root_causes: List[str]
    most_effective_interventions: List[str]
    system_health: str  # "healthy", "degraded", "error"


# ============================================================================
# Dashboard Request Models
# ============================================================================

class DashboardExplainRequest(BaseModel):
    """Request to explain an incident in dashboard."""
    incident_id: str = Field(..., description="The incident to explain")
    prediction_id: str = Field(..., description="PASM prediction ID")
    threat_type: str = Field(..., description="Type of threat")
    confidence: float = Field(..., ge=0.0, le=1.0)


class DashboardSimulateRequest(BaseModel):
    """Request to simulate interventions in dashboard."""
    incident_id: str
    scenario_name: str = Field(default="Intervention Scenario")
    interventions: List[Dict[str, Any]] = Field(..., description="List of interventions to test")


# ============================================================================
# API Endpoint Handler Templates
# ============================================================================

async def handle_dashboard_explain(request: DashboardExplainRequest) -> DashboardExplanation:
    """
    Generate a threat explanation optimized for SOC dashboard.
    
    This endpoint:
    1. Retrieves incident and prediction data
    2. Builds causal graph
    3. Generates dashboard-optimized visualization
    4. Creates natural language explanation
    5. Ranks interventions by effectiveness
    6. Returns complete dashboard payload
    """
    # Implementation will be in backend/api/routes/ced_dashboard.py
    pass


async def handle_dashboard_simulate(request: DashboardSimulateRequest) -> DashboardSimulationResult:
    """
    Simulate what-if interventions for dashboard.
    
    Runs counterfactual analysis and returns:
    - Risk reduction estimate
    - Time to resolution
    - Operational impact
    - Success probability
    - Confidence score
    """
    # Implementation will be in backend/api/routes/ced_dashboard.py
    pass


async def handle_dashboard_incident_detail(incident_id: str) -> DashboardIncidentDetail:
    """
    Retrieve complete incident detail for dashboard view.
    
    Returns:
    - Threat summary
    - Causal explanation
    - Active simulations
    - Recommended action
    - Approval requirements
    """
    # Implementation will be in backend/api/routes/ced_dashboard.py
    pass


async def handle_dashboard_metrics() -> DashboardMetrics:
    """
    Get CED metrics for dashboard statistics.
    
    Returns:
    - Total incidents analyzed
    - Resolution statistics
    - Root cause trends
    - Intervention effectiveness
    - System health
    """
    # Implementation will be in backend/api/routes/ced_dashboard.py
    pass


__all__ = [
    "DashboardThreatSummary",
    "DashboardCausalGraph",
    "DashboardIntervention",
    "DashboardExplanation",
    "DashboardSimulationResult",
    "DashboardIncidentDetail",
    "DashboardMetrics",
    "DashboardExplainRequest",
    "DashboardSimulateRequest",
]
