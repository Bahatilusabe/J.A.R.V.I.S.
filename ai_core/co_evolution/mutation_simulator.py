"""
Mutation Simulator - Evolve attack and defense genomes through mutation

Simulates genetic mutations that create variation in populations.
Similar to biological evolution:
- Point mutations (single changes)
- Crossover (combine parent traits)
- Large mutations (radical changes)
- Targeted mutations (based on selection pressure)
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
import random
from copy import deepcopy

from .attacker_genome import (
    AttackerGenome, AttackTactic, EvationTechnique, PayloadCharacteristics
)
from .defense_genome import (
    DefenseGenome, DetectionMethod, ResponseStrategy, HardeningMeasure,
    DetectionConfiguration, ResponseConfiguration
)


class MutationSimulator:
    """Simulates genetic mutations in attack and defense genomes"""
    
    def __init__(self, mutation_rate: float = 0.15, crossover_rate: float = 0.3):
        """
        Initialize simulator
        
        Args:
            mutation_rate: Probability of mutation (0.0-1.0)
            crossover_rate: Probability of crossover during reproduction
        """
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.mutation_history: List[Dict[str, Any]] = []
    
    # ========================================================================
    # ATTACKER MUTATIONS
    # ========================================================================
    
    def mutate_attacker(self, genome: AttackerGenome, intensity: float = 1.0) -> AttackerGenome:
        """
        Mutate an attacker genome
        
        Args:
            genome: Original genome
            intensity: Mutation intensity (0.0-1.0), 1.0 = heavy mutations
        
        Returns:
            Mutated copy of genome
        """
        mutated = deepcopy(genome)
        mutated.genome_id = f"{genome.genome_id}_m{genome.mutation_count + 1}"
        mutated.parent_genome_ids.append(genome.genome_id)
        mutated.mutation_count += 1
        # Simple generation increment (parent.generation + 1)
        mutated.generation = genome.generation + 1
        
        # Chance of mutation
        if random.random() < self.mutation_rate * intensity:
            mutation_type = random.choice([
                self._mutate_tactics,
                self._mutate_evasion,
                self._mutate_payload,
                self._mutate_chain,
            ])
            # Apply mutation and record it
            before = mutated.to_dict() if hasattr(mutated, "to_dict") else {}
            mutation_type(mutated)
            after = mutated.to_dict() if hasattr(mutated, "to_dict") else {}
            effect = "changed" if before != after else "no_change"
            self.record_mutation(mutation_type.__name__, "attacker", genome.genome_id, mutated.genome_id, effect)
        
        return mutated
    
    def _mutate_tactics(self, genome: AttackerGenome) -> None:
        """Add/remove/change attack tactics"""
        operation = random.choice(["add", "remove", "replace"])
        
        if operation == "add" and len(genome.tactics) < 5:
            new_tactic = random.choice(list(AttackTactic))
            if new_tactic not in genome.tactics:
                genome.tactics.append(new_tactic)
        
        elif operation == "remove" and len(genome.tactics) > 1:
            genome.tactics.pop(random.randint(0, len(genome.tactics) - 1))
        
        elif operation == "replace" and genome.tactics:
            idx = random.randint(0, len(genome.tactics) - 1)
            genome.tactics[idx] = random.choice(list(AttackTactic))
    
    def _mutate_evasion(self, genome: AttackerGenome) -> None:
        """Add/remove/change evasion techniques"""
        operation = random.choice(["add", "remove", "replace"])
        
        if operation == "add" and len(genome.evasion_techniques) < 4:
            new_tech = random.choice(list(EvationTechnique))
            if new_tech not in genome.evasion_techniques:
                genome.evasion_techniques.append(new_tech)
        
        elif operation == "remove" and len(genome.evasion_techniques) > 0:
            genome.evasion_techniques.pop(random.randint(0, len(genome.evasion_techniques) - 1))
        
        elif operation == "replace" and genome.evasion_techniques:
            idx = random.randint(0, len(genome.evasion_techniques) - 1)
            genome.evasion_techniques[idx] = random.choice(list(EvationTechnique))
    
    def _mutate_payload(self, genome: AttackerGenome) -> None:
        """Mutate payload characteristics"""
        # Size mutation
        if random.random() < 0.5:
            change = random.randint(-2000, 2000)
            genome.payload.size_bytes = max(100, genome.payload.size_bytes + change)
        
        # Entropy mutation
        if random.random() < 0.5:
            change = random.uniform(-0.3, 0.3)
            genome.payload.entropy = max(0.0, min(1.0, genome.payload.entropy + change))
        
        # Protocol mutation
        if random.random() < 0.3:
            genome.payload.c2_protocol = random.choice([
                "tcp", "udp", "https", "dns", "http", "icmp", "gre", "ssh"
            ])
        
        # Beacon interval mutation (faster/slower)
        if random.random() < 0.3:
            factor = random.uniform(0.5, 2.0)
            genome.payload.beacon_interval_ms = int(genome.payload.beacon_interval_ms * factor)
        
        # Jitter mutation
        if random.random() < 0.3:
            genome.payload.jitter_percent = max(0.0, min(100.0, 
                genome.payload.jitter_percent + random.uniform(-20, 20)))
    
    def _mutate_chain(self, genome: AttackerGenome) -> None:
        """Mutate attack chain (sequence of actions)"""
        if not genome.attack_chain:
            genome.attack_chain = ["reconnaissance", "initial_access", "execution"]
            return
        
        operation = random.choice(["add", "remove", "reorder"])
        
        if operation == "add":
            action = random.choice([
                "privilege_escalation", "persistence", "lateral_movement",
                "data_exfiltration", "cleanup", "c2_communication"
            ])
            genome.attack_chain.insert(random.randint(0, len(genome.attack_chain)), action)
        
        elif operation == "remove" and len(genome.attack_chain) > 1:
            genome.attack_chain.pop(random.randint(0, len(genome.attack_chain) - 1))
        
        elif operation == "reorder" and len(genome.attack_chain) > 2:
            i, j = random.sample(range(len(genome.attack_chain)), 2)
            genome.attack_chain[i], genome.attack_chain[j] = genome.attack_chain[j], genome.attack_chain[i]
    
    def crossover_attackers(self, parent1: AttackerGenome, parent2: AttackerGenome) -> List[AttackerGenome]:
        """
        Create offspring by combining parent genomes
        
        Args:
            parent1: First parent genome
            parent2: Second parent genome
        
        Returns:
            List of 2 offspring genomes
        """
        child1 = deepcopy(parent1)
        child2 = deepcopy(parent2)
        
        child1.genome_id = f"offspring_{random.randint(100000, 999999)}_1"
        child2.genome_id = f"offspring_{random.randint(100000, 999999)}_2"
        child1.parent_genome_ids = [parent1.genome_id, parent2.genome_id]
        child2.parent_genome_ids = [parent1.genome_id, parent2.genome_id]
        
        # Split-point crossover for tactics
        split_point = random.randint(0, min(len(parent1.tactics), len(parent2.tactics)))
        child1.tactics = parent1.tactics[:split_point] + parent2.tactics[split_point:]
        child2.tactics = parent2.tactics[:split_point] + parent1.tactics[split_point:]
        
        # Split-point crossover for evasion
        split_point = random.randint(0, min(len(parent1.evasion_techniques), len(parent2.evasion_techniques)))
        child1.evasion_techniques = parent1.evasion_techniques[:split_point] + parent2.evasion_techniques[split_point:]
        child2.evasion_techniques = parent2.evasion_techniques[:split_point] + parent1.evasion_techniques[split_point:]
        
        # Average payload characteristics
        child1.payload = PayloadCharacteristics(
            size_bytes=(parent1.payload.size_bytes + parent2.payload.size_bytes) // 2,
            entropy=(parent1.payload.entropy + parent2.payload.entropy) / 2,
            c2_port=random.choice([parent1.payload.c2_port, parent2.payload.c2_port]),
            c2_protocol=random.choice([parent1.payload.c2_protocol, parent2.payload.c2_protocol]),
            beacon_interval_ms=(parent1.payload.beacon_interval_ms + parent2.payload.beacon_interval_ms) // 2,
            jitter_percent=(parent1.payload.jitter_percent + parent2.payload.jitter_percent) / 2,
            encryption_algorithm=random.choice([parent1.payload.encryption_algorithm, parent2.payload.encryption_algorithm]),
            obfuscation_layers=random.choice([parent1.payload.obfuscation_layers, parent2.payload.obfuscation_layers]),
        )
        child2.payload = deepcopy(child1.payload)
        
        # Record crossover event
        self.record_mutation("crossover", "attacker", parent1.genome_id, child1.genome_id, "offspring_created")
        self.record_mutation("crossover", "attacker", parent2.genome_id, child2.genome_id, "offspring_created")

        return [child1, child2]
    
    # ========================================================================
    # DEFENSE MUTATIONS
    # ========================================================================
    
    def mutate_defense(self, genome: DefenseGenome, intensity: float = 1.0) -> DefenseGenome:
        """
        Mutate a defense genome
        
        Args:
            genome: Original genome
            intensity: Mutation intensity (0.0-1.0), 1.0 = heavy mutations
        
        Returns:
            Mutated copy of genome
        """
        mutated = deepcopy(genome)
        mutated.genome_id = f"{genome.genome_id}_m{genome.mutation_count + 1}"
        mutated.parent_genome_ids.append(genome.genome_id)
        mutated.mutation_count += 1
        mutated.generation = genome.generation + 1
        
        if random.random() < self.mutation_rate * intensity:
            mutation_type = random.choice([
                self._mutate_detection,
                self._mutate_response,
                self._mutate_hardening,
            ])
            before = mutated.to_dict() if hasattr(mutated, "to_dict") else {}
            mutation_type(mutated)
            after = mutated.to_dict() if hasattr(mutated, "to_dict") else {}
            effect = "changed" if before != after else "no_change"
            self.record_mutation(mutation_type.__name__, "defense", genome.genome_id, mutated.genome_id, effect)
        
        return mutated
    
    def _mutate_detection(self, genome: DefenseGenome) -> None:
        """Mutate detection methods and sensitivity"""
        # Change detection methods
        operation = random.choice(["add", "remove", "replace"])
        
        if operation == "add" and len(genome.detection_config.methods) < 4:
            new_method = random.choice(list(DetectionMethod))
            if new_method not in genome.detection_config.methods:
                genome.detection_config.methods.append(new_method)
        
        elif operation == "remove" and len(genome.detection_config.methods) > 1:
            idx = random.randint(0, len(genome.detection_config.methods) - 1)
            genome.detection_config.methods.pop(idx)
        
        elif operation == "replace" and genome.detection_config.methods:
            idx = random.randint(0, len(genome.detection_config.methods) - 1)
            genome.detection_config.methods[idx] = random.choice(list(DetectionMethod))
        
        # Adjust sensitivity (trade-off: more sensitive = more FP)
        if random.random() < 0.5:
            change = random.uniform(-0.2, 0.2)
            genome.detection_config.sensitivity_level = max(0.1, min(0.95, 
                genome.detection_config.sensitivity_level + change))
        
        # Adjust latency
        if random.random() < 0.3:
            factor = random.uniform(0.7, 1.5)
            genome.detection_config.detection_latency_ms = int(
                genome.detection_config.detection_latency_ms * factor)
    
    def _mutate_response(self, genome: DefenseGenome) -> None:
        """Mutate response strategy"""
        if random.random() < 0.5:
            genome.response_config.primary_strategy = random.choice(list(ResponseStrategy))
        
        if random.random() < 0.3:
            genome.response_config.auto_remediate = not genome.response_config.auto_remediate
        
        if random.random() < 0.3:
            genome.response_config.escalation_enabled = not genome.response_config.escalation_enabled
    
    def _mutate_hardening(self, genome: DefenseGenome) -> None:
        """Mutate hardening measures"""
        operation = random.choice(["add", "remove", "replace"])
        
        if operation == "add" and len(genome.hardening_measures) < 5:
            new_measure = random.choice(list(HardeningMeasure))
            if new_measure not in genome.hardening_measures:
                genome.hardening_measures.append(new_measure)
        
        elif operation == "remove" and len(genome.hardening_measures) > 1:
            idx = random.randint(0, len(genome.hardening_measures) - 1)
            genome.hardening_measures.pop(idx)
        
        elif operation == "replace" and genome.hardening_measures:
            idx = random.randint(0, len(genome.hardening_measures) - 1)
            genome.hardening_measures[idx] = random.choice(list(HardeningMeasure))
    
    def crossover_defenses(self, parent1: DefenseGenome, parent2: DefenseGenome) -> List[DefenseGenome]:
        """
        Create offspring by combining parent defense genomes
        
        Args:
            parent1: First parent genome
            parent2: Second parent genome
        
        Returns:
            List of 2 offspring genomes
        """
        child1 = deepcopy(parent1)
        child2 = deepcopy(parent2)
        
        child1.genome_id = f"offspring_{random.randint(100000, 999999)}_1"
        child2.genome_id = f"offspring_{random.randint(100000, 999999)}_2"
        child1.parent_genome_ids = [parent1.genome_id, parent2.genome_id]
        child2.parent_genome_ids = [parent1.genome_id, parent2.genome_id]
        
        # Crossover detection methods
        split_point = random.randint(0, min(len(parent1.detection_config.methods), len(parent2.detection_config.methods)))
        child1.detection_config.methods = parent1.detection_config.methods[:split_point] + parent2.detection_config.methods[split_point:]
        child2.detection_config.methods = parent2.detection_config.methods[:split_point] + parent1.detection_config.methods[split_point:]
        
        # Average detection parameters
        child1.detection_config.sensitivity_level = (parent1.detection_config.sensitivity_level + parent2.detection_config.sensitivity_level) / 2
        child2.detection_config.sensitivity_level = child1.detection_config.sensitivity_level
        
        # Crossover hardening measures
        split_point = random.randint(0, min(len(parent1.hardening_measures), len(parent2.hardening_measures)))
        child1.hardening_measures = parent1.hardening_measures[:split_point] + parent2.hardening_measures[split_point:]
        child2.hardening_measures = parent2.hardening_measures[:split_point] + parent1.hardening_measures[split_point:]
        
        # Record crossover events
        self.record_mutation("crossover", "defense", parent1.genome_id, child1.genome_id, "offspring_created")
        self.record_mutation("crossover", "defense", parent2.genome_id, child2.genome_id, "offspring_created")

        return [child1, child2]
    
    def record_mutation(self, mutation_type: str, genome_type: str, parent_id: str, 
                       child_id: str, effect: str) -> None:
        """Record mutation in history"""
        self.mutation_history.append({
            "timestamp": datetime.utcnow(),
            "mutation_type": mutation_type,
            "genome_type": genome_type,
            "parent_id": parent_id,
            "child_id": child_id,
            "effect": effect,
        })
