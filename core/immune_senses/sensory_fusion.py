"""
IMMUNE SENSORY SYSTEM - Sensory Fusion Engine
============================================
Converts raw security signals (packet capture, DPI, UEBA, telemetry) 
into coherent "digital sensations" mimicking biological immune response.

Biological Mapping:
  Pain Receptors    → Anomaly Spikes (sudden threat elevation)
  Smell             → Network Fingerprints (signature recognition)
  Vision            → Graph Attack Maps (topology visualization)
  Memory Cells      → Temporal Threat Memory (historical correlation)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
import numpy as np
from collections import defaultdict, deque
import json


class SenseType(Enum):
    """Digital sense categories"""
    PAIN = "pain"              # Anomaly spikes - sudden threats
    SMELL = "smell"            # Network fingerprints - known patterns
    VISION = "vision"          # Graph attack maps - topology threats
    MEMORY = "memory"          # Temporal correlation - historical threats
    TASTE = "taste"            # Protocol analysis - traffic characterization
    TOUCH = "touch"            # Connection state - link quality


class SensoryLevel(Enum):
    """Sensory signal intensity"""
    SUBLIMINAL = 0.0           # <10% confidence
    FAINT = 0.1                # 10-20% - barely perceptible
    MILD = 0.3                 # 20-40% - noticeable
    MODERATE = 0.5             # 40-60% - clear signal
    STRONG = 0.7               # 60-80% - urgent
    INTENSE = 0.9              # 80-95% - critical
    OVERWHELMING = 1.0         # 95-100% - emergency


@dataclass
class SensorySignal:
    """A single sensory perception"""
    sense_type: SenseType
    signal_id: str
    intensity: float            # 0.0-1.0
    confidence: float           # 0.0-1.0
    
    # Signal metadata
    source: str                 # "packet_capture", "dpi", "ueba", "telemetry"
    timestamp: datetime
    duration_ms: float          # How long signal was detected
    
    # Spatial context
    source_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    affected_hosts: List[str] = field(default_factory=list)
    
    # Signal characteristics
    signal_data: Dict[str, any] = field(default_factory=dict)
    related_signals: List[str] = field(default_factory=list)  # Other signal IDs
    
    # Response metadata
    acknowledged: bool = False
    response_action: Optional[str] = None
    
    def get_level(self) -> SensoryLevel:
        """Convert intensity to sensory level"""
        if self.intensity >= 0.95:
            return SensoryLevel.OVERWHELMING
        elif self.intensity >= 0.80:
            return SensoryLevel.INTENSE
        elif self.intensity >= 0.60:
            return SensoryLevel.STRONG
        elif self.intensity >= 0.40:
            return SensoryLevel.MODERATE
        elif self.intensity >= 0.20:
            return SensoryLevel.MILD
        elif self.intensity >= 0.10:
            return SensoryLevel.FAINT
        else:
            return SensoryLevel.SUBLIMINAL


@dataclass
class SensoryPercept:
    """A synthesized perception (multiple signals fused)"""
    percept_id: str
    primary_sense: SenseType
    signals: List[SensorySignal]
    
    # Fused characteristics
    combined_intensity: float   # Weighted average of signals
    combined_confidence: float  # Consensus confidence
    threat_type: str           # "ddos", "intrusion", "lateral_movement", etc.
    
    # Temporal properties
    first_seen: datetime
    last_seen: datetime
    recurrence_count: int       # How many times this percept repeated
    
    # Spatial properties
    affected_network_segment: Optional[str] = None
    attack_graph: Dict[str, List[str]] = field(default_factory=dict)  # Source -> [targets]
    
    # Analysis
    is_adaptive_attack: bool = False    # Changes behavior over time
    is_coordinated: bool = False        # Multiple sources
    anomaly_score: float = 0.0          # 0-1
    
    def get_severity(self) -> str:
        """Determine threat severity"""
        score = self.combined_intensity * self.combined_confidence
        if score >= 0.90:
            return "CRITICAL"
        elif score >= 0.70:
            return "HIGH"
        elif score >= 0.50:
            return "MEDIUM"
        elif score >= 0.30:
            return "LOW"
        else:
            return "INFO"


@dataclass
class ImmuneSensoryState:
    """Current state of all sensory inputs"""
    # Active signals per sense
    active_signals: Dict[SenseType, List[SensorySignal]] = field(default_factory=lambda: defaultdict(list))
    
    # Recent percepts
    recent_percepts: deque = field(default_factory=lambda: deque(maxlen=100))
    
    # Sensory attention weights
    sense_weights: Dict[SenseType, float] = field(default_factory=lambda: {
        SenseType.PAIN: 0.40,      # Anomalies weighted highest
        SenseType.SMELL: 0.25,     # Known patterns important
        SenseType.VISION: 0.20,    # Topology threats
        SenseType.MEMORY: 0.15,    # Historical context
        SenseType.TASTE: 0.15,     # Protocol analysis
        SenseType.TOUCH: 0.10,     # Connection state
    })
    
    # Signal history per source
    signal_history: Dict[str, deque] = field(default_factory=lambda: defaultdict(lambda: deque(maxlen=1000)))
    
    # Network topology (for vision sense)
    network_graph: Dict[str, Set[str]] = field(default_factory=dict)  # Host -> connected_hosts
    
    # Fingerprint database (for smell sense)
    known_fingerprints: Dict[str, Dict[str, any]] = field(default_factory=dict)
    
    # Threat memory (for memory sense)
    threat_memory: Dict[str, Dict[str, any]] = field(default_factory=dict)
    
    # Last update times
    last_pain_spike: Optional[datetime] = None
    last_smell_detection: Optional[datetime] = None
    last_vision_threat: Optional[datetime] = None
    last_memory_correlation: Optional[datetime] = None
    
    # Statistics
    total_signals_processed: int = 0
    total_percepts_generated: int = 0
    current_threat_level: float = 0.0


class ImmuneNervousSystem:
    """
    Central coordinator for immune sensory fusion.
    Converts disparate security signals into biological metaphors.
    """
    
    def __init__(self, max_signals_per_sense: int = 500):
        self.state = ImmuneSensoryState()
        self.max_signals = max_signals_per_sense
        self.signal_correlations: Dict[str, List[str]] = defaultdict(list)
        self.threat_cascade: deque = deque(maxlen=50)  # Cascading threats
        
    def receive_pain_signal(
        self,
        anomaly_type: str,
        intensity: float,
        source_ip: str,
        dest_ip: Optional[str],
        details: Dict[str, any]
    ) -> SensorySignal:
        """
        Process anomaly spike (pain receptor).
        UEBA, Zeek, packet analysis → anomaly detection
        """
        signal = SensorySignal(
            sense_type=SenseType.PAIN,
            signal_id=f"pain_{int(datetime.now().timestamp()*1000)}",
            intensity=min(intensity, 1.0),
            confidence=details.get("confidence", 0.8),
            source="anomaly_engine",
            timestamp=datetime.now(),
            duration_ms=details.get("duration_ms", 1000),
            source_ip=source_ip,
            dest_ip=dest_ip,
            signal_data={
                "anomaly_type": anomaly_type,
                "baseline_deviation": details.get("baseline_deviation", 0),
                "spike_percentage": details.get("spike_percentage", 0),
            }
        )
        
        self._register_signal(signal)
        self.state.last_pain_spike = datetime.now()
        return signal
    
    def receive_smell_signal(
        self,
        fingerprint_id: str,
        matched_pattern: str,
        confidence: float,
        hosts_affected: List[str],
        details: Dict[str, any]
    ) -> SensorySignal:
        """
        Process network fingerprint (smell sense).
        DPI, signature matching → known pattern detection
        """
        signal = SensorySignal(
            sense_type=SenseType.SMELL,
            signal_id=f"smell_{int(datetime.now().timestamp()*1000)}",
            intensity=confidence * 0.9,
            confidence=confidence,
            source="dpi_engine",
            timestamp=datetime.now(),
            duration_ms=details.get("duration_ms", 500),
            affected_hosts=hosts_affected,
            signal_data={
                "fingerprint_id": fingerprint_id,
                "matched_pattern": matched_pattern,
                "pattern_category": details.get("category", "unknown"),
            }
        )
        
        self._register_signal(signal)
        self.state.last_smell_detection = datetime.now()
        return signal
    
    def receive_vision_signal(
        self,
        threat_topology: Dict[str, List[str]],
        threat_type: str,
        intensity: float,
        details: Dict[str, any]
    ) -> SensorySignal:
        """
        Process graph attack map (vision sense).
        Network topology + threat correlation → attack graph detection
        """
        signal = SensorySignal(
            sense_type=SenseType.VISION,
            signal_id=f"vision_{int(datetime.now().timestamp()*1000)}",
            intensity=min(intensity, 1.0),
            confidence=details.get("confidence", 0.75),
            source="topology_analyzer",
            timestamp=datetime.now(),
            duration_ms=details.get("duration_ms", 2000),
            signal_data={
                "threat_topology": threat_topology,
                "threat_type": threat_type,
                "num_hops": details.get("num_hops", 0),
                "lateral_movement_depth": details.get("lateral_movement_depth", 0),
            }
        )
        
        self._register_signal(signal)
        self.state.last_vision_threat = datetime.now()
        return signal
    
    def receive_memory_signal(
        self,
        historical_threat_id: str,
        correlation_score: float,
        similar_threats: List[str],
        details: Dict[str, any]
    ) -> SensorySignal:
        """
        Process temporal correlation (memory sense).
        Historical threat database → known threat recurrence detection
        """
        signal = SensorySignal(
            sense_type=SenseType.MEMORY,
            signal_id=f"memory_{int(datetime.now().timestamp()*1000)}",
            intensity=correlation_score * 0.85,
            confidence=correlation_score,
            source="threat_memory",
            timestamp=datetime.now(),
            duration_ms=details.get("duration_ms", 3000),
            signal_data={
                "historical_threat_id": historical_threat_id,
                "similar_threats": similar_threats,
                "days_since_similar": details.get("days_since_similar", 0),
            }
        )
        
        self._register_signal(signal)
        self.state.last_memory_correlation = datetime.now()
        return signal
    
    def receive_taste_signal(
        self,
        protocol: str,
        protocol_anomaly: str,
        intensity: float,
        hosts: List[str],
        details: Dict[str, any]
    ) -> SensorySignal:
        """
        Process protocol analysis (taste sense).
        Protocol behavior → traffic characterization
        """
        signal = SensorySignal(
            sense_type=SenseType.TASTE,
            signal_id=f"taste_{int(datetime.now().timestamp()*1000)}",
            intensity=min(intensity, 1.0),
            confidence=details.get("confidence", 0.7),
            source="protocol_analyzer",
            timestamp=datetime.now(),
            duration_ms=details.get("duration_ms", 1500),
            affected_hosts=hosts,
            signal_data={
                "protocol": protocol,
                "anomaly_type": protocol_anomaly,
                "deviation_from_baseline": details.get("deviation", 0),
            }
        )
        
        self._register_signal(signal)
        return signal
    
    def receive_touch_signal(
        self,
        connection_state: str,
        link_quality: float,
        affected_connections: List[Tuple[str, str]],
        details: Dict[str, any]
    ) -> SensorySignal:
        """
        Process connection state (touch sense).
        Link quality → connection health monitoring
        """
        signal = SensorySignal(
            sense_type=SenseType.TOUCH,
            signal_id=f"touch_{int(datetime.now().timestamp()*1000)}",
            intensity=1.0 - link_quality,  # Higher intensity = worse state
            confidence=details.get("confidence", 0.8),
            source="connection_monitor",
            timestamp=datetime.now(),
            duration_ms=details.get("duration_ms", 1000),
            affected_hosts=[conn[0] for conn in affected_connections],
            signal_data={
                "connection_state": connection_state,
                "link_quality": link_quality,
                "affected_connections": affected_connections,
            }
        )
        
        self._register_signal(signal)
        return signal
    
    def fuse_signals_into_percept(self, signal_ids: List[str]) -> Optional[SensoryPercept]:
        """
        Fuse multiple signals into a coherent sensory percept.
        Implements sensory binding and attention.
        """
        # Find all signals
        signals = []
        for sense_type in self.state.active_signals:
            for sig in self.state.active_signals[sense_type]:
                if sig.signal_id in signal_ids:
                    signals.append(sig)
        
        if not signals:
            return None
        
        # Primary sense = sense with highest weighted intensity
        primary_sense = max(
            signals,
            key=lambda s: s.intensity * self.state.sense_weights.get(s.sense_type, 0.1)
        ).sense_type
        
        # Fuse characteristics
        combined_intensity = np.mean([s.intensity for s in signals])
        combined_confidence = np.mean([s.confidence for s in signals])
        
        # Build attack graph if vision sense present
        attack_graph = {}
        for sig in signals:
            if sig.sense_type == SenseType.VISION:
                attack_graph = sig.signal_data.get("threat_topology", {})
        
        percept = SensoryPercept(
            percept_id=f"percept_{int(datetime.now().timestamp()*1000)}",
            primary_sense=primary_sense,
            signals=signals,
            combined_intensity=combined_intensity,
            combined_confidence=combined_confidence,
            threat_type=self._classify_threat(signals),
            first_seen=min(s.timestamp for s in signals),
            last_seen=max(s.timestamp for s in signals),
            recurrence_count=1,
            attack_graph=attack_graph,
            anomaly_score=combined_intensity * combined_confidence,
        )
        
        self.state.recent_percepts.append(percept)
        self.state.total_percepts_generated += 1
        
        # Update threat cascade
        self.threat_cascade.append({
            "percept_id": percept.percept_id,
            "threat_type": percept.threat_type,
            "severity": percept.get_severity(),
            "timestamp": datetime.now(),
        })
        
        return percept
    
    def get_sensory_summary(self) -> Dict[str, any]:
        """Get current state of all sensory inputs"""
        return {
            "active_signals_per_sense": {
                sense.value: len(sigs) 
                for sense, sigs in self.state.active_signals.items()
            },
            "total_signals": self.state.total_signals_processed,
            "total_percepts": self.state.total_percepts_generated,
            "current_threat_level": self.state.current_threat_level,
            "recent_threats": [
                {
                    "threat_type": p.threat_type,
                    "severity": p.get_severity(),
                    "signal_count": len(p.signals),
                }
                for p in list(self.state.recent_percepts)[-10:]
            ],
            "last_pain_spike": self.state.last_pain_spike.isoformat() if self.state.last_pain_spike else None,
            "last_smell_detection": self.state.last_smell_detection.isoformat() if self.state.last_smell_detection else None,
            "last_vision_threat": self.state.last_vision_threat.isoformat() if self.state.last_vision_threat else None,
            "last_memory_correlation": self.state.last_memory_correlation.isoformat() if self.state.last_memory_correlation else None,
        }
    
    def _register_signal(self, signal: SensorySignal) -> None:
        """Register a new signal in the system"""
        self.state.active_signals[signal.sense_type].append(signal)
        self.state.signal_history[signal.source].append(signal)
        self.state.total_signals_processed += 1
        
        # Keep signals list bounded
        if len(self.state.active_signals[signal.sense_type]) > self.max_signals:
            self.state.active_signals[signal.sense_type].pop(0)
    
    def _classify_threat(self, signals: List[SensorySignal]) -> str:
        """Classify threat type from signal characteristics"""
        sense_types = {s.sense_type for s in signals}
        data_fields = set()
        
        for sig in signals:
            data_fields.update(sig.signal_data.keys())
        
        # Pattern recognition
        if "spike_percentage" in data_fields and "baseline_deviation" in data_fields:
            return "anomaly_spike"
        if "threat_topology" in data_fields:
            return "lateral_movement"
        if "matched_pattern" in data_fields:
            return "known_attack_pattern"
        if "historical_threat_id" in data_fields:
            return "recurring_threat"
        if "protocol_anomaly" in data_fields:
            return "protocol_abuse"
        
        return "unknown_threat"


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    ns = ImmuneNervousSystem()
    
    # Simulate pain signal (anomaly spike)
    pain = ns.receive_pain_signal(
        anomaly_type="traffic_spike",
        intensity=0.85,
        source_ip="192.168.1.100",
        dest_ip="10.0.0.5",
        details={"confidence": 0.92, "spike_percentage": 250, "baseline_deviation": 3.5}
    )
    print(f"Pain Signal: {pain.signal_id} - Level: {pain.get_level().name}")
    
    # Simulate smell signal (fingerprint match)
    smell = ns.receive_smell_signal(
        fingerprint_id="fp_trickbot_2024",
        matched_pattern="TrickBot C2 beacon",
        confidence=0.88,
        hosts_affected=["192.168.1.100", "192.168.1.101"],
        details={"category": "trojan", "duration_ms": 500}
    )
    print(f"Smell Signal: {smell.signal_id} - Level: {smell.get_level().name}")
    
    # Fuse into percept
    percept = ns.fuse_signals_into_percept([pain.signal_id, smell.signal_id])
    if percept:
        print(f"Fused Percept: {percept.threat_type} - Severity: {percept.get_severity()}")
    
    # Summary
    print("\nSensory System Status:")
    print(json.dumps(ns.get_sensory_summary(), indent=2, default=str))
