"""
Strategy Genome - Evolution Building Block
🧬 DNA of defense and attack strategies
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import numpy as np
import hashlib


class StrategyType(Enum):
    """Type of strategy"""
    DEFENSE = "defense"
    ATTACK = "attack"
    HYBRID = "hybrid"


class MutationOperator(Enum):
    """Types of mutations"""
    POINT_MUTATION = "point"           # Change single gene
    CROSSOVER = "crossover"            # Combine two genomes
    INVERSION = "inversion"            # Reverse gene sequence
    INSERTION = "insertion"            # Add new genes
    DELETION = "deletion"              # Remove genes
    DUPLICATION = "duplication"        # Copy genes


@dataclass
class Gene:
    """Individual gene in strategy genome"""
    name: str
    value: float                        # 0.0-1.0 gene expression
    mutation_rate: float = 0.1          # Probability this gene mutates
    interaction_strength: float = 0.5   # How strongly this interacts with other genes
    age: int = 0                        # Generations since creation
    last_modified: datetime = field(default_factory=datetime.now)
    
    def mutate(self, magnitude: float = 0.1) -> None:
        """Mutate this gene"""
        # Gaussian mutation with clipping
        delta = np.random.normal(0, magnitude)
        self.value = np.clip(self.value + delta, 0.0, 1.0)
        self.last_modified = datetime.now()
    
    def get_expression(self, environmental_pressure: float = 0.5) -> float:
        """Get actual expression considering age and environment"""
        age_factor = 1.0 - (self.age * 0.01)  # Genes lose potency over time
        env_factor = environmental_pressure * self.interaction_strength
        return self.value * age_factor * (1.0 + env_factor)


@dataclass
class StrategyGenome:
    """Complete strategy genome - DNA of an AI defense or attack strategy"""
    
    # Identity
    genome_id: str
    strategy_type: StrategyType
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    
    # Genes (behavioral blueprints)
    genes: Dict[str, Gene] = field(default_factory=dict)
    
    # Phenotype (expressed traits)
    phenotype: Dict[str, float] = field(default_factory=dict)
    
    # Performance metrics
    fitness_score: float = 0.0
    survival_count: int = 0              # Times survived selection
    reproduction_count: int = 0          # Times reproduced
    
    # Evolution history
    creation_time: datetime = field(default_factory=datetime.now)
    last_evaluation: Optional[datetime] = None
    mutation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Novelty
    novelty_score: float = 0.0           # How different from population
    behavioral_diversity: float = 0.0    # Behavioral uniqueness
    
    # Success metrics
    wins: int = 0                        # Battles won
    losses: int = 0                      # Battles lost
    draw_count: int = 0                  # Draws
    
    def __post_init__(self):
        """Initialize phenotype from genes"""
        self._express_phenotype()
    
    def _express_phenotype(self) -> None:
        """Express genes into phenotype"""
        self.phenotype = {}
        for gene_name, gene in self.genes.items():
            env_pressure = 0.5  # Can be adjusted
            self.phenotype[gene_name] = gene.get_expression(env_pressure)
    
    def add_gene(self, name: str, value: float, mutation_rate: float = 0.1) -> None:
        """Add gene to genome"""
        self.genes[name] = Gene(
            name=name,
            value=np.clip(value, 0.0, 1.0),
            mutation_rate=mutation_rate
        )
        self._express_phenotype()
    
    def mutate(self, operator: MutationOperator, magnitude: float = 0.1) -> None:
        """Apply mutation to this genome"""
        if operator == MutationOperator.POINT_MUTATION:
            self._point_mutation(magnitude)
        elif operator == MutationOperator.INSERTION:
            self._insertion_mutation()
        elif operator == MutationOperator.DELETION:
            self._deletion_mutation()
        elif operator == MutationOperator.DUPLICATION:
            self._duplication_mutation()
        elif operator == MutationOperator.INVERSION:
            self._inversion_mutation()
        
        self.mutation_history.append({
            "operator": operator.value,
            "magnitude": magnitude,
            "timestamp": datetime.now(),
            "pre_fitness": self.fitness_score
        })
        
        self._express_phenotype()
    
    def _point_mutation(self, magnitude: float) -> None:
        """Mutate random gene"""
        if not self.genes:
            return
        
        gene_name = np.random.choice(list(self.genes.keys()))
        self.genes[gene_name].mutate(magnitude)
    
    def _insertion_mutation(self) -> None:
        """Insert new gene"""
        gene_count = len(self.genes)
        new_gene_name = f"gene_{gene_count + 1}"
        self.add_gene(new_gene_name, np.random.random())
    
    def _deletion_mutation(self) -> None:
        """Delete weakest gene"""
        if len(self.genes) <= 1:
            return
        
        weakest = min(self.genes.items(), key=lambda x: x[1].value)
        del self.genes[weakest[0]]
    
    def _duplication_mutation(self) -> None:
        """Duplicate random gene"""
        if not self.genes:
            return
        
        gene_name = np.random.choice(list(self.genes.keys()))
        original = self.genes[gene_name]
        
        new_gene_name = f"{gene_name}_dup"
        self.add_gene(new_gene_name, original.value, original.mutation_rate)
    
    def _inversion_mutation(self) -> None:
        """Invert gene sequence"""
        gene_names = list(self.genes.keys())
        if len(gene_names) < 2:
            return
        
        # Reverse a random segment
        start = np.random.randint(0, len(gene_names) - 1)
        end = np.random.randint(start + 1, len(gene_names))
        
        segment = gene_names[start:end]
        segment.reverse()
        
        for i, gene_name in enumerate(segment):
            # Update order (simplified - just swap values)
            pass
    
    def crossover(self, other: 'StrategyGenome') -> 'StrategyGenome':
        """Breed with another genome to create offspring"""
        offspring = StrategyGenome(
            genome_id=self._generate_id(),
            strategy_type=self.strategy_type,
            generation=max(self.generation, other.generation) + 1,
            parent_ids=[self.genome_id, other.genome_id]
        )
        
        # Inherit genes from both parents
        all_genes = set(self.genes.keys()) | set(other.genes.keys())
        
        for gene_name in all_genes:
            if gene_name in self.genes and gene_name in other.genes:
                # Blend from both parents
                value = (self.genes[gene_name].value + other.genes[gene_name].value) / 2.0
            elif gene_name in self.genes:
                value = self.genes[gene_name].value
            else:
                value = other.genes[gene_name].value
            
            offspring.add_gene(gene_name, value)
        
        return offspring
    
    def get_fitness(self) -> float:
        """Calculate fitness based on performance"""
        total_battles = self.wins + self.losses + self.draw_count
        if total_battles == 0:
            return 0.0
        
        # Win rate + survival + reproduction + novelty
        win_rate = self.wins / total_battles if total_battles > 0 else 0.0
        survival_factor = min(self.survival_count / 10.0, 1.0)
        reproduction_factor = min(self.reproduction_count / 5.0, 1.0)
        
        self.fitness_score = (
            0.5 * win_rate +
            0.2 * survival_factor +
            0.2 * reproduction_factor +
            0.1 * self.novelty_score
        )
        
        return self.fitness_score
    
    def _generate_id(self) -> str:
        """Generate unique genome ID"""
        content = f"{datetime.now().isoformat()}{np.random.random()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def get_gene_expression_profile(self) -> Dict[str, float]:
        """Get complete gene expression for analysis"""
        return {
            name: self.genes[name].get_expression()
            for name in self.genes.keys()
        }
    
    def clone(self) -> 'StrategyGenome':
        """Create exact copy of this genome"""
        clone = StrategyGenome(
            genome_id=self._generate_id(),
            strategy_type=self.strategy_type,
            generation=self.generation,
            parent_ids=[self.genome_id]
        )
        
        for gene_name, gene in self.genes.items():
            clone.add_gene(gene_name, gene.value, gene.mutation_rate)
        
        return clone


class GenomePopulation:
    """Population of genomes undergoing evolution"""
    
    def __init__(self, size: int = 100):
        self.genomes: List[StrategyGenome] = []
        self.size = size
        self.generation = 0
        self.history: List[Dict[str, Any]] = []
    
    def add_genome(self, genome: StrategyGenome) -> None:
        """Add genome to population"""
        self.genomes.append(genome)
    
    def get_fittest(self, n: int = 10) -> List[StrategyGenome]:
        """Get n fittest genomes"""
        sorted_genomes = sorted(self.genomes, key=lambda g: g.get_fitness(), reverse=True)
        return sorted_genomes[:n]
    
    def get_diversity_metrics(self) -> Dict[str, float]:
        """Calculate population diversity"""
        if not self.genomes:
            return {}
        
        # Calculate phenotypic diversity
        phenotypes = [g.get_gene_expression_profile() for g in self.genomes]
        
        # Simple metric: average distance between phenotypes
        total_distance = 0.0
        pairs = 0
        
        for i, p1 in enumerate(phenotypes):
            for p2 in phenotypes[i+1:]:
                # Euclidean distance
                distance = np.sqrt(sum((p1.get(k, 0) - p2.get(k, 0))**2 for k in set(p1.keys()) | set(p2.keys())))
                total_distance += distance
                pairs += 1
        
        avg_diversity = total_distance / pairs if pairs > 0 else 0.0
        
        return {
            "average_diversity": avg_diversity,
            "population_size": len(self.genomes),
            "average_fitness": np.mean([g.get_fitness() for g in self.genomes]),
            "max_fitness": max([g.get_fitness() for g in self.genomes]) if self.genomes else 0.0
        }
    
    def next_generation(self) -> None:
        """Advance to next generation"""
        self.generation += 1
        self.history.append({
            "generation": self.generation,
            "metrics": self.get_diversity_metrics()
        })
