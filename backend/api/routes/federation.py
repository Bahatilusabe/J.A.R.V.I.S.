from fastapi import APIRouter, HTTPException, Query, Header, Depends
from typing import Dict, Any, List, Optional, Tuple
import logging
import os
import time
import datetime
import json
import threading
from pathlib import Path

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

router = APIRouter()


def _verify_admin_access(x_admin_token: Optional[str] = Header(None)) -> bool:
    """Verify admin access via X-Admin-Token header or Bearer token.
    
    This is a simple RBAC check. In production, this would validate against
    a real auth service or JWT token with role claims.
    """
    # Check for admin token (can be configured via env variable)
    admin_token = os.getenv('FEDERATION_ADMIN_TOKEN', 'admin-secret')
    
    if x_admin_token and x_admin_token == admin_token:
        return True
    
    # Fallback: no token means read-only (can be made stricter)
    logger.debug("No valid admin token provided")
    return False

# Try to import real federation components
try:
    from federation.node_agent import NodeSyncManager, MindSporeFederatedClient
    HAS_NODE_AGENT = True
except ImportError:
    HAS_NODE_AGENT = False
    NodeSyncManager = None
    MindSporeFederatedClient = None

try:
    from federation.federated_training import MindSporeFederatedServer
    HAS_FEDERATED_TRAINING = True
except ImportError:
    HAS_FEDERATED_TRAINING = False
    MindSporeFederatedServer = None

# Registry of active node sync managers keyed by node_id
_active_managers: Dict[str, Any] = {}
_manager_lock = threading.Lock()

# Demo registry as fallback when real managers not available
_node_registry: Dict[str, Dict[str, Any]] = {}
_models_registry: Dict[str, Dict[str, Any]] = {}
_server_instance: Optional[Any] = None  # Global federated server instance


def _ensure_server_instance():
    """Lazy-initialize the global federated server if available."""
    global _server_instance
    if _server_instance is None and HAS_FEDERATED_TRAINING:
        try:
            _server_instance = MindSporeFederatedServer()
            logger.info("Initialized global MindSporeFederatedServer instance")
        except Exception as e:
            logger.warning("Failed to initialize MindSporeFederatedServer: %s", e)


def _node_history_path() -> Path:
    """Get the path to the node history file."""
    history_dir = Path(".backups")
    history_dir.mkdir(exist_ok=True)
    return history_dir / "node_history.json"


def _append_node_history(node_status: Dict[str, Any]) -> None:
    """Append a node status snapshot to the node history file.
    
    Each entry includes timestamp, node_id, sync_health, trust_score, last_ledger.
    """
    try:
        path = _node_history_path()
        history = []
        
        # Load existing history
        if path.exists():
            try:
                with open(path, 'r') as f:
                    history = json.load(f)
                if not isinstance(history, list):
                    history = []
            except Exception as e:
                logger.warning("Failed to load node history: %s; starting fresh", e)
                history = []
        
        # Append new entry
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "node_id": node_status.get("id", "unknown"),
            "sync_health": node_status.get("sync_health", 0.0),
            "trust_score": node_status.get("trust_score", 0.0),
            "last_ledger": node_status.get("last_ledger", ""),
            "active": node_status.get("active", False),
        }
        history.append(entry)
        
        # Keep only last 1000 entries to avoid unbounded growth
        if len(history) > 1000:
            history = history[-1000:]
        
        # Write back
        with open(path, 'w') as f:
            json.dump(history, f, indent=2)
        logger.debug("Persisted node status for %s", node_status.get("id"))
    except Exception as e:
        logger.error("Failed to append to node history: %s", e)


