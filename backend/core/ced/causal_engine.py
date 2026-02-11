"""A small, dependency-light causal reasoning helper for counterfactual analysis.

This is intentionally minimal: it provides a tiny structural causal model (SCM)
abstraction that can be used in tests and for lightweight counterfactual queries
in the codebase. It's not a production causal inference library; instead it's a
well-documented scaffold you can extend later.

Key concepts implemented here:
- Nodes with deterministic structural functions (callables) that map parent
  values to the node value.
- A simple `counterfactual` method that does abduction (estimate exogenous
  noise from an observation), action (apply intervention), and prediction.

The code avoids heavy ML dependencies so it runs in CI and in constrained
developer environments.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional
import logging
from pathlib import Path

logger = logging.getLogger("jarvis.ced.causal_engine")
try:
    import numpy as np  # type: ignore
except Exception:
    np = None  # type: ignore


class CausalEngine:
    """Small structural causal model container.

    Example usage:
        ce = CausalEngine()
        # node 'x' has no parents and is sampled using a callable
        ce.add_node('x', lambda parents: 1.0, parents=())
        ce.add_node('y', lambda parents: parents['x'] * 2, parents=('x',))

        obs = {'x': 1.0, 'y': 2.0}
        cf = ce.counterfactual(obs, intervention={'x': 2.0})

    Notes:
        - Structural functions receive a dict of parent values and must return a
          single value (numeric or categorical).
        - This engine treats exogenous noise as deterministic offsets inferred
          from the observed value; this is suitable for simple unit tests and
          narrative counterfactuals.
    """

    def __init__(self) -> None:
        # node -> (callable, parents)
        self._nodes: Dict[str, Callable[[Mapping[str, Any]], Any]] = {}
        self._parents: Dict[str, Iterable[str]] = {}

    def add_node(self, name: str, func: Callable[[Mapping[str, Any]], Any], parents: Iterable[str] | None = None) -> None:
        """Register a node in the SCM.

        Args:
            name: node name
            func: structural function mapping parent-values dict -> value
            parents: iterable of parent node names (optional)
        """
        self._nodes[name] = func
        self._parents[name] = tuple(parents or ())

    def predict(self, interventions: Mapping[str, Any] | None = None) -> Dict[str, Any]:
        """Compute the forward prediction for the model under interventions.

        Nodes whose values are provided in `interventions` are set to the
        provided values (the 'do' operation). All other nodes are computed in
        topological order (the method assumes the caller registers nodes in an
        acyclic order).
        """
        interventions = interventions or {}
        values: Dict[str, Any] = {}
        for node in self._nodes:
            if node in interventions:
                values[node] = interventions[node]
                continue
            parents = {p: values[p] for p in self._parents.get(node, ())}
            values[node] = self._nodes[node](parents)
        return values

    def _infer_noise(self, observed: Mapping[str, Any]) -> Dict[str, Any]:
        """Infer a simple exogenous noise term per node by running the
        structural function with parents (if available) and computing the
        residual between observed and deterministic prediction.

        This is a heuristic for small-scale counterfactuals used in tests and
        narrations.
        """
        noise: Dict[str, Any] = {}
        # we compute nodes in registration order
        values: Dict[str, Any] = {}
        for node in self._nodes:
            parents = {p: values.get(p, observed.get(p)) for p in self._parents.get(node, ())}
            pred = self._nodes[node](parents)
            observed_val = observed.get(node, pred)
            try:
                noise[node] = observed_val - pred  # numeric residual
            except Exception:
                # for non-numeric values we store a tuple (obs, pred)
                noise[node] = (observed_val, pred)
            values[node] = observed_val
        return noise

    def counterfactual(self, observed: Mapping[str, Any], intervention: Mapping[str, Any]) -> Dict[str, Any]:
        """Compute a counterfactual outcome given an observation and an intervention.

        Steps:
            1. Abduction: infer exogenous noise from the observation.
            2. Action: apply the intervention (do operation).
            3. Prediction: re-run the structural functions using inferred noise
               where appropriate. For numeric nodes the noise is added to the
               deterministic prediction.

        Returns the complete dict of node values under the counterfactual.
        """
        noise = self._infer_noise(observed)

        # run forward with intervention, adding noise back in where numeric
        cf_values: Dict[str, Any] = {}
        for node in self._nodes:
            if node in intervention:
                cf_values[node] = intervention[node]
                continue
            parents = {p: cf_values.get(p, intervention.get(p, observed.get(p))) for p in self._parents.get(node, ())}
            base = self._nodes[node](parents)
            n = noise.get(node)
            try:
                cf_values[node] = base + n
            except Exception:
                # non-numeric fallback: prefer base, then observed
                cf_values[node] = base
        return cf_values


# Optional heavy integrations (DoWhy for identification, MindSpore for learned
# structural functions). We import them lazily and gate runtime behavior so
# tests and lightweight CI environments don't need these packages.
_DOWHY_AVAILABLE = False
_MINDSPORE_AVAILABLE = False
try:
    import dowhy  # type: ignore
    _DOWHY_AVAILABLE = True
except Exception:
    dowhy = None  # type: ignore

try:
    import mindspore as ms  # type: ignore
    _MINDSPORE_AVAILABLE = True
except Exception:
    ms = None  # type: ignore


class DoWhyMindSporeCausalEngine(CausalEngine):
    """Hybrid engine that uses DoWhy for causal graph/identification and
    MindSpore to fit lightweight structural functions where applicable.

    This class is gated: if DoWhy or MindSpore are not available it still
    imports but raises at runtime when their features are invoked. The
    implementation here is intentionally minimal: it demonstrates how one
    could wire identification with learned structural functions while
    preserving testability.
    """

    def __init__(self, graph: Optional[Dict[str, Iterable[str]]] = None) -> None:
        super().__init__()
        self._graph = graph or {}
        # place to store simple MindSpore networks per node
        self._ms_models: Dict[str, Any] = {}

    def identify(self, treatment: str, outcome: str, graph: Optional[Dict] = None) -> Dict[str, Any]:
        """Run DoWhy identification to obtain an estimand for treatment->outcome.

        Returns the estimand dict returned by DoWhy. Raises RuntimeError if
        DoWhy is not installed.
        """
        if not _DOWHY_AVAILABLE:
            raise RuntimeError("DoWhy is not available in this environment")
        # Minimal wrapper: in real code you'd construct a causal model object
        # and call model.identify_effect(). We return a placeholder.
        return {"treatment": treatment, "outcome": outcome, "status": "identified"}

    def fit_node_with_mindspore(self, node: str, X: Any, y: Any, epochs: int = 10, use_dataset: bool = False, checkpoint_dir: Optional[str] = None) -> None:
        """Fit a tiny MindSpore MLP to predict node from parents (X->y).

        This requires MindSpore to be installed. The function stores the
        trained model in `self._ms_models[node]` and registers a callable
        structural function that uses the model for prediction.
        """
        if not _MINDSPORE_AVAILABLE:
            raise RuntimeError("MindSpore is not available in this environment")

        # Minimal MLP: this is illustrative only and purposefully tiny so tests
        # can mock away training if needed.
        net = ms.nn.SequentialCell(ms.nn.Dense(X.shape[1], 16), ms.nn.ReLU(), ms.nn.Dense(16, 1))

        # Training primitives
        loss_fn = ms.nn.MSELoss()
        opt = ms.nn.Adam(net.trainable_params(), learning_rate=1e-3)

        # Option A: use MindSpore Dataset APIs when requested and available
        if use_dataset:
            try:
                ds = ms.dataset.NumpySlicesDataset({"data": X, "label": y}, shuffle=False)  # type: ignore
                for _ in range(max(1, int(epochs))):
                    for batch in ds.create_tuple_iterator():
                        Xb, yb = batch
                        preds = net(Xb)
                        loss = loss_fn(preds, yb)
                        loss.backward()
                        opt.step()
                        opt.clear_grad()
            except Exception:
                # Fallback to simple loop below if dataset APIs behave differently
                use_dataset = False

        if not use_dataset:
            # create MindSpore tensors directly
            X_t = ms.Tensor(X)
            y_t = ms.Tensor(y)

            for _ in range(max(1, int(epochs))):
                preds = net(X_t)
                loss = loss_fn(preds, y_t)
                loss.backward()
                opt.step()
                opt.clear_grad()

        # optional checkpointing
        if checkpoint_dir:
            try:
                Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)
                ckpt_path = str(Path(checkpoint_dir) / f"{node}.ckpt")
                # MindSpore checkpoint API varies; call save_checkpoint if present
                if hasattr(ms, "save_checkpoint"):
                    ms.save_checkpoint(net, ckpt_path)  # type: ignore
            except Exception:
                # non-fatal: checkpointing is best-effort
                logger.warning("Failed to checkpoint model for node %s", node)

        self._ms_models[node] = net

        # register structural function that uses the trained model
        def model_func(parents: Mapping[str, Any]):
            import numpy as _np

            parent_vals = _np.array([parents.get(p, 0.0) for p in self._parents.get(node, ())], dtype=_np.float32).reshape(1, -1)
            t = ms.Tensor(parent_vals)
            pred = net(t).asnumpy().ravel()[0]
            return float(pred)

        self.add_node(node, model_func, parents=self._parents.get(node, ()))


class AttackChainCausalEngine(CausalEngine):
    """Specialized causal engine for security attack chain modeling.
    
    This engine:
    1. Builds causal DAGs from MITRE ATT&CK attack chains
    2. Maps threat scores to attack chain nodes
    3. Infers attack progression and root causes
    4. Simulates intervention impacts on attack chains
    5. Ranks minimal interventions by effectiveness
    """
    
    def __init__(self, attack_chain_type: Optional[str] = None) -> None:
        """Initialize attack chain causal engine.
        
        Args:
            attack_chain_type: Type of attack (e.g., "ransomware", "lateral_movement")
        """
        super().__init__()
        self.attack_chain_type = attack_chain_type
        self.attack_chain = None
        self._node_metadata: Dict[str, Dict[str, Any]] = {}
        
        if attack_chain_type:
            self._load_attack_chain(attack_chain_type)
    
    def _load_attack_chain(self, chain_type: str) -> None:
        """Load a MITRE ATT&CK attack chain DAG."""
        try:
            from .attack_models import get_attack_chain_dag
            self.attack_chain = get_attack_chain_dag(chain_type)
            if self.attack_chain:
                self._build_attack_graph()
        except ImportError:
            logger.warning("attack_models not available, using generic engine")
    
    def _build_attack_graph(self) -> None:
        """Convert attack chain to causal graph structure."""
        if not self.attack_chain:
            return
        
        # Add nodes from attack chain
        for node_id, node in self.attack_chain.nodes.items():
            # Store metadata
            self._node_metadata[node_id] = {
                "mitre_id": node.mitre_id,
                "name": node.name,
                "description": node.description,
                "category": node.category,
                "severity": node.severity,
            }
            
            # Define structural function based on prerequisites
            def make_func(node_id, node_obj, chain):
                def func(parents):
                    if not parents:
                        return node_obj.severity
                    
                    # Attack progresses if all prerequisites are active
                    min_parent_val = min(parents.values()) if parents else 0.0
                    return node_obj.severity * min_parent_val
                return func
            
            prerequisites = self.attack_chain.get_node(node_id).prerequisites
            self.add_node(node_id, make_func(node_id, node, self.attack_chain), 
                         parents=prerequisites)
    
    def extract_threat_chain(self, threat_scores: Dict[str, float]) -> Dict[str, Any]:
        """Extract attack chain from threat scores.
        
        Maps PASM threat scores to attack chain nodes to infer progression.
        
        Args:
            threat_scores: Dict mapping threat types to scores (0-1)
                Example: {"privilege_escalation": 0.92, "lateral_movement": 0.78}
        
        Returns:
            Dict with inferred attack chain, confidence, root causes
        """
        if not self.attack_chain:
            return {"error": "No attack chain loaded"}
        
        # Map threat scores to nodes
        activated_nodes = {}
        for node_id in self.attack_chain.nodes:
            threat_type = self.attack_chain.nodes[node_id].category
            score = threat_scores.get(threat_type, 0.0)
            if score > 0.5:  # Threshold for activation
                activated_nodes[node_id] = score
        
        # Find root causes (entry points with activation)
        root_causes = [
            node_id for node_id in self.attack_chain.entry_points 
            if node_id in activated_nodes
        ]
        
        # Trace attack progression
        attack_path = []
        for entry in root_causes:
            path = self._trace_progression(entry, activated_nodes)
            if path:
                attack_path.extend(path)
        
        return {
            "attack_chain_type": self.attack_chain_type,
            "activated_nodes": activated_nodes,
            "root_causes": root_causes,
            "attack_progression": attack_path,
            "confidence": min(activated_nodes.values()) if activated_nodes else 0.0,
            "estimated_stage": len(attack_path),
        }
    
    def _trace_progression(self, start_node: str, activated: Dict[str, float]) -> List[str]:
        """Trace attack progression from start node through activated nodes."""
        path = [start_node]
        current = start_node
        visited = {start_node}
        
        while True:
            outgoing = self.attack_chain.get_outgoing_edges(current)
            next_node = None
            
            for edge in outgoing:
                if edge.target in activated and edge.target not in visited:
                    next_node = edge.target
                    break
            
            if not next_node:
                break
            
            path.append(next_node)
            visited.add(next_node)
            current = next_node
        
        return path
    
    def rank_interventions(self, threat_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank intervention strategies by effectiveness.
        
        Args:
            threat_data: Threat information including attack chain
        
        Returns:
            List of interventions ranked by ROI score
        """
        if not self.attack_chain:
            return []
        
        interventions = []
        
        for node_id, node in self.attack_chain.nodes.items():
            # Block early-stage attacks is most effective
            stage_index = self.attack_chain.entry_points.count(node_id) == 1
            
            intervention = {
                "type": f"block_{node.category}",
                "target": node_id,
                "target_name": node.name,
                "mitre_id": node.mitre_id,
                "effectiveness": node.severity,
                "implementation_cost": self._estimate_cost(node.category),
                "disruption_level": self._estimate_disruption(node.category),
                "roi_score": (node.severity * (1.0 - self._estimate_disruption(node.category))) / max(self._estimate_cost(node.category), 0.1)
            }
            interventions.append(intervention)
        
        # Sort by ROI score
        interventions.sort(key=lambda x: x["roi_score"], reverse=True)
        return interventions[:5]  # Top 5 interventions
    
    def _estimate_cost(self, category: str) -> float:
        """Estimate implementation cost (0-1) for intervention category."""
        costs = {
            "initial_access": 0.3,
            "execution": 0.4,
            "persistence": 0.5,
            "privilege_escalation": 0.6,
            "defense_evasion": 0.5,
            "credential_access": 0.4,
            "discovery": 0.2,
            "lateral_movement": 0.7,
            "collection": 0.6,
            "exfiltration": 0.8,
            "impact": 0.9,
        }
        return costs.get(category, 0.5)
    
    def _estimate_disruption(self, category: str) -> float:
        """Estimate operational disruption (0-1) for intervention category."""
        disruptions = {
            "initial_access": 0.1,
            "execution": 0.2,
            "persistence": 0.3,
            "privilege_escalation": 0.4,
            "defense_evasion": 0.2,
            "credential_access": 0.6,
            "discovery": 0.1,
            "lateral_movement": 0.7,
            "collection": 0.5,
            "exfiltration": 0.8,
            "impact": 0.9,
        }
        return disruptions.get(category, 0.5)


# ============================================================================
# Singleton Factory Pattern - Lazy Initialization
# ============================================================================

_causal_engine_singleton: Optional[CausalEngine] = None


def get_causal_engine() -> CausalEngine:
    """Get or create the singleton CausalEngine instance.
    
    This function implements lazy initialization following the J.A.R.V.I.S.
    pattern for stateful services. The engine is initialized on first call
    and reused for all subsequent requests.
    
    Returns:
        Initialized CausalEngine singleton
    """
    global _causal_engine_singleton
    if _causal_engine_singleton is None:
        _causal_engine_singleton = AttackChainCausalEngine()
        logger.info("CausalEngine singleton initialized")
    return _causal_engine_singleton


__all__ = ["CausalEngine", "DoWhyMindSporeCausalEngine", "AttackChainCausalEngine", "get_causal_engine"]
