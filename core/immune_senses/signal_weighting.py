"""
IMMUNE SENSORY SYSTEM - Signal Weighting Engine
============================================
Adaptive weighting of sensory signals based on context, threat level,
and biological attention mechanisms (like reticular activation system).

Key Concept: Not all senses are equally important in all situations.
- During latency attacks: PAIN signals weighted highest
- During reconnaissance: SMELL and VISION weighted highest
- During lateral movement: VISION heavily weighted
- During data exfiltration: MEMORY weighted heavily
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np
from datetime import datetime, timedelta


class AttentionMode(Enum):
    """System attention focus modes"""
    BASELINE = "baseline"           # Normal operations
    ANOMALY_ALERT = "anomaly_alert"  # Spike detected
    ATTACK_MODE = "attack_mode"      # Active threat response
    CRITICAL = "critical"            # System compromise suspected
    FORENSIC = "forensic"            # Post-incident analysis


class ThreatPhase(Enum):
    """Attack lifecycle phases (Lockheed Cyber Kill Chain)"""
    RECONNAISSANCE = "reconnaissance"      # Info gathering
    WEAPONIZATION = "weaponization"        # Tool preparation
    DELIVERY = "delivery"                  # Payload delivery
    EXPLOITATION = "exploitation"          # Initial access
    INSTALLATION = "installation"          # Persistence
    COMMAND_CONTROL = "command_control"    # C2 communication
    LATERAL_MOVEMENT = "lateral_movement"  # Network traversal
    DATA_EXFILTRATION = "data_exfiltration"  # Data theft


@dataclass
class SignalWeight:
    """Weight configuration for a signal type"""
    base_weight: float                          # Default weight (0-1)
    attention_mode_multipliers: Dict[str, float] = field(default_factory=dict)
    threat_phase_multipliers: Dict[str, float] = field(default_factory=dict)
    recency_decay_hours: float = 24.0           # Weight decay over time
    source_reliability: Dict[str, float] = field(default_factory=dict)  # Source -> reliability


@dataclass
class WeightingContext:
    """Context that influences signal weighting"""
    current_threat_level: float         # 0-1 overall threat
    attention_mode: AttentionMode
    suspected_attack_phase: Optional[ThreatPhase] = None
    time_since_alert: Optional[timedelta] = None
    affected_network_segment: Optional[str] = None
    is_high_value_target: bool = False  # VIP hosts
    is_weekend: bool = False
    is_working_hours: bool = True


class AdaptiveWeightingEngine:
    """
    Adaptively weights security signals based on:
    1. Biological attention (importance)
    2. Temporal context (recency)
    3. Threat phase (attack lifecycle)
    4. Source reliability (signal trust)
    5. System attention mode (focus area)
    """
    
    def __init__(self):
        self.weights = self._initialize_default_weights()
        self.source_reliability_scores = self._initialize_source_reliability()
        self.phase_signal_importance = self._initialize_phase_importance()
        
    def _initialize_default_weights(self) -> Dict[str, SignalWeight]:
        """Set baseline signal weights"""
        return {
            "pain": SignalWeight(
                base_weight=0.40,
                attention_mode_multipliers={
                    AttentionMode.BASELINE.value: 1.0,
                    AttentionMode.ANOMALY_ALERT.value: 1.8,
                    AttentionMode.ATTACK_MODE.value: 2.0,
                    AttentionMode.CRITICAL.value: 2.5,
                    AttentionMode.FORENSIC.value: 1.2,
                },
                threat_phase_multipliers={
                    ThreatPhase.EXPLOITATION.value: 2.5,      # Anomalies = compromise
                    ThreatPhase.LATERAL_MOVEMENT.value: 1.8,
                    ThreatPhase.RECONNAISSANCE.value: 1.2,
                },
            ),
            "smell": SignalWeight(
                base_weight=0.25,
                attention_mode_multipliers={
                    AttentionMode.BASELINE.value: 1.0,
                    AttentionMode.ANOMALY_ALERT.value: 1.3,
                    AttentionMode.ATTACK_MODE.value: 1.5,
                    AttentionMode.CRITICAL.value: 2.0,
                    AttentionMode.FORENSIC.value: 1.8,
                },
                threat_phase_multipliers={
                    ThreatPhase.WEAPONIZATION.value: 2.0,
                    ThreatPhase.DELIVERY.value: 2.2,
                    ThreatPhase.RECONNAISSANCE.value: 1.5,
                },
            ),
            "vision": SignalWeight(
                base_weight=0.20,
                attention_mode_multipliers={
                    AttentionMode.BASELINE.value: 1.0,
                    AttentionMode.ANOMALY_ALERT.value: 1.4,
                    AttentionMode.ATTACK_MODE.value: 1.8,
                    AttentionMode.CRITICAL.value: 2.2,
                    AttentionMode.FORENSIC.value: 1.9,
                },
                threat_phase_multipliers={
                    ThreatPhase.LATERAL_MOVEMENT.value: 2.5,
                    ThreatPhase.EXPLOITATION.value: 2.0,
                    ThreatPhase.INSTALLATION.value: 1.8,
                },
            ),
            "memory": SignalWeight(
                base_weight=0.15,
                attention_mode_multipliers={
                    AttentionMode.BASELINE.value: 1.0,
                    AttentionMode.ANOMALY_ALERT.value: 1.2,
                    AttentionMode.ATTACK_MODE.value: 1.5,
                    AttentionMode.CRITICAL.value: 2.5,      # Context matters
                    AttentionMode.FORENSIC.value: 2.8,      # Historical patterns
                },
                threat_phase_multipliers={
                    ThreatPhase.COMMAND_CONTROL.value: 2.2,
                    ThreatPhase.DATA_EXFILTRATION.value: 2.0,
                },
            ),
            "taste": SignalWeight(
                base_weight=0.15,
                attention_mode_multipliers={
                    AttentionMode.BASELINE.value: 1.0,
                    AttentionMode.ANOMALY_ALERT.value: 1.3,
                    AttentionMode.ATTACK_MODE.value: 1.6,
                    AttentionMode.CRITICAL.value: 1.9,
                    AttentionMode.FORENSIC.value: 1.4,
                },
                threat_phase_multipliers={
                    ThreatPhase.COMMAND_CONTROL.value: 2.3,
                    ThreatPhase.EXPLOITATION.value: 1.7,
                },
            ),
            "touch": SignalWeight(
                base_weight=0.10,
                attention_mode_multipliers={
                    AttentionMode.BASELINE.value: 1.0,
                    AttentionMode.ANOMALY_ALERT.value: 1.1,
                    AttentionMode.ATTACK_MODE.value: 1.3,
                    AttentionMode.CRITICAL.value: 1.5,
                    AttentionMode.FORENSIC.value: 1.0,
                },
                threat_phase_multipliers={
                    ThreatPhase.RECONNAISSANCE.value: 0.8,
                    ThreatPhase.DATA_EXFILTRATION.value: 1.5,
                },
            ),
        }
    
    def _initialize_source_reliability(self) -> Dict[str, float]:
        """Source trust scores"""
        return {
            "packet_capture": 0.98,        # Raw packets - highest fidelity
            "dpi_engine": 0.95,            # Deep inspection - very reliable
            "ids_engine": 0.92,            # IDS detections - reliable
            "ueba_engine": 0.85,           # Behavioral - moderate confidence
            "anomaly_engine": 0.83,        # Statistical - varies
            "topology_analyzer": 0.88,     # Graph analysis - good
            "threat_memory": 0.90,         # Historical - reliable
            "protocol_analyzer": 0.87,     # Protocol parsing - good
            "connection_monitor": 0.91,    # Link quality - reliable
            "firewall_logs": 0.94,         # Direct observation
            "ml_model": 0.80,              # ML predictions - varies
            "user_report": 0.60,           # User-reported - unreliable
        }
    
    def _initialize_phase_importance(self) -> Dict[str, Dict[str, float]]:
        """Signal importance per attack phase"""
        return {
            ThreatPhase.RECONNAISSANCE.value: {
                "smell": 0.80,      # Pattern matching
                "vision": 0.60,     # Topology scanning
                "touch": 0.40,      # Connection probes
                "pain": 0.30,       # Some anomalies
                "memory": 0.50,     # Known scanners
                "taste": 0.40,      # Protocol probes
            },
            ThreatPhase.WEAPONIZATION.value: {
                "smell": 0.90,      # Tool signatures
                "memory": 0.70,     # Known tools
                "pain": 0.40,       # Some spikes
                "vision": 0.30,
                "touch": 0.20,
                "taste": 0.25,
            },
            ThreatPhase.DELIVERY.value: {
                "smell": 0.95,      # Delivery signatures
                "taste": 0.70,      # Protocol abuse
                "pain": 0.50,
                "vision": 0.40,
                "memory": 0.60,
                "touch": 0.30,
            },
            ThreatPhase.EXPLOITATION.value: {
                "pain": 1.0,        # CRITICAL - anomalies = compromise
                "vision": 0.85,     # Lateral movement prep
                "smell": 0.80,      # Exploit signatures
                "taste": 0.60,      # Unusual protocols
                "memory": 0.75,
                "touch": 0.40,
            },
            ThreatPhase.INSTALLATION.value: {
                "vision": 0.90,     # Host-to-host changes
                "pain": 0.85,       # Behavior changes
                "smell": 0.75,      # Persistence signatures
                "taste": 0.65,      # Unusual connections
                "memory": 0.70,
                "touch": 0.35,
            },
            ThreatPhase.COMMAND_CONTROL.value: {
                "taste": 1.0,       # C2 protocols = distinctive
                "memory": 0.95,     # Known C2 patterns
                "pain": 0.70,       # Anomalies
                "vision": 0.60,
                "smell": 0.75,
                "touch": 0.50,
            },
            ThreatPhase.LATERAL_MOVEMENT.value: {
                "vision": 1.0,      # CRITICAL - graph patterns
                "pain": 0.90,       # Unusual behavior
                "smell": 0.70,      # Known tools
                "taste": 0.65,      # Protocol abuse
                "memory": 0.75,
                "touch": 0.40,
            },
            ThreatPhase.DATA_EXFILTRATION.value: {
                "pain": 0.95,       # Data volume anomalies
                "taste": 0.90,      # Exfil protocols
                "memory": 1.0,      # Known exfil patterns
                "vision": 0.75,     # Destination patterns
                "smell": 0.70,
                "touch": 0.45,
            },
        }
    
    def calculate_signal_weight(
        self,
        signal_type: str,
        context: WeightingContext,
        signal_timestamp: datetime,
        source: str = "ids_engine",
    ) -> float:
        """
        Calculate effective weight for a signal considering:
        1. Signal importance in context
        2. Attention mode multiplier
        3. Attack phase multiplier
        4. Source reliability
        5. Temporal decay
        6. System state
        """
        if signal_type not in self.weights:
            return 0.0
        
        weight_config = self.weights[signal_type]
        base_weight = weight_config.base_weight
        
        # 1. Attention mode multiplier
        attention_multiplier = weight_config.attention_mode_multipliers.get(
            context.attention_mode.value, 1.0
        )
        
        # 2. Threat phase multiplier
        phase_multiplier = 1.0
        if context.suspected_attack_phase:
            phase_importance = self.phase_importance.get(
                context.suspected_attack_phase.value, {}
            )
            phase_multiplier = phase_importance.get(signal_type, 1.0)
        
        # 3. Source reliability adjustment
        source_reliability = self.source_reliability_scores.get(source, 0.5)
        
        # 4. Temporal decay (older signals less important)
        time_decay = self._calculate_temporal_decay(signal_timestamp)
        
        # 5. Context adjustments
        context_multiplier = 1.0
        if context.is_high_value_target:
            context_multiplier *= 1.2
        if context.current_threat_level > 0.8:
            context_multiplier *= 1.3
        if not context.is_working_hours and signal_type == "pain":
            context_multiplier *= 1.2  # Off-hours alerts more important
        
        # Combine all factors
        effective_weight = (
            base_weight * 
            attention_multiplier * 
            phase_multiplier * 
            source_reliability * 
            time_decay * 
            context_multiplier
        )
        
        return min(effective_weight, 1.0)  # Cap at 1.0
    
    def calculate_weighted_threat_score(
        self,
        signals: List[Dict[str, any]],  # [{type, intensity, source, timestamp}, ...]
        context: WeightingContext
    ) -> float:
        """
        Calculate overall threat score from weighted signals.
        Implements sensory binding and attention weighting.
        """
        if not signals:
            return 0.0
        
        weighted_contributions = []
        
        for sig in signals:
            weight = self.calculate_signal_weight(
                sig.get("type", "unknown"),
                context,
                sig.get("timestamp", datetime.now()),
                sig.get("source", "ids_engine")
            )
            
            intensity = sig.get("intensity", 0.5)
            confidence = sig.get("confidence", 0.7)
            
            contribution = weight * intensity * confidence
            weighted_contributions.append(contribution)
        
        # Use weighted average but cap the result
        if weighted_contributions:
            avg_contribution = np.mean(weighted_contributions)
            return min(avg_contribution, 1.0)
        
        return 0.0
    
    def adjust_weights_for_context(
        self,
        context: WeightingContext
    ) -> Dict[str, float]:
        """
        Get current signal weights adjusted for context.
        Returns {signal_type: current_weight}
        """
        adjusted = {}
        
        for signal_type in self.weights:
            base = self.weights[signal_type].base_weight
            attention_mult = self.weights[signal_type].attention_mode_multipliers.get(
                context.attention_mode.value, 1.0
            )
            
            adjusted[signal_type] = base * attention_mult
        
        # Normalize so sum = 1.0 (optional)
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v/total for k, v in adjusted.items()}
        
        return adjusted
    
    def recommend_attention_mode(
        self,
        current_threat_level: float,
        anomaly_count_last_hour: int,
        known_threat_patterns: int,
        is_high_value_target: bool,
    ) -> AttentionMode:
        """
        Recommend attention mode based on system state.
        Implements biological arousal/vigilance response.
        """
        threat_score = (
            current_threat_level * 0.5 +
            (min(anomaly_count_last_hour / 50.0, 1.0)) * 0.2 +
            (min(known_threat_patterns / 20.0, 1.0)) * 0.2 +
            (0.1 if is_high_value_target else 0)
        )
        
        if threat_score >= 0.9:
            return AttentionMode.CRITICAL
        elif threat_score >= 0.7:
            return AttentionMode.ATTACK_MODE
        elif threat_score >= 0.5:
            return AttentionMode.ANOMALY_ALERT
        else:
            return AttentionMode.BASELINE
    
    def estimate_attack_phase(
        self,
        signal_types_detected: List[str],
        historical_pattern: Optional[str] = None,
    ) -> Optional[ThreatPhase]:
        """
        Estimate which attack phase we're in based on signal patterns.
        Uses Cyber Kill Chain as framework.
        """
        # Count detected signal types
        signal_set = set(signal_types_detected)
        
        # Simple heuristic
        if signal_set == {"smell"}:
            return ThreatPhase.RECONNAISSANCE
        elif signal_set == {"smell"} and len(signal_types_detected) > 5:
            return ThreatPhase.WEAPONIZATION
        elif {"smell", "taste"}.issubset(signal_set):
            return ThreatPhase.DELIVERY
        elif {"pain", "vision"}.issubset(signal_set):
            return ThreatPhase.EXPLOITATION
        elif {"vision", "taste"}.issubset(signal_set):
            return ThreatPhase.LATERAL_MOVEMENT
        elif "taste" in signal_set and "pain" in signal_set:
            return ThreatPhase.COMMAND_CONTROL
        elif "pain" in signal_set and "memory" in signal_set:
            return ThreatPhase.DATA_EXFILTRATION
        
        return None
    
    def _calculate_temporal_decay(self, signal_timestamp: datetime) -> float:
        """Signals decay in importance over time"""
        age = datetime.now() - signal_timestamp
        hours_old = age.total_seconds() / 3600.0
        
        # Exponential decay: 50% weight per 24 hours
        decay = 0.5 ** (hours_old / 24.0)
        return max(decay, 0.1)  # Never go below 10%


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    engine = AdaptiveWeightingEngine()
    
    # Scenario: Active attack detected during working hours
    context = WeightingContext(
        current_threat_level=0.75,
        attention_mode=AttentionMode.ATTACK_MODE,
        suspected_attack_phase=ThreatPhase.LATERAL_MOVEMENT,
        is_high_value_target=True,
        is_working_hours=True,
    )
    
    # Sample signals
    signals = [
        {
            "type": "vision",
            "intensity": 0.95,
            "confidence": 0.92,
            "source": "topology_analyzer",
            "timestamp": datetime.now(),
        },
        {
            "type": "pain",
            "intensity": 0.85,
            "confidence": 0.88,
            "source": "anomaly_engine",
            "timestamp": datetime.now(),
        },
        {
            "type": "smell",
            "intensity": 0.70,
            "confidence": 0.82,
            "source": "dpi_engine",
            "timestamp": datetime.now() - timedelta(hours=1),
        },
    ]
    
    # Calculate weighted threat score
    threat_score = engine.calculate_weighted_threat_score(signals, context)
    print(f"Threat Score: {threat_score:.3f}")
    
    # Get adjusted weights
    weights = engine.adjust_weights_for_context(context)
    print(f"\nAdjusted Weights (for {context.attention_mode.value}):")
    for signal_type, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        print(f"  {signal_type}: {weight:.3f}")
    
    # Recommend attention mode
    recommended = engine.recommend_attention_mode(
        current_threat_level=0.75,
        anomaly_count_last_hour=12,
        known_threat_patterns=3,
        is_high_value_target=True,
    )
    print(f"\nRecommended Attention Mode: {recommended.name}")
