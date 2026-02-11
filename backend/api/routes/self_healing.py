from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, Any, List, Optional
import logging
import datetime
import os
import json

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

router = APIRouter()

# Import RL-based self-healing service
try:
    from backend.core.self_healing.rl_service import selfhealing_service
    _RL_SERVICE_AVAILABLE = True
except ImportError:
    _RL_SERVICE_AVAILABLE = False
    logger.warning("RL-based self-healing service not available")


@router.get("/metrics")
def metrics(episodes: int = Query(3, ge=1, le=20)) -> Dict[str, Any]:
    """Return simple RL metrics gathered from the MARL trainer.

    - episodes: how many evaluation episodes to average for the metric.
    """
    try:
        from backend.core.self_healing.marl_agent import MultiAgentEnv, MARLTrainer
    except Exception as e:
        logger.exception("Failed to import MARL trainer: %s", e)
        raise HTTPException(status_code=500, detail="marl_agent unavailable")

    env = MultiAgentEnv(num_agents=3, obs_size=4, action_size=3, max_steps=30)
    trainer = MARLTrainer(env, backend="emulated")

    try:
        eval_scores = trainer.evaluate(episodes=episodes)
    except Exception:
        logger.exception("MARL evaluation failed; falling back to single-episode run")
        eval_scores = trainer.evaluate(episodes=1)

    # compute a simple normalized confidence in [0,1]
    try:
        total = sum(eval_scores.values())
        max_possible = env.num_agents * env.max_steps
        confidence = min(1.0, float(total) / float(max_possible)) if max_possible > 0 else 0.0
    except Exception:
        confidence = 0.0

    # per-agent confidence (normalize by max_steps) and persist metrics history
    per_agent_conf: Dict[str, float] = {}
    try:
        for k, v in eval_scores.items():
            per_agent_conf[k] = float(v) / float(env.max_steps) if env.max_steps > 0 else 0.0
    except Exception:
        per_agent_conf = {k: 0.0 for k in eval_scores.keys()}

    # model id for this evaluator (env var override)
    model_id = os.environ.get("SELF_HEALING_MODEL_ID", "emulated-v1")

    # persist metrics to .backups/self_healing_metrics.json
    metrics_store_dir = os.environ.get("SELF_HEALING_METRICS_DIR", ".backups")
    os.makedirs(metrics_store_dir, exist_ok=True)
    metrics_path = os.path.join(metrics_store_dir, "self_healing_metrics.json")
    try:
        if os.path.exists(metrics_path):
            with open(metrics_path, "r", encoding="utf-8") as fh:
                hist = json.load(fh)
        else:
            hist = []
    except Exception:
        hist = []

    entry = {"ts": datetime.datetime.utcnow().isoformat() + "Z", "model_id": model_id, "per_agent_conf": per_agent_conf}
    hist.append(entry)
    try:
        with open(metrics_path, "w", encoding="utf-8") as fh:
            json.dump(hist, fh, default=str)
    except Exception:
        logger.exception("failed to persist self-healing metrics")

    # emit metrics via backend.utils.metrics if available
    try:
        from backend.utils import metrics as _metrics
        # overall confidence gauge
        _metrics.set_gauge("self_healing_confidence", float(confidence))
        # per-agent gauges
        for aid, conf in per_agent_conf.items():
            # sanitize metric name
            name = f"self_healing_agent_{aid}_confidence".replace('-', '_')
            _metrics.set_gauge(name, float(conf))
        # mark a counter for metrics samples
        _metrics.increment("self_healing_metrics_samples", 1)
    except Exception:
        logger.debug("metrics emission skipped or failed")

    # rolling average across last N entries
    rolling_average: Dict[str, float] = {}
    try:
        last_n = hist[-5:]
        if last_n:
            agents = set().union(*(set(e.get("per_agent_conf", {}).keys()) for e in last_n))
            for a in agents:
                vals = [e.get("per_agent_conf", {}).get(a, 0.0) for e in last_n]
                rolling_average[a] = float(sum(vals)) / float(len(vals)) if vals else 0.0
        else:
            rolling_average = {k: per_agent_conf.get(k, 0.0) for k in per_agent_conf.keys()}
    except Exception:
        rolling_average = {k: per_agent_conf.get(k, 0.0) for k in per_agent_conf.keys()}

    # build a small policy timeline by running one deterministic episode
    timeline: List[Dict[str, Any]] = []
    try:
        obs = env.reset()
        done = {k: False for k in obs.keys()}
        step = 0
        # use the trainer's agents directly for deterministic actions where possible
        while not all(done.values()) and step < env.max_steps:
            actions = {}
            infos = {}
            for aid in list(obs.keys()):
                agent = trainer.agents.get(aid)
                info = {}
                try:
                    a = agent.act(obs[aid], deterministic=True, info=info)
                except Exception:
                    a = 0
                actions[aid] = int(a)
                infos[aid] = info
            sr = env.step(actions)
            timeline.append({
                "step": step,
                "actions": actions,
                "rewards": sr.rewards,
                "infos": sr.infos,
                "ts": datetime.datetime.utcnow().isoformat() + "Z",
            })
            obs = sr.observations
            done = sr.dones
            step += 1
    except Exception:
        logger.exception("failed to build policy timeline")

    return {
        "ok": True,
        "per_agent": eval_scores,
        "per_agent_confidence": per_agent_conf,
        "rolling_average": rolling_average,
        "model_id": model_id,
        "confidence": confidence,
        "timeline": timeline,
    }


