from fastapi import APIRouter, HTTPException, Query, Body
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
import os
import json
import logging
import asyncio
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

router = APIRouter()

# Import firewall policy engine
from backend.firewall_policy_engine import (
    StatefulFirewallPolicyEngine,
    FirewallRule,
    FlowTuple,
    PolicyDecision,
    PolicyEvaluationResult,
    ACLAction,
    TrafficDirection,
    QoSClass,
    GeoBlockAction,
    NATMode,
    PolicyVersion,
    NATMapping,
    ConnectionState,
)

# Initialize global firewall engine
_firewall_engine = StatefulFirewallPolicyEngine(max_connections=100000)

# ============================================================================
# PYDANTIC MODELS FOR API REQUESTS/RESPONSES
# ============================================================================

class FirewallRuleRequest(BaseModel):
    """Request model for creating/updating a firewall rule"""
    name: str = Field(..., description="Rule name")
    priority: int = Field(default=100, description="Rule priority (higher = higher priority)")
    direction: str = Field(default="bidirectional")
    src_ip_prefix: Optional[str] = None
    dst_ip_prefix: Optional[str] = None
    src_port_range: Optional[Tuple[int, int]] = None
    dst_port_range: Optional[Tuple[int, int]] = None
    protocol: Optional[str] = None
    app_name: Optional[str] = None
    dpi_category: Optional[str] = None
    user_identity: Optional[str] = None
    user_role: Optional[str] = None
    action: str = "allow"
    qos_class: Optional[str] = None
    nat_mode: Optional[str] = None
    rate_limit_kbps: Optional[int] = None
    geo_block_countries: List[str] = Field(default_factory=list)
    geo_block_action: str = "allow"
    enabled: bool = True
    description: str = ""


class FlowEvaluationRequest(BaseModel):
    """Request model for evaluating a flow"""
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str = "tcp"
    direction: str = "inbound"
    dpi_app: Optional[str] = None
    dpi_category: Optional[str] = None
    user_identity: Optional[str] = None
    user_role: Optional[str] = None
    src_country: Optional[str] = None
    packet_bytes: int = 1500


class PolicyVersionRequest(BaseModel):
    """Request model for creating a policy version"""
    name: str
    description: str
    parent_version_id: Optional[str] = None


class StagedRolloutRequest(BaseModel):
    """Request model for staged rollout"""
    deployment_percentage: int = Field(10, ge=0, le=100)
    deployment_target: Optional[str] = None


class NATMappingRequest(BaseModel):
    """Request model for NAT mapping"""
    mode: str
    source_pool_start: Optional[str] = None
    source_pool_end: Optional[str] = None
    target_server: Optional[str] = None
    target_port: Optional[int] = None
    src_ip_prefix: Optional[str] = None
    dst_ip_prefix: Optional[str] = None
    protocol: Optional[str] = None


# ============================================================================
# FIREWALL RULE MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/firewall/rules", tags=["firewall"])
async def create_firewall_rule(req: FirewallRuleRequest):
    """Create a new firewall rule"""
    try:
        rule_id = f"rule_{int(__import__('time').time())}_{str(uuid.uuid4())[:8]}"
        
        rule = FirewallRule(
            rule_id=rule_id,
            name=req.name,
            priority=req.priority,
            direction=TrafficDirection(req.direction),
            src_ip_prefix=req.src_ip_prefix,
            dst_ip_prefix=req.dst_ip_prefix,
            src_port_range=req.src_port_range,
            dst_port_range=req.dst_port_range,
            protocol=req.protocol,
            app_name=req.app_name,
            dpi_category=req.dpi_category,
            user_identity=req.user_identity,
            user_role=req.user_role,
            action=ACLAction(req.action),
            qos_class=QoSClass(req.qos_class) if req.qos_class else None,
            nat_mode=NATMode(req.nat_mode) if req.nat_mode else None,
            rate_limit_kbps=req.rate_limit_kbps,
            geo_block_countries=req.geo_block_countries,
            geo_block_action=GeoBlockAction(req.geo_block_action),
            enabled=req.enabled,
            description=req.description,
        )
        
        if _firewall_engine.add_rule(rule):
            return {"status": "created", "rule_id": rule_id, "rule": rule.to_dict()}
        else:
            raise HTTPException(status_code=409, detail="Rule already exists")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid value: {str(e)}")
    except Exception as e:
        logger.exception(f"Error creating firewall rule: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating rule: {str(e)}")


