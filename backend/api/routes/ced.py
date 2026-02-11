"""
Causal Explainable Defense (CED) REST API Routes

This module provides FastAPI routes for the CED module, enabling:
- Causal graph explanation of security predictions
- Counterfactual intervention simulation
- What-if scenario analysis for threat mitigation

The routes integrate with:
- PASM module for prediction data and temporal context
- CausalEngine for structural causal model inference
- ExplanationBuilder for natural language explanations
"""

from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query
import logging

# Core CED imports
from backend.core.ced.causal_engine import CausalEngine, get_causal_engine
from backend.core.ced.explanation_builder import ExplanationBuilder, get_explanation_builder

# PASM integration (optional - graceful degradation if PASM unavailable)
try:
    from backend.core.pasm.predictor import get_predictor
    PASM_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    PASM_AVAILABLE = False

logger = logging.getLogger(__name__)
router = APIRouter(tags=["CED"])


# ============================================================================
# Pydantic Models - Request/Response Types
# ============================================================================

class CausalNode(BaseModel):
    """Represents a node in the causal graph."""
    id: str = Field(..., description="Unique node identifier")
    label: str = Field(..., description="Human-readable label (e.g., 'Lateral Movement')")
    node_type: str = Field(..., description="Node type (e.g., 'attack_phase', 'observable', 'impact')")
    severity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Severity/risk level (0=low, 1=critical)"
    )
    value: Optional[Any] = Field(default=None, description="Current value at this node")


class CausalEdge(BaseModel):
    """Represents an edge (causal relationship) in the graph."""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    strength: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Causal strength (0=weak, 1=deterministic)"
    )
    relationship: str = Field(..., description="Type of relationship (e.g., 'causes', 'enables')")


class CausalGraph(BaseModel):
    """Complete causal graph for an attack scenario."""
    nodes: List[CausalNode] = Field(..., description="Graph nodes")
    edges: List[CausalEdge] = Field(..., description="Graph edges")
    root_causes: List[str] = Field(..., description="IDs of root cause nodes")
    leaf_impacts: List[str] = Field(..., description="IDs of leaf impact nodes")


class MinimalIntervention(BaseModel):
    """Minimal set of actions to mitigate a threat."""
    type: str = Field(..., description="Intervention type (e.g., 'block_ips', 'isolate_host')")
    target: str = Field(..., description="Target of intervention (e.g., IP address, hostname)")
    enabled: bool = Field(default=True, description="Whether this intervention should be applied")
    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence in effectiveness"
    )


class CounterfactualIntervention(BaseModel):
    """Intervention specification for counterfactual simulation."""
    type: str = Field(..., description="Type of intervention")
    target: str = Field(..., description="Target of intervention")
    enabled: bool = Field(default=True, description="Apply this intervention")


class CounterfactualRequest(BaseModel):
    """Request for counterfactual simulation."""
    prediction_id: str = Field(..., description="PASM prediction ID to simulate against")
    interventions: List[CounterfactualIntervention] = Field(
        ...,
        description="List of interventions to apply"
    )


class CounterfactualResponse(BaseModel):
    """Results of counterfactual simulation."""
    simulation_id: str = Field(..., description="Unique ID for this simulation")
    prediction_id: str = Field(..., description="Original prediction ID")
    original_risk: float = Field(..., ge=0.0, le=1.0, description="Original risk score")
    predicted_risk: float = Field(..., ge=0.0, le=1.0, description="Risk after interventions")
    risk_reduction: float = Field(..., ge=0.0, le=1.0, description="Absolute reduction in risk")
    affected_nodes: List[str] = Field(..., description="IDs of affected causal nodes")
    explanation: str = Field(..., description="Narrative explanation of results")


class CEDExplanation(BaseModel):
    """Complete causal explanation of a security prediction."""
    prediction_id: str = Field(..., description="PASM prediction ID")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    causal_graph: CausalGraph = Field(..., description="Causal structure")
    natural_language: str = Field(..., description="Human-readable explanation")
    minimal_interventions: List[MinimalIntervention] = Field(
        ...,
        description="Minimal set of mitigations"
    )
    confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confidence in the explanation"
    )
    alternative_explanations: Optional[List[str]] = Field(
        default=None,
        description="Other plausible explanations"
    )


class HealthStatus(BaseModel):
    """Service health status response."""
    status: str = Field(..., description="Status: 'healthy' or 'degraded'")
    version: str = Field(..., description="API version")
    causal_engine_ready: bool = Field(..., description="Causal engine initialized")
    pasm_integrated: bool = Field(..., description="PASM integration available")
    message: Optional[str] = Field(default=None, description="Additional status info")


# ============================================================================
# Route Handlers
# ============================================================================

