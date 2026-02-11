"""
IDS/IPS API Routes
REST endpoints for threat detection, alert management, and explainability.

Endpoints:
- POST /ids/detect - Analyze flow for threats
- GET /ids/alerts - List alerts with filtering
- GET /ids/alerts/{alert_id} - Get alert details
- POST /ids/alerts/{alert_id}/investigate - Mark alert as investigating
- GET /ids/alerts/{alert_id}/explanation - Get SHAP/LIME explanation
- GET /ids/models/status - Get model status
- GET /ids/metrics - Get operational metrics
- POST /ids/models/retrain - Trigger retraining
- GET /ids/drift - Get drift metrics

Author: J.A.R.V.I.S. IDS API Team
Date: December 2025
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid
import sys
from pathlib import Path

# Add backend to path for imports
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

try:
    from backend.ids_engine import (
        AIIntrusionDetectionEngine, NetworkFlow, ThreatAlert, 
        ThreatLevel, AlertStatus, DetectionMethod, ResponseAction,
        create_network_flow
    )
except (ImportError, ModuleNotFoundError):
    try:
        # Fallback: import directly if running as backend module
        import ids_engine
        AIIntrusionDetectionEngine = ids_engine.AIIntrusionDetectionEngine
        NetworkFlow = ids_engine.NetworkFlow
        ThreatAlert = ids_engine.ThreatAlert
        ThreatLevel = ids_engine.ThreatLevel
        AlertStatus = ids_engine.AlertStatus
        DetectionMethod = ids_engine.DetectionMethod
        ResponseAction = ids_engine.ResponseAction
        create_network_flow = ids_engine.create_network_flow
    except (ImportError, ModuleNotFoundError, AttributeError) as e:
        print(f"Warning: Could not import IDS engines: {e}")
        # Create dummy classes so the module can still load
        class AIIntrusionDetectionEngine: pass
        class NetworkFlow: pass
        class ThreatAlert: pass
        class ThreatLevel: pass
        class AlertStatus: pass
        class DetectionMethod: pass
        class ResponseAction: pass
        def create_network_flow(*args, **kwargs): return {}

# Try to import optional modules
try:
    from backend.explainability_engine import ExplainabilityEngine, ExplanationNarrativeGenerator
except (ImportError, ModuleNotFoundError):
    class ExplainabilityEngine: pass
    class ExplanationNarrativeGenerator: pass

try:
    from backend.mlops_infrastructure import (
        MLOpsOrchestrator, DriftDetector, ModelRegistryManager,
        RetrainingTrigger
    )
except (ImportError, ModuleNotFoundError):
    class MLOpsOrchestrator: pass
    class DriftDetector: pass
    class ModelRegistryManager: pass
    class RetrainingTrigger: pass


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class FlowAnalysisRequest(BaseModel):
    """Request model for flow analysis"""
    src_ip: str
    dst_ip: str
    src_port: int = Field(ge=0, le=65535)
    dst_port: int = Field(ge=0, le=65535)
    protocol: str
    duration_sec: float
    packet_count: int
    byte_count: int
    dpi_app: Optional[str] = None
    dpi_category: Optional[str] = None
    src_host_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    dst_host_risk: float = Field(default=0.0, ge=0.0, le=1.0)


class FlowAnalysisResponse(BaseModel):
    """Response model for flow analysis"""
    threat_detected: bool
    threat_score: float
    threat_level: Optional[str] = None
    alert_id: Optional[str] = None
    detection_methods: List[str]
    latency_ms: float
    models_evaluated: int
    explanation_available: bool


class ThreatAlertResponse(BaseModel):
    """Response model for threat alert"""
    alert_id: str
    timestamp: datetime
    threat_level: str
    threat_score: float
    confidence: float
    threat_name: str
    threat_category: str
    threat_description: str
    flow_info: Dict[str, Any]
    host_risk_context: Dict[str, Any]
    network_context: Dict[str, Any]
    recommended_actions: List[str]
    status: str
    assigned_analyst: Optional[str] = None


class AlertUpdateRequest(BaseModel):
    """Request to update alert status"""
    status: str  # "open", "investigating", "escalated", "resolved", "false_positive"
    analyst: Optional[str] = None
    notes: str = ""


class ExplanationResponse(BaseModel):
    """Response model for explanation"""
    alert_id: str
    explanation_method: str
    primary_reasons: List[str]
    secondary_reasons: List[str]
    confidence: float
    narrative: str
    feature_contributions: Optional[Dict[str, float]] = None
    attention_weights: Optional[Dict[str, float]] = None


class ModelStatusResponse(BaseModel):
    """Response model for model status"""
    model_id: str
    model_name: str
    model_type: str
    status: str
    version: str
    accuracy: float
    auc_roc: float
    drift_score: float
    retraining_required: bool


class MetricsResponse(BaseModel):
    """Response model for metrics"""
    engine_id: str
    uptime_seconds: float
    total_flows_analyzed: int
    total_threats_detected: int
    detection_rate: float
    threat_distribution: Dict[str, int]
    active_models: int
    open_alerts: int
    model_status: Dict[str, Any]


class DriftResponse(BaseModel):
    """Response model for drift detection"""
    detection_id: str
    timestamp: datetime
    model_id: str
    drift_types: List[str]
    overall_drift_score: float
    retraining_recommended: bool
    retraining_urgency: str


# ============================================================================
# GLOBAL ENGINE & DEPENDENCIES
# ============================================================================

# Initialize engines (would be done in main.py in production)
_ids_engine = AIIntrusionDetectionEngine()
_explainability_engine = ExplainabilityEngine()
_mlops_orchestrator = MLOpsOrchestrator()


# ============================================================================
# API ROUTES
# ============================================================================

router = APIRouter(prefix="/ids", tags=["ids"])


# ============================================================================
# THREAT DETECTION
# ============================================================================

@router.post("/detect", response_model=FlowAnalysisResponse)
async def detect_threats(request: FlowAnalysisRequest):
    """
    Analyze network flow for threats using ensemble of ML models.
    
    **Features:**
    - Multi-model ensemble (LSTM, GNN, Transformer, Autoencoder)
    - Real-time threat scoring
    - Confidence intervals
    - Detection method attribution
    
    **Example:**
    ```json
    {
        "src_ip": "192.168.1.100",
        "dst_ip": "10.0.0.50",
        "src_port": 54321,
        "dst_port": 443,
        "protocol": "tcp",
        "duration_sec": 120.5,
        "packet_count": 5000,
        "byte_count": 2500000,
        "dpi_app": "malware_beacon",
        "dpi_category": "malicious"
    }
    ```
    """
    try:
        # Create network flow
        flow = create_network_flow(
            src_ip=request.src_ip,
            dst_ip=request.dst_ip,
            src_port=request.src_port,
            dst_port=request.dst_port,
            protocol=request.protocol,
            duration_sec=request.duration_sec,
            packet_count=request.packet_count,
            byte_count=request.byte_count,
            dpi_app=request.dpi_app,
            dpi_category=request.dpi_category
        )
        
        flow.src_host_risk = request.src_host_risk
        flow.dst_host_risk = request.dst_host_risk
        
        # Detect threats
        threat_detected, alert, info = _ids_engine.detect_threats(flow)
        
        return FlowAnalysisResponse(
            threat_detected=threat_detected,
            threat_score=info["ensemble_score"],
            threat_level=alert.threat_level.value if alert else None,
            alert_id=info["alert_id"],
            detection_methods=[m.value for m in info["detection_results"]],
            latency_ms=info["latency_ms"],
            models_evaluated=info["models_evaluated"],
            explanation_available=bool(alert and alert.alert_id in _explainability_engine.explanation_cache)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


# ============================================================================
# ALERT MANAGEMENT
# ============================================================================

@router.get("/alerts", response_model=List[ThreatAlertResponse])
async def list_alerts(
    status: Optional[str] = Query(None, description="Filter by status"),
    threat_level: Optional[str] = Query(None, description="Filter by threat level"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    List security alerts with filtering and pagination.
    
    **Query Parameters:**
    - `status`: open, investigating, escalated, resolved, false_positive
    - `threat_level`: critical, high, medium, low, info
    - `limit`: Number of alerts per page (default: 100)
    - `offset`: Pagination offset (default: 0)
    """
    try:
        status_enum = AlertStatus[status.upper()] if status else None
        threat_enum = ThreatLevel[threat_level.upper()] if threat_level else None
        
        alerts = _ids_engine.get_alerts(status_enum, threat_enum, limit, offset)
        
        return [
            ThreatAlertResponse(
                alert_id=a.alert_id,
                timestamp=a.timestamp,
                threat_level=a.threat_level.value,
                threat_score=a.threat_score,
                confidence=a.confidence,
                threat_name=a.threat_name,
                threat_category=a.threat_category,
                threat_description=a.threat_description,
                flow_info={
                    "src_ip": a.flow.src_ip,
                    "dst_ip": a.flow.dst_ip,
                    "src_port": a.flow.src_port,
                    "dst_port": a.flow.dst_port,
                    "protocol": a.flow.protocol,
                    "dpi_app": a.flow.dpi_app
                },
                host_risk_context=a.host_risk_context,
                network_context=a.network_context,
                recommended_actions=[action.value for action in a.recommended_actions],
                status=a.status.value,
                assigned_analyst=a.assigned_analyst
            )
            for a in alerts
        ]
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to list alerts: {str(e)}")


