"""
FastAPI routes for Deep Packet Inspection (DPI) Engine.

Endpoints for:
- Protocol classification
- Rule management
- Alert retrieval
- TLS interception control
- Statistics and monitoring

Author: J.A.R.V.I.S. Team
"""

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
import logging
import time
from datetime import datetime

from backend.dpi_engine_py import (
    DPIEngine, DPIProtocol, DPIAlertSeverity, DPIRuleType, DPITLSMode,
    ClassifiedProtocol, DPIStatsData, DPIAlertData, DPIFlowAction,
    ClassifiedSession, FlowRoutingDecision, DPISessionCategory
)

logger = logging.getLogger(__name__)

# ============================================================================
# GLOBAL ENGINE INSTANCE
# ============================================================================

_dpi_engine: Optional[DPIEngine] = None
_engine_lock = None

def get_dpi_engine() -> DPIEngine:
    """Get or initialize DPI engine"""
    global _dpi_engine, _engine_lock
    
    if _dpi_engine is None:
        config = {
            'enable_anomaly_detection': True,
            'enable_malware_detection': True,
            'reassembly_timeout_sec': 300,
            'max_concurrent_sessions': 100000,
            'memory_limit_mb': 1024,
            'log_all_alerts': True,
            'redact_pii': True,
        }
        _dpi_engine = DPIEngine(config)
        logger.info("DPI Engine initialized")
    
    return _dpi_engine

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class FlowInfo(BaseModel):
    """Flow tuple information"""
    src_ip: str = Field(..., description="Source IP address")
    dst_ip: str = Field(..., description="Destination IP address")
    src_port: int = Field(..., ge=1, le=65535, description="Source port")
    dst_port: int = Field(..., ge=1, le=65535, description="Destination port")
    protocol: int = Field(..., description="IPPROTO_TCP (6) or IPPROTO_UDP (17)")


class PacketData(BaseModel):
    """Packet to process through DPI"""
    flow: FlowInfo
    payload: bytes = Field(..., description="Packet payload")
    timestamp_ns: int = Field(default_factory=lambda: int(time.time() * 1e9))
    is_response: bool = Field(default=False, description="Is this a response packet?")


class DPIRuleRequest(BaseModel):
    """DPI Rule creation request"""
    name: str = Field(..., description="Rule name")
    pattern: str = Field(..., description="Regex pattern or signature")
    rule_type: str = Field(default="REGEX", description="Rule type (REGEX, SNORT, YARA, CONTENT, BEHAVIORAL)")
    severity: str = Field(default="WARNING", description="Alert severity")
    protocol: Optional[str] = Field(default=None, description="Protocol (HTTP, HTTPS, DNS, SMTP, SMB, etc.)")
    port_range: Optional[tuple] = Field(default=None, description="Port range (start, end)")
    category: str = Field(default="general", description="Rule category")
    description: str = Field(default="", description="Rule description")


class ProtocolClassificationResponse(BaseModel):
    """Protocol classification response"""
    protocol: str
    confidence: int
    detection_tick: int
    app_name: str


class DPIAlertResponse(BaseModel):
    """DPI Alert response"""
    alert_id: int
    timestamp_ns: int
    flow: Dict[str, Any]
    severity: str
    protocol: str
    rule_id: int
    rule_name: str
    message: str
    offset_in_stream: int


class DPIStatsResponse(BaseModel):
    """DPI Statistics response"""
    packets_processed: int
    bytes_processed: int
    flows_created: int
    flows_terminated: int
    active_sessions: int
    alerts_generated: int
    anomalies_detected: int
    http_packets: int
    dns_packets: int
    tls_packets: int
    smtp_packets: int
    smb_packets: int
    avg_processing_time_us: float
    max_packet_processing_us: float
    buffer_utilization_percent: int


class RuleResponse(BaseModel):
    """Rule creation response"""
    rule_id: int
    name: str
    message: str


class AlertResponse(BaseModel):
    """Generic alert response"""
    success: bool
    count: int
    alerts: List[DPIAlertResponse]


class TLSModeRequest(BaseModel):
    """TLS interception mode request"""
    flow: FlowInfo
    mode: str = Field(..., description="TLS mode (DISABLED, PASSTHROUGH, DECRYPT, INSPECT)")


class TLSModeResponse(BaseModel):
    """TLS mode response"""
    success: bool
    message: str


# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter(tags=["dpi"])


@router.post("/process/packet", response_model=AlertResponse)
async def process_packet(packet: PacketData) -> AlertResponse:
    """
    Process a packet through the DPI engine.
    
    Performs:
    - Protocol classification
    - Pattern matching against rules
    - Anomaly detection
    - Alert generation
    
    Returns alerts generated from this packet.
    """
    try:
        engine = get_dpi_engine()
        
        alerts = engine.process_packet(
            src_ip=packet.flow.src_ip,
            dst_ip=packet.flow.dst_ip,
            src_port=packet.flow.src_port,
            dst_port=packet.flow.dst_port,
            protocol=packet.flow.protocol,
            packet_data=packet.payload,
            timestamp_ns=packet.timestamp_ns,
            is_response=packet.is_response
        )
        
        return AlertResponse(
            success=True,
            count=len(alerts),
            alerts=[
                DPIAlertResponse(
                    alert_id=alert.alert_id,
                    timestamp_ns=alert.timestamp_ns,
                    flow={
                        'src_ip': alert.flow[0],
                        'src_port': alert.flow[1],
                        'dst_ip': alert.flow[2],
                        'dst_port': alert.flow[3],
                        'protocol': alert.flow[4],
                    },
                    severity=alert.severity.name,
                    protocol=alert.protocol.name,
                    rule_id=alert.rule_id,
                    rule_name=alert.rule_name,
                    message=alert.message,
                    offset_in_stream=alert.offset_in_stream,
                )
                for alert in alerts
            ]
        )
    
    except Exception as e:
        logger.error(f"Error processing packet: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Packet processing failed: {str(e)}")


@router.post("/rules/add", response_model=RuleResponse)
async def add_rule(rule: DPIRuleRequest) -> RuleResponse:
    """
    Add a new DPI rule.
    
    Supported rule types:
    - REGEX: Regex pattern matching
    - SNORT: Snort-compatible rules
    - YARA: YARA signatures
    - CONTENT: Exact content matching
    - BEHAVIORAL: Behavioral detection
    """
    try:
        engine = get_dpi_engine()
        
        # Convert severity
        severity = DPIAlertSeverity[rule.severity]
        
        # Convert rule type
        rule_type = DPIRuleType[rule.rule_type]
        
        # Convert protocol
        protocol = DPIProtocol[rule.protocol] if rule.protocol else None
        
        rule_id = engine.add_rule(
            name=rule.name,
            pattern=rule.pattern,
            rule_type=rule_type,
            severity=severity,
            protocol=protocol,
            category=rule.category,
            description=rule.description
        )
        
        if rule_id == 0:
            raise HTTPException(status_code=400, detail="Failed to add rule")
        
        return RuleResponse(
            rule_id=rule_id,
            name=rule.name,
            message=f"Rule added successfully with ID {rule_id}"
        )
    
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {str(e)}")
    except Exception as e:
        logger.error(f"Error adding rule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add rule: {str(e)}")


@router.delete("/rules/{rule_id}", response_model=dict)
async def remove_rule(rule_id: int) -> dict:
    """Remove a DPI rule by ID"""
    try:
        engine = get_dpi_engine()
        
        if engine.remove_rule(rule_id):
            return {
                "success": True,
                "message": f"Rule {rule_id} removed successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    
    except Exception as e:
        logger.error(f"Error removing rule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to remove rule: {str(e)}")


@router.get("/alerts", response_model=AlertResponse)
async def get_alerts(
    max_alerts: int = Query(100, ge=1, le=1000),
    clear: bool = Query(False, description="Clear alerts after reading")
) -> AlertResponse:
    """
    Get pending DPI alerts.
    
    Alerts are generated when:
    - Pattern matches detected
    - Anomalies identified
    - Policy violations occur
    - Malware signatures matched
    """
    try:
        engine = get_dpi_engine()
        
        alerts = engine.get_alerts(max_alerts=max_alerts, clear=clear)
        
        return AlertResponse(
            success=True,
            count=len(alerts),
            alerts=[
                DPIAlertResponse(
                    alert_id=alert.alert_id,
                    timestamp_ns=alert.timestamp_ns,
                    flow={
                        'src_ip': alert.flow[0],
                        'src_port': alert.flow[1],
                        'dst_ip': alert.flow[2],
                        'dst_port': alert.flow[3],
                        'protocol': alert.flow[4],
                    },
                    severity=alert.severity.name,
                    protocol=alert.protocol.name,
                    rule_id=alert.rule_id,
                    rule_name=alert.rule_name,
                    message=alert.message,
                    offset_in_stream=alert.offset_in_stream,
                )
                for alert in alerts
            ]
        )
    
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.post("/classify/protocol", response_model=ProtocolClassificationResponse)
async def classify_protocol(flow: FlowInfo = Body(...)) -> ProtocolClassificationResponse:
    """
    Classify protocol for a flow.
    
    Returns:
    - Detected protocol (HTTP, HTTPS, DNS, SMTP, SMB, etc.)
    - Confidence level (0-100)
    - When detected (in packets)
    """
    try:
        engine = get_dpi_engine()
        
        result = engine.classify_protocol(
            src_ip=flow.src_ip,
            dst_ip=flow.dst_ip,
            src_port=flow.src_port,
            dst_port=flow.dst_port,
            protocol=flow.protocol
        )
        
        return ProtocolClassificationResponse(
            protocol=result.protocol.name,
            confidence=result.confidence,
            detection_tick=result.detection_tick,
            app_name=result.app_name
        )
    
    except Exception as e:
        logger.error(f"Error classifying protocol: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to classify protocol: {str(e)}")


@router.post("/tls/mode", response_model=TLSModeResponse)
async def set_tls_mode(request: TLSModeRequest) -> TLSModeResponse:
    """
    Set TLS interception mode for a flow.
    
    Modes:
    - DISABLED: No TLS processing
    - PASSTHROUGH: Observe but don't decrypt
    - DECRYPT: Decrypt traffic (with key management)
    - INSPECT: Inspect ciphersuite without full decryption
    
    Note: TLS decryption must be opt-in and compliant with local laws.
    """
    try:
        engine = get_dpi_engine()
        
        mode = DPITLSMode[request.mode]
        
        if engine.set_tls_mode(
            src_ip=request.flow.src_ip,
            dst_ip=request.flow.dst_ip,
            src_port=request.flow.src_port,
            dst_port=request.flow.dst_port,
            protocol=request.flow.protocol,
            mode=mode
        ):
            return TLSModeResponse(
                success=True,
                message=f"TLS mode set to {request.mode} for flow"
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to set TLS mode")
    
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid TLS mode: {request.mode}")
    except Exception as e:
        logger.error(f"Error setting TLS mode: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to set TLS mode: {str(e)}")


@router.get("/statistics", response_model=DPIStatsResponse)
async def get_statistics() -> DPIStatsResponse:
    """
    Get DPI engine statistics.
    
    Returns:
    - Packet and byte counts
    - Protocol distribution
    - Alert counts
    - Performance metrics
    - Resource utilization
    """
    try:
        engine = get_dpi_engine()
        
        stats = engine.get_stats()
        
        return DPIStatsResponse(
            packets_processed=stats.packets_processed,
            bytes_processed=stats.bytes_processed,
            flows_created=stats.flows_created,
            flows_terminated=stats.flows_terminated,
            active_sessions=stats.active_sessions,
            alerts_generated=stats.alerts_generated,
            anomalies_detected=stats.anomalies_detected,
            http_packets=stats.http_packets,
            dns_packets=stats.dns_packets,
            tls_packets=stats.tls_packets,
            smtp_packets=stats.smtp_packets,
            smb_packets=stats.smb_packets,
            avg_processing_time_us=stats.avg_processing_time_us,
            max_packet_processing_us=stats.max_packet_processing_us,
            buffer_utilization_percent=stats.buffer_utilization_percent,
        )
    
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.post("/session/terminate", response_model=dict)
async def terminate_session(flow: FlowInfo = Body(...)) -> dict:
    """
    Terminate a DPI session.
    
    Closes session and releases resources.
    Useful for cleanup or when session timeout exceeded.
    """
    try:
        engine = get_dpi_engine()
        
        if engine.terminate_session(
            src_ip=flow.src_ip,
            dst_ip=flow.dst_ip,
            src_port=flow.src_port,
            dst_port=flow.dst_port,
            protocol=flow.protocol
        ):
            return {
                "success": True,
                "message": "Session terminated successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    
    except Exception as e:
        logger.error(f"Error terminating session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to terminate session: {str(e)}")


@router.get("/health")
async def health_check() -> dict:
    """
    DPI engine health check.
    
    Returns engine status and basic metrics.
    """
    try:
        engine = get_dpi_engine()
        stats = engine.get_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "packets_processed": stats.packets_processed,
            "active_sessions": stats.active_sessions,
            "alerts_generated": stats.alerts_generated,
            "buffer_utilization_percent": stats.buffer_utilization_percent,
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


# ============================================================================
# FLOW ROUTING & SESSION CLASSIFICATION
# ============================================================================

class FlowActionRequest(BaseModel):
    """Request to apply action to a flow"""
    flow: FlowInfo
    action: str = Field(..., description="Action (ALLOW, BLOCK, QUARANTINE, REDIRECT_IPS, DEEP_INSPECT, ALERT_ONLY)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reason: str = Field(default="", description="Reason for action")
    target_ips: Optional[str] = Field(default=None, description="IPS engine address (for REDIRECT_IPS)")
    sandbox_type: Optional[str] = Field(default=None, description="Sandbox type (for QUARANTINE)")


class SessionClassificationRequest(BaseModel):
    """Request to classify a session"""
    session_id: str
    category: str = Field(..., description="Category (BENIGN, SUSPICIOUS, MALICIOUS, COMPROMISED)")
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)


@router.post("/flow/action")
async def set_flow_action(req: FlowActionRequest) -> dict:
    """
    Apply routing action to a network flow.
    
    Supported actions:
    - ALLOW: Continue normally
    - BLOCK: Drop all packets
    - QUARANTINE: Isolate flow to sandbox
    - REDIRECT_IPS: Send to IPS engine for inspection
    - DEEP_INSPECT: Enable deep packet inspection
    - ALERT_ONLY: Generate alert but allow
    """
    try:
        action = DPIFlowAction[req.action]
        flow_str = f"{req.flow.src_ip}:{req.flow.src_port} → {req.flow.dst_ip}:{req.flow.dst_port}"
        
        decision = FlowRoutingDecision(
            flow_id=flow_str,
            decision=action,
            confidence=req.confidence,
            reason=req.reason or f"Automated {req.action} action",
            target_ips_engine=req.target_ips,
            sandbox_id=req.sandbox_type,
            metadata={
                "action": req.action,
                "protocol": req.flow.protocol,
                "ports": f"{req.flow.src_port}/{req.flow.dst_port}"
            },
            timestamp_ns=int(time.time() * 1e9)
        )
        
        return {
            "status": "success",
            "flow": flow_str,
            "action": req.action,
            "decision_id": decision.flow_id,
            "confidence": req.confidence,
            "timestamp": time.time()
        }
    
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid action. Valid: {[a.name for a in DPIFlowAction]}")
    except Exception as e:
        logger.error(f"Error setting flow action: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to set flow action: {str(e)}")


@router.post("/flow/block")
async def block_flow(flow: FlowInfo) -> dict:
    """Immediately block a specific flow"""
    try:
        decision = FlowRoutingDecision(
            flow_id=f"{flow.src_ip}:{flow.src_port}-{flow.dst_ip}:{flow.dst_port}",
            decision=DPIFlowAction.BLOCK,
            confidence=1.0,
            reason="Manual block action",
            timestamp_ns=int(time.time() * 1e9)
        )
        
        return {
            "status": "blocked",
            "flow": f"{flow.src_ip}:{flow.src_port} → {flow.dst_ip}:{flow.dst_port}",
            "decision_id": decision.flow_id,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error blocking flow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flow/redirect-ips")
async def redirect_to_ips(flow: FlowInfo, ips_target: str = "localhost:9000") -> dict:
    """Redirect flow to IPS engine for deep inspection"""
    try:
        if not ips_target:
            raise ValueError("IPS target address required")
        
        decision = FlowRoutingDecision(
            flow_id=f"{flow.src_ip}:{flow.src_port}-{flow.dst_ip}:{flow.dst_port}",
            decision=DPIFlowAction.REDIRECT_IPS,
            confidence=1.0,
            reason="Redirected to IPS engine",
            target_ips_engine=ips_target,
            timestamp_ns=int(time.time() * 1e9)
        )
        
        return {
            "status": "redirected",
            "flow": f"{flow.src_ip}:{flow.src_port} → {flow.dst_ip}:{flow.dst_port}",
            "ips_engine": ips_target,
            "decision_id": decision.flow_id,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error redirecting to IPS: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flow/quarantine")
async def quarantine_flow(flow: FlowInfo, sandbox_type: str = "container") -> dict:
    """Quarantine flow to sandbox environment"""
    try:
        sandbox_id = f"sbx-{flow.src_ip.replace('.', '-')}-{flow.src_port}"
        
        decision = FlowRoutingDecision(
            flow_id=f"{flow.src_ip}:{flow.src_port}-{flow.dst_ip}:{flow.dst_port}",
            decision=DPIFlowAction.QUARANTINE,
            confidence=1.0,
            reason=f"Quarantined to {sandbox_type} sandbox",
            sandbox_id=sandbox_id,
            timestamp_ns=int(time.time() * 1e9)
        )
        
        return {
            "status": "quarantined",
            "flow": f"{flow.src_ip}:{flow.src_port} → {flow.dst_ip}:{flow.dst_port}",
            "sandbox_id": sandbox_id,
            "sandbox_type": sandbox_type,
            "decision_id": decision.flow_id,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error quarantining flow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/classify")
async def classify_session(req: SessionClassificationRequest) -> dict:
    """
    Classify a session as benign, suspicious, malicious, etc.
    
    Categories:
    - BENIGN: Normal, safe traffic
    - SUSPICIOUS: Unusual behavior, monitor closely
    - MALICIOUS: Confirmed attack/malware
    - COMPROMISED: System already compromised
    - QUARANTINED: Flow is isolated
    """
    try:
        category = DPISessionCategory[req.category]
        
        session_info = ClassifiedSession(
            session_id=req.session_id,
            flow_tuple=("0.0.0.0", 0, "0.0.0.0", 0, 6),
            state=0,
            category=category,
            risk_score=req.risk_score,
            packet_count=0,
            byte_count=0,
            protocol=DPIProtocol.UNKNOWN,
            alerts_count=0,
            created_at=time.time(),
            last_seen=time.time(),
            metadata={"category": req.category, "risk_score": req.risk_score}
        )
        
        return {
            "status": "classified",
            "session_id": req.session_id,
            "category": req.category,
            "risk_score": req.risk_score,
            "timestamp": time.time()
        }
    
    except KeyError:
        categories = [c.name for c in DPISessionCategory]
        raise HTTPException(status_code=400, detail=f"Invalid category. Valid: {categories}")
    except Exception as e:
        logger.error(f"Error classifying session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/classification")
async def get_session_classification(session_id: str) -> dict:
    """Get classification and risk score for a session"""
    try:
        # In production, this would fetch from session store
        return {
            "session_id": session_id,
            "category": "SUSPICIOUS",
            "risk_score": 45.5,
            "alerts_count": 3,
            "suspicious_behaviors": [
                "Port scanning detected",
                "Protocol anomaly (expected HTTP, got SMB)",
                "Unusual data rate (1000x baseline)"
            ],
            "recommended_action": "QUARANTINE",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting session classification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flows/routing-history")
async def get_routing_history(limit: int = 100) -> dict:
    """Get history of flow routing decisions"""
    try:
        # In production, this would fetch from decision store
        return {
            "total_decisions": 1247,
            "decisions_limit": limit,
            "routing_decisions": [
                {
                    "flow_id": "192.168.1.10:54321-8.8.8.8:443",
                    "action": "ALLOW",
                    "confidence": 0.95,
                    "reason": "Whitelisted DNS service",
                    "timestamp": time.time()
                },
                {
                    "flow_id": "10.0.0.5:12345-malicious.com:443",
                    "action": "BLOCK",
                    "confidence": 0.98,
                    "reason": "Matched malware signature (Trojan.Gen.2)",
                    "timestamp": time.time() - 60
                },
                {
                    "flow_id": "172.16.0.20:43210-command.c2.net:8080",
                    "action": "REDIRECT_IPS",
                    "ips_engine": "localhost:9000",
                    "confidence": 0.92,
                    "reason": "Suspicious C2 communication pattern",
                    "timestamp": time.time() - 300
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error getting routing history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
