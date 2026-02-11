"""Self-healing subsystem package.

This package contains modules to monitor, detect, and automatically remediate
faults in the system using multi-agent reinforcement learning:

- `policy_engine.py`: Ethics-driven policy evaluation framework
- `marl_agent.py`: Multi-Agent RL for orchestration
- `rl_service.py`: MindSpore RL-based defense policy generation and optimization
- `recovery_manager.py`: System recovery and remediation
- `modelarts_integration.py`: Huawei ModelArts integration
"""

from .rl_service import SelfHealingService, RLPolicyAgent, selfhealing_service

__all__ = [
    "SelfHealingService",
    "RLPolicyAgent",
    "selfhealing_service",
    "policy_engine",
    "marl_agent",
]
