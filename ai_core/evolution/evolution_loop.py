"""
Evolution Loop - Self-Improving Intelligence Engine
🧬🔄 Adversarial co-evolution with Ascend acceleration
"""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np
from enum import Enum
import json

from .strategy_genome import (
    StrategyGenome, 
    StrategyType,
    GenomePopulation,
    MutationOperator
)
from .mutation_engine import MutationEngine, MutationStrategy
from .fitness_function import (
    FitnessFunction,
    FitnessProfile,
    FitnessMetric,
    BattleResult
)


class SelectionMethod(Enum):
    """Tournament/selection strategies"""
    TOURNAMENT = "tournament"           # Tournament selection
    ROULETTE = "roulette"              # Fitness-proportionate
    RANK_BASED = "rank_based"          # Rank-based selection
    ELITISM = "elitism"                # Keep best individuals


@dataclass
class EvolutionConfig:
    """Configuration for evolution process"""
    population_size: int = 100
    generations: int = 100
    tournament_size: int = 5
    elitism_percent: float = 0.1       # Keep best 10%
    mutation_fraction: float = 0.3     # Mutate 30% each gen
    crossover_fraction: float = 0.5    # Crossover 50% each gen
    selection_method: SelectionMethod = SelectionMethod.TOURNAMENT
    target_fitness: float = 0.85       # Stop if fitness exceeds this


@dataclass
class EvolutionStep:
    """Record of one evolution step"""
    generation: int
    timestamp: datetime
    population_stats: Dict[str, float]
    elite_fitness: float
    average_fitness: float
    diversity: float
    battles_executed: int
    elite_genomes: List[str] = field(default_factory=list)  # Top genome IDs


