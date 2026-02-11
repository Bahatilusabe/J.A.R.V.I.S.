"""
Unified TDS API Routes
======================

Consolidated REST API for Tactical Defense Shield (TDS) module.
Provides unified endpoints for device attestation, session management,
DPI rules, access decisions, and health metrics.

Endpoints:
----------
- POST   /attest              - Device attestation
- GET    /vpn/sessions        - List active VPN sessions
- POST   /vpn/sessions/{id}   - Session details with scoring
- GET    /rules               - List active DPI rules
- POST   /decision            - Get access decision for flow
- GET    /metrics             - TDS system metrics
- GET    /device/{id}/health  - Device health assessment
- POST   /alerts              - TDS security alerts

Author: J.A.R.V.I.S. Security Team
Date: December 2025
"""

from fastapi import APIRouter, HTTPException, Query, Path, Body
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import uuid

from backend.core.tds.zero_trust import attest_device, enforce_microsegmentation
from backend.core.tds.vpn_gateway import VPNGateway
from backend.core.tds.dpi_engine import DpiEngine, load_signatures
from backend.core.tds.session_scorer import get_session_scorer, SessionMetrics, BehaviorType
from backend.core.tds.device_health import get_device_health_classifier

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class AttestationRequest(BaseModel):
    """Device attestation request"""
    device_id: str = Field(..., description="Unique device identifier")
    device_info: Dict[str, Any] = Field(default_factory=dict, description="Device information")
    location: Optional[str] = Field(None, description="Device location/gateway")
    enforce_policy: bool = Field(False, description="Enforce policy on failure")


class AttestationResponse(BaseModel):
    """Device attestation response"""
    device_id: str
    attestation_id: str
    status: str  # "success", "partial", "failed"
    trust_score: float = Field(..., ge=0.0, le=1.0)
    policy_compliant: bool
    issues: List[str] = Field(default_factory=list)
    timestamp: datetime


class SessionScoreResponse(BaseModel):
    """Session scoring response"""
    session_id: str
    device_id: str
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: str  # "critical", "high", "medium", "low", "safe"
    behavior_classification: str
    packet_rate: float
    throughput_bps: float
    anomaly_score: float
    behavioral_score: float
    privilege_escalation_risk: float
    timestamp: datetime


class AccessDecisionRequest(BaseModel):
    """Access control decision request"""
    source_ip: str
    dest_ip: str
    protocol: str = Field(default="tcp", description="tcp, udp, icmp")
    port: int = Field(..., ge=1, le=65535)
    device_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class AccessDecisionResponse(BaseModel):
    """Access control decision"""
    decision_id: str
    decision: str  # "allow", "deny", "challenge"
    reason: str
    risk_score: float
    recommended_action: Optional[str] = None
    enforcement_point: str  # "vpn_gateway", "firewall", "ids"
    timestamp: datetime


class DPIRuleResponse(BaseModel):
    """DPI rule information"""
    rule_id: int
    pattern: str
    category: str
    severity: str
    description: str
    enabled: bool


class MetricsResponse(BaseModel):
    """TDS system metrics"""
    timestamp: datetime
    active_sessions: int
    active_devices: int
    risky_sessions: int
    detection_rate: float  # detections per minute
    false_positive_rate: float
    avg_session_risk: float
    dpi_throughput_mbps: float
    vpn_throughput_mbps: float
    cpu_usage: float
    memory_usage: float


class AlertResponse(BaseModel):
    """Security alert"""
    alert_id: str
    severity: str  # "critical", "high", "medium", "low"
    alert_type: str  # "attack_detected", "policy_violation", "anomaly", etc.
    source: str  # "vpn", "dpi", "ids", "behavior"
    device_id: str
    description: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    recommended_action: str
    timestamp: datetime


class DeviceHealthResponse(BaseModel):
    """Device health assessment"""
    device_id: str
    health_status: str  # "critical", "poor", "fair", "good", "excellent"
    composite_score: float = Field(..., ge=0.0, le=1.0)
    trust_level: float = Field(..., ge=0.0, le=1.0)
    vulnerabilities: Dict[str, Any]
    security_controls: Dict[str, Any]
    compliance: Dict[str, Any]
    recommendations: List[str]
    timestamp: datetime


# ============================================================================
# ENDPOINTS - DEVICE ATTESTATION
# ============================================================================

@router.post("/attest", response_model=AttestationResponse, tags=["Attestation"])
async def attest_device_endpoint(request: AttestationRequest) -> AttestationResponse:
    """
    Perform device attestation.
    
    Validates device identity, checks compliance, and assigns trust score.
    Supports optional policy enforcement.
    """
    try:
        # Perform attestation
        result = attest_device(request.device_info)
        
        # Extract attestation result
        status = result.get("status", "unknown")
        trust_score = result.get("trust_score", 0.0)
        policy_compliant = result.get("policy_compliant", False)
        issues = result.get("issues", [])
        
        return AttestationResponse(
            device_id=request.device_id,
            attestation_id=str(uuid.uuid4()),
            status=status,
            trust_score=trust_score,
            policy_compliant=policy_compliant,
            issues=issues,
            timestamp=datetime.now(),
        )
    
    except Exception as e:
        logger.error(f"Attestation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Attestation failed: {str(e)}")