def _get_node_history(node_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieve historical snapshots for a specific node.
    
    Returns a list of status snapshots ordered by timestamp (oldest first).
    """
    try:
        path = _node_history_path()
        if not path.exists():
            return []
        
        with open(path, 'r') as f:
            history = json.load(f)
        
        # Filter by node_id
        node_entries = [e for e in history if e.get("node_id") == node_id]
        
        # Apply limit (most recent entries)
        if limit and len(node_entries) > limit:
            node_entries = node_entries[-limit:]
        
        return node_entries
    except Exception as e:
        logger.error("Failed to retrieve node history for %s: %s", node_id, e)
        return []


def _register_or_get_manager(node_id: str, server_url: Optional[str] = None, interval: int = 30) -> Optional[Any]:
    """Get or create a NodeSyncManager for the given node_id.
    
    Uses a global registry to avoid spawning multiple managers for the same node.
    """
    if not HAS_NODE_AGENT:
        return None
    
    with _manager_lock:
        if node_id in _active_managers:
            return _active_managers[node_id]
        
        try:
            mgr = NodeSyncManager(node_id=node_id, server_url=server_url, interval=interval)
            mgr.start()
            _active_managers[node_id] = mgr
            logger.info("Started NodeSyncManager for node %s", node_id)
            return mgr
        except Exception as e:
            logger.error("Failed to create NodeSyncManager for %s: %s", node_id, e)
            return None


def _extract_manager_metrics(manager: Any) -> Dict[str, Any]:
    """Extract sync health and related metrics from an active NodeSyncManager.
    
    This simulates real metrics based on manager state. In production, this would
    query actual telemetry from the manager's sync history.
    """
    metrics = {
        "sync_health": 0.9,  # Simulated: would be tracked by manager
        "trust_score": 0.85,  # Simulated: would be computed from sync reliability
        "last_sync": datetime.datetime.utcnow().isoformat() + "Z",
        "sync_count": 0,  # Would be tracked by manager
    }
    
    # If manager has internal state we can inspect
    if hasattr(manager, '_thread') and manager._thread is not None:
        metrics["active"] = manager._thread.is_alive()
    if hasattr(manager, 'node_id'):
        metrics["node_id"] = manager.node_id
    
    return metrics


def _register_demo_nodes():
    """Populate with demo federated nodes for testing (fallback when real managers unavailable)."""
    if _node_registry:
        return  # already populated
    nodes = [
        {"id": "node-us-1", "country": "USA", "tag": "us-east", "sync_health": 0.95, "trust_score": 0.92, "last_ledger": "block-12345"},
        {"id": "node-eu-1", "country": "EU", "tag": "eu-central", "sync_health": 0.88, "trust_score": 0.85, "last_ledger": "block-12340"},
        {"id": "node-asia-1", "country": "ASIA", "tag": "asia-pacific", "sync_health": 0.91, "trust_score": 0.89, "last_ledger": "block-12342"},
    ]
    models = [
        {"id": "model-v1", "version": "1.0.0", "node_id": "node-us-1", "created_at": datetime.datetime.utcnow().isoformat() + "Z", "status": "training"},
        {"id": "model-v2", "version": "1.0.1", "node_id": "node-eu-1", "created_at": (datetime.datetime.utcnow() - datetime.timedelta(hours=2)).isoformat() + "Z", "status": "aggregated"},
        {"id": "model-v3", "version": "1.0.2", "node_id": "node-asia-1", "created_at": (datetime.datetime.utcnow() - datetime.timedelta(hours=4)).isoformat() + "Z", "status": "validated"},
    ]
    for n in nodes:
        _node_registry[n["id"]] = {**n, "last_sync": datetime.datetime.utcnow().isoformat() + "Z"}
    for m in models:
        _models_registry[m["id"]] = m


@router.get("/status")
def status() -> Dict[str, Any]:
    """Return federated node status including sync health, trust score, last ledger entry.

    If real NodeSyncManager instances are available, queries them for live sync data.
    Otherwise falls back to demo registry.
    """
    nodes_list = []
    
    # Try to use real managers if available
    if HAS_NODE_AGENT and _active_managers:
        with _manager_lock:
            for node_id, manager in list(_active_managers.items()):
                try:
                    metrics = _extract_manager_metrics(manager)
                    nodes_list.append({
                        "id": node_id,
                        "country": "FEDERATED",  # Would be retrieved from config
                        "tag": "real-node",
                        "sync_health": metrics.get("sync_health", 0.0),
                        "trust_score": metrics.get("trust_score", 0.0),
                        "last_ledger": f"ledger-{int(time.time())}",
                        "last_sync": metrics.get("last_sync", ""),
                        "active": metrics.get("active", False),
                    })
                except Exception as e:
                    logger.error("Failed to extract metrics from manager %s: %s", node_id, e)
    
    # Fallback to demo registry
    if not nodes_list:
        _register_demo_nodes()
        for node_id, node_data in _node_registry.items():
            nodes_list.append({
                "id": node_id,
                "country": node_data.get("country", "unknown"),
                "tag": node_data.get("tag", ""),
                "sync_health": float(node_data.get("sync_health", 0.0)),
                "trust_score": float(node_data.get("trust_score", 0.0)),
                "last_ledger": node_data.get("last_ledger", ""),
                "last_sync": node_data.get("last_sync", ""),
            })
    
    # Persist node history snapshots
    for node in nodes_list:
        _append_node_history(node)
    
    # compute overall network stats
    health_scores = [n.get("sync_health", 0.0) for n in nodes_list]
    trust_scores = [n.get("trust_score", 0.0) for n in nodes_list]
    avg_health = sum(health_scores) / len(health_scores) if health_scores else 0.0
    avg_trust = sum(trust_scores) / len(trust_scores) if trust_scores else 0.0

    return {
        "ok": True,
        "nodes": nodes_list,
        "network_health": float(avg_health),
        "network_trust": float(avg_trust),
        "total_nodes": len(nodes_list),
        "using_real_data": HAS_NODE_AGENT and bool(_active_managers),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }


@router.get("/models")
def models() -> Dict[str, Any]:
    """Return federated model provenance and metadata.

    If a real MindSporeFederatedServer is available, attempts to query aggregated weights.
    Otherwise falls back to demo registry.
    """
    _ensure_server_instance()
    
    models_list = []
    latest_model = None
    
    # Try to use real server if available
    if HAS_FEDERATED_TRAINING and _server_instance is not None:
        try:
            # Attempt to fetch aggregated weights from server
            aggregated = _server_instance.secure_aggregate(mask=False)
            if aggregated:
                latest_model = {
                    "id": "agg-latest",
                    "version": "aggregated",
                    "node_id": "server",
                    "created_at": datetime.datetime.utcnow().isoformat() + "Z",
                    "status": "aggregated",
                }
                models_list.append(latest_model)
                logger.info("Retrieved aggregated model from MindSporeFederatedServer")
        except Exception as e:
            logger.warning("Failed to aggregate from server: %s; falling back to demo", e)
    
    # Fallback to demo registry
    if not models_list:
        _register_demo_nodes()
        for model_id, model_data in _models_registry.items():
            models_list.append({
                "id": model_id,
                "version": model_data.get("version", "unknown"),
                "node_id": model_data.get("node_id", ""),
                "created_at": model_data.get("created_at", ""),
                "status": model_data.get("status", "unknown"),  # training, aggregated, validated
            })
        
        # find latest model
        if models_list:
            latest_model = sorted(models_list, key=lambda m: m.get("created_at", ""), reverse=True)[0]

    return {
        "ok": True,
        "models": models_list,
        "latest_model": latest_model,
        "total_models": len(models_list),
        "using_real_data": HAS_FEDERATED_TRAINING and _server_instance is not None,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }


@router.get("/nodes/{node_id}")
def node_detail(node_id: str, limit: int = Query(100, ge=1, le=1000)) -> Dict[str, Any]:
    """Return detailed status history for a specific federated node.
    
    Returns historical snapshots of the node's sync_health, trust_score, and ledger status,
    ordered by timestamp (oldest first).
    """
    history = _get_node_history(node_id, limit=limit)
    
    if not history:
        raise HTTPException(
            status_code=404,
            detail=f"No history found for node {node_id}"
        )
    
    # Compute trend statistics
    health_values = [e.get("sync_health", 0.0) for e in history]
    trust_values = [e.get("trust_score", 0.0) for e in history]
    
    avg_health = sum(health_values) / len(health_values) if health_values else 0.0
    avg_trust = sum(trust_values) / len(trust_values) if trust_values else 0.0
    min_health = min(health_values) if health_values else 0.0
    max_health = max(health_values) if health_values else 0.0
    min_trust = min(trust_values) if trust_values else 0.0
    max_trust = max(trust_values) if trust_values else 0.0
    
    return {
        "ok": True,
        "node_id": node_id,
        "history": history,
        "total_entries": len(history),
        "stats": {
            "avg_health": float(avg_health),
            "avg_trust": float(avg_trust),
            "min_health": float(min_health),
            "max_health": float(max_health),
            "min_trust": float(min_trust),
            "max_trust": float(max_trust),
        },
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }


@router.post("/nodes/{node_id}/sync")
def trigger_node_sync(node_id: str, x_admin_token: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Manually trigger a sync for a specific node.
    
    Requires admin authentication via X-Admin-Token header.
    If a real NodeSyncManager exists for this node, triggers _do_sync_once().
    Otherwise returns a simulated success.
    """
    # Check admin access
    if not _verify_admin_access(x_admin_token):
        logger.warning("Unauthorized sync request for node %s", node_id)
        raise HTTPException(
            status_code=403,
            detail="Admin token required for sync operations"
        )
    
    # Check if a manager exists for this node
    manager = None
    with _manager_lock:
        manager = _active_managers.get(node_id)
    
    if manager is not None and HAS_NODE_AGENT:
        try:
            # Call the manager's sync method
            if hasattr(manager, '_do_sync_once'):
                manager._do_sync_once()
                logger.info("Triggered sync for node %s", node_id)
                return {
                    "ok": True,
                    "action": "sync",
                    "node_id": node_id,
                    "status": "triggered",
                    "message": f"Sync triggered for node {node_id}",
                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                }
        except Exception as e:
            logger.error("Failed to trigger sync for node %s: %s", node_id, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to trigger sync: {str(e)}"
            )
    
    # Fallback: simulated success
    return {
        "ok": True,
        "action": "sync",
        "node_id": node_id,
        "status": "triggered",
        "message": f"Sync triggered for node {node_id} (simulated)",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }


@router.post("/aggregate")
def trigger_aggregate(x_admin_token: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Manually trigger a global model aggregation.
    
    Requires admin authentication via X-Admin-Token header.
    If a real MindSporeFederatedServer exists, calls secure_aggregate().
    Otherwise returns a simulated success.
    """
    # Check admin access
    if not _verify_admin_access(x_admin_token):
        logger.warning("Unauthorized aggregation request")
        raise HTTPException(
            status_code=403,
            detail="Admin token required for aggregation operations"
        )
    
    _ensure_server_instance()
    
    if _server_instance is not None and HAS_FEDERATED_TRAINING:
        try:
            # Call the server's aggregation method
            if hasattr(_server_instance, 'secure_aggregate'):
                result = _server_instance.secure_aggregate(mask=True)
                logger.info("Triggered model aggregation; result keys: %s", list(result.keys()) if result else "None")
                return {
                    "ok": True,
                    "action": "aggregate",
                    "status": "completed",
                    "message": "Model aggregation completed",
                    "result_keys": list(result.keys()) if result else [],
                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                }
        except Exception as e:
            logger.error("Failed to trigger aggregation: %s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to aggregate: {str(e)}"
            )
    
    # Fallback: simulated success
    return {
        "ok": True,
        "action": "aggregate",
        "status": "completed",
        "message": "Model aggregation completed (simulated)",
        "result_keys": ["simulated_model"],
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }
