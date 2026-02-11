"""
Reflex Engine: Autonomous Defense Reflexes

Defense reflex arcs mirror biological spinal reflexes:
- CRITICAL (<10ms):  Isolate first, explain later
- HIGH (<100ms):     Conditional containment
- MEDIUM (<500ms):   Monitoring
- LOW (<2s):         Full AI reasoning

No dashboard latency. No human delay for critical threats.
Just immediate automatic response.

Components:
1. latency_controller.py   - Ensures reflex happens within budget
2. auto_containment.py     - Actually executes the isolation
3. escalation_manager.py   - Routes to right human at right time
4. reflex_rules.yaml       - Rules for each threat level

Key Insight: Fast threats need sub-100ms responses.
This layer provides that autonomously while keeping humans
in the loop for approval/override.
"""

from .latency_controller import (
    LatencyController,
    ThreatLevel,
    LatencyBudgetStatus,
    LatencyBudget,
    ReflexDecision
)

from .auto_containment import (
    AutoContainmentEngine,
    IsolationMode,
    ContainmentAction,
    ContainmentResult,
    IsolatedHost
)

from .escalation_manager import (
    EscalationManager,
    Escalation,
    EscalationLevel,
    EscalationStatus,
    EscalationNotification
)

__all__ = [
    # Latency Control
    "LatencyController",
    "ThreatLevel",
    "LatencyBudgetStatus",
    "LatencyBudget",
    "ReflexDecision",
    
    # Auto-Containment
    "AutoContainmentEngine",
    "IsolationMode",
    "ContainmentAction",
    "ContainmentResult",
    "IsolatedHost",
    
    # Escalation
    "EscalationManager",
    "Escalation",
    "EscalationLevel",
    "EscalationStatus",
    "EscalationNotification",
]

__version__ = "1.0.0"
__description__ = "Autonomous Defense Reflex Arcs"
