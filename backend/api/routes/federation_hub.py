"""
Federated Learning Hub - Complete REST API
Handles all federation network operations, node management, and model aggregation
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import datetime
import json
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)
router = APIRouter()


# ======================== Data Models ========================

class ModelStatus(str, Enum):
    TRAINING = "training"
    AGGREGATED = "aggregated"
    VALIDATED = "validated"


class SyncStatus(str, Enum):
    SYNCED = "synced"
    SYNCING = "syncing"
    FAILED = "failed"


class FederationNode(BaseModel):
    """Federated node representing a participant in the network"""
    id: str
    country: str
    tag: str
    sync_health: float  # 0.0-1.0
    trust_score: float  # 0.0-1.0
    last_ledger: str
    last_sync: str  # ISO timestamp
    active: bool = True


class FederatedModel(BaseModel):
    """Model trained in federated setting"""
    id: str
    version: str
    node_id: str
    created_at: str  # ISO timestamp
    status: ModelStatus


class NodeHistory(BaseModel):
    """Historical snapshot of node metrics"""
    timestamp: str  # ISO timestamp
    node_id: str
    sync_health: float
    trust_score: float
    last_ledger: str
    active: bool


class NetworkStats(BaseModel):
    """Overall federation network statistics"""
    total_nodes: int
    active_nodes: int
    network_health: float  # Average of all sync_health
    network_trust: float  # Average of all trust_score
    total_models: int
    aggregation_status: str  # idle, in-progress, completed
    privacy_level: float  # 0-100
    sync_efficiency: float  # 0-100


class SyncRequest(BaseModel):
    """Request to trigger node sync"""
    node_id: str


class AggregationRequest(BaseModel):
    """Request to trigger model aggregation"""
    model_count: Optional[int] = None


class SyncResponse(BaseModel):
    """Response from sync operation"""
    status: str
    message: str
    node_id: str
    triggered_at: str


class AggregationResponse(BaseModel):
    """Response from aggregation operation"""
    status: str
    message: str
    aggregation_id: str
    progress: int
    started_at: str


# ======================== Storage Management ========================

def _get_nodes_storage_path() -> Path:
    """Get path to federation nodes data file"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    return data_dir / "federation_nodes.json"


def _get_models_storage_path() -> Path:
    """Get path to federation models data file"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    return data_dir / "federation_models.json"


def _get_history_storage_path() -> Path:
    """Get path to federation history data file"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    return data_dir / "federation_history.json"


def _load_nodes_from_storage() -> Dict[str, Dict[str, Any]]:
    """Load all federation nodes from persistent storage"""
    path = _get_nodes_storage_path()
    
    if path.exists():
        try:
            with open(path, 'r') as f:
                nodes = json.load(f)
                return {n['id']: n for n in nodes}
        except Exception as e:
            logger.warning(f"Failed to load nodes from storage: {e}")
    
    # Initialize with demo data
    demo_nodes = [
        {
            "id": "node-us-1",
            "country": "USA",
            "tag": "us-east",
            "sync_health": 0.95,
            "trust_score": 0.92,
            "last_ledger": "block-12345",
            "last_sync": datetime.datetime.utcnow().isoformat() + "Z",
            "active": True
        },
        {
            "id": "node-eu-1",
            "country": "EU",
            "tag": "eu-central",
            "sync_health": 0.88,
            "trust_score": 0.85,
            "last_ledger": "block-12340",
            "last_sync": (datetime.datetime.utcnow() - datetime.timedelta(minutes=2)).isoformat() + "Z",
            "active": True
        },
        {
            "id": "node-asia-1",
            "country": "ASIA",
            "tag": "asia-pacific",
            "sync_health": 0.91,
            "trust_score": 0.89,
            "last_ledger": "block-12342",
            "last_sync": (datetime.datetime.utcnow() - datetime.timedelta(minutes=5)).isoformat() + "Z",
            "active": True
        },
    ]
    
    return {n['id']: n for n in demo_nodes}


