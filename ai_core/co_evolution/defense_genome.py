"""
Defense Genome - Evolutionary representation of defense strategies

This module represents defense mechanisms as genomes that evolve and adapt.
Each defense has:
- Detection methods (signature, behavioral, anomaly, etc.)
- Response strategies (block, isolate, alert, investigate, etc.)
- Hardening measures (encryption, MFA, segmentation, etc.)
- Success/failure history (fitness score)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple
from enum import Enum
import hashlib
import random
from uuid import uuid4


class DetectionMethod(Enum):
    """Detection approaches"""
    SIGNATURE_MATCHING = "signature_matching"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"
    ANOMALY_DETECTION = "anomaly_detection"
    HEURISTIC_ANALYSIS = "heuristic_analysis"
    SANDBOXING = "sandboxing"
    NETWORK_ANALYSIS = "network_analysis"
    MEMORY_FORENSICS = "memory_forensics"
    FILE_ANALYSIS = "file_analysis"
    THREAT_INTELLIGENCE = "threat_intelligence"


class ResponseStrategy(Enum):
    """Response actions"""
    ALERT = "alert"
    BLOCK = "block"
    ISOLATE = "isolate"
    KILL_PROCESS = "kill_process"
    QUARANTINE = "quarantine"
    REMEDIATE = "remediate"
    ROLLBACK = "rollback"
    INVESTIGATE = "investigate"


class HardeningMeasure(Enum):
    """Hardening techniques"""
    ENCRYPTION = "encryption"
    MFA = "mfa"
    SEGMENTATION = "segmentation"
    LEAST_PRIVILEGE = "least_privilege"
    ENDPOINT_HARDENING = "endpoint_hardening"
    NETWORK_HARDENING = "network_hardening"
    APPLICATION_HARDENING = "application_hardening"
    BEHAVIORAL_CONTROLS = "behavioral_controls"


@dataclass
class DetectionConfiguration:
    """Describes detection setup"""
    methods: List[DetectionMethod]
    sensitivity_level: float  # 0.0-1.0, higher = more sensitive (more FP)
    false_positive_tolerance: float  # % acceptable FP
    detection_latency_ms: int  # How fast detection occurs
    coverage_percent: float  # % of infrastructure covered


@dataclass
class ResponseConfiguration:
    """Describes response setup"""
    primary_strategy: ResponseStrategy
    fallback_strategies: List[ResponseStrategy]
    auto_remediate: bool
    human_approval_required: bool
    approval_timeout_minutes: int
    escalation_enabled: bool


@dataclass
class DefenseGenome:
    """Genome representing a defense strategy"""
    
    # Identity
    genome_id: str = field(default_factory=lambda: str(uuid4()))
    defense_name: str = ""
    parent_genome_ids: List[str] = field(default_factory=list)
    
    # Evolutionary properties
    generation: int = 0
    mutation_count: int = 0
    creation_time: datetime = field(default_factory=datetime.utcnow)
    
    # Defense composition
    detection_config: DetectionConfiguration = field(default_factory=lambda: DetectionConfiguration(
        methods=[DetectionMethod.ANOMALY_DETECTION, DetectionMethod.BEHAVIORAL_ANALYSIS],
        sensitivity_level=0.7,
        false_positive_tolerance=1.0,
        detection_latency_ms=500,
        coverage_percent=100.0
    ))
    
    response_config: ResponseConfiguration = field(default_factory=lambda: ResponseConfiguration(
        primary_strategy=ResponseStrategy.ALERT,
        fallback_strategies=[ResponseStrategy.BLOCK],
        auto_remediate=False,
        human_approval_required=True,
        approval_timeout_minutes=15,
        escalation_enabled=True
    ))
    
    hardening_measures: List[HardeningMeasure] = field(default_factory=lambda: [
        HardeningMeasure.ENCRYPTION,
        HardeningMeasure.SEGMENTATION,
        HardeningMeasure.LEAST_PRIVILEGE
    ])
    
    # Defense scope
    protected_assets: List[str] = field(default_factory=list)
    threat_model: List[str] = field(default_factory=list)  # Types of attacks defended against
    
    # Performance metrics
    total_attacks_faced: int = 0
    attacks_detected: int = 0
    attacks_blocked: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    average_response_time_ms: float = 0.0
    
    # Effectiveness tracking
    mean_time_to_detect_minutes: float = 0.0
    mean_time_to_respond_minutes: float = 0.0
    impact_prevented_percent: float = 0.0
    cost_of_defense: float = 0.0  # Operational cost
    
    # Metadata
    data: Dict[str, any] = field(default_factory=dict)
    notes: str = ""
    
    def __hash__(self) -> int:
        """Hash based on genome content"""
        content = (f"{self.detection_config.methods}|{self.detection_config.sensitivity_level}|"
                  f"{self.response_config.primary_strategy}|{self.hardening_measures}")
        return int(hashlib.md5(content.encode()).hexdigest(), 16)
    
    def calculate_fitness(self) -> float:
        """
        Calculate fitness score (0-1)
        
        Higher fitness = more effective defense
        Combines:
        - Detection rate
        - Response speed
        - Impact prevented
        - Cost efficiency
        """
        if self.total_attacks_faced == 0:
            return 0.5  # Default for untested defenses
        
        detection_rate = self.attacks_detected / self.total_attacks_faced
        blocking_rate = self.attacks_blocked / max(1, self.attacks_detected)
        
        # FP rate should be low
        fp_rate = self.false_positives / max(1, self.total_attacks_faced)
        fp_penalty = min(0.5, fp_rate * 5.0)  # Heavy penalty for FPs
        
        # Response speed: faster is better
        response_score = max(0.0, 1.0 - (self.average_response_time_ms / 5000.0))
        
        # Impact prevention: higher is better
        impact_score = self.impact_prevented_percent / 100.0
        
        # Cost efficiency: lower cost is better
        cost_penalty = min(0.3, self.cost_of_defense / 100000.0)
        
        fitness = (detection_rate * 0.35 + blocking_rate * 0.25 +
                  response_score * 0.15 + impact_score * 0.15 - fp_penalty * 0.1 - cost_penalty * 0.1)
        
        return min(1.0, max(0.0, fitness))
    
    def get_genome_string(self) -> str:
        """Get compact string representation of genome"""
        detection_str = ",".join([m.value[0] for m in self.detection_config.methods])
        response_str = self.response_config.primary_strategy.value[0]
        hardening_str = ",".join([h.value[0] for h in self.hardening_measures])
        
        return f"[{detection_str}|{response_str}|{hardening_str}|{self.detection_config.sensitivity_level:.1f}]"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/transmission"""
        return {
            "genome_id": self.genome_id,
            "defense_name": self.defense_name,
            "generation": self.generation,
            "mutation_count": self.mutation_count,
            "detection_methods": [m.value for m in self.detection_config.methods],
            "primary_response": self.response_config.primary_strategy.value,
            "hardening_measures": [h.value for h in self.hardening_measures],
            "fitness": self.calculate_fitness(),
            "detection_rate": self.attacks_detected / max(1, self.total_attacks_faced),
            "blocking_rate": self.attacks_blocked / max(1, self.attacks_detected),
            "false_positive_rate": self.false_positives / max(1, self.total_attacks_faced),
            "average_response_time_ms": self.average_response_time_ms,
            "impact_prevented_percent": self.impact_prevented_percent,
        }


@dataclass
class DefensePopulation:
    """Population of defense genomes"""
    
    population_id: str = field(default_factory=lambda: str(uuid4()))
    genomes: List[DefenseGenome] = field(default_factory=list)
    generation: int = 0
    creation_time: datetime = field(default_factory=datetime.utcnow)
    
    # Statistics
    total_attacks_defended: int = 0
    average_fitness: float = 0.0
    max_fitness_achieved: float = 0.0
    
    def add_genome(self, genome: DefenseGenome) -> None:
        """Add genome to population"""
        self.genomes.append(genome)
        self._update_statistics()
    
    def remove_genome(self, genome_id: str) -> bool:
        """Remove genome by ID"""
        before = len(self.genomes)
        self.genomes = [g for g in self.genomes if g.genome_id != genome_id]
        if len(self.genomes) < before:
            self._update_statistics()
            return True
        return False
    
    def get_fittest(self, count: int = 1) -> List[DefenseGenome]:
        """Get top fittest genomes"""
        sorted_genomes = sorted(
            self.genomes,
            key=lambda g: g.calculate_fitness(),
            reverse=True
        )
        return sorted_genomes[:count]
    
    def get_weakest(self, count: int = 1) -> List[DefenseGenome]:
        """Get weakest genomes (candidates for replacement)"""
        sorted_genomes = sorted(
            self.genomes,
            key=lambda g: g.calculate_fitness(),
            reverse=False
        )
        return sorted_genomes[:count]
    
    def _update_statistics(self) -> None:
        """Update population statistics"""
        if not self.genomes:
            self.average_fitness = 0.0
            self.max_fitness_achieved = 0.0
            return
        
        fitness_scores = [g.calculate_fitness() for g in self.genomes]
        self.average_fitness = sum(fitness_scores) / len(fitness_scores)
        self.max_fitness_achieved = max(fitness_scores)
    
    def diversity_score(self) -> float:
        """
        Calculate population diversity (0-1)
        1.0 = all genomes unique
        0.0 = all identical
        """
        if len(self.genomes) < 2:
            return 0.0
        
        genome_hashes = [hash(g) for g in self.genomes]
        unique_hashes = len(set(genome_hashes))
        
        return unique_hashes / len(self.genomes)
    
    def to_dict(self) -> Dict:
        """Convert population to dictionary"""
        return {
            "population_id": self.population_id,
            "generation": self.generation,
            "population_size": len(self.genomes),
            "average_fitness": self.average_fitness,
            "max_fitness_achieved": self.max_fitness_achieved,
            "diversity_score": self.diversity_score(),
            "total_attacks_defended": self.total_attacks_defended,
            "fittest_genomes": [g.to_dict() for g in self.get_fittest(5)],
        }