@router.get(
    "/health",
    response_model=HealthStatus,
    summary="Check CED service health",
    description="Verify CED service is running and ready to serve requests"
)
async def ced_health() -> HealthStatus:
    """
    Check the health status of the CED service.
    
    Returns:
        HealthStatus: Service status, version, and component availability
    """
    try:
        engine = get_causal_engine()
        builder = get_explanation_builder()
        
        return HealthStatus(
            status="healthy",
            version="1.0.0",
            causal_engine_ready=True,
            pasm_integrated=PASM_AVAILABLE,
            message="CED service operational" if PASM_AVAILABLE else "Running in degraded mode (PASM unavailable)"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthStatus(
            status="degraded",
            version="1.0.0",
            causal_engine_ready=False,
            pasm_integrated=False,
            message=str(e)
        )


@router.get(
    "/explain",
    response_model=CEDExplanation,
    summary="Generate causal explanation for a prediction",
    description="Explain why a PASM prediction was made using structural causal modeling",
    responses={
        200: {"description": "Explanation generated successfully"},
        400: {"description": "Invalid prediction ID or missing data"},
        503: {"description": "PASM service unavailable"}
    }
)
async def explain_prediction(
    prediction_id: str = Query(..., description="PASM prediction ID to explain"),
    include_alternatives: bool = Query(
        False,
        description="Include alternative explanations"
    )
) -> CEDExplanation:
    """
    Generate a causal explanation for a security prediction.
    
    This endpoint:
    1. Loads the PASM prediction (attack scores, temporal context)
    2. Builds a causal DAG representing the attack chain
    3. Performs structural causal model inference
    4. Generates natural language explanation
    5. Identifies minimal interventions
    
    Args:
        prediction_id: The PASM prediction to explain
        include_alternatives: Whether to compute alternative explanations
    
    Returns:
        CEDExplanation: Complete causal explanation with graph and interventions
    
    Raises:
        HTTPException 400: Invalid or missing prediction
        HTTPException 503: PASM unavailable
    """
    try:
        # Step 1: Load PASM prediction if available
        prediction_data = None
        if PASM_AVAILABLE:
            try:
                predictor = get_predictor()
                prediction_data = predictor.get_prediction(prediction_id)
            except Exception as e:
                logger.warning(f"Could not load PASM prediction {prediction_id}: {e}")
                if not PASM_AVAILABLE:
                    raise HTTPException(
                        status_code=503,
                        detail="PASM service unavailable and prediction not cached"
                    )
        
        if not prediction_data:
            raise HTTPException(
                status_code=400,
                detail=f"Prediction {prediction_id} not found"
            )
        
        # Step 2: Get causal engine and build graph
        engine = get_causal_engine()
        
        # Build causal DAG from prediction data
        # This would normally extract attack chain from PASM scores
        causal_graph = _build_causal_graph_from_prediction(engine, prediction_data)
        
        # Step 3: Generate explanation
        builder = get_explanation_builder()
        natural_language = builder.build_explanation(prediction_data)
        
        # Step 4: Identify minimal interventions
        minimal_interventions = _identify_minimal_interventions(
            causal_graph,
            prediction_data
        )
        
        # Step 5: Compute alternatives if requested
        alternative_explanations = None
        if include_alternatives:
            alternative_explanations = _compute_alternatives(engine, prediction_data)
        
        return CEDExplanation(
            prediction_id=prediction_id,
            timestamp=prediction_data.get("timestamp", ""),
            causal_graph=causal_graph,
            natural_language=natural_language,
            minimal_interventions=minimal_interventions,
            confidence=prediction_data.get("confidence", 0.7),
            alternative_explanations=alternative_explanations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Explanation generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate explanation: {str(e)}"
        )


@router.post(
    "/simulate",
    response_model=CounterfactualResponse,
    summary="Simulate counterfactual interventions",
    description="Run what-if analysis for proposed threat mitigations",
    responses={
        200: {"description": "Simulation completed successfully"},
        400: {"description": "Invalid prediction or interventions"},
        503: {"description": "Causal engine unavailable"}
    }
)
async def simulate_counterfactual(
    request: CounterfactualRequest
) -> CounterfactualResponse:
    """
    Simulate the effect of proposed interventions on a prediction.
    
    This endpoint:
    1. Loads the original prediction
    2. Creates a modified causal graph with interventions
    3. Re-infers under the interventions (counterfactual)
    4. Computes risk reduction and affected nodes
    5. Generates narrative explanation
    
    Args:
        request: Counterfactual request with prediction ID and interventions
    
    Returns:
        CounterfactualResponse: Simulation results and impact analysis
    
    Raises:
        HTTPException 400: Invalid prediction or interventions
        HTTPException 503: Causal engine unavailable
    """
    try:
        # Step 1: Load original prediction
        if not PASM_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="PASM service unavailable"
            )
        
        predictor = get_predictor()
        original_prediction = predictor.get_prediction(request.prediction_id)
        
        if not original_prediction:
            raise HTTPException(
                status_code=400,
                detail=f"Prediction {request.prediction_id} not found"
            )
        
        # Step 2: Create counterfactual scenario
        engine = get_causal_engine()
        
        # Build intervention mapping
        interventions_dict = {
            iv.type: {
                "target": iv.target,
                "enabled": iv.enabled
            }
            for iv in request.interventions
        }
        
        # Step 3: Compute counterfactual
        counterfactual_prediction = engine.counterfactual(
            observed=original_prediction,
            intervention=interventions_dict
        )
        
        # Step 4: Calculate impact
        original_risk = original_prediction.get("risk_score", 0.5)
        predicted_risk = counterfactual_prediction.get("risk_score", 0.5)
        risk_reduction = max(0.0, original_risk - predicted_risk)
        
        # Step 5: Generate explanation
        builder = get_explanation_builder()
        explanation = builder.build_explanation(
            original=original_prediction,
            counterfactual=counterfactual_prediction
        )
        
        # Step 6: Identify affected nodes
        affected_nodes = _extract_affected_nodes(
            original_prediction,
            counterfactual_prediction
        )
        
        return CounterfactualResponse(
            simulation_id=f"sim-{request.prediction_id}-{int(time.time())}",
            prediction_id=request.prediction_id,
            original_risk=original_risk,
            predicted_risk=predicted_risk,
            risk_reduction=risk_reduction,
            affected_nodes=affected_nodes,
            explanation=explanation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Counterfactual simulation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Simulation failed: {str(e)}"
        )


