"""
Deception Grid API Routes

Endpoints for managing honeypots, decoys, and deception technologies.
Routes interact with backend/core/deception modules.

Endpoints:
- POST /honeypots - Create honeypot
- GET /honeypots - List all honeypots
- GET /honeypots/{id} - Get honeypot details
- DELETE /honeypots/{id} - Stop honeypot
- GET /honeypots/{id}/interactions - Get recorded interactions
- POST /decoys - Deploy decoy resource
- GET /decoys - List active decoys
- GET /honeypots/{id}/stats - Get honeypot statistics

Author: J.A.R.V.I.S. Deception Team
Date: December 2025
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
import time
import uuid
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

router = APIRouter()

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class HoneypotRequest(BaseModel):
    """Request model for honeypot creation"""

    name: str = Field(..., description="Honeypot instance name")
    service_type: str = Field(..., description="Service type (SSH, HTTP, FTP, SMTP, etc.)")
    port: int = Field(default=0, description="Port to monitor (0 = auto)")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Optional configuration")


class HoneypotResponse(BaseModel):
    """Response model for honeypot details"""

    honeypot_id: str
    name: str
    service_type: str
    port: int
    status: str  # running, stopped, error
    created_at: str
    interactions_count: int


class InteractionEvent(BaseModel):
    """Recorded interaction event"""

    timestamp: str
    client_ip: Optional[str]
    client_port: Optional[int]
    payload_summary: str
    notes: Optional[str]


class DecoyRequest(BaseModel):
    """Request model for decoy deployment"""

    decoy_type: str = Field(..., description="Type of decoy (file, network_share, credential, etc.)")
    location: str = Field(..., description="Deployment location/path")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Decoy configuration")


class DecoyResponse(BaseModel):
    """Response model for decoy details"""

    decoy_id: str
    decoy_type: str
    location: str
    status: str  # active, inactive, triggered
    created_at: str
    interactions: int


class DeceptionStatsResponse(BaseModel):
    """Response model for deception statistics"""
    totalHoneypots: int
    activeHoneypots: int
    totalInteractions: int
    threatLevel: str
    avgResponseTime: int
    decoyModelsDeployed: int


class InteractionEventResponse(BaseModel):
    """Response model for interaction events"""
    id: str
    honeypotId: str
    honeypotName: str
    timestamp: int
    clientIp: str
    clientPort: int
    payloadSummary: str
    severity: str
    notes: Optional[str]


# ============================================================================
# IN-MEMORY STORAGE (for dev/testing)
# ============================================================================

_honeypots: Dict[str, Dict[str, Any]] = {}
_decoys: Dict[str, Dict[str, Any]] = {}
_interactions: List[Dict[str, Any]] = []


# ============================================================================
# HONEYPOT ENDPOINTS
# ============================================================================


@router.post("/honeypots", response_model=HoneypotResponse)
async def create_honeypot(request: HoneypotRequest):
    """Create a new honeypot instance.

    Honeypots are used to detect and analyze attack patterns
    by simulating vulnerable services.
    """
    honeypot_id = str(uuid.uuid4())
    honeypot_data = {
        "id": honeypot_id,
        "name": request.name,
        "service_type": request.service_type,
        "port": request.port,
        "status": "running",
        "created_at": datetime.utcnow().isoformat(),
        "config": request.config or {},
        "interactions": [],
    }

    _honeypots[honeypot_id] = honeypot_data

    logger.info(f"Honeypot created: {honeypot_id} ({request.name})")

    return HoneypotResponse(
        honeypot_id=honeypot_id,
        name=request.name,
        service_type=request.service_type,
        port=request.port,
        status="running",
        created_at=honeypot_data["created_at"],
        interactions_count=0,
    )


@router.get("/honeypots", response_model=List[HoneypotResponse])
async def list_honeypots():
    """List all active honeypots."""
    result = []
    for honeypot_id, data in _honeypots.items():
        result.append(
            HoneypotResponse(
                honeypot_id=honeypot_id,
                name=data["name"],
                service_type=data["service_type"],
                port=data["port"],
                status=data["status"],
                created_at=data["created_at"],
                interactions_count=len(data.get("interactions", [])),
            )
        )
    return result


@router.get("/honeypots/{honeypot_id}", response_model=HoneypotResponse)
async def get_honeypot(honeypot_id: str):
    """Get details of a specific honeypot."""
    if honeypot_id not in _honeypots:
        raise HTTPException(status_code=404, detail="Honeypot not found")

    data = _honeypots[honeypot_id]
    return HoneypotResponse(
        honeypot_id=honeypot_id,
        name=data["name"],
        service_type=data["service_type"],
        port=data["port"],
        status=data["status"],
        created_at=data["created_at"],
        interactions_count=len(data.get("interactions", [])),
    )


@router.delete("/honeypots/{honeypot_id}")
async def stop_honeypot(honeypot_id: str):
    """Stop and remove a honeypot instance."""
    if honeypot_id not in _honeypots:
        raise HTTPException(status_code=404, detail="Honeypot not found")

    data = _honeypots.pop(honeypot_id)
    logger.info(f"Honeypot stopped: {honeypot_id}")

    return {
        "status": "stopped",
        "honeypot_id": honeypot_id,
        "interactions_recorded": len(data.get("interactions", [])),
    }


@router.get("/honeypots/{honeypot_id}/interactions", response_model=List[InteractionEvent])
async def get_honeypot_interactions(honeypot_id: str, limit: int = Query(100, ge=1, le=1000)):
    """Get recorded interaction events for a honeypot."""
    if honeypot_id not in _honeypots:
        raise HTTPException(status_code=404, detail="Honeypot not found")

    data = _honeypots[honeypot_id]
    interactions = data.get("interactions", [])

    # Return last 'limit' interactions
    return interactions[-limit:]


@router.get("/honeypots/{honeypot_id}/stats")
async def get_honeypot_stats(honeypot_id: str):
    """Get statistics for a honeypot."""
    if honeypot_id not in _honeypots:
        raise HTTPException(status_code=404, detail="Honeypot not found")

    data = _honeypots[honeypot_id]
    interactions = data.get("interactions", [])

    return {
        "honeypot_id": honeypot_id,
        "name": data["name"],
        "total_interactions": len(interactions),
        "unique_clients": len(set(i.get("client_ip") for i in interactions if "client_ip" in i)),
        "uptime_seconds": (datetime.utcnow() - datetime.fromisoformat(data["created_at"])).total_seconds(),
    }


# ============================================================================
# DECOY ENDPOINTS
# ============================================================================


@router.post("/decoys", response_model=DecoyResponse)
async def deploy_decoy(request: DecoyRequest):
    """Deploy a new decoy resource.

    Decoys are fake resources (files, credentials, network shares)
    used to trigger and log attack attempts.
    """
    decoy_id = str(uuid.uuid4())
    decoy_data = {
        "id": decoy_id,
        "type": request.decoy_type,
        "location": request.location,
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "config": request.config or {},
        "interactions": 0,
    }

    _decoys[decoy_id] = decoy_data

    logger.info(f"Decoy deployed: {decoy_id} ({request.decoy_type})")

    return DecoyResponse(
        decoy_id=decoy_id,
        decoy_type=request.decoy_type,
        location=request.location,
        status="active",
        created_at=decoy_data["created_at"],
        interactions=0,
    )


@router.get("/decoys", response_model=List[DecoyResponse])
async def list_decoys():
    """List all active decoys."""
    result = []
    for decoy_id, data in _decoys.items():
        result.append(
            DecoyResponse(
                decoy_id=decoy_id,
                decoy_type=data["type"],
                location=data["location"],
                status=data["status"],
                created_at=data["created_at"],
                interactions=data.get("interactions", 0),
            )
        )
    return result


@router.get("/decoys/{decoy_id}", response_model=DecoyResponse)
async def get_decoy(decoy_id: str):
    """Get details of a specific decoy."""
    if decoy_id not in _decoys:
        raise HTTPException(status_code=404, detail="Decoy not found")

    data = _decoys[decoy_id]
    return DecoyResponse(
        decoy_id=decoy_id,
        decoy_type=data["type"],
        location=data["location"],
        status=data["status"],
        created_at=data["created_at"],
        interactions=data.get("interactions", 0),
    )


@router.delete("/decoys/{decoy_id}")
async def remove_decoy(decoy_id: str):
    """Remove a decoy resource."""
    if decoy_id not in _decoys:
        raise HTTPException(status_code=404, detail="Decoy not found")

    data = _decoys.pop(decoy_id)
    logger.info(f"Decoy removed: {decoy_id}")

    return {
        "status": "removed",
        "decoy_id": decoy_id,
        "interactions_triggered": data.get("interactions", 0),
    }


# ============================================================================
# ADMIN/STATUS ENDPOINTS
# ============================================================================


@router.get("/deception/status")
async def deception_system_status():
    """Get overall deception system status."""
    return {
        "status": "active",
        "active_honeypots": len(_honeypots),
        "active_decoys": len(_decoys),
        "total_interactions": sum(len(h.get("interactions", [])) for h in _honeypots.values())
        + sum(d.get("interactions", 0) for d in _decoys.values()),
    }


@router.get("/events", response_model=List[InteractionEventResponse])
async def list_interaction_events(honeypot_id: Optional[str] = None):
    """
    List all interaction events, optionally filtered by honeypot.
    
    Args:
        honeypot_id: Optional honeypot ID to filter events by
        
    Returns:
        List of interaction events across all honeypots
    """
    events = []
    
    # Aggregate events from all honeypots
    for hpot_id, hpot_data in _honeypots.items():
        # Filter by honeypot_id if specified
        if honeypot_id and hpot_id != honeypot_id:
            continue
            
        honeypot_name = hpot_data.get("name", f"Honeypot-{hpot_id}")
        interactions = hpot_data.get("interactions", [])
        
        for interaction in interactions:
            event = InteractionEventResponse(
                id=interaction.get("id", str(uuid4())),
                honeypotId=hpot_id,
                honeypotName=honeypot_name,
                timestamp=interaction.get("timestamp", int(time.time() * 1000)),
                clientIp=interaction.get("client_ip", "unknown"),
                clientPort=interaction.get("client_port", 0),
                payloadSummary=interaction.get("payload", ""),
                severity=interaction.get("severity", "low"),
                notes=interaction.get("notes"),
            )
            events.append(event)
    
    return events


@router.get("/stats", response_model=DeceptionStatsResponse)
async def get_deception_stats():
    """
    Get system-wide deception statistics.
    
    Returns:
        Aggregated statistics for the deception system
    """
    # Calculate basic counts
    total_honeypots = len(_honeypots)
    active_honeypots = sum(1 for h in _honeypots.values() if h.get("status") == "running")
    total_interactions = sum(len(h.get("interactions", [])) for h in _honeypots.values())
    decoy_models_deployed = len(_decoys)
    
    # Determine threat level from honeypots
    threat_levels = []
    for honeypot in _honeypots.values():
        threat = honeypot.get("threat_level", "low")
        threat_levels.append(threat)
    
    # Map threat level to priority for max determination
    threat_priority = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    threat_level = max(
        threat_levels,
        key=lambda x: threat_priority.get(x, 0),
        default="low"
    ) if threat_levels else "low"
    
    # Calculate average response time (simulated, in milliseconds)
    # In production, this would be from actual metrics
    avg_response_time = 250 if total_interactions > 0 else 0
    
    return DeceptionStatsResponse(
        totalHoneypots=total_honeypots,
        activeHoneypots=active_honeypots,
        totalInteractions=total_interactions,
        threatLevel=threat_level,
        avgResponseTime=avg_response_time,
        decoyModelsDeployed=decoy_models_deployed,
    )