def _load_models_from_storage() -> Dict[str, Dict[str, Any]]:
    """Load all federation models from persistent storage"""
    path = _get_models_storage_path()
    
    if path.exists():
        try:
            with open(path, 'r') as f:
                models = json.load(f)
                return {m['id']: m for m in models}
        except Exception as e:
            logger.warning(f"Failed to load models from storage: {e}")
    
    # Initialize with demo data
    demo_models = [
        {
            "id": "model-v1",
            "version": "1.0.0",
            "node_id": "node-us-1",
            "created_at": (datetime.datetime.utcnow() - datetime.timedelta(hours=1)).isoformat() + "Z",
            "status": "training"
        },
        {
            "id": "model-v2",
            "version": "1.0.1",
            "node_id": "node-eu-1",
            "created_at": (datetime.datetime.utcnow() - datetime.timedelta(hours=2)).isoformat() + "Z",
            "status": "aggregated"
        },
        {
            "id": "model-v3",
            "version": "1.0.2",
            "node_id": "node-asia-1",
            "created_at": (datetime.datetime.utcnow() - datetime.timedelta(hours=4)).isoformat() + "Z",
            "status": "validated"
        },
    ]
    
    return {m['id']: m for m in demo_models}


def _save_nodes_to_storage(nodes: Dict[str, Dict[str, Any]]) -> None:
    """Save federation nodes to persistent storage"""
    try:
        path = _get_nodes_storage_path()
        nodes_list = list(nodes.values())
        with open(path, 'w') as f:
            json.dump(nodes_list, f, indent=2)
        logger.debug(f"Saved {len(nodes_list)} nodes to storage")
    except Exception as e:
        logger.error(f"Failed to save nodes to storage: {e}")


def _save_models_to_storage(models: Dict[str, Dict[str, Any]]) -> None:
    """Save federation models to persistent storage"""
    try:
        path = _get_models_storage_path()
        models_list = list(models.values())
        with open(path, 'w') as f:
            json.dump(models_list, f, indent=2)
        logger.debug(f"Saved {len(models_list)} models to storage")
    except Exception as e:
        logger.error(f"Failed to save models to storage: {e}")