# ============================================================================
# ENDPOINTS - VPN SESSION MANAGEMENT
# ============================================================================

_vpn_gateway: Optional[VPNGateway] = None


def get_vpn_gateway() -> VPNGateway:
    """Get or create VPN gateway instance"""
    global _vpn_gateway
    
    if _vpn_gateway is None:
        _vpn_gateway = VPNGateway()
    
    return _vpn_gateway


@router.get("/vpn/sessions", response_model=List[SessionScoreResponse], tags=["VPN Sessions"])
async def list_sessions(
    device_id: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
) -> List[SessionScoreResponse]:
    """
    List active VPN sessions with risk scoring.
    
    Optionally filter by device_id or minimum risk_level.
    """
    scorer = get_session_scorer()
    
    sessions = []
    for session_id, metrics in scorer.metrics.items():
        # Apply filters
        if device_id and metrics.device_id != device_id:
            continue
        
        if risk_level and metrics.risk_level.value != risk_level:
            continue
        
        sessions.append(SessionScoreResponse(
            session_id=metrics.session_id,
            device_id=metrics.device_id,
            risk_score=metrics.composite_risk_score,
            risk_level=metrics.risk_level.value,
            behavior_classification=metrics.behavior_classification.value,
            packet_rate=metrics.packet_rate,
            throughput_bps=metrics.throughput,
            anomaly_score=metrics.anomaly_score,
            behavioral_score=metrics.behavioral_score,
            privilege_escalation_risk=metrics.privilege_escalation_risk,
            timestamp=datetime.now(),
        ))
    
    return sessions


@router.get("/vpn/sessions/{session_id}", response_model=SessionScoreResponse, tags=["VPN Sessions"])
async def get_session_details(
    session_id: str = Path(..., description="Session ID"),
) -> SessionScoreResponse:
    """
    Get detailed session information and scoring.
    """
    scorer = get_session_scorer()
    metrics = scorer.get_session_score(session_id)
    
    if not metrics:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return SessionScoreResponse(
        session_id=metrics.session_id,
        device_id=metrics.device_id,
        risk_score=metrics.composite_risk_score,
        risk_level=metrics.risk_level.value,
        behavior_classification=metrics.behavior_classification.value,
        packet_rate=metrics.packet_rate,
        throughput_bps=metrics.throughput,
        anomaly_score=metrics.anomaly_score,
        behavioral_score=metrics.behavioral_score,
        privilege_escalation_risk=metrics.privilege_escalation_risk,
        timestamp=datetime.now(),
    )


# ============================================================================
# ENDPOINTS - DPI RULES
# ============================================================================

@router.get("/rules", response_model=List[DPIRuleResponse], tags=["DPI Rules"])
async def list_dpi_rules(
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
) -> List[DPIRuleResponse]:
    """
    List active DPI detection rules.
    
    Optionally filter by category or severity.
    """
    try:
        # Load signatures
        signatures = load_signatures()
        
        rules = []
        for rule_id, pattern in signatures:
            # In production, would map to full rule metadata
            rule = DPIRuleResponse(
                rule_id=rule_id,
                pattern=pattern.decode("utf-8", errors="ignore")[:50],  # Truncated
                category="malware",  # Would come from metadata
                severity="medium",  # Would come from metadata
                description=f"Pattern-based detection rule {rule_id}",
                enabled=True,
            )
            
            if category and rule.category != category:
                continue
            
            if severity and rule.severity != severity:
                continue
            
            rules.append(rule)
        
        return rules[:50]  # Return first 50 rules
    
    except Exception as e:
        logger.error(f"Failed to list DPI rules: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load rules: {str(e)}")


# ============================================================================
# ENDPOINTS - ACCESS DECISIONS
# ============================================================================

