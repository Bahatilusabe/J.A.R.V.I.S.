"""
Mutation Engine - Evolution Driver
🧬 Generates strategic diversity through mutations
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from .strategy_genome import (
    StrategyGenome, 
    MutationOperator, 
    GenomePopulation
)


@dataclass
class MutationStrategy:
    """Configuration for mutation behavior"""
    base_mutation_rate: float = 0.1
    mutation_magnitude: float = 0.15
    adaptive: bool = True              # Adapt mutation rate based on fitness
    operator_distribution: Dict[MutationOperator, float] = None
    
    def __post_init__(self):
        if self.operator_distribution is None:
            # Default distribution
            self.operator_distribution = {
                MutationOperator.POINT_MUTATION: 0.5,
                MutationOperator.INSERTION: 0.2,
                MutationOperator.DELETION: 0.1,
                MutationOperator.DUPLICATION: 0.1,
                MutationOperator.INVERSION: 0.1,
            }


class MutationEngine:
    """Engine for generating mutations and evolutionary diversity"""
    
    def __init__(self, strategy: MutationStrategy = None):
        self.strategy = strategy or MutationStrategy()
        self.mutation_count = 0
        self.mutation_history: List[Dict[str, Any]] = []
        self.success_rates: Dict[MutationOperator, float] = {
            op: 0.5 for op in MutationOperator
        }
    
    def mutate_genome(self, genome: StrategyGenome, adaptive: bool = True) -> StrategyGenome:
        """
        Apply mutation to genome
        adaptive=True: adjust mutation rate based on fitness
        """
        # Decide mutation rate
        mutation_rate = self.strategy.base_mutation_rate
        
        if adaptive:
            mutation_rate = self._adaptive_mutation_rate(genome)
        
        # Select mutation operator
        operator = self._select_operator()
        
        # Clone and mutate
        mutant = genome.clone()
        mutant.mutate(operator, self.strategy.mutation_magnitude)
        
        self.mutation_count += 1
        self.mutation_history.append({
            "timestamp": datetime.now(),
            "parent_id": genome.genome_id,
            "mutant_id": mutant.genome_id,
            "operator": operator.value,
            "parent_fitness": genome.fitness_score,
            "mutation_rate": mutation_rate
        })
        
        return mutant
    
    def _adaptive_mutation_rate(self, genome: StrategyGenome) -> float:
        """
        Adapt mutation rate based on fitness
        Low fitness → higher mutation (explore more)
        High fitness → lower mutation (refine)
        """
        if genome.fitness_score > 0.8:
            return self.strategy.base_mutation_rate * 0.5  # Fine-tune
        elif genome.fitness_score > 0.5:
            return self.strategy.base_mutation_rate  # Normal
        else:
            return self.strategy.base_mutation_rate * 2.0  # Explore more
    
    def _select_operator(self) -> MutationOperator:
        """Select mutation operator based on distribution"""
        operators = list(self.strategy.operator_distribution.keys())
        weights = list(self.strategy.operator_distribution.values())
        
        # Adjust weights based on historical success rates
        adjusted_weights = [
            self.success_rates[op] * w 
            for op, w in zip(operators, weights)
        ]
        
        # Normalize
        total = sum(adjusted_weights)
        if total > 0:
            adjusted_weights = [w / total for w in adjusted_weights]
        
        return np.random.choice(operators, p=adjusted_weights)
    
    def mutate_population(self, population: GenomePopulation, 
                         mutation_fraction: float = 0.3) -> List[StrategyGenome]:
        """
        Apply mutations to subset of population
        mutation_fraction: percentage of population to mutate (0.0-1.0)
        """
        num_to_mutate = max(1, int(len(population.genomes) * mutation_fraction))
        
        # Select diverse genomes to mutate
        selected_indices = np.random.choice(
            len(population.genomes),
            size=num_to_mutate,
            replace=False
        )
        
        mutants = []
        for idx in selected_indices:
            original = population.genomes[idx]
            mutant = self.mutate_genome(original, adaptive=True)
            mutants.append(mutant)
        
        return mutants
    
    def crossover_and_mutate(self, parent1: StrategyGenome, 
                            parent2: StrategyGenome) -> Tuple[StrategyGenome, StrategyGenome]:
        """
        Crossover two parents and mutate offspring
        Returns: (offspring1, offspring2)
        """
        # Crossover
        child1 = parent1.crossover(parent2)
        child2 = parent2.crossover(parent1)
        
        # Mutate offspring
        child1 = self.mutate_genome(child1, adaptive=False)
        child2 = self.mutate_genome(child2, adaptive=False)
        
        return child1, child2
    
    def record_operator_success(self, operator: MutationOperator, 
                               success: bool, weight: float = 0.1) -> None:
        """Update success rate of mutation operator"""
        current_rate = self.success_rates[operator]
        
        if success:
            self.success_rates[operator] = current_rate + weight
        else:
            self.success_rates[operator] = current_rate - weight
        
        # Keep in valid range
        self.success_rates[operator] = np.clip(self.success_rates[operator], 0.1, 1.0)
    
    def get_mutation_stats(self) -> Dict[str, Any]:
        """Get mutation statistics"""
        return {
            "total_mutations": self.mutation_count,
            "history_entries": len(self.mutation_history),
            "operator_success_rates": {
                op.value: rate for op, rate in self.success_rates.items()
            },
            "recent_mutations": self.mutation_history[-10:] if self.mutation_history else []
        }
    
    def adaptive_mutation_strategy(self, population_fitness: float) -> None:
        """
        Adapt mutation strategy based on population fitness
        Called periodically to adjust evolution parameters
        """
        if population_fitness > 0.8:
            # Population converged - reduce mutation to refine
            self.strategy.base_mutation_rate = 0.05
            self.strategy.mutation_magnitude = 0.05
        elif population_fitness > 0.5:
            # Normal evolution
            self.strategy.base_mutation_rate = 0.1
            self.strategy.mutation_magnitude = 0.15
        else:
            # Low fitness - increase mutation to explore
            self.strategy.base_mutation_rate = 0.2
            self.strategy.mutation_magnitude = 0.25
    
    def generate_mutation_schedule(self, generations: int) -> Dict[int, float]:
        """
        Generate adaptive mutation schedule for n generations
        Returns: generation -> mutation_rate mapping
        """
        schedule = {}
        
        for gen in range(generations):
            # Decrease mutation over time (simulated annealing)
            progress = gen / generations
            base_rate = self.strategy.base_mutation_rate
            
            # Exponential decay with small floor to maintain diversity
            rate = base_rate * (0.9 ** (progress * 10)) + 0.01
            schedule[gen] = rate
        
        return schedule
