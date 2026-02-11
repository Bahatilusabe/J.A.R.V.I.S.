"""Policy Engine for self-healing: Neural Ethics Engine (NEE) integration + fallback.

This module provides a small API to evaluate AI decisions for ethics/safety.
It attempts to use a (hypothetical) `nee` package (Neural Ethics Engine). If the
real package is not available, a rule-based fallback (`RuleBasedEthicsEngine`)
will be used so the repo remains runnable in CI and development environments.

Exports:
- PolicyOutcome (dataclass) -- normalized result of evaluation
- BaseEthicsEngine -- abstract interface
- NeuralEthicsEngine -- wrapper around real `nee` package (gated import)
- RuleBasedEthicsEngine -- deterministic, test-friendly fallback
- get_default_engine() -- convenience to obtain whichever backend is available

Usage:
>>> engine = get_default_engine()
>>> outcome = engine.evaluate({'action': 'block_ip', 'params': {'ip': '1.2.3.4'}}, context)
>>> print(outcome.verdict, outcome.score)

Note: `nee` is treated as an optional dependency. Replace the import name with
the actual Neural Ethics Engine package you intend to use, or install a proper
implementation into your environment.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class PolicyOutcome:
    """Normalized result returned by the policy engine."""

    verdict: str  # 'safe'|'unsafe'|'review'
    score: float  # 0.0..1.0 where higher is more safe
    reasons: List[str]
    confidence: float  # model or heuristic confidence 0..1
    meta: Dict[str, Any]


class BaseEthicsEngine:
    """Abstract minimal interface for any ethics engine implementation."""

    def evaluate(self, decision: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> PolicyOutcome:
        """Evaluate `decision` in given `context`. Must return a PolicyOutcome.

        decision: dictionary describing the candidate action/decision, e.g.
          {'action': 'allow', 'resource': 'file', 'user': 'alice', ...}
        context: optional contextual signals (logs, telemetry, model outputs)
        """
        raise NotImplementedError()

    def explain(self, decision: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return a structured explanation for the last evaluation or for a new one.

        Default implementation calls `evaluate` and returns a dictionary.
        """
        outcome = self.evaluate(decision, context)
        return asdict(outcome)


# Try to import a hypothetical Neural Ethics Engine (NEE). Replace the module
# name with the real package if different. We gate this import so the repo
# remains importable in CI / environments without the heavy dependency.
try:
    import nee  # type: ignore

    _HAS_NEE = True
    logger.info("Neural Ethics Engine (nee) available: using NEE backend")
except Exception:  # pragma: no cover - import-time gating
    nee = None  # type: ignore
    _HAS_NEE = False
    logger.info("Neural Ethics Engine (nee) not available: falling back to rule-based engine")


