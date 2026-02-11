"""
Attacker Genome - Evolutionary representation of attack strategies

This module represents attack patterns as genomes that evolve and mutate.
Each attack has:
- Tactics (initial access, persistence, privilege escalation, etc.)
- Evasion techniques (obfuscation, timing, decoys, etc.)
- Payload characteristics (size, entropy, C2 patterns, etc.)
- Success/failure history (fitness score)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple
from enum import Enum
import hashlib
import random
from uuid import uuid4


class AttackTactic(Enum):
    """MITRE ATT&CK Framework tactics"""
    RECONNAISSANCE = "reconnaissance"
    RESOURCE_DEVELOPMENT = "resource_development"
    INITIAL_ACCESS = "initial_access"
    EXECUTION = "execution"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_ACCESS = "credential_access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral_movement"
    COLLECTION = "collection"
    COMMAND_AND_CONTROL = "command_and_control"
    EXFILTRATION = "exfiltration"
    IMPACT = "impact"


class EvationTechnique(Enum):
    """Evasion methods"""
    OBFUSCATION = "obfuscation"
    TIMING_VARIATION = "timing_variation"
    ENCRYPTION = "encryption"
    DECOY_TRAFFIC = "decoy_traffic"
    PROTOCOL_SWITCHING = "protocol_switching"
    FRAGMENTATION = "fragmentation"
    POLYMORPHISM = "polymorphism"
    ANTI_ANALYSIS = "anti_analysis"
    FOOTPRINT_MINIMIZATION = "footprint_minimization"


@dataclass
class PayloadCharacteristics:
    """Describes payload properties"""
    size_bytes: int
    entropy: float  # 0.0-1.0, higher = more random
    c2_port: int
    c2_protocol: str  # tcp, udp, https, dns, etc.
    beacon_interval_ms: int
    jitter_percent: float
    encryption_algorithm: str
    obfuscation_layers: int


@dataclass
class AttackerGenome:
    """Genome representing an attack strategy"""
    
    # Identity
    genome_id: str = field(default_factory=lambda: str(uuid4()))
    attack_name: str = ""
    parent_genome_ids: List[str] = field(default_factory=list)
    
    # Evolutionary properties
    generation: int = 0
    mutation_count: int = 0
    creation_time: datetime = field(default_factory=datetime.utcnow)
    
    # Attack composition
    tactics: List[AttackTactic] = field(default_factory=list)
    evasion_techniques: List[EvationTechnique] = field(default_factory=list)
    payload: PayloadCharacteristics = field(default_factory=lambda: PayloadCharacteristics(
        size_bytes=5000,
        entropy=0.7,
        c2_port=443,
        c2_protocol="https",
        beacon_interval_ms=60000,
        jitter_percent=20.0,
        encryption_algorithm="aes-256-cbc",
        obfuscation_layers=2
    ))
    
    # Behavior patterns
    attack_chain: List[str] = field(default_factory=list)  # Sequence of commands/actions
    lateral_movement_target_count: int = 0
    exfiltration_channels: List[str] = field(default_factory=list)
    
    # Fitness tracking
    total_attempts: int = 0
    successful_attempts: int = 0
    detection_evasion_rate: float = 0.0  # % of times it evaded detection
    average_duration_minutes: float = 0.0
    impact_score: float = 0.0  # 0-1, higher = more damage
    
    # Defense resistance
    known_iocs: Set[str] = field(default_factory=set)  # Indicators of compromise
    known_signatures: Set[str] = field(default_factory=set)
    known_behaviors: Set[str] = field(default_factory=set)
    
    # Metadata
    data: Dict[str, any] = field(default_factory=dict)
    notes: str = ""
    
    def __hash__(self) -> int:
        """Hash based on genome content"""
        content = f"{self.tactics}{self.evasion_techniques}{self.payload}"
        return int(hashlib.md5(content.encode()).hexdigest(), 16)
    
    def calculate_fitness(self) -> float:
        """
        Calculate fitness score (0-1)
        
        Higher fitness = more successful attack
        Combines:
        - Success rate
        - Evasion ability
        - Impact achieved
        - Resistance to known defenses
        """
        if self.total_attempts == 0:
            return 0.0
        
        success_rate = self.successful_attempts / self.total_attempts
        evasion_score = self.detection_evasion_rate
        impact_weighted = self.impact_score * 0.5
        
        # Heavily penalize if known to defenses
        known_factor = max(0.0, 1.0 - len(self.known_signatures) * 0.1)
        
        fitness = (success_rate * 0.4 + evasion_score * 0.3 + 
                  impact_weighted * 0.2 + known_factor * 0.1)
        
        return min(1.0, max(0.0, fitness))
    
    def get_genome_string(self) -> str:
        """Get compact string representation of genome"""
        tactics_str = ",".join([t.value[0] for t in self.tactics])
        evasion_str = ",".join([e.value[0] for e in self.evasion_techniques])
        payload_str = f"{self.payload.size_bytes}b-{self.payload.entropy:.1f}e-{self.payload.c2_protocol}"
        
        return f"[{tactics_str}|{evasion_str}|{payload_str}]"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/transmission"""
        return {
            "genome_id": self.genome_id,
            "attack_name": self.attack_name,
            "generation": self.generation,
            "mutation_count": self.mutation_count,
            "tactics": [t.value for t in self.tactics],
            "evasion_techniques": [e.value for e in self.evasion_techniques],
            "fitness": self.calculate_fitness(),
            "success_rate": self.successful_attempts / max(1, self.total_attempts),
            "detection_evasion_rate": self.detection_evasion_rate,
            "impact_score": self.impact_score,
            "total_attempts": self.total_attempts,
            "known_signatures_count": len(self.known_signatures),
            "known_behaviors_count": len(self.known_behaviors),
        }


@dataclass
class AttackerPopulation:
    """Population of attacker genomes"""
    
    population_id: str = field(default_factory=lambda: str(uuid4()))
    genomes: List[AttackerGenome] = field(default_factory=list)
    generation: int = 0
    creation_time: datetime = field(default_factory=datetime.utcnow)
    
    # Statistics
    total_attacks_simulated: int = 0
    average_fitness: float = 0.0
    max_fitness_achieved: float = 0.0
    
    def add_genome(self, genome: AttackerGenome) -> None:
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
    
    def get_fittest(self, count: int = 1) -> List[AttackerGenome]:
        """Get top fittest genomes"""
        sorted_genomes = sorted(
            self.genomes,
            key=lambda g: g.calculate_fitness(),
            reverse=True
        )
        return sorted_genomes[:count]
    
    def get_least_fit(self, count: int = 1) -> List[AttackerGenome]:
        """Get least fit genomes (candidates for extinction)"""
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
        
        # Compare hashes of genomes
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
            "total_attacks_simulated": self.total_attacks_simulated,
            "fittest_genomes": [g.to_dict() for g in self.get_fittest(5)],
        }