@router.post("/decision", response_model=AccessDecisionResponse, tags=["Access Control"])
async def get_access_decision(request: AccessDecisionRequest) -> AccessDecisionResponse:
    """
    Get access control decision for network flow.
    
    Evaluates device trust, behavioral risk, and policy compliance.
    Returns allow/deny/challenge decision.
    """
    try:
        # Get device health
        classifier = get_device_health_classifier()
        health = classifier.get_profile(request.device_id)
        
        if not health:
            trust_score = 0.5
            device_risk = 0.5
        else:
            trust_score = health.trust_level
            device_risk = 1.0 - trust_score
        
        # Get session risk if available
        scorer = get_session_scorer()
        session_risk = 0.0
        
        if request.session_id:
            metrics = scorer.get_session_score(request.session_id)
            if metrics:
                session_risk = metrics.composite_risk_score
        
        # Compute final risk score
        combined_risk = (device_risk * 0.6) + (session_risk * 0.4)
        
        # Make decision
        if combined_risk > 0.8:
            decision = "deny"
            reason = "High combined risk score"
            action = "Terminate connection and isolate device"
        elif combined_risk > 0.6:
            decision = "challenge"
            reason = "Medium risk - additional authentication required"
            action = "Request MFA and device scan"
        else:
            decision = "allow"
            reason = "Risk acceptable"
            action = None
        
        return AccessDecisionResponse(
            decision_id=str(uuid.uuid4()),
            decision=decision,
            reason=reason,
            risk_score=combined_risk,
            recommended_action=action,
            enforcement_point="vpn_gateway",
            timestamp=datetime.now(),
        )
    
    except Exception as e:
        logger.error(f"Access decision failed: {e}")
        raise HTTPException(status_code=500, detail=f"Decision failed: {str(e)}")


# ============================================================================
# ENDPOINTS - METRICS
# ============================================================================

@router.get("/metrics", response_model=MetricsResponse, tags=["Metrics"])
async def get_tds_metrics() -> MetricsResponse:
    """
    Get TDS system metrics and performance data.
    """
    scorer = get_session_scorer()
    
    active_sessions = len(scorer.metrics)
    risky_sessions = len(scorer.get_risky_sessions(min_risk=0.5))
    
    # Calculate average risk
    avg_risk = 0.0
    if scorer.metrics:
        avg_risk = sum(m.composite_risk_score for m in scorer.metrics.values()) / len(scorer.metrics)
    
    # Active devices
    active_devices = len(set(m.device_id for m in scorer.metrics.values()))
    
    return MetricsResponse(
        timestamp=datetime.now(),
        active_sessions=active_sessions,
        active_devices=active_devices,
        risky_sessions=risky_sessions,
        detection_rate=0.0,  # Would integrate with DPI engine
        false_positive_rate=0.0,  # Would track over time
        avg_session_risk=avg_risk,
        dpi_throughput_mbps=0.0,  # Would measure DPI
        vpn_throughput_mbps=0.0,  # Would measure VPN
        cpu_usage=0.0,  # Would measure system
        memory_usage=0.0,  # Would measure system
    )


# ============================================================================
# ENDPOINTS - HEALTH ASSESSMENT
# ============================================================================

@router.get("/device/{device_id}/health", response_model=DeviceHealthResponse, tags=["Health"])
async def get_device_health(
    device_id: str = Path(..., description="Device ID"),
) -> DeviceHealthResponse:
    """
    Get comprehensive device health assessment.
    """
    classifier = get_device_health_classifier()
    profile = classifier.get_profile(device_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    # Calculate health if not done recently
    score, status = classifier.calculate_health(device_id)
    
    # Get recommendations
    recommendations = classifier.get_remediation_recommendations(device_id)
    
    return DeviceHealthResponse(
        device_id=device_id,
        health_status=status.value,
        composite_score=profile.composite_health_score,
        trust_level=profile.trust_level,
        vulnerabilities=profile.to_dict()["vulnerabilities"],
        security_controls={name: ctrl.to_dict() for name, ctrl in profile.security_controls.items()},
        compliance=profile.to_dict()["compliance"],
        recommendations=recommendations,
        timestamp=profile.last_assessment,
    )


# ============================================================================
# ENDPOINTS - ALERTS
# ============================================================================

_alerts: Dict[str, AlertResponse] = {}


@router.post("/alerts", response_model=AlertResponse, tags=["Alerts"])
async def create_alert(
    severity: str = Body(...),
    alert_type: str = Body(...),
    device_id: str = Body(...),
    description: str = Body(...),
    source: str = Body(default="tds"),
) -> AlertResponse:
    """
    Create security alert (internal endpoint).
    """
    alert = AlertResponse(
        alert_id=str(uuid.uuid4()),
        severity=severity,
        alert_type=alert_type,
        source=source,
        device_id=device_id,
        description=description,
        recommended_action="Review and investigate",
        timestamp=datetime.now(),
    )
    
    _alerts[alert.alert_id] = alert
    logger.warning(f"TDS Alert [{severity}]: {description}")
    
    return alert


@router.get("/alerts", response_model=List[AlertResponse], tags=["Alerts"])
async def list_alerts(
    severity: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=720),
) -> List[AlertResponse]:
    """
    List recent security alerts.
    """
    import time
    from datetime import timedelta
    
    cutoff = datetime.now() - timedelta(hours=hours)
    
    alerts = [
        a for a in _alerts.values()
        if a.timestamp >= cutoff and
        (not severity or a.severity == severity)
    ]
    
    return sorted(alerts, key=lambda x: x.timestamp, reverse=True)


# Register with app
__all__ = ["router"]