class NeuralEthicsEngine(BaseEthicsEngine):
    """Wrapper around a Neural Ethics Engine (NEE) implementation.

    This class assumes the external `nee` package exposes an API roughly like:
      model = nee.load_model(...)
      result = model.evaluate(decision, context)
    and that `result` contains fields like `score`, `verdict`, `reasons`,
    and `confidence`. The wrapper is defensive: if `nee` is present but
    something goes wrong during the call, we return a conservative "review"
    outcome rather than raising an exception.
    """

    def __init__(self, model_name: Optional[str] = None, **kwargs):
        if not _HAS_NEE:
            raise RuntimeError("NeuralEthicsEngine requires 'nee' package which is not installed")
        # Load or initialize the real NEE model. This is intentionally small –
        # adapt to the real package API when integrating.
        self.model_name = model_name or "default"
        try:
            # The real API will differ; adapt when you have the package.
            self.model = nee.load_model(self.model_name, **kwargs)
        except Exception as exc:  # pragma: no cover - depends on runtime package
            logger.exception("Failed to load NEE model; will raise")
            raise

    def evaluate(self, decision: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> PolicyOutcome:
        try:
            raw = self.model.evaluate(decision, context or {})
            # Normalize common fields; adapt to the real output structure.
            score = float(getattr(raw, "score", raw.get("score", 0.0)))
            verdict = getattr(raw, "verdict", raw.get("verdict", "review"))
            reasons = list(getattr(raw, "reasons", raw.get("reasons", [])))
            confidence = float(getattr(raw, "confidence", raw.get("confidence", 0.0)))
            meta = dict(getattr(raw, "meta", raw.get("meta", {})))
            return PolicyOutcome(verdict=verdict, score=score, reasons=reasons, confidence=confidence, meta=meta)
        except Exception:
            # If the model errors, provide a conservative safe-fail response.
            logger.exception("NEE evaluation failed; returning conservative review outcome")
            return PolicyOutcome(verdict="review", score=0.5, reasons=["nee_error"], confidence=0.0, meta={})


class RuleBasedEthicsEngine(BaseEthicsEngine):
    """Simple deterministic rule-based fallback.

    The rules are intentionally conservative and explainable. They are
    easy to unit-test and suitable for CI / demo environments where the
    neural package isn't available.
    """

    def __init__(self, deny_list: Optional[List[str]] = None):
        # deny_list contains actions/resources that are automatically unsafe
        self.deny_list = set(deny_list or ["exfiltrate_data", "delete_ledger", "wipe_disk"])

    def evaluate(self, decision: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> PolicyOutcome:
        ctx = context or {}
        reasons: List[str] = []
        score = 1.0
        confidence = 1.0

        action = decision.get("action") or decision.get("type") or "unknown"

        # Rule 1: explicit deny-list
        if action in self.deny_list:
            reasons.append(f"action_in_deny_list:{action}")
            score = 0.0
            confidence = 1.0
            verdict = "unsafe"
            return PolicyOutcome(verdict=verdict, score=score, reasons=reasons, confidence=confidence, meta={})

        # Rule 2: if decision touches PII or 'secrets' field
        targets = decision.get("targets") or decision.get("resource") or []
        if isinstance(targets, str):
            targets_list = [targets]
        else:
            targets_list = list(targets)

        for t in targets_list:
            if isinstance(t, str) and ("password" in t.lower() or "ssn" in t.lower() or "secret" in t.lower()):
                reasons.append("touches_sensitive_field")
                score = min(score, 0.2)

        # Rule 3: if confidence from upstream model is low, escalate to review
        upstream_conf = None
        if ctx:
            upstream_conf = ctx.get("model_confidence") or ctx.get("confidence")
        if upstream_conf is not None:
            try:
                uc = float(upstream_conf)
                if uc < 0.3:
                    reasons.append("low_upstream_confidence")
                    score = min(score, 0.4)
                    confidence = 0.2
            except Exception:
                pass

        # Rule 4: heuristic for rate-limit or frequency anomalies in telemetry
        telemetry = ctx.get("telemetry") or {}
        suspicious = False
        if telemetry:
            if telemetry.get("rate") and telemetry.get("rate") > 1000:
                reasons.append("high_rate_event")
                suspicious = True
                score = min(score, 0.3)

        # Synthesize verdict
        if score >= 0.8 and not suspicious:
            verdict = "safe"
        elif score >= 0.4:
            verdict = "review"
        else:
            verdict = "unsafe"

        meta = {"used_rules": reasons}
        return PolicyOutcome(verdict=verdict, score=score, reasons=reasons, confidence=confidence, meta=meta)


def get_default_engine() -> BaseEthicsEngine:
    """Return a best-effort engine: NeuralEthicsEngine if available, else rule-based.

    Consumers may call this convenience function to get an engine that will work
    in both development and production (where NEE is installed).
    """
    if _HAS_NEE:
        try:
            return NeuralEthicsEngine()
        except Exception:
            logger.exception("Failed to construct NeuralEthicsEngine; falling back to RuleBasedEthicsEngine")
    return RuleBasedEthicsEngine()


# Small CLI/demo when executed directly – keeps the module runnable.
if __name__ == "__main__":
    import json
    import sys

    logging.basicConfig(level=logging.INFO)

    engine = get_default_engine()

    sample_decision = {
        "action": "exfiltrate_data",
        "targets": ["/etc/passwd", "user_secret_token"],
        "initiator": "agent-42",
    }

    outcome = engine.evaluate(sample_decision, context={"model_confidence": 0.9})
    print(json.dumps(asdict(outcome), indent=2))