class EvolutionEngine:
    """
    Self-Improving Intelligence Engine
    Adversarial co-evolution of attack and defense strategies
    """
    
    def __init__(self, config: EvolutionConfig = None):
        self.config = config or EvolutionConfig()
        self.mutation_engine = MutationEngine()
        self.fitness_function = FitnessFunction()
        
        # Populations
        self.defense_population = GenomePopulation(self.config.population_size)
        self.attack_population = GenomePopulation(self.config.population_size)
        
        # Evolution state
        self.generation = 0
        self.total_battles = 0
        self.evolution_history: List[EvolutionStep] = []
        self.start_time = datetime.now()
        
        # Performance tracking
        self.defense_fitness_over_time: List[float] = []
        self.attack_fitness_over_time: List[float] = []
    
    def initialize_populations(self,
                              defense_genome_template: StrategyGenome,
                              attack_genome_template: StrategyGenome) -> None:
        """
        Initialize defense and attack populations
        Creates diverse population from templates
        """
        # Defense population
        for i in range(self.config.population_size):
            defense_genome = defense_genome_template.clone()
            defense_genome.genome_id = f"defense_{self.generation}_{i}"
            
            # Add random variation
            for gene in defense_genome.genes.values():
                gene.mutate(0.3)
            
            self.defense_population.add_genome(defense_genome)
        
        # Attack population
        for i in range(self.config.population_size):
            attack_genome = attack_genome_template.clone()
            attack_genome.genome_id = f"attack_{self.generation}_{i}"
            
            # Add random variation
            for gene in attack_genome.genes.values():
                gene.mutate(0.3)
            
            self.attack_population.add_genome(attack_genome)
    
    def run_evolution_loop(self, 
                          max_generations: Optional[int] = None) -> Dict[str, Any]:
        """
        Main evolution loop
        Evolves both populations through adversarial interaction
        """
        max_gen = max_generations or self.config.generations
        
        for gen in range(max_gen):
            self.generation = gen
            print(f"\n🧬 Generation {gen + 1}/{max_gen}")
            
            # Run battles (adversarial interactions)
            battles_this_gen = self._run_battles()
            
            # Evaluate fitness
            self._evaluate_populations()
            
            # Selection and breeding
            self._selection_and_breeding()
            
            # Mutation
            self._apply_mutations()
            
            # Record stats
            step = self._record_generation_stats(battles_this_gen)
            self.evolution_history.append(step)
            
            # Check termination
            elite_defense = self.defense_population.get_fittest(1)[0]
            if elite_defense.get_fitness() >= self.config.target_fitness:
                print(f"✅ Target fitness {self.config.target_fitness} achieved!")
                break
            
            # Adapt mutation strategy based on progress
            avg_defense_fitness = np.mean([g.get_fitness() for g in self.defense_population.genomes])
            self.mutation_engine.adaptive_mutation_strategy(avg_defense_fitness)
        
        return self._get_final_results()
    
    def _run_battles(self) -> int:
        """Execute battles between attack and defense genomes"""
        battles_count = 0
        battles_per_defense = max(1, self.config.population_size // 10)
        
        for defense_genome in self.defense_population.genomes:
            # Each defense genome fights multiple attack genomes
            opponents = np.random.choice(
                self.attack_population.genomes,
                size=min(battles_per_defense, len(self.attack_population.genomes)),
                replace=False
            )
            
            for attack_genome in opponents:
                result = self._simulate_battle(attack_genome, defense_genome)
                battles_count += 1
                
                # Update genome records
                if result.winner == "defender":
                    defense_genome.wins += 1
                    attack_genome.losses += 1
                elif result.winner == "attacker":
                    attack_genome.wins += 1
                    defense_genome.losses += 1
                else:
                    defense_genome.draw_count += 1
                    attack_genome.draw_count += 1
        
        self.total_battles += battles_count
        return battles_count
    
    def _simulate_battle(self, 
                        attack_genome: StrategyGenome,
                        defense_genome: StrategyGenome) -> BattleResult:
        """Simulate battle between two strategies"""
        # Extract strategy parameters
        attack_phenotype = attack_genome.get_gene_expression_profile()
        defense_phenotype = defense_genome.get_gene_expression_profile()
        
        # Simulate engagement
        attack_aggressiveness = attack_phenotype.get('aggressiveness', 0.5)
        defense_response_speed = defense_phenotype.get('response_speed', 0.5)
        
        # Determine winner based on phenotypes
        attack_strength = attack_aggressiveness * 100
        defense_strength = defense_response_speed * 100
        
        # Add randomness
        attack_strength += np.random.normal(0, 20)
        defense_strength += np.random.normal(0, 20)
        
        # Determine outcome
        if attack_strength > defense_strength * 1.2:
            winner = "attacker"
            penetration = 0.7 + np.random.random() * 0.3
            damage_prevented = np.random.random() * 30
        elif defense_strength > attack_strength * 1.2:
            winner = "defender"
            penetration = np.random.random() * 0.3
            damage_prevented = 70 + np.random.random() * 30
        else:
            winner = "draw"
            penetration = 0.4 + np.random.random() * 0.2
            damage_prevented = 50 + np.random.random() * 20
        
        # Create battle result
        result = BattleResult(
            attacker_genome_id=attack_genome.genome_id,
            defender_genome_id=defense_genome.genome_id,
            winner=winner,
            attacker_penetration=penetration,
            defender_detection_time=np.clip(1.0 - defense_response_speed, 0.1, 10.0),
            defender_containment_time=np.clip(0.5 * (1.0 - defense_response_speed), 0.05, 5.0),
            damage_prevented=damage_prevented,
            attacker_resources_used=attack_aggressiveness * 100,
            defender_resources_used=defense_response_speed * 50
        )
        
        return result
    
    def _evaluate_populations(self) -> None:
        """Evaluate fitness of all genomes"""
        for genome in self.defense_population.genomes:
            genome.get_fitness()
        
        for genome in self.attack_population.genomes:
            genome.get_fitness()
    
    def _selection_and_breeding(self) -> None:
        """Select fittest genomes and breed offspring"""
        # Select elite
        elite_defense = self.defense_population.get_fittest(
            max(1, int(self.config.elitism_percent * len(self.defense_population.genomes)))
        )
        elite_attack = self.attack_population.get_fittest(
            max(1, int(self.config.elitism_percent * len(self.attack_population.genomes)))
        )
        
        # Generate offspring through crossover
        offspring_defense = []
        offspring_attack = []
        
        num_offspring = int(self.config.crossover_fraction * len(self.defense_population.genomes))
        
        for _ in range(num_offspring):
            # Select parents
            parent1_d = self._tournament_select(self.defense_population, self.config.tournament_size)
            parent2_d = self._tournament_select(self.defense_population, self.config.tournament_size)
            
            child1_d, child2_d = self.mutation_engine.crossover_and_mutate(parent1_d, parent2_d)
            offspring_defense.extend([child1_d, child2_d])
            
            # Same for attack
            parent1_a = self._tournament_select(self.attack_population, self.config.tournament_size)
            parent2_a = self._tournament_select(self.attack_population, self.config.tournament_size)
            
            child1_a, child2_a = self.mutation_engine.crossover_and_mutate(parent1_a, parent2_a)
            offspring_attack.extend([child1_a, child2_a])
        
        # Update populations (keep elite + add offspring)
        self.defense_population.genomes = elite_defense + offspring_defense[:len(self.defense_population.genomes) - len(elite_defense)]
        self.attack_population.genomes = elite_attack + offspring_attack[:len(self.attack_population.genomes) - len(elite_attack)]
    
    def _apply_mutations(self) -> None:
        """Apply mutations to populations"""
        mutants_defense = self.mutation_engine.mutate_population(
            self.defense_population,
            self.config.mutation_fraction
        )
        
        mutants_attack = self.mutation_engine.mutate_population(
            self.attack_population,
            self.config.mutation_fraction
        )
        
        # Add some mutants to population
        for mutant in mutants_defense[:len(self.defense_population.genomes) // 5]:
            # Replace weakest
            weakest_idx = np.argmin([g.get_fitness() for g in self.defense_population.genomes])
            self.defense_population.genomes[weakest_idx] = mutant
        
        for mutant in mutants_attack[:len(self.attack_population.genomes) // 5]:
            # Replace weakest
            weakest_idx = np.argmin([g.get_fitness() for g in self.attack_population.genomes])
            self.attack_population.genomes[weakest_idx] = mutant
    
    def _tournament_select(self, population: GenomePopulation, tournament_size: int) -> StrategyGenome:
        """Select genome via tournament"""
        candidates = np.random.choice(population.genomes, size=tournament_size, replace=False)
        return max(candidates, key=lambda g: g.get_fitness())
    
    def _record_generation_stats(self, battles: int) -> EvolutionStep:
        """Record statistics for this generation"""
        defense_fitnesses = [g.get_fitness() for g in self.defense_population.genomes]
        attack_fitnesses = [g.get_fitness() for g in self.attack_population.genomes]
        
        defense_elite = max(defense_fitnesses)
        attack_elite = max(attack_fitnesses)
        
        defense_avg = np.mean(defense_fitnesses)
        attack_avg = np.mean(attack_fitnesses)
        
        self.defense_fitness_over_time.append(defense_avg)
        self.attack_fitness_over_time.append(attack_avg)
        
        diversity = self.defense_population.get_diversity_metrics()
        
        step = EvolutionStep(
            generation=self.generation,
            timestamp=datetime.now(),
            population_stats={
                "defense_avg": defense_avg,
                "defense_elite": defense_elite,
                "attack_avg": attack_avg,
                "attack_elite": attack_elite,
            },
            elite_fitness=max(defense_elite, attack_elite),
            average_fitness=(defense_avg + attack_avg) / 2.0,
            diversity=diversity.get("average_diversity", 0.0),
            battles_executed=battles,
            elite_genomes=[g.genome_id for g in self.defense_population.get_fittest(5)]
        )
        
        print(f"   Defense avg: {defense_avg:.3f} | elite: {defense_elite:.3f}")
        print(f"   Attack avg: {attack_avg:.3f} | elite: {attack_elite:.3f}")
        print(f"   Battles: {battles} | Diversity: {step.diversity:.3f}")
        
        return step
    
    def _get_final_results(self) -> Dict[str, Any]:
        """Compile final evolution results"""
        elapsed = datetime.now() - self.start_time
        
        defense_elite = self.defense_population.get_fittest(1)[0]
        attack_elite = self.attack_population.get_fittest(1)[0]
        
        return {
            "status": "evolution_complete",
            "generations_evolved": self.generation + 1,
            "total_battles": self.total_battles,
            "elapsed_time": str(elapsed),
            "elite_defense": {
                "genome_id": defense_elite.genome_id,
                "fitness": defense_elite.get_fitness(),
                "wins": defense_elite.wins,
                "losses": defense_elite.losses,
                "genes": len(defense_elite.genes)
            },
            "elite_attack": {
                "genome_id": attack_elite.genome_id,
                "fitness": attack_elite.get_fitness(),
                "wins": attack_elite.wins,
                "losses": attack_elite.losses,
                "genes": len(attack_elite.genes)
            },
            "defense_fitness_trajectory": self.defense_fitness_over_time[-10:],
            "attack_fitness_trajectory": self.attack_fitness_over_time[-10:],
            "total_mutations": self.mutation_engine.mutation_count,
        }
    
    def get_elite_strategies(self, top_n: int = 5) -> Dict[str, List[Dict]]:
        """Get top N elite strategies from each population"""
        defense_elite = self.defense_population.get_fittest(top_n)
        attack_elite = self.attack_population.get_fittest(top_n)
        
        return {
            "defense_elite": [
                {
                    "genome_id": g.genome_id,
                    "fitness": g.get_fitness(),
                    "genes": g.get_gene_expression_profile(),
                    "generation": g.generation
                }
                for g in defense_elite
            ],
            "attack_elite": [
                {
                    "genome_id": g.genome_id,
                    "fitness": g.get_fitness(),
                    "genes": g.get_gene_expression_profile(),
                    "generation": g.generation
                }
                for g in attack_elite
            ]
        }
