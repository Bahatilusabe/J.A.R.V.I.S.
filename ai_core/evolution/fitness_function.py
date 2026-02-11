"""
Fitness Function - Evolution Scoring
🏆 Measures strategy effectiveness in cyber warfare
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
from enum import Enum


class FitnessMetric(Enum):
    """Types of fitness metrics"""
    WIN_RATE = "win_rate"
    SURVIVAL_RATE = "survival_rate"
    THREAT_DETECTION = "threat_detection"
    RESPONSE_TIME = "response_time"
    FALSE_POSITIVE_RATE = "false_positive_rate"
    RESOURCE_EFFICIENCY = "resource_efficiency"
    ADAPTATION_SPEED = "adaptation_speed"
    NOVELTY = "novelty"


@dataclass
class BattleResult:
    """Result of strategy battle"""
    attacker_genome_id: str
    defender_genome_id: str
    winner: str                         # "attacker", "defender", or "draw"
    
    # Performance metrics
    attacker_penetration: float         # How deep did attack get (0-1)
    defender_detection_time: float      # Seconds to detect
    defender_containment_time: float    # Seconds to contain
    damage_prevented: float             # Percentage of attack stopped (0-100)
    
    # Resource usage
    attacker_resources_used: float
    defender_resources_used: float
    
    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_defender_advantage(self) -> float:
        """Calculate defender advantage (0-1)"""
        # Faster detection = better
        detection_advantage = max(0, 1.0 - defender_detection_time / 10.0)
        
        # Higher damage prevention = better
        prevention_advantage = damage_prevented / 100.0
        
        # Lower penetration = better
        penetration_advantage = 1.0 - attacker_penetration
        
        return (detection_advantage * 0.3 + 
                prevention_advantage * 0.5 + 
                penetration_advantage * 0.2)


@dataclass
class FitnessProfile:
    """Complete fitness assessment of a strategy"""
    genome_id: str
    fitness_scores: Dict[FitnessMetric, float] = field(default_factory=dict)
    weighted_fitness: float = 0.0
    evaluations_count: int = 0
    last_evaluated: datetime = field(default_factory=datetime.now)
    
    # History for trend analysis
    fitness_history: List[Tuple[datetime, float]] = field(default_factory=list)
    
    # Comparative metrics
    percentile_rank: float = 0.0        # Rank in population (0-100)
    relative_fitness: float = 0.0       # vs population average


class FitnessFunction:
    """Comprehensive fitness evaluation for evolutionary selection"""
    
    def __init__(self):
        self.weights: Dict[FitnessMetric, float] = {
            FitnessMetric.WIN_RATE: 0.25,
            FitnessMetric.SURVIVAL_RATE: 0.15,
            FitnessMetric.THREAT_DETECTION: 0.15,
            FitnessMetric.RESPONSE_TIME: 0.15,
            FitnessMetric.FALSE_POSITIVE_RATE: 0.1,
            FitnessMetric.RESOURCE_EFFICIENCY: 0.1,
            FitnessMetric.ADAPTATION_SPEED: 0.05,
            FitnessMetric.NOVELTY: 0.05,
        }
        
        self.battle_history: List[BattleResult] = []
        self.population_fitness_baseline: float = 0.5
    
    def evaluate_battle(self, result: BattleResult) -> Tuple[float, float]:
        """
        Evaluate battle result
        Returns: (attacker_fitness, defender_fitness)
        """
        self.battle_history.append(result)
        
        defender_advantage = result.get_defender_advantage()
        attacker_advantage = 1.0 - defender_advantage
        
        # Winner gets bonus
        if result.winner == "defender":
            defender_fitness = defender_advantage * 1.2
            attacker_fitness = attacker_advantage * 0.8
        elif result.winner == "attacker":
            attacker_fitness = attacker_advantage * 1.2
            defender_fitness = defender_advantage * 0.8
        else:  # draw
            attacker_fitness = 0.5
            defender_fitness = 0.5
        
        return attacker_fitness, defender_fitness
    
    def evaluate_strategy_performance(self, 
                                     genome_id: str,
                                     metrics: Dict[FitnessMetric, float]) -> FitnessProfile:
        """
        Calculate weighted fitness from multiple metrics
        
        metrics: dict of metric -> score (0-1 typically)
        """
        profile = FitnessProfile(genome_id=genome_id)
        profile.fitness_scores = metrics
        
        # Calculate weighted fitness
        weighted_sum = 0.0
        weight_sum = 0.0
        
        for metric, score in metrics.items():
            if metric in self.weights:
                weight = self.weights[metric]
                weighted_sum += score * weight
                weight_sum += weight
        
        profile.weighted_fitness = weighted_sum / weight_sum if weight_sum > 0 else 0.0
        profile.last_evaluated = datetime.now()
        profile.fitness_history.append((datetime.now(), profile.weighted_fitness))
        
        return profile
    
    def evaluate_threat_detection(self, 
                                  true_positives: int,
                                  false_positives: int,
                                  false_negatives: int,
                                  detection_latency_ms: float) -> Dict[FitnessMetric, float]:
        """
        Calculate threat detection fitness metrics
        Returns dict of metrics
        """
        total_positives = true_positives + false_negatives
        total_detections = true_positives + false_positives
        
        # Precision and recall
        precision = true_positives / total_detections if total_detections > 0 else 0.0
        recall = true_positives / total_positives if total_positives > 0 else 0.0
        
        # F1 score
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Latency score (lower is better, max 1.0 at <100ms)
        latency_score = max(0, 1.0 - (detection_latency_ms / 100.0))
        
        # False positive penalty
        fp_rate = 1.0 - min(false_positives / 100.0, 1.0)
        
        return {
            FitnessMetric.THREAT_DETECTION: f1,
            FitnessMetric.RESPONSE_TIME: latency_score,
            FitnessMetric.FALSE_POSITIVE_RATE: fp_rate,
        }
    
    def evaluate_resource_efficiency(self,
                                    cpu_percent: float,
                                    memory_mb: float,
                                    network_mbps: float,
                                    max_cpu: float = 100.0,
                                    max_memory: float = 4096.0,
                                    max_network: float = 1000.0) -> float:
        """
        Calculate resource efficiency (lower usage = higher fitness)
        Returns fitness score 0-1
        """
        cpu_efficiency = 1.0 - (cpu_percent / max_cpu)
        memory_efficiency = 1.0 - (memory_mb / max_memory)
        network_efficiency = 1.0 - (network_mbps / max_network)
        
        efficiency = np.mean([cpu_efficiency, memory_efficiency, network_efficiency])
        return np.clip(efficiency, 0.0, 1.0)
    
    def evaluate_adaptation_speed(self,
                                 detection_time_first: float,
                                 detection_time_subsequent: float,
                                 improvement_percent: float) -> float:
        """
        Evaluate how quickly strategy adapts to new threats
        Returns fitness score 0-1
        """
        # Faster initial detection is better (max 1.0 at <1 second)
        initial_speed = max(0, 1.0 - detection_time_first / 1.0)
        
        # Learning from experience
        learning_effectiveness = improvement_percent / 100.0
        
        # Reuse speed (subsequent detections should be much faster)
        reuse_advantage = max(0, detection_time_first / detection_time_subsequent) if detection_time_subsequent > 0 else 1.0
        reuse_advantage = np.clip(reuse_advantage, 1.0, 10.0) / 10.0
        
        adaptation_fitness = (
            0.3 * initial_speed +
            0.4 * learning_effectiveness +
            0.3 * reuse_advantage
        )
        
        return np.clip(adaptation_fitness, 0.0, 1.0)
    
    def calculate_novelty_score(self, 
                               genome_id: str,
                               genome_behaviors: Dict[str, float],
                               population_behaviors: List[Dict[str, float]]) -> float:
        """
        Calculate novelty of a genome's behavior
        Higher = more unique/novel
        """
        if not population_behaviors:
            return 0.5
        
        # Calculate average distance to population
        distances = []
        for pop_behavior in population_behaviors:
            distance = self._behavioral_distance(genome_behaviors, pop_behavior)
            distances.append(distance)
        
        avg_distance = np.mean(distances)
        max_possible_distance = np.sqrt(len(genome_behaviors))  # Max euclidean distance
        
        novelty = avg_distance / max_possible_distance if max_possible_distance > 0 else 0.0
        return np.clip(novelty, 0.0, 1.0)
    
    def _behavioral_distance(self, behavior1: Dict[str, float], 
                           behavior2: Dict[str, float]) -> float:
        """Euclidean distance between two behavior profiles"""
        all_keys = set(behavior1.keys()) | set(behavior2.keys())
        
        distance_sq = sum(
            (behavior1.get(k, 0.0) - behavior2.get(k, 0.0)) ** 2
            for k in all_keys
        )
        
        return np.sqrt(distance_sq)
    
    def rank_population_fitness(self, 
                               fitness_profiles: List[FitnessProfile]) -> None:
        """
        Rank genomes in population by fitness
        Updates percentile_rank and relative_fitness
        """
        if not fitness_profiles:
            return
        
        fitnesses = [p.weighted_fitness for p in fitness_profiles]
        avg_fitness = np.mean(fitnesses)
        
        for i, profile in enumerate(fitness_profiles):
            # Percentile rank
            rank = sum(1 for f in fitnesses if f < profile.weighted_fitness)
            profile.percentile_rank = (rank / len(fitness_profiles)) * 100.0
            
            # Relative fitness
            profile.relative_fitness = profile.weighted_fitness / avg_fitness if avg_fitness > 0 else 0.0
    
    def get_population_stats(self, 
                            fitness_profiles: List[FitnessProfile]) -> Dict[str, float]:
        """Get population-level statistics"""
        if not fitness_profiles:
            return {}
        
        fitnesses = [p.weighted_fitness for p in fitness_profiles]
        
        return {
            "average_fitness": np.mean(fitnesses),
            "max_fitness": np.max(fitnesses),
            "min_fitness": np.min(fitnesses),
            "std_deviation": np.std(fitnesses),
            "fitness_range": np.max(fitnesses) - np.min(fitnesses),
        }
    
    def identify_elite(self, 
                      fitness_profiles: List[FitnessProfile],
                      percentile: float = 0.1) -> List[FitnessProfile]:
        """
        Identify elite genomes (top percentile)
        percentile: 0.1 = top 10%
        """
        sorted_profiles = sorted(
            fitness_profiles,
            key=lambda p: p.weighted_fitness,
            reverse=True
        )
        
        elite_count = max(1, int(len(sorted_profiles) * percentile))
        return sorted_profiles[:elite_count]
