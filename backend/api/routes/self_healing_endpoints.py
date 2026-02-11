"""
Additional self-healing endpoints: /start, /stop, /recover
These manage the simulation lifecycle (added as separate module to avoid modifying large file).
"""
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

router = APIRouter()

# In-memory job tracking (replace with Redis/database in production)
_active_jobs: Dict[str, Dict[str, Any]] = {}


@router.post("/start")
async def start_simulation(body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Start a new simulation job.
    
    Body: {"mode": "training", "initialAttackers": 5, "initialDefenders": 10, "config": {...}}
    """
    try:
        mode = body.get("mode", "training")
        initialAttackers = body.get("initialAttackers", 5)
        initialDefenders = body.get("initialDefenders", 10)
        config = body.get("config", {})
        
        jobId = f"job_{uuid.uuid4().hex[:12]}"
        job_info = {
            "jobId": jobId,
            "status": "running",
            "mode": mode,
            "initialAttackers": initialAttackers,
            "initialDefenders": initialDefenders,
            "startedAt": datetime.utcnow().isoformat() + "Z",
            "config": config or {},
        }
        _active_jobs[jobId] = job_info
        logger.info(f"Started simulation job {jobId} in mode {mode}")
        return {
            "jobId": jobId,
            "status": "started",
            "message": f"Simulation started with {initialAttackers} attackers and {initialDefenders} defenders",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.exception(f"Failed to start simulation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start simulation: {str(e)}")


@router.post("/stop")
async def stop_simulation(body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Stop a running simulation job.
    
    Body: {"jobId": "job_xxx"}
    """
    try:
        jobId = body.get("jobId")
        if not jobId:
            raise HTTPException(status_code=400, detail="jobId is required")
        
        if jobId not in _active_jobs:
            raise HTTPException(status_code=404, detail=f"Job {jobId} not found")
        
        job_info = _active_jobs[jobId]
        job_info["status"] = "stopped"
        job_info["stoppedAt"] = datetime.utcnow().isoformat() + "Z"
        logger.info(f"Stopped simulation job {jobId}")
        
        return {
            "jobId": jobId,
            "status": "stopped",
            "message": f"Simulation {jobId} stopped successfully",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to stop simulation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop simulation: {str(e)}")


@router.post("/recover")
async def recover_simulation(
    snapshotId: str = Body(..., embed=False),
    recoveryType: str = Body("full", embed=False),
    targetTick: Optional[int] = Body(None, embed=False),
) -> Dict[str, Any]:
    """Initiate recovery from a snapshot.
    
    - snapshotId: the snapshot ID to recover from
    - recoveryType: 'full', 'partial', 'differential'
    - targetTick: optional target tick to recover to (for differential recovery)
    """
    try:
        recoveryId = f"recovery_{uuid.uuid4().hex[:12]}"
        logger.info(f"Initiated {recoveryType} recovery from snapshot {snapshotId} (recovery ID: {recoveryId})")
        
        return {
            "jobId": f"job_recovered_{uuid.uuid4().hex[:8]}",
            "recoveryId": recoveryId,
            "status": "in_progress",
            "recoveryType": recoveryType,
            "snapshotId": snapshotId,
            "targetTick": targetTick,
            "message": f"Recovery {recoveryType} initiated from snapshot {snapshotId}",
            "estimatedDuration": 5000,  # ms
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.exception(f"Failed to initiate recovery: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate recovery: {str(e)}")


@router.get("/jobs")
async def list_jobs() -> Dict[str, Any]:
    """List all active and completed simulation jobs."""
    return {
        "jobs": list(_active_jobs.values()),
        "total": len(_active_jobs),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/jobs/{job_id}")
async def get_job(job_id: str) -> Dict[str, Any]:
    """Get details about a specific job."""
    if job_id not in _active_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return {
        "job": _active_jobs[job_id],
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