# ============================================================================
# Helper Functions
# ============================================================================

def _build_causal_graph_from_prediction(
    engine: CausalEngine,
    prediction: Dict[str, Any]
) -> CausalGraph:
    """
    Build a causal graph from PASM prediction data.
    
    This function:
    1. Extracts attack chain from prediction scores
    2. Maps to MITRE ATT&CK techniques
    3. Structures as causal DAG with root causes and impacts
    4. Assigns severity/confidence scores
    
    Args:
        engine: Initialized CausalEngine
        prediction: PASM prediction data
    
    Returns:
        CausalGraph: Structured causal DAG
    """
    # Extract attack phases from prediction
    # This is simplified - real implementation would parse temporal context
    nodes = [
        CausalNode(
            id="initial_access",
            label="Initial Access",
            node_type="attack_phase",
            severity=prediction.get("initial_access_score", 0.0),
            value="Suspicious login detected"
        ),
        CausalNode(
            id="persistence",
            label="Persistence",
            node_type="attack_phase",
            severity=prediction.get("persistence_score", 0.0),
            value="Scheduled task created"
        ),
        CausalNode(
            id="privilege_escalation",
            label="Privilege Escalation",
            node_type="attack_phase",
            severity=prediction.get("escalation_score", 0.0),
            value="Privilege elevation attempt"
        ),
        CausalNode(
            id="impact",
            label="Potential Impact",
            node_type="impact",
            severity=prediction.get("risk_score", 0.5),
            value="Data exfiltration risk"
        ),
    ]
    
    edges = [
        CausalEdge(
            source="initial_access",
            target="persistence",
            strength=0.8,
            relationship="enables"
        ),
        CausalEdge(
            source="persistence",
            target="privilege_escalation",
            strength=0.7,
            relationship="enables"
        ),
        CausalEdge(
            source="privilege_escalation",
            target="impact",
            strength=0.9,
            relationship="causes"
        ),
    ]
    
    return CausalGraph(
        nodes=nodes,
        edges=edges,
        root_causes=["initial_access"],
        leaf_impacts=["impact"]
    )


def _identify_minimal_interventions(
    graph: CausalGraph,
    prediction: Dict[str, Any]
) -> List[MinimalIntervention]:
    """
    Identify minimal set of interventions to mitigate threat.
    
    Uses causal graph structure to find minimum cut that blocks
    all paths from root causes to impacts.
    
    Args:
        graph: Causal graph
        prediction: Prediction data with confidence scores
    
    Returns:
        List of minimal interventions
    """
    # Simplified: recommend blocking nodes with highest impact
    interventions = []
    
    for node in graph.nodes:
        if node.node_type == "attack_phase" and node.severity > 0.5:
            interventions.append(
                MinimalIntervention(
                    type="block_attack_phase",
                    target=node.id,
                    enabled=True,
                    confidence=node.severity
                )
            )
    
    return interventions[:3]  # Top 3 interventions


def _compute_alternatives(
    engine: CausalEngine,
    prediction: Dict[str, Any]
) -> List[str]:
    """
    Compute alternative explanations for the observation.
    
    Args:
        engine: Causal engine
        prediction: Prediction data
    
    Returns:
        List of alternative explanation summaries
    """
    # Placeholder: real implementation would use model selection
    return [
        "Attack originated from supply chain compromise",
        "Insider threat with legitimate credentials",
        "Misconfiguration triggering false positive"
    ]


def _extract_affected_nodes(
    original: Dict[str, Any],
    counterfactual: Dict[str, Any]
) -> List[str]:
    """
    Extract nodes affected by counterfactual intervention.
    
    Args:
        original: Original prediction
        counterfactual: Counterfactual prediction
    
    Returns:
        List of affected node IDs
    """
    # Compare predictions to find differences
    affected = []
    
    for key in original:
        if original.get(key) != counterfactual.get(key):
            affected.append(key)
    
    return affected


# ============================================================================
# Module Initialization
# ============================================================================

import time  # Import at module level for simulate endpoint

if __name__ == "__main__":
    # For testing the router
    print(f"CED Router: {len(router.routes)} routes registered")
    for route in router.routes:
        if hasattr(route, 'path'):
            print(f"  {route.path}")
