import pytest

from backend.core.self_healing import policy_engine


def test_rule_based_safe():
    engine = policy_engine.RuleBasedEthicsEngine()
    decision = {"action": "read_file", "targets": ["/var/log/syslog"]}
    outcome = engine.evaluate(decision, context={"model_confidence": 0.9})

    assert outcome.verdict == "safe"
    assert outcome.score == 1.0
    assert isinstance(outcome.reasons, list)


def test_deny_list_unsafe():
    engine = policy_engine.RuleBasedEthicsEngine()
    decision = {"action": "exfiltrate_data", "targets": ["/tmp/creds.txt"]}
    outcome = engine.evaluate(decision)

    assert outcome.verdict == "unsafe"
    assert outcome.score == 0.0
    assert any(r.startswith("action_in_deny_list") for r in outcome.reasons)


def test_get_default_engine_fallback():
    # If the optional NEE package isn't installed, get_default_engine should
    # return the rule-based fallback. If NEE is present in the environment,
    # this test will skip because it's exercising the fallback behavior.
    if getattr(policy_engine, "_HAS_NEE", False):
        pytest.skip("NEE available in environment; skipping fallback assertion")

    engine = policy_engine.get_default_engine()
    assert isinstance(engine, policy_engine.RuleBasedEthicsEngine)
