"""
Co-Evolution Engine - Adversarial co-evolution of attack and defense strategies

This is the KILLER FEATURE of J.A.R.V.I.S.

Attack strategies and defense strategies evolve together in a Darwinian arms race.
- Weak defenses die
- Strong attacks die
- Only the fittest survive

This is NOT just learning from attacks.
This is EVOLVING BECAUSE OF attackers.

Powered by MindSpore evolutionary RL and Ascend simulation acceleration.
"""

from .attacker_genome import (
    AttackerGenome,
    AttackerPopulation,
    AttackTactic,
    EvationTechnique,
    PayloadCharacteristics,
)

from .defense_genome import (
    DefenseGenome,
    DefensePopulation,
    DetectionMethod,
    ResponseStrategy,
    HardeningMeasure,
    DetectionConfiguration,
    ResponseConfiguration,
)

from .mutation_simulator import MutationSimulator

from .fitness_evaluator import (
    FitnessEvaluator,
    CombatSimulation,
    CombatOutcome,
)

__all__ = [
    # Attacker
    "AttackerGenome",
    "AttackerPopulation",
    "AttackTactic",
    "EvationTechnique",
    "PayloadCharacteristics",
    # Defense
    "DefenseGenome",
    "DefensePopulation",
    "DetectionMethod",
    "ResponseStrategy",
    "HardeningMeasure",
    "DetectionConfiguration",
    "ResponseConfiguration",
    # Evolution
    "MutationSimulator",
    "FitnessEvaluator",
    "CombatSimulation",
    "CombatOutcome",
]
