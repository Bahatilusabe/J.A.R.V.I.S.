"""Smoke test for the Reflex Engine components.

Runs lightweight scenarios to validate imports and basic behavior:
 - creates a latency budget and makes a decision
 - executes a critical reflex via AutoContainmentEngine
 - registers a responder and creates/assigns an escalation
"""

from response.reflex_engine import (
    LatencyController,
    ThreatLevel,
    AutoContainmentEngine,
    EscalationManager,
)


def run():
    print("Starting Reflex Engine smoke test...")

    # Latency controller
    lc = LatencyController()
    dec = lc.make_decision(
        threat_id="t1",
        threat_level=ThreatLevel.CRITICAL,
        threat_score=0.92,
        reflex_action="isolate_host",
    )
    print("Decision created:", dec.reflex_action, dec.confidence, f"{dec.decision_time_ms:.2f}ms")

    # Auto containment
    ac = AutoContainmentEngine()
    iso = ac.execute_critical_reflex(threat_id="t1", host_id="host-123", threat_score=0.92, attack_type="ransomware")
    print("Critical reflex result:", iso)

    # Escalation manager
    em = EscalationManager()
    em.register_responder("r1", "Alice", "alice@example.com", "Lead", "IR", on_call=True)
    esc = em.create_escalation(threat_id="t1", threat_level="critical", threat_score=0.92, reason="Auto-isolated")
    assigned = em.assign_escalation(esc.escalation_id)
    print("Escalation created and assigned to:", assigned)

    # approve it
    approved = em.approve_escalation(esc.escalation_id, "r1", notes="Looks legit, keep isolated")
    print("Escalation approved:", approved)

    print("Reflex Engine smoke test completed successfully.")


if __name__ == "__main__":
    run()