@router.get("/alerts/{alert_id}", response_model=ThreatAlertResponse)
async def get_alert(alert_id: str):
    """Get detailed information about a specific alert"""
    try:
        alert = _ids_engine.alerts.get(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return ThreatAlertResponse(
            alert_id=alert.alert_id,
            timestamp=alert.timestamp,
            threat_level=alert.threat_level.value,
            threat_score=alert.threat_score,
            confidence=alert.confidence,
            threat_name=alert.threat_name,
            threat_category=alert.threat_category,
            threat_description=alert.threat_description,
            flow_info={
                "src_ip": alert.flow.src_ip,
                "dst_ip": alert.flow.dst_ip,
                "src_port": alert.flow.src_port,
                "dst_port": alert.flow.dst_port,
                "protocol": alert.flow.protocol,
                "duration_sec": alert.flow.duration_sec,
                "packet_count": alert.flow.packet_count,
                "byte_count": alert.flow.byte_count,
                "dpi_app": alert.flow.dpi_app,
                "dpi_category": alert.flow.dpi_category
            },
            host_risk_context=alert.host_risk_context,
            network_context=alert.network_context,
            recommended_actions=[action.value for action in alert.recommended_actions],
            status=alert.status.value,
            assigned_analyst=alert.assigned_analyst
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alert: {str(e)}")


@router.post("/alerts/{alert_id}/investigate")
async def investigate_alert(alert_id: str, request: AlertUpdateRequest):
    """Update alert investigation status"""
    try:
        status_enum = AlertStatus[request.status.upper()]
        success = _ids_engine.update_alert_status(
            alert_id,
            status_enum,
            request.analyst,
            request.notes
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {
            "success": True,
            "alert_id": alert_id,
            "status": request.status,
            "updated_at": datetime.now()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update alert: {str(e)}")


# ============================================================================
# EXPLAINABILITY
# ============================================================================

@router.get("/alerts/{alert_id}/explanation", response_model=ExplanationResponse)
async def get_alert_explanation(alert_id: str):
    """
    Get SHAP/LIME explanation for alert.
    
    Shows:
    - Primary reasons alert was triggered
    - Secondary evidence
    - Feature contributions
    - Confidence level
    - Human-readable narrative
    """
    try:
        alert = _ids_engine.alerts.get(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Get or generate explanation
        explanation = _explainability_engine.get_explanation(alert_id)
        
        if not explanation:
            # Generate if not cached
            features = {
                "packet_count": alert.flow.packet_count,
                "byte_count": alert.flow.byte_count,
                "duration": alert.flow.duration_sec,
                "src_port": alert.flow.src_port / 65536.0,
                "dst_port": alert.flow.dst_port / 65536.0
            }
            
            feature_importance = {
                "packet_count": 0.25,
                "byte_count": 0.30,
                "duration": 0.15,
                "src_port": 0.15,
                "dst_port": 0.15
            }
            
            explanation = _explainability_engine.generate_full_explanation(
                alert_id=alert_id,
                prediction=alert.threat_score,
                features=features,
                feature_importance=feature_importance,
                prediction_fn=lambda x: alert.threat_score
            )
        
        # Generate narrative
        narrative = ExplanationNarrativeGenerator.generate_narrative(
            explanation,
            alert.threat_name
        )
        
        return ExplanationResponse(
            alert_id=alert_id,
            explanation_method="ensemble",
            primary_reasons=explanation.primary_reasons,
            secondary_reasons=explanation.secondary_reasons,
            confidence=explanation.confidence_in_explanation,
            narrative=narrative,
            feature_contributions=explanation.shap_values
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")


# ============================================================================
# MODEL MANAGEMENT
# ============================================================================

@router.get("/models/status", response_model=List[ModelStatusResponse])
async def get_model_status():
    """Get status of all active IDS models"""
    try:
        model_status = _ids_engine.get_model_status()
        
        return [
            ModelStatusResponse(
                model_id=mid,
                model_name=mdata["name"],
                model_type=mdata["type"],
                status=mdata["status"],
                version=mdata["version"],
                accuracy=mdata["accuracy"],
                auc_roc=mdata["auc_roc"],
                drift_score=mdata["drift_score"],
                retraining_required=mdata["retraining_required"]
            )
            for mid, mdata in model_status.items()
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model status: {str(e)}")


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get operational metrics and system health"""
    try:
        metrics = _ids_engine.get_metrics_summary()
        
        return MetricsResponse(
            engine_id=metrics["engine_id"],
            uptime_seconds=metrics["uptime_seconds"],
            total_flows_analyzed=metrics["total_flows_analyzed"],
            total_threats_detected=metrics["total_threats_detected"],
            detection_rate=metrics["detection_rate"],
            threat_distribution=metrics["threat_distribution"],
            active_models=metrics["active_models"],
            open_alerts=metrics["open_alerts"],
            model_status=metrics["model_status"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


# ============================================================================
# ML OPS
# ============================================================================

@router.post("/models/retrain")
async def trigger_retraining(model_type: str):
    """Trigger manual retraining for a model"""
    try:
        job = _mlops_orchestrator.retraining_pipeline.schedule_retraining(
            model_id=model_type,
            trigger=RetrainingTrigger.MANUAL
        )
        
        return {
            "job_id": job.job_id,
            "model_id": job.model_id,
            "status": job.status,
            "created_at": job.created_at
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule retraining: {str(e)}")


@router.get("/drift")
async def get_drift_metrics(model_id: Optional[str] = None):
    """Get drift detection metrics"""
    try:
        detector = _mlops_orchestrator.drift_detector
        
        if model_id:
            history = detector.drift_history.get(model_id, [])
        else:
            history = []
            for drifts in detector.drift_history.values():
                history.extend(drifts)
        
        # Return latest 10
        recent = sorted(history, key=lambda x: x.timestamp, reverse=True)[:10]
        
        return [
            DriftResponse(
                detection_id=d.detection_id,
                timestamp=d.timestamp,
                model_id=d.model_id,
                drift_types=[dt.value for dt in d.drift_types],
                overall_drift_score=d.overall_drift_score,
                retraining_recommended=d.retraining_recommended,
                retraining_urgency=d.retraining_urgency
            )
            for d in recent
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get drift metrics: {str(e)}")


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def health_check():
    """IDS engine health check"""
    return {
        "status": "healthy",
        "engine_id": _ids_engine.engine_id,
        "active_models": len(_ids_engine.active_model_ids),
        "alerts_queued": len(_ids_engine.alert_queue),
        "timestamp": datetime.now()
    }