@router.get("/actions")
def actions(resource: Optional[str] = Query(None, description="Resource path to inspect snapshots (local emulator)")) -> Dict[str, Any]:
    """Return recent self-healing actions (snapshots / rollbacks) using RecoveryManager.

    If `resource` is omitted the local working directory is used.
    """
    try:
        from backend.core.self_healing.recovery_manager import RecoveryManager, LocalEmulatorBackup
    except Exception as e:
        logger.exception("Recovery manager import failed: %s", e)
        raise HTTPException(status_code=500, detail="recovery_manager unavailable")

    resource_path = resource or "."
    manager = RecoveryManager(LocalEmulatorBackup())
    try:
        snaps = manager.list_checkpoints(resource_path)
    except Exception as e:
        logger.exception("listing snapshots failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    actions_out: List[Dict[str, Any]] = []
    for s in snaps:
        actions_out.append({
            "action": "snapshot_created",
            "snapshot_id": s.id,
            "resource": s.resource,
            "created_at": s.created_at.isoformat() + "Z",
            "size_bytes": s.size_bytes,
            "notes": s.notes,
        })

    # read persistent history (if present) from the LocalEmulatorBackup directory
    history_events: List[Dict[str, Any]] = []
    try:
        history_path = os.path.join(LocalEmulatorBackup().backup_dir, "history.json")
        if os.path.exists(history_path):
            with open(history_path, "r", encoding="utf-8") as fh:
                history_events = json.load(fh)
    except Exception:
        logger.exception("failed to load history events")

    last_action = history_events[-1] if history_events else (actions_out[0] if actions_out else {"action": "none"})
    return {"ok": True, "last_action": last_action, "actions": actions_out, "events": history_events}



@router.get("/history")
def history(page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=200)) -> Dict[str, Any]:
    """Paginated access to the persistent history of snapshot events.

    Returns: { ok: True, total: int, page: int, per_page: int, items: [ ... ] }
    """
    try:
        from backend.core.self_healing.recovery_manager import LocalEmulatorBackup
    except Exception as e:
        logger.exception("Recovery manager import failed for history: %s", e)
        raise HTTPException(status_code=500, detail="recovery_manager unavailable")

    history_path = os.path.join(LocalEmulatorBackup().backup_dir, "history.json")
    if not os.path.exists(history_path):
        return {"ok": True, "total": 0, "page": page, "per_page": per_page, "items": []}

    try:
        with open(history_path, "r", encoding="utf-8") as fh:
            events = json.load(fh)
    except Exception:
        logger.exception("failed to read history for pagination")
        raise HTTPException(status_code=500, detail="failed to read history")

    total = len(events)
    start = (page - 1) * per_page
    end = start + per_page
    items = events[start:end]
    return {"ok": True, "total": total, "page": page, "per_page": per_page, "items": items}


@router.delete("/history")
def clear_history(confirm: Optional[bool] = Query(False, description="Set to true to confirm deletion")) -> Dict[str, Any]:
    """Clear the persistent history file. Requires confirm=true to actually delete.

    This is a destructive admin operation.
    """
    if not confirm:
        raise HTTPException(status_code=400, detail="confirm=true required to clear history")
    try:
        from backend.core.self_healing.recovery_manager import LocalEmulatorBackup
    except Exception as e:
        logger.exception("Recovery manager import failed for clear_history: %s", e)
        raise HTTPException(status_code=500, detail="recovery_manager unavailable")

    history_path = os.path.join(LocalEmulatorBackup().backup_dir, "history.json")
    try:
        if os.path.exists(history_path):
            os.remove(history_path)
        return {"ok": True, "cleared": True}
    except Exception as e:
        logger.exception("failed to clear history: %s", e)
        raise HTTPException(status_code=500, detail="failed to clear history")