@router.get("/firewall/rules", tags=["firewall"])
async def list_firewall_rules():
    """List all firewall rules"""
    try:
        rules = _firewall_engine.list_rules()
        return {
            "status": "ok",
            "count": len(rules),
            "rules": [r.to_dict() for r in rules]
        }
    except Exception as e:
        logger.exception(f"Error listing rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/firewall/rules/{rule_id}", tags=["firewall"])
async def get_firewall_rule(rule_id: str):
    """Get a specific firewall rule"""
    try:
        rule = _firewall_engine.get_rule(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
        return {"status": "ok", "rule": rule.to_dict()}
    except Exception as e:
        logger.exception(f"Error getting rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/firewall/rules/{rule_id}", tags=["firewall"])
async def update_firewall_rule(rule_id: str, req: FirewallRuleRequest):
    """Update a firewall rule"""
    try:
        old_rule = _firewall_engine.get_rule(rule_id)
        if not old_rule:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
        
        _firewall_engine.delete_rule(rule_id)
        
        rule = FirewallRule(
            rule_id=rule_id,
            name=req.name,
            priority=req.priority,
            direction=TrafficDirection(req.direction),
            src_ip_prefix=req.src_ip_prefix,
            dst_ip_prefix=req.dst_ip_prefix,
            src_port_range=req.src_port_range,
            dst_port_range=req.dst_port_range,
            protocol=req.protocol,
            app_name=req.app_name,
            dpi_category=req.dpi_category,
            user_identity=req.user_identity,
            user_role=req.user_role,
            action=ACLAction(req.action),
            qos_class=QoSClass(req.qos_class) if req.qos_class else None,
            nat_mode=NATMode(req.nat_mode) if req.nat_mode else None,
            rate_limit_kbps=req.rate_limit_kbps,
            geo_block_countries=req.geo_block_countries,
            geo_block_action=GeoBlockAction(req.geo_block_action),
            enabled=req.enabled,
            description=req.description,
        )
        
        _firewall_engine.add_rule(rule)
        return {"status": "updated", "rule": rule.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid value: {str(e)}")
    except Exception as e:
        logger.exception(f"Error updating rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/firewall/rules/{rule_id}", tags=["firewall"])
async def delete_firewall_rule(rule_id: str):
    """Delete a firewall rule"""
    try:
        if _firewall_engine.delete_rule(rule_id):
            return {"status": "deleted", "rule_id": rule_id}
        else:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    except Exception as e:
        logger.exception(f"Error deleting rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FLOW EVALUATION ENDPOINTS
# ============================================================================

@router.post("/firewall/evaluate", tags=["firewall"])
async def evaluate_flow(req: FlowEvaluationRequest):
    """Evaluate a flow against firewall policies"""
    try:
        flow = FlowTuple(
            src_ip=req.src_ip,
            dst_ip=req.dst_ip,
            src_port=req.src_port,
            dst_port=req.dst_port,
            protocol=req.protocol,
        )
        
        decision = _firewall_engine.evaluate_flow(
            flow=flow,
            direction=TrafficDirection(req.direction),
            dpi_app=req.dpi_app,
            dpi_category=req.dpi_category,
            user_identity=req.user_identity,
            user_role=req.user_role,
            src_country=req.src_country,
            packet_bytes=req.packet_bytes,
        )
        
        return {
            "status": "evaluated",
            "flow": {
                "src_ip": req.src_ip,
                "dst_ip": req.dst_ip,
                "src_port": req.src_port,
                "dst_port": req.dst_port,
                "protocol": req.protocol,
            },
            "decision": decision.to_dict(),
        }
    except Exception as e:
        logger.exception(f"Error evaluating flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/firewall/close-connection", tags=["firewall"])
async def close_connection(src_ip: str, dst_ip: str, src_port: int, dst_port: int, protocol: str = "tcp"):
    """Close a connection (mark as terminated)"""
    try:
        flow = FlowTuple(
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            protocol=protocol,
        )
        
        if _firewall_engine.close_connection(flow):
            return {"status": "closed", "flow": flow.to_key()}
        else:
            return {"status": "not_found", "flow": flow.to_key()}
    except Exception as e:
        logger.exception(f"Error closing connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# POLICY VERSION & STAGED ROLLOUT ENDPOINTS
# ============================================================================

@router.post("/firewall/versions", tags=["policy-versions"])
async def create_policy_version(req: PolicyVersionRequest):
    """Create a new policy version"""
    try:
        version = _firewall_engine.create_policy_version(
            name=req.name,
            description=req.description,
            parent_version_id=req.parent_version_id,
        )
        return {
            "status": "created",
            "version": version.to_dict(),
        }
    except Exception as e:
        logger.exception(f"Error creating policy version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/firewall/versions", tags=["policy-versions"])
async def list_policy_versions():
    """List all policy versions"""
    try:
        versions = _firewall_engine.list_policy_versions()
        return {
            "status": "ok",
            "count": len(versions),
            "versions": [v.to_dict() for v in versions]
        }
    except Exception as e:
        logger.exception(f"Error listing versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/firewall/versions/{version_id}", tags=["policy-versions"])
async def get_policy_version(version_id: str):
    """Get a specific policy version"""
    try:
        version = _firewall_engine.get_policy_version(version_id)
        if not version:
            raise HTTPException(status_code=404, detail=f"Version {version_id} not found")
        return {"status": "ok", "version": version.to_dict()}
    except Exception as e:
        logger.exception(f"Error getting version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/firewall/versions/{version_id}/stage", tags=["policy-versions"])
async def stage_policy_version(version_id: str, req: StagedRolloutRequest):
    """Stage a policy version for canary rollout"""
    try:
        if _firewall_engine.stage_policy_version(
            version_id=version_id,
            deployment_percentage=req.deployment_percentage,
            deployment_target=req.deployment_target,
        ):
            version = _firewall_engine.get_policy_version(version_id)
            return {
                "status": "staged",
                "version": version.to_dict(),
            }
        else:
            raise HTTPException(status_code=404, detail=f"Version {version_id} not found")
    except Exception as e:
        logger.exception(f"Error staging version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/firewall/versions/{version_id}/activate", tags=["policy-versions"])
async def activate_policy_version(version_id: str):
    """Activate a policy version (100% rollout)"""
    try:
        if _firewall_engine.activate_policy_version(version_id):
            version = _firewall_engine.get_policy_version(version_id)
            return {
                "status": "activated",
                "version": version.to_dict(),
            }
        else:
            raise HTTPException(status_code=404, detail=f"Version {version_id} not found")
    except Exception as e:
        logger.exception(f"Error activating version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# METRICS & STATUS ENDPOINTS
# ============================================================================

@router.get("/firewall/metrics", tags=["metrics"])
async def get_firewall_metrics():
    """Get firewall metrics"""
    try:
        metrics = _firewall_engine.get_metrics()
        return {
            "status": "ok",
            "metrics": metrics,
        }
    except Exception as e:
        logger.exception(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/firewall/connections", tags=["metrics"])
async def get_active_connections(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    """Get active connections"""
    try:
        connections = _firewall_engine.get_active_connections(limit=limit, offset=offset)
        return {
            "status": "ok",
            "count": len(connections),
            "limit": limit,
            "offset": offset,
            "connections": connections,
        }
    except Exception as e:
        logger.exception(f"Error getting connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LEGACY ENDPOINTS (MAINTAINED FOR BACKWARD COMPATIBILITY)
# ============================================================================
_huawei_iam_enabled = os.environ.get("HUAWEI_IAM_ENABLED", "0") in ("1", "true", "True")
_huawei_client = None
if _huawei_iam_enabled:
    try:
        # try to use a local integration if present
        from backend.integrations.huawei_aom import HuaweiAOMClient  # type: ignore

        _huawei_client = HuaweiAOMClient()
        logger.info("Policy: Huawei AIM client loaded via backend.integrations.huawei_aom")
    except Exception:
        try:
            from backend.integrations.huawei_modelarts import HuaweiModelArtsClient  # type: ignore

            _huawei_client = HuaweiModelArtsClient()
            logger.info("Policy: Huawei IAM client loaded via backend.integrations.huawei_modelarts")
        except Exception:
            logger.exception("Policy: Huawei IAM integrations not available; disabling Huawei IAM checks")
            _huawei_client = None
            _huawei_iam_enabled = False


# --- gRPC policy engine configuration (guarded) ---
_grpc_address = os.environ.get("POLICY_GRPC_ADDRESS")
_grpc_method = os.environ.get("POLICY_GRPC_METHOD")  # full method name, e.g. "/policy.Policy/Enforce"
_grpc_enabled = bool(_grpc_address and _grpc_method)


def _call_huawei_iam(subject: str, action: str, resource: str) -> Dict[str, Any]:
    """Synchronous Huawei IAM check wrapper. Returns dict with decision."""
    if not _huawei_iam_enabled or _huawei_client is None:
        return {"allowed": None, "reason": "huawei_disabled"}
    try:
        # integration clients may offer check_permission or authorize; probe common names
        for name in ("check_permission", "authorize", "is_allowed"):
            fn = getattr(_huawei_client, name, None)
            if callable(fn):
                try:
                    res = fn(subject=subject, action=action, resource=resource)
                    return {"allowed": bool(res), "reason": "huawei_iam"}
                except TypeError:
                    # try positional
                    try:
                        res = fn(subject, action, resource)
                        return {"allowed": bool(res), "reason": "huawei_iam"}
                    except Exception:
                        logger.exception("Policy: Huawei IAM client method %s failed", name)
        logger.warning("Policy: Huawei IAM client present but no usable method found")
        return {"allowed": None, "reason": "huawei_no_method"}
    except Exception:
        logger.exception("Policy: Huawei IAM check failed")
        return {"allowed": None, "reason": "huawei_error"}


def _call_grpc_policy(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not _grpc_enabled:
        return {"decision": None, "reason": "grpc_disabled"}
    try:
        import grpc  # type: ignore

        # Use a simple bytes-over-unary approach: pass JSON bytes and expect JSON bytes back.
        channel = grpc.insecure_channel(_grpc_address)
        stub = channel
        method = _grpc_method
        # create a callable
        unary = stub.unary_unary(method)
        req_bytes = json.dumps(payload).encode("utf-8")
        resp = unary(req_bytes, timeout=5)
        # resp may be bytes
        if isinstance(resp, (bytes, bytearray)):
            try:
                return json.loads(resp.decode("utf-8"))
            except Exception:
                return {"decision": None, "raw": resp}
        # otherwise try to coerce
        try:
            return dict(resp)
        except Exception:
            return {"decision": None, "raw": str(resp)}
    except Exception:
        logger.exception("Policy: gRPC policy call failed")
        return {"decision": None, "reason": "grpc_error"}


def _simple_enforce(subject: str, action: str, resource: str) -> Dict[str, Any]:
    """Fallback enforcement: deny on configured blocked actions, allow otherwise."""
    blocked = os.environ.get("POLICY_BLOCKED_ACTIONS", "").split(",")
    blocked = {x.strip() for x in blocked if x.strip()}
    if action in blocked:
        return {"allowed": False, "reason": "blocked_action"}
    allowed_subjects = os.environ.get("POLICY_ALLOWED_SUBJECTS", "").split(",")
    allowed_subjects = {x.strip() for x in allowed_subjects if x.strip()}
    if allowed_subjects and subject not in allowed_subjects:
        return {"allowed": False, "reason": "subject_not_allowed"}
    return {"allowed": True, "reason": "default_allow"}


@router.post("/simulate")
async def simulate(payload: dict):
    # simple local simulation of policy evaluation
    subj = payload.get("subject", "unknown")
    act = payload.get("action", "unknown")
    res = payload.get("resource", "")
    decision = _simple_enforce(subj, act, res)
    return {"result": "simulated", "decision": decision}


@router.post("/enforce")
async def enforce(payload: dict):
    """Enforce containment policy for an action. Flow:
    1. If Huawei IAM enabled, ask IAM.
    2. If IAM yields allow/deny, return it.
    3. Else, if gRPC policy engine configured, call it.
    4. Else, fall back to simple local enforcement.
    """
    subj = payload.get("subject")
    act = payload.get("action")
    res = payload.get("resource")
    if not subj or not act:
        raise HTTPException(status_code=400, detail="subject and action required")

    # 1. Huawei IAM
    iam_dec = _call_huawei_iam(subj, act, res)
    if iam_dec.get("allowed") is True:
        return {"result": "allowed", "via": "huawei_iam", "detail": iam_dec}
    if iam_dec.get("allowed") is False:
        return {"result": "denied", "via": "huawei_iam", "detail": iam_dec}

    # 2. gRPC policy engine
    grpc_dec = _call_grpc_policy(payload)
    if grpc_dec.get("decision") is True:
        return {"result": "allowed", "via": "grpc", "detail": grpc_dec}
    if grpc_dec.get("decision") is False:
        return {"result": "denied", "via": "grpc", "detail": grpc_dec}

    # 3. fallback
    simple = _simple_enforce(subj, act, res)
    return {"result": "allowed" if simple.get("allowed") else "denied", "via": "local", "detail": simple}


# ============================================================================
# DPI ↔ IAM ↔ FIREWALL INTEGRATION ENDPOINTS
# ============================================================================

# Initialize integration engine
try:
    from backend.integrations.firewall_dpi_iam_integration import (
        FirewallDPIIAMIntegration,
        DPIClassification,
        IAMIdentityAssertion,
        AdminPolicy,
        PolicyCondition,
        PolicyMatchType,
        create_block_application_policy,
        create_block_category_policy,
        create_restrict_by_role_policy,
        create_rate_limit_policy,
        create_high_risk_quarantine_policy,
        create_contractor_policy,
    )
    _integration = FirewallDPIIAMIntegration()
    _integration_enabled = True
except Exception as e:
    logger.exception("Failed to initialize integration engine")
    _integration = None
    _integration_enabled = False


class AdminPolicyRequest(BaseModel):
    """Request for creating/updating an admin policy"""
    name: str = Field(..., description="Policy name")
    description: str = Field(..., description="Policy description")
    conditions: List[Dict[str, Any]] = Field(..., description="List of conditions")
    condition_logic: str = Field(default="ALL", description="ALL or ANY")
    action: str = Field(..., description="Action to take")
    action_params: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=50)
    enabled: bool = Field(default=True)


class DPIClassificationRequest(BaseModel):
    """DPI classification data from DPI engine"""
    app_name: str
    category: str
    protocol: str
    confidence: int
    detection_tick: int
    is_encrypted: bool = False
    is_tunneled: bool = False
    risk_score: int = 0
    detected_anomalies: List[str] = Field(default_factory=list)


class IAMAssertionRequest(BaseModel):
    """IAM identity assertion data from IAM system"""
    user_id: str
    username: str
    user_role: str
    user_groups: List[str] = Field(default_factory=list)
    organization_unit: Optional[str] = None
    location: Optional[str] = None
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    is_mfa_verified: bool = False
    permission_level: int = 0
    clearance_level: Optional[str] = None
    restrictions: List[str] = Field(default_factory=list)


class IntegratedFlowEvaluationRequest(BaseModel):
    """
    Complete flow evaluation with DPI + IAM context.
    This combines network tuple, DPI classification, and IAM assertion.
    """
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str = "tcp"
    
    # Optional DPI context
    dpi_classification: Optional[DPIClassificationRequest] = None
    
    # Optional IAM context
    iam_assertion: Optional[IAMAssertionRequest] = None


@router.post("/integration/evaluate-with-context")
async def evaluate_flow_with_context(request: IntegratedFlowEvaluationRequest):
    """
    Evaluate a flow with full DPI + IAM context.
    
    This endpoint performs policy evaluation considering:
    1. Network layer info (IPs, ports, protocol)
    2. Application layer info (DPI classification)
    3. Identity/authentication info (IAM assertion)
    4. Admin-defined policies
    
    Returns: Suggested policy decision and matching admin policy (if any)
    
    Example:
    ```bash
    curl -X POST http://localhost:8000/policy/integration/evaluate-with-context \
      -H "Content-Type: application/json" \
      -d '{
        "src_ip": "192.168.1.100",
        "dst_ip": "10.0.0.50",
        "src_port": 51234,
        "dst_port": 443,
        "protocol": "tcp",
        "dpi_classification": {
          "app_name": "Spotify",
          "category": "Video Streaming",
          "protocol": "HTTPS",
          "confidence": 95,
          "detection_tick": 150,
          "risk_score": 10
        },
        "iam_assertion": {
          "user_id": "user123",
          "username": "john.doe",
          "user_role": "employee",
          "user_groups": ["engineers"],
          "location": "office",
          "device_type": "laptop",
          "is_mfa_verified": true
        }
      }'
    ```
    """
    try:
        if not _integration_enabled:
            raise HTTPException(status_code=503, detail="Integration engine not available")
        
        # Convert requests to domain objects
        dpi_class = None
        if request.dpi_classification:
            dpi_class = DPIClassification(
                app_name=request.dpi_classification.app_name,
                category=request.dpi_classification.category,
                protocol=request.dpi_classification.protocol,
                confidence=request.dpi_classification.confidence,
                detection_tick=request.dpi_classification.detection_tick,
                is_encrypted=request.dpi_classification.is_encrypted,
                is_tunneled=request.dpi_classification.is_tunneled,
                risk_score=request.dpi_classification.risk_score,
                detected_anomalies=request.dpi_classification.detected_anomalies,
            )
        
        iam_assert = None
        if request.iam_assertion:
            iam_assert = IAMIdentityAssertion(
                user_id=request.iam_assertion.user_id,
                username=request.iam_assertion.username,
                user_role=request.iam_assertion.user_role,
                user_groups=request.iam_assertion.user_groups,
                organization_unit=request.iam_assertion.organization_unit,
                location=request.iam_assertion.location,
                device_id=request.iam_assertion.device_id,
                device_type=request.iam_assertion.device_type,
                is_mfa_verified=request.iam_assertion.is_mfa_verified,
                permission_level=request.iam_assertion.permission_level,
                clearance_level=request.iam_assertion.clearance_level,
                restrictions=request.iam_assertion.restrictions,
            )
        
        # Build context
        context = _integration.build_policy_context(
            src_ip=request.src_ip,
            dst_ip=request.dst_ip,
            src_port=request.src_port,
            dst_port=request.dst_port,
            protocol=request.protocol,
            dpi_classification=dpi_class,
            iam_assertion=iam_assert,
        )
        
        # Evaluate policies
        matching_policy, action, action_params = _integration.evaluate_policies(context)
        
        # Get suggestions for debugging
        suggestions = _integration.get_policy_suggestions(context)
        
        return {
            "status": "success",
            "flow": {
                "src_ip": request.src_ip,
                "src_port": request.src_port,
                "dst_ip": request.dst_ip,
                "dst_port": request.dst_port,
                "protocol": request.protocol,
            },
            "context": context,
            "matching_policy": matching_policy.to_dict() if matching_policy else None,
            "suggested_action": action or "pass",
            "action_parameters": action_params,
            "matching_policies_count": len(suggestions),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.exception("Flow evaluation with context failed")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.post("/integration/policies/add")
async def add_admin_policy(request: AdminPolicyRequest):
    """
    Add a new admin policy to the integration engine.
    
    Policies are matched in priority order (highest first).
    Multiple conditions can be combined with ALL or ANY logic.
    
    Example:
    ```bash
    curl -X POST http://localhost:8000/policy/integration/policies/add \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Block Torrent",
        "description": "Block all BitTorrent traffic",
        "conditions": [
          {
            "match_type": "application",
            "field": "dpi_category",
            "operator": "eq",
            "value": "P2P"
          }
        ],
        "condition_logic": "ALL",
        "action": "drop",
        "priority": 100
      }'
    ```
    """
    try:
        if not _integration_enabled:
            raise HTTPException(status_code=503, detail="Integration engine not available")
        
        import uuid
        policy_id = f"policy_{uuid.uuid4().hex[:8]}"
        
        # Convert conditions
        conditions = []
        for cond_dict in request.conditions:
            cond = PolicyCondition(
                match_type=PolicyMatchType(cond_dict.get("match_type", "network")),
                field=cond_dict.get("field"),
                operator=cond_dict.get("operator", "eq"),
                value=cond_dict.get("value"),
            )
            conditions.append(cond)
        
        # Create policy
        policy = AdminPolicy(
            policy_id=policy_id,
            name=request.name,
            description=request.description,
            conditions=conditions,
            condition_logic=request.condition_logic,
            action=request.action,
            action_params=request.action_params,
            priority=request.priority,
            enabled=request.enabled,
        )
        
        # Add to engine
        _integration.add_admin_policy(policy)
        
        return {
            "status": "success",
            "policy_id": policy_id,
            "message": f"Policy '{request.name}' added with priority {request.priority}",
            "policy": policy.to_dict(),
        }
    except Exception as e:
        logger.exception("Failed to add admin policy")
        raise HTTPException(status_code=500, detail=f"Failed to add policy: {str(e)}")


@router.get("/integration/policies/list")
async def list_admin_policies():
    """
    List all admin policies currently loaded.
    Sorted by priority (highest first).
    """
    try:
        if not _integration_enabled:
            raise HTTPException(status_code=503, detail="Integration engine not available")
        
        policies = [p.to_dict() for p in _integration.admin_policies]
        
        return {
            "status": "success",
            "count": len(policies),
            "policies": policies,
        }
    except Exception as e:
        logger.exception("Failed to list policies")
        raise HTTPException(status_code=500, detail=f"Failed to list policies: {str(e)}")


@router.delete("/integration/policies/{policy_id}")
async def remove_admin_policy(policy_id: str):
    """
    Remove an admin policy by ID.
    
    Example:
    ```bash
    curl -X DELETE http://localhost:8000/policy/integration/policies/policy_abc12345
    ```
    """
    try:
        if not _integration_enabled:
            raise HTTPException(status_code=503, detail="Integration engine not available")
        
        removed = _integration.remove_admin_policy(policy_id)
        
        if not removed:
            raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
        
        return {
            "status": "success",
            "message": f"Policy {policy_id} removed",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to remove policy")
        raise HTTPException(status_code=500, detail=f"Failed to remove policy: {str(e)}")


@router.post("/integration/policies/templates/block-application")
async def create_block_app_policy(app_name: str = Query(...)):
    """
    Quick template: Block a specific application.
    
    Example:
    ```bash
    curl -X POST "http://localhost:8000/policy/integration/policies/templates/block-application?app_name=Spotify"
    ```
    """
    try:
        if not _integration_enabled:
            raise HTTPException(status_code=503, detail="Integration engine not available")
        
        policy = create_block_application_policy(app_name)
        _integration.add_admin_policy(policy)
        
        return {
            "status": "success",
            "policy_id": policy.policy_id,
            "message": f"Block policy created for {app_name}",
            "policy": policy.to_dict(),
        }
    except Exception as e:
        logger.exception("Failed to create block application policy")
        raise HTTPException(status_code=500, detail=f"Failed to create policy: {str(e)}")


@router.post("/integration/policies/templates/block-category")
async def create_block_cat_policy(category: str = Query(...)):
    """
    Quick template: Block a traffic category.
    
    Example:
    ```bash
    curl -X POST "http://localhost:8000/policy/integration/policies/templates/block-category?category=P2P"
    ```
    """
    try:
        if not _integration_enabled:
            raise HTTPException(status_code=503, detail="Integration engine not available")
        
        policy = create_block_category_policy(category)
        _integration.add_admin_policy(policy)
        
        return {
            "status": "success",
            "policy_id": policy.policy_id,
            "message": f"Block policy created for {category}",
            "policy": policy.to_dict(),
        }
    except Exception as e:
        logger.exception("Failed to create block category policy")
        raise HTTPException(status_code=500, detail=f"Failed to create policy: {str(e)}")


@router.post("/integration/policies/templates/rate-limit")
async def create_rate_limit_policy_endpoint(
    category: str = Query(...),
    rate_limit_kbps: int = Query(5000),
):
    """
    Quick template: Rate limit a traffic category.
    
    Example:
    ```bash
    curl -X POST "http://localhost:8000/policy/integration/policies/templates/rate-limit?category=Video%20Streaming&rate_limit_kbps=5000"
    ```
    """
    try:
        if not _integration_enabled:
            raise HTTPException(status_code=503, detail="Integration engine not available")
        
        policy = create_rate_limit_policy(category, rate_limit_kbps)
        _integration.add_admin_policy(policy)
        
        return {
            "status": "success",
            "policy_id": policy.policy_id,
            "message": f"Rate limit policy created for {category} at {rate_limit_kbps} kbps",
            "policy": policy.to_dict(),
        }
    except Exception as e:
        logger.exception("Failed to create rate limit policy")
        raise HTTPException(status_code=500, detail=f"Failed to create policy: {str(e)}")


@router.post("/integration/policies/templates/high-risk-quarantine")
async def create_quarantine_policy_endpoint():
    """
    Quick template: Quarantine high-risk traffic.
    
    Example:
    ```bash
    curl -X POST "http://localhost:8000/policy/integration/policies/templates/high-risk-quarantine"
    ```
    """
    try:
        if not _integration_enabled:
            raise HTTPException(status_code=503, detail="Integration engine not available")
        
        policy = create_high_risk_quarantine_policy()
        _integration.add_admin_policy(policy)
        
        return {
            "status": "success",
            "policy_id": policy.policy_id,
            "message": "High-risk quarantine policy created",
            "policy": policy.to_dict(),
        }
    except Exception as e:
        logger.exception("Failed to create quarantine policy")
        raise HTTPException(status_code=500, detail=f"Failed to create policy: {str(e)}")


@router.post("/integration/policies/templates/contractor-restriction")
async def create_contractor_policy_endpoint():
    """
    Quick template: Restrict contractor access to office network only.
    
    Example:
    ```bash
    curl -X POST "http://localhost:8000/policy/integration/policies/templates/contractor-restriction"
    ```
    """
    try:
        if not _integration_enabled:
            raise HTTPException(status_code=503, detail="Integration engine not available")
        
        policy = create_contractor_policy()
        _integration.add_admin_policy(policy)
        
        return {
            "status": "success",
            "policy_id": policy.policy_id,
            "message": "Contractor restriction policy created",
            "policy": policy.to_dict(),
        }
    except Exception as e:
        logger.exception("Failed to create contractor policy")
        raise HTTPException(status_code=500, detail=f"Failed to create policy: {str(e)}")


@router.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "ok": True,
        "firewall": "operational",
        "huawei_iam": _huawei_iam_enabled,
        "grpc": _grpc_enabled,
        "integration": _integration_enabled,
        "metrics": _firewall_engine.get_metrics(),
    }