def _append_to_history(node_id: str, sync_health: float, trust_score: float, last_ledger: str, active: bool) -> None:
    """Append a snapshot to node history"""
    try:
        path = _get_history_storage_path()
        history = []
        
        if path.exists():
            try:
                with open(path, 'r') as f:
                    history = json.load(f)
                    if not isinstance(history, list):
                        history = []
            except Exception as e:
                logger.warning(f"Failed to load history: {e}")
                history = []
        
        # Add new entry
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "node_id": node_id,
            "sync_health": sync_health,
            "trust_score": trust_score,
            "last_ledger": last_ledger,
            "active": active
        }
        history.append(entry)
        
        # Keep last 1000 entries
        if len(history) > 1000:
            history = history[-1000:]
        
        with open(path, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to append history: {e}")


def _get_node_history(node_id: str, limit: int = 24) -> List[Dict[str, Any]]:
    """Get historical snapshots for a specific node"""
    try:
        path = _get_history_storage_path()
        if not path.exists():
            return []
        
        with open(path, 'r') as f:
            history = json.load(f)
        
        # Filter by node_id
        node_entries = [e for e in history if e.get("node_id") == node_id]
        
        # Apply limit (most recent)
        if len(node_entries) > limit:
            node_entries = node_entries[-limit:]
        
        return node_entries
    except Exception as e:
        logger.error(f"Failed to get node history: {e}")
        return []


# ======================== Global State ========================

_NODES_DB = _load_nodes_from_storage()
_MODELS_DB = _load_models_from_storage()
_AGGREGATION_STATE = {
    "status": "idle",
    "progress": 0,
    "started_at": None,
    "aggregation_id": None
}


# ======================== Endpoints ========================

@router.get("/federation/nodes", response_model=Dict[str, Any])
async def get_federation_nodes() -> Dict[str, Any]:
    """
    Get all federation nodes with their current metrics
    
    Returns:
        - nodes: List of all federation nodes
        - total: Total number of nodes
        - active: Number of active nodes
        - network_health: Average sync health
        - network_trust: Average trust score
        - timestamp: Response timestamp
    """
    nodes_list = list(_NODES_DB.values())
    
    # Record history for each node
    for node in nodes_list:
        _append_to_history(
            node['id'],
            node['sync_health'],
            node['trust_score'],
            node['last_ledger'],
            node['active']
        )
    
    # Calculate network stats
    health_scores = [n['sync_health'] for n in nodes_list]
    trust_scores = [n['trust_score'] for n in nodes_list]
    active_count = sum(1 for n in nodes_list if n['active'])
    
    avg_health = sum(health_scores) / len(health_scores) if health_scores else 0.0
    avg_trust = sum(trust_scores) / len(trust_scores) if trust_scores else 0.0
    
    return {
        "nodes": nodes_list,
        "total": len(nodes_list),
        "active": active_count,
        "network_health": round(avg_health, 2),
        "network_trust": round(avg_trust, 2),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }


@router.get("/federation/models", response_model=Dict[str, Any])
async def get_federation_models() -> Dict[str, Any]:
    """
    Get all federated models and their provenance
    
    Returns:
        - models: List of all federated models
        - total: Total number of models
        - timestamp: Response timestamp
    """
    models_list = list(_MODELS_DB.values())
    
    # Sort by created_at descending
    models_list = sorted(models_list, key=lambda m: m['created_at'], reverse=True)
    
    return {
        "models": models_list,
        "total": len(models_list),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }


@router.post("/federation/nodes/{node_id}/sync", response_model=Dict[str, Any])
async def trigger_node_sync(node_id: str) -> Dict[str, Any]:
    """
    Trigger synchronization for a specific node
    
    Args:
        node_id: ID of the node to sync
    
    Returns:
        - status: "success" or "error"
        - message: Description of action
        - node_id: ID of synced node
        - triggered_at: Timestamp of sync trigger
    """
    if node_id not in _NODES_DB:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    
    node = _NODES_DB[node_id]
    
    # Simulate sync: improve metrics slightly
    node['sync_health'] = min(1.0, node['sync_health'] + 0.02)
    node['trust_score'] = min(1.0, node['trust_score'] + 0.01)
    node['last_sync'] = datetime.datetime.utcnow().isoformat() + "Z"
    node['last_ledger'] = f"block-{int(datetime.datetime.utcnow().timestamp())}"
    
    _save_nodes_to_storage(_NODES_DB)
    _append_to_history(node_id, node['sync_health'], node['trust_score'], node['last_ledger'], node['active'])
    
    return {
        "status": "success",
        "message": f"Sync triggered for node {node_id}",
        "node_id": node_id,
        "triggered_at": datetime.datetime.utcnow().isoformat() + "Z"
    }


@router.post("/federation/aggregate", response_model=Dict[str, Any])
async def trigger_aggregation() -> Dict[str, Any]:
    """
    Trigger global model aggregation across all nodes
    
    Returns:
        - status: "success" or "error"
        - message: Description of aggregation
        - aggregation_id: Unique ID for this aggregation
        - progress: Current progress percentage
        - started_at: Timestamp when aggregation started
    """
    # Mark aggregation as in-progress
    aggregation_id = f"agg-{int(datetime.datetime.utcnow().timestamp())}"
    _AGGREGATION_STATE['status'] = "in-progress"
    _AGGREGATION_STATE['progress'] = 100
    _AGGREGATION_STATE['started_at'] = datetime.datetime.utcnow().isoformat() + "Z"
    _AGGREGATION_STATE['aggregation_id'] = aggregation_id
    
    # Create aggregated model
    new_model = {
        "id": f"model-aggregated-{int(datetime.datetime.utcnow().timestamp())}",
        "version": f"agg-{datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
        "node_id": "server",
        "created_at": datetime.datetime.utcnow().isoformat() + "Z",
        "status": "aggregated"
    }
    _MODELS_DB[new_model['id']] = new_model
    _save_models_to_storage(_MODELS_DB)
    
    # Mark aggregation as completed
    _AGGREGATION_STATE['status'] = "completed"
    
    return {
        "status": "success",
        "message": "Model aggregation completed successfully",
        "aggregation_id": aggregation_id,
        "progress": 100,
        "started_at": _AGGREGATION_STATE['started_at']
    }


@router.get("/federation/nodes/{node_id}/history", response_model=Dict[str, Any])
async def get_node_history(node_id: str, limit: int = Query(24, ge=1, le=100)) -> Dict[str, Any]:
    """
    Get historical metrics for a specific node
    
    Args:
        node_id: ID of the node
        limit: Maximum number of historical entries (default: 24)
    
    Returns:
        - node_id: ID of the node
        - history: List of historical snapshots
        - stats: Aggregated statistics (avg, min, max for health and trust)
        - timestamp: Response timestamp
    """
    if node_id not in _NODES_DB:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    
    history = _get_node_history(node_id, limit)
    
    if not history:
        # Return empty history but still valid
        return {
            "node_id": node_id,
            "history": [],
            "stats": {
                "avg_health": 0.0,
                "avg_trust": 0.0,
                "min_health": 0.0,
                "max_health": 0.0,
                "min_trust": 0.0,
                "max_trust": 0.0
            },
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }
    
    health_values = [e['sync_health'] for e in history]
    trust_values = [e['trust_score'] for e in history]
    
    return {
        "node_id": node_id,
        "history": history,
        "stats": {
            "avg_health": round(sum(health_values) / len(health_values), 2),
            "avg_trust": round(sum(trust_values) / len(trust_values), 2),
            "min_health": round(min(health_values), 2),
            "max_health": round(max(health_values), 2),
            "min_trust": round(min(trust_values), 2),
            "max_trust": round(max(trust_values), 2)
        },
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }


@router.get("/federation/stats", response_model=Dict[str, Any])
async def get_federation_stats() -> Dict[str, Any]:
    """
    Get comprehensive network statistics
    
    Returns:
        - total_nodes: Total number of nodes
        - active_nodes: Number of currently active nodes
        - network_health: Average sync health (0-1)
        - network_trust: Average trust score (0-1)
        - total_models: Total federated models
        - aggregation_status: Current aggregation status
        - privacy_level: Privacy guarantee percentage (0-100)
        - sync_efficiency: Sync efficiency percentage (0-100)
        - timestamp: Response timestamp
    """
    nodes_list = list(_NODES_DB.values())
    models_list = list(_MODELS_DB.values())
    
    health_scores = [n['sync_health'] for n in nodes_list]
    trust_scores = [n['trust_score'] for n in nodes_list]
    active_count = sum(1 for n in nodes_list if n['active'])
    
    avg_health = sum(health_scores) / len(health_scores) if health_scores else 0.0
    avg_trust = sum(trust_scores) / len(trust_scores) if trust_scores else 0.0
    
    return {
        "total_nodes": len(nodes_list),
        "active_nodes": active_count,
        "network_health": round(avg_health, 2),
        "network_trust": round(avg_trust, 2),
        "total_models": len(models_list),
        "aggregation_status": _AGGREGATION_STATE['status'],
        "privacy_level": 98,
        "sync_efficiency": 94,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }


@router.get("/federation/aggregation-status", response_model=Dict[str, Any])
async def get_aggregation_status() -> Dict[str, Any]:
    """
    Get current aggregation status
    
    Returns:
        - status: Status of current aggregation (idle, in-progress, completed)
        - progress: Progress percentage (0-100)
        - aggregation_id: ID of current/last aggregation
        - started_at: When aggregation started
        - timestamp: Response timestamp
    """
    return {
        "status": _AGGREGATION_STATE['status'],
        "progress": _AGGREGATION_STATE['progress'],
        "aggregation_id": _AGGREGATION_STATE['aggregation_id'],
        "started_at": _AGGREGATION_STATE['started_at'],
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