# ============================================================================
# RL-Based Policy Generation Routes (MindSpore Integration)
# ============================================================================

@router.post("/policies/generate")
async def generate_defense_policy(
    org_id: str = Body(..., description="Organization identifier"),
    recent_incidents: List[str] = Body(..., description="List of recent incident descriptions"),
    threat_landscape: str = Body(..., description="Description of threat environment"),
    custom_rules: Optional[List[Dict[str, Any]]] = Body(None, description="Optional custom policy rules")
) -> Dict[str, Any]:
    """
    Generate RL-optimized defense policy using MindSpore.
    
    The service analyzes threat landscape and incident history to generate optimal
    defense policies using multi-agent reinforcement learning.
    """
    if not _RL_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="RL service not available")
    
    try:
        policy = await selfhealing_service.generate_defense_policy(
            org_id=org_id,
            recent_incidents=recent_incidents,
            threat_landscape=threat_landscape,
            custom_rules=custom_rules
        )
        return policy
    except Exception as e:
        logger.exception("Policy generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Policy generation failed: {str(e)}")


@router.post("/policies/{policy_id}/simulate")
async def simulate_policy_response(
    policy_id: str,
    simulated_attacks: List[str] = Body(..., description="Attack scenarios to simulate"),
    simulation_rounds: int = Body(100, description="Number of simulation rounds"),
    threat_models: Optional[List[str]] = Body(None, description="Optional threat models")
) -> Dict[str, Any]:
    """
    Simulate policy effectiveness against attack scenarios.
    
    Runs multi-agent RL simulation to evaluate policy robustness and response times.
    """
    if not _RL_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="RL service not available")
    
    try:
        simulation = await selfhealing_service.simulate_attack_response(
            policy_id=policy_id,
            simulated_attacks=simulated_attacks,
            simulation_rounds=simulation_rounds,
            threat_models=threat_models
        )
        return simulation
    except Exception as e:
        logger.exception("Policy simulation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.post("/policies/{policy_id}/submit-blockchain")
async def submit_policy_to_blockchain(
    policy_id: str,
    policy_hash: str = Body(..., description="SHA256 hash of policy"),
    policy_content: Optional[str] = Body(None, description="Full policy content"),
    org_id: Optional[str] = Body(None, description="Organization ID")
) -> Dict[str, Any]:
    """
    Submit policy to blockchain for immutable audit trail.
    
    Creates tamper-proof record on Hyperledger Fabric.
    """
    if not _RL_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="RL service not available")
    
    try:
        result = await selfhealing_service.submit_policy_to_blockchain(
            policy_id=policy_id,
            policy_hash=policy_hash,
            policy_content=policy_content,
            org_id=org_id
        )
        return result
    except Exception as e:
        logger.exception("Blockchain submission failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Blockchain submission failed: {str(e)}")


@router.get("/policies")
async def get_policies(
    org_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000)
) -> List[Dict[str, Any]]:
    """Retrieve policy generation history."""
    if not _RL_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="RL service not available")
    
    try:
        policies = await selfhealing_service.get_policy_history(org_id)
        return policies[:limit]
    except Exception as e:
        logger.exception("Policy retrieval failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Policy retrieval failed: {str(e)}")


@router.get("/policies/{policy_id}")
async def get_policy_details(policy_id: str) -> Dict[str, Any]:
    """Get details for a specific policy."""
    if not _RL_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="RL service not available")
    
    try:
        policies = await selfhealing_service.get_policy_history()
        for policy in policies:
            if policy.get("policy_id") == policy_id:
                return policy
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Policy lookup failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Policy lookup failed: {str(e)}")


@router.get("/policies/{policy_id}/simulations")
async def get_policy_simulations(
    policy_id: str,
    limit: int = Query(50, ge=1, le=1000)
) -> List[Dict[str, Any]]:
    """Get simulation history for a policy."""
    if not _RL_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="RL service not available")
    
    try:
        simulations = await selfhealing_service.get_simulation_history(policy_id)
        return simulations[:limit]
    except Exception as e:
        logger.exception("Simulation retrieval failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Simulation retrieval failed: {str(e)}")
