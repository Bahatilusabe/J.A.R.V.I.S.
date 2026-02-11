"""
AI Core Evolution Module
🧬🔄 Adversarial Co-Evolution Engine

Self-improving intelligence through:
- Evolutionary algorithms on strategy genomes
- Adversarial interactions (attack vs defense)
- Fitness-driven selection
- MindSpore RL integration
- Ascend GPU acceleration
"""

from .strategy_genome import (
    StrategyGenome,
    StrategyType,
    Gene,
    MutationOperator,
    GenomePopulation,
)

from .mutation_engine import (
    MutationEngine,
    MutationStrategy,
)

from .fitness_function import (
    FitnessFunction,
    FitnessProfile,
    FitnessMetric,
    BattleResult,
)

from .evolution_loop import (
    EvolutionEngine,
    EvolutionConfig,
    EvolutionStep,
    SelectionMethod,
)

__all__ = [
    # Strategy genome
    "StrategyGenome",
    "StrategyType",
    "Gene",
    "MutationOperator",
    "GenomePopulation",
    
    # Mutation engine
    "MutationEngine",
    "MutationStrategy",
    
    # Fitness evaluation
    "FitnessFunction",
    "FitnessProfile",
    "FitnessMetric",
    "BattleResult",
    
    # Evolution loop
    "EvolutionEngine",
    "EvolutionConfig",
    "EvolutionStep",
    "SelectionMethod",
]

__version__ = "1.0.0"
__description__ = "Self-Improving AI Through Adversarial Co-Evolution"
