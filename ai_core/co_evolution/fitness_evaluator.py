"""
Fitness Evaluator - Evaluate and rank genomes based on performance

Simulates attacks against defenses and measures outcomes.
Updates fitness scores based on:
- Attack success/failure
- Detection/evasion
- Impact
- Cost
- Sustainability (how long it lasts before being detected)
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import random
from uuid import uuid4

from .attacker_genome import AttackerGenome, AttackerPopulation
from .defense_genome import DefenseGenome, DefensePopulation, ResponseStrategy


class CombatOutcome(Enum):
    """Result of attack vs defense simulation"""
    ATTACK_SUCCESS = "attack_success"           # Attack succeeded, not detected
    ATTACK_DETECTED = "attack_detected"         # Attack detected before major impact
    ATTACK_BLOCKED = "attack_blocked"           # Attack blocked before execution
    ATTACK_MITIGATED = "attack_mitigated"       # Attack detected and response applied
    DEFENSE_FAILURE = "defense_failure"         # Defense failed unexpectedly
    MUTUAL_DESTRUCTION = "mutual_destruction"   # Both damaged significantly


@dataclass
class CombatSimulation:
    """Result of simulating attack vs defense"""
    
    simulation_id: str = ""
    timestamp: datetime = None
    
    # Participants
    attacker_genome_id: str = ""
    defense_genome_id: str = ""
    
    # Outcome
    outcome: CombatOutcome = CombatOutcome.ATTACK_SUCCESS
    duration_seconds: int = 0
    
    # Attack metrics
    attack_damage: float = 0.0  # 0-1, impact achieved
    attack_detected: bool = False
    detection_time_seconds: Optional[int] = None
    data_exfiltrated_bytes: int = 0
    systems_compromised: int = 0
    
    # Defense metrics
    response_triggered: bool = False
    response_time_seconds: Optional[int] = None
    containment_success: bool = False
    false_positive: bool = False
    
    # Outcome scores
    attacker_score: float = 0.0  # 0-1, higher = better for attacker
    defender_score: float = 0.0  # 0-1, higher = better for defender
    
    def __post_init__(self):
        if not self.simulation_id:
            self.simulation_id = str(uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class FitnessEvaluator:
    """Evaluates fitness of genomes through simulated combat"""
    
    def __init__(self, simulation_duration_seconds: int = 3600):
        """
        Initialize fitness evaluator
        
        Args:
            simulation_duration_seconds: How long each simulated attack lasts
        """
        self.simulation_duration_seconds = simulation_duration_seconds
        self.combat_history: List[CombatSimulation] = []
        self.total_simulations_run = 0
    
    def simulate_combat(self, attacker: AttackerGenome, defender: DefenseGenome) -> CombatSimulation:
        """
        Simulate attack vs defense engagement
        
        Args:
            attacker: Attack genome
            defender: Defense genome
        
        Returns:
            CombatSimulation result
        """
        combat = CombatSimulation(
            attacker_genome_id=attacker.genome_id,
            defense_genome_id=defender.genome_id,
        )
        
        # Simulate attack progression
        detection_occurred = self._simulate_detection(attacker, defender, combat)
        
        if detection_occurred:
            # Defense detects attack
            combat.attack_detected = True
            combat.response_triggered = True
            response_success = self._simulate_response(defender, combat)
            
            if response_success:
                combat.outcome = CombatOutcome.ATTACK_MITIGATED
                combat.containment_success = True
                combat.attacker_score = 0.2
                combat.defender_score = 0.9
            else:
                combat.outcome = CombatOutcome.ATTACK_DETECTED
                combat.attacker_score = 0.5
                combat.defender_score = 0.5
        else:
            # Attack proceeds undetected
            if self._check_if_blocked_early(attacker, defender):
                combat.outcome = CombatOutcome.ATTACK_BLOCKED
                combat.attacker_score = 0.1
                combat.defender_score = 0.95
            else:
                # Attack succeeds
                combat.attack_damage = self._calculate_attack_damage(attacker)
                combat.systems_compromised = random.randint(1, 50)
                combat.data_exfiltrated_bytes = random.randint(10000, 10000000)
                combat.outcome = CombatOutcome.ATTACK_SUCCESS
                combat.attacker_score = 0.9
                combat.defender_score = 0.1
        
        # Update genomes with results
        self._update_genome_stats(attacker, defender, combat)
        
        # Record combat
        self.combat_history.append(combat)
        self.total_simulations_run += 1
        
        return combat
    
    def _simulate_detection(self, attacker: AttackerGenome, defender: DefenseGenome, 
                           combat: CombatSimulation) -> bool:
        """
        Simulate whether defense detects attack
        
        Returns:
            True if detected, False if evades
        """
        # Detection chance based on:
        # - Defense sensitivity
        # - Number of detection methods
        # - Attacker evasion techniques
        
        defense_strength = (
            len(defender.detection_config.methods) * 0.15 +
            defender.detection_config.sensitivity_level * 0.5 +
            defender.detection_config.coverage_percent / 100.0 * 0.35
        )
        
        evasion_strength = (
            len(attacker.evasion_techniques) * 0.25 +
            attacker.payload.entropy * 0.3 +
            len([t for t in attacker.tactics if t.value == "defense_evasion"]) * 0.2
        )
        
        detection_probability = min(0.95, max(0.05, defense_strength - evasion_strength * 0.5))
        
        if random.random() < detection_probability:
            # Detection time depends on methods and latency
            base_latency = defender.detection_config.detection_latency_ms / 1000.0
            variation = random.uniform(0.5, 2.0)
            combat.detection_time_seconds = int(base_latency * variation)
            return True
        
        return False
    
    def _check_if_blocked_early(self, attacker: AttackerGenome, defender: DefenseGenome) -> bool:
        """Check if attack is blocked before execution"""
        # Preventive defenses
        hardening_score = len(defender.hardening_measures) * 0.2
        
        # Initial access difficulty
        initial_access_difficulty = 0.5 if len(attacker.tactics) > 0 else 0.1
        
        block_probability = min(0.5, max(0.05, hardening_score * initial_access_difficulty))
        
        return random.random() < block_probability
    
    def _simulate_response(self, defender: DefenseGenome, combat: CombatSimulation) -> bool:
        """
        Simulate response effectiveness
        
        Returns:
            True if response successful, False otherwise
        """
        # Response time depends on strategy and automation
        if defender.response_config.auto_remediate:
            response_latency = 5 + random.randint(0, 10)  # Seconds
        else:
            response_latency = 300 + random.randint(0, 600)  # 5-15 minutes
        
        combat.response_time_seconds = response_latency
        
        # Response strategy effectiveness
        strategy_effectiveness = {
            ResponseStrategy.ALERT: 0.3,
            ResponseStrategy.BLOCK: 0.7,
            ResponseStrategy.ISOLATE: 0.85,
            ResponseStrategy.KILL_PROCESS: 0.8,
            ResponseStrategy.QUARANTINE: 0.75,
            ResponseStrategy.REMEDIATE: 0.9,
            ResponseStrategy.ROLLBACK: 0.95,
        }
        
        success_probability = strategy_effectiveness.get(
            defender.response_config.primary_strategy, 0.5)
        
        return random.random() < success_probability
    
    def _calculate_attack_damage(self, attacker: AttackerGenome) -> float:
        """Calculate damage score if attack succeeds (0-1)"""
        # Damage from:
        # - Number of compromised systems
        # - Impact of tactics used
        # - Duration of compromise
        
        tactic_impact = len(attacker.tactics) * 0.15
        payload_impact = attacker.payload.entropy * 0.3
        chain_length_impact = min(0.4, len(attacker.attack_chain) * 0.08)
        
        damage = min(1.0, tactic_impact + payload_impact + chain_length_impact)
        
        return damage
    
    def _update_genome_stats(self, attacker: AttackerGenome, defender: DefenseGenome,
                            combat: CombatSimulation) -> None:
        """Update genome statistics based on combat result"""
        
        # Update attacker stats
        attacker.total_attempts += 1
        if combat.outcome == CombatOutcome.ATTACK_SUCCESS:
            attacker.successful_attempts += 1
            attacker.detection_evasion_rate = (attacker.successful_attempts / 
                                             attacker.total_attempts)
            attacker.impact_score = combat.attack_damage
        elif combat.outcome == CombatOutcome.ATTACK_DETECTED:
            attacker.detection_evasion_rate = ((attacker.successful_attempts) / 
                                              attacker.total_attempts)
        
        # Update defender stats
        defender.total_attacks_faced += 1
        
        if combat.outcome in [CombatOutcome.ATTACK_BLOCKED, CombatOutcome.ATTACK_MITIGATED]:
            defender.attacks_detected += 1
            if combat.containment_success:
                defender.attacks_blocked += 1
        
        if combat.false_positive:
            defender.false_positives += 1
        
        defender.average_response_time_ms = (
            (defender.average_response_time_ms * (defender.total_attacks_faced - 1) +
             (combat.response_time_seconds * 1000 if combat.response_time_seconds else 0)) /
            defender.total_attacks_faced
        )
        
        if combat.containment_success:
            defender.impact_prevented_percent = 100.0
        else:
            defender.impact_prevented_percent = max(0.0, 
                100.0 * (1.0 - combat.attack_damage))
    
    def evaluate_population_fitness(self, attackers: AttackerPopulation, 
                                   defenders: DefensePopulation,
                                   simulations_per_pair: int = 5) -> Dict[str, Any]:
        """
        Run full population simulations
        
        Args:
            attackers: Attacker population
            defenders: Defense population
            simulations_per_pair: How many times to simulate each pair
        
        Returns:
            Summary of results
        """
        results = {
            "total_combats": 0,
            "attacker_wins": 0,
            "defender_wins": 0,
            "mutual": 0,
            "attacker_population_avg_fitness": 0.0,
            "defender_population_avg_fitness": 0.0,
            "combat_results": []
        }
        
        # Run combat simulations
        for _ in range(simulations_per_pair):
            for attacker in attackers.genomes:
                for defender in defenders.genomes:
                    combat = self.simulate_combat(attacker, defender)
                    results["combat_results"].append(combat)
                    results["total_combats"] += 1
                    
                    if combat.attacker_score > combat.defender_score:
                        results["attacker_wins"] += 1
                    elif combat.defender_score > combat.attacker_score:
                        results["defender_wins"] += 1
                    else:
                        results["mutual"] += 1
        
        # Calculate population fitness
        if attackers.genomes:
            attackers._update_statistics()
            results["attacker_population_avg_fitness"] = attackers.average_fitness
        
        if defenders.genomes:
            defenders._update_statistics()
            results["defender_population_avg_fitness"] = defenders.average_fitness
        
        return results
    
    def get_combat_history(self, limit: int = 100) -> List[CombatSimulation]:
        """Get recent combat history"""
        return self.combat_history[-limit:]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_simulations_run": self.total_simulations_run,
            "simulation_duration_seconds": self.simulation_duration_seconds,
            "recent_combats": [c.__dict__ for c in self.combat_history[-10:]],
        }
