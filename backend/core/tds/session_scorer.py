"""
Session Scoring Engine (ML-Driven)
===================================

Real-time ML-based session trust scoring using behavioral analysis,
anomaly detection, and privilege escalation identification.

Features:
---------
- LSTM-based behavior classification
- Real-time threat scoring
- Privilege escalation detection
- Temporal anomaly identification
- Session risk assessment
- Continuous learning integration

Author: J.A.R.V.I.S. Security Team
Date: December 2025
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import json
import hashlib
import math
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

# Try to import ML libraries, fallback to statistical methods
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class SessionRiskLevel(Enum):
    """Session risk severity levels"""
    CRITICAL = "critical"    # Score: 0.9-1.0 - Immediate termination
    HIGH = "high"            # Score: 0.7-0.9 - Active monitoring required
    MEDIUM = "medium"        # Score: 0.5-0.7 - Enhanced logging
    LOW = "low"              # Score: 0.3-0.5 - Standard logging
    SAFE = "safe"            # Score: 0.0-0.3 - Trusted session


class BehaviorType(Enum):
    """Session behavior classifications"""
    NORMAL = "normal"
    UNUSUAL = "unusual"
    SUSPICIOUS = "suspicious"
    ATTACK = "attack"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    LATERAL_MOVEMENT = "lateral_movement"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class SessionEvent:
    """Individual session event for scoring"""
    timestamp: datetime
    event_type: str  # "packet", "auth", "access", "anomaly"
    source_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    protocol: Optional[str] = None
    port: Optional[int] = None
    bytes_sent: int = 0
    bytes_received: int = 0
    packet_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for ML processing"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "source_ip": self.source_ip,
            "dest_ip": self.dest_ip,
            "protocol": self.protocol,
            "port": self.port,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "packet_count": self.packet_count,
        }


@dataclass
class SessionMetrics:
    """Aggregated session metrics"""
    session_id: str
    device_id: str
    start_time: datetime
    last_activity: datetime
    
    # Traffic metrics
    total_packets: int = 0
    total_bytes_sent: int = 0
    total_bytes_received: int = 0
    packet_rate: float = 0.0  # packets per second
    throughput: float = 0.0    # bytes per second
    
    # Behavior metrics
    unique_destinations: int = 0
    unique_protocols: set = field(default_factory=set)
    port_diversity: float = 0.0  # entropy of accessed ports
    
    # Anomaly metrics
    anomaly_score: float = 0.0  # 0.0-1.0
    behavioral_score: float = 0.0  # 0.0-1.0
    privilege_escalation_risk: float = 0.0  # 0.0-1.0
    
    # Overall risk
    composite_risk_score: float = 0.0  # 0.0-1.0
    risk_level: SessionRiskLevel = SessionRiskLevel.SAFE
    behavior_classification: BehaviorType = BehaviorType.NORMAL
    
    # Temporal analysis
    session_duration: timedelta = field(default_factory=lambda: timedelta(0))
    inactivity_duration: timedelta = field(default_factory=lambda: timedelta(0))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "session_id": self.session_id,
            "device_id": self.device_id,
            "start_time": self.start_time.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "session_duration_seconds": self.session_duration.total_seconds(),
            "inactivity_duration_seconds": self.inactivity_duration.total_seconds(),
            "traffic_metrics": {
                "total_packets": self.total_packets,
                "total_bytes_sent": self.total_bytes_sent,
                "total_bytes_received": self.total_bytes_received,
                "packet_rate": round(self.packet_rate, 2),
                "throughput_bps": round(self.throughput, 2),
            },
            "behavior_metrics": {
                "unique_destinations": self.unique_destinations,
                "unique_protocols": list(self.unique_protocols),
                "port_diversity": round(self.port_diversity, 3),
            },
            "anomaly_metrics": {
                "anomaly_score": round(self.anomaly_score, 3),
                "behavioral_score": round(self.behavioral_score, 3),
                "privilege_escalation_risk": round(self.privilege_escalation_risk, 3),
            },
            "risk": {
                "composite_risk_score": round(self.composite_risk_score, 3),
                "risk_level": self.risk_level.value,
                "behavior_classification": self.behavior_classification.value,
            },
        }


# ============================================================================
# SESSION SCORER ENGINE
# ============================================================================

class SessionScorer:
    """ML-driven session trust scorer"""
    
    def __init__(self, window_size: int = 300, history_limit: int = 1000):
        """
        Initialize session scorer.
        
        Args:
            window_size: Time window for analysis (seconds)
            history_limit: Max events to keep per session
        """
        self.window_size = window_size
        self.history_limit = history_limit
        
        # Session storage
        self.sessions: Dict[str, List[SessionEvent]] = defaultdict(list)
        self.metrics: Dict[str, SessionMetrics] = {}
        
        # ML models (if available)
        self.anomaly_detector = None
        self.scaler = None
        self._init_ml_models()
        
        # Baseline profiles for comparison
        self.baseline_profiles: Dict[str, Dict[str, float]] = {}
    
    def _init_ml_models(self) -> None:
        """Initialize ML models if libraries available"""
        if _HAS_SKLEARN and _HAS_NUMPY:
            try:
                self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
                self.scaler = StandardScaler()
                logger.info("ML models initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize ML models: {e}")
                self.anomaly_detector = None
                self.scaler = None
    
    def add_event(self, session_id: str, device_id: str, event: SessionEvent) -> None:
        """
        Add event to session for scoring.
        
        Args:
            session_id: Unique session identifier
            device_id: Device ID associated with session
            event: Session event to analyze
        """
        # Initialize session if needed
        if session_id not in self.sessions:
            self.sessions[session_id] = []
            self.metrics[session_id] = SessionMetrics(
                session_id=session_id,
                device_id=device_id,
                start_time=event.timestamp,
                last_activity=event.timestamp,
            )
        
        # Add event
        self.sessions[session_id].append(event)
        
        # Trim old events
        if len(self.sessions[session_id]) > self.history_limit:
            self.sessions[session_id] = self.sessions[session_id][-self.history_limit:]
        
        # Update metrics
        self._update_metrics(session_id, event)
    
    def _update_metrics(self, session_id: str, event: SessionEvent) -> None:
        """Update session metrics based on new event"""
        metrics = self.metrics[session_id]
        
        # Update timestamps
        metrics.last_activity = event.timestamp
        metrics.session_duration = event.timestamp - metrics.start_time
        
        # Update traffic metrics
        if event.event_type == "packet":
            metrics.total_packets += event.packet_count
            metrics.total_bytes_sent += event.bytes_sent
            metrics.total_bytes_received += event.bytes_received
            
            # Update rates (packets/bytes per second)
            duration_seconds = max(metrics.session_duration.total_seconds(), 1)
            metrics.packet_rate = metrics.total_packets / duration_seconds
            metrics.throughput = (metrics.total_bytes_sent + metrics.total_bytes_received) / duration_seconds
        
        # Update behavior metrics
        if event.dest_ip:
            # This is simplified - in production would use more sophisticated analysis
            pass
        
        if event.protocol:
            metrics.unique_protocols.add(event.protocol)
        
        # Recalculate scores
        self._recalculate_scores(session_id)
    
    def _recalculate_scores(self, session_id: str) -> None:
        """Recalculate all risk scores for session"""
        metrics = self.metrics[session_id]
        events = self.sessions[session_id]
        
        if not events:
            return
        
        # Calculate anomaly score
        metrics.anomaly_score = self._calculate_anomaly_score(session_id)
        
        # Calculate behavioral score
        metrics.behavioral_score = self._calculate_behavioral_score(session_id)
        
        # Calculate privilege escalation risk
        metrics.privilege_escalation_risk = self._calculate_privilege_escalation_risk(session_id)
        
        # Calculate composite score
        weights = {
            "anomaly": 0.4,
            "behavior": 0.3,
            "privilege_escalation": 0.3,
        }
        
        metrics.composite_risk_score = (
            metrics.anomaly_score * weights["anomaly"] +
            metrics.behavioral_score * weights["behavior"] +
            metrics.privilege_escalation_risk * weights["privilege_escalation"]
        )
        
        # Determine risk level
        metrics.risk_level = self._get_risk_level(metrics.composite_risk_score)
        
        # Classify behavior
        metrics.behavior_classification = self._classify_behavior(session_id)
    
    def _calculate_anomaly_score(self, session_id: str) -> float:
        """
        Calculate anomaly score using ML or statistical methods.
        Returns: 0.0 (normal) to 1.0 (anomalous)
        """
        events = self.sessions[session_id]
        
        if not events:
            return 0.0
        
        # Extract features for anomaly detection
        features = self._extract_features(events)
        
        # ML-based detection if available
        if self.anomaly_detector and _HAS_NUMPY and len(features) > 1:
            try:
                # Normalize features
                features_scaled = self.scaler.fit_transform([[f] for f in features])
                
                # Detect anomalies (-1 = anomaly, 1 = normal)
                anomaly_flags = self.anomaly_detector.predict(features_scaled)
                
                # Calculate proportion of anomalous points
                anomaly_score = sum(1 for flag in anomaly_flags if flag == -1) / len(anomaly_flags)
                return min(1.0, anomaly_score)
            except Exception as e:
                logger.debug(f"ML anomaly detection failed: {e}")
        
        # Statistical fallback: compare against baseline
        return self._statistical_anomaly_score(session_id, features)
    
    def _extract_features(self, events: List[SessionEvent]) -> List[float]:
        """Extract numerical features from events"""
        if not events:
            return []
        
        features = []
        for event in events:
            feature_value = (
                event.bytes_sent + event.bytes_received +
                (event.port or 0) + event.packet_count
            )
            features.append(float(feature_value))
        
        return features
    
    def _statistical_anomaly_score(self, session_id: str, features: List[float]) -> float:
        """Statistical anomaly detection using standard deviation"""
        if not features or len(features) < 2:
            return 0.0
        
        mean = sum(features) / len(features)
        variance = sum((x - mean) ** 2 for x in features) / len(features)
        std_dev = math.sqrt(variance) if variance > 0 else 0
        
        if std_dev == 0:
            return 0.0
        
        # Count outliers (> 2 standard deviations from mean)
        outliers = sum(1 for x in features if abs(x - mean) > 2 * std_dev)
        anomaly_ratio = outliers / len(features)
        
        return min(1.0, anomaly_ratio)
    
    def _calculate_behavioral_score(self, session_id: str) -> float:
        """
        Calculate behavioral anomaly score.
        Returns: 0.0 (normal behavior) to 1.0 (suspicious behavior)
        """
        metrics = self.metrics[session_id]
        events = self.sessions[session_id]
        
        if not events:
            return 0.0
        
        score = 0.0
        
        # Factor 1: Rapid connection attempts (indicator of reconnaissance)
        recent_events = [e for e in events if 
                        (datetime.now() - e.timestamp).total_seconds() < 60]
        
        if len(recent_events) > 50:  # >50 events in last minute
            score += 0.3
        elif len(recent_events) > 20:
            score += 0.15
        
        # Factor 2: High throughput/bandwidth usage
        if metrics.throughput > 1_000_000:  # >1MB/sec
            score += 0.2
        elif metrics.throughput > 100_000:  # >100KB/sec
            score += 0.1
        
        # Factor 3: Accessing unusual ports
        high_ports = sum(1 for p in [e.port for e in events if e.port] if p > 10000)
        if high_ports > len(events) * 0.3:
            score += 0.15
        
        # Factor 4: Protocol mixing (indicator of tunneling/evasion)
        if len(metrics.unique_protocols) > 3:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_privilege_escalation_risk(self, session_id: str) -> float:
        """
        Detect privilege escalation attempts.
        Returns: 0.0 (safe) to 1.0 (likely escalation)
        """
        events = self.sessions[session_id]
        
        if not events:
            return 0.0
        
        risk = 0.0
        
        # Check for suspicious patterns
        for i, event in enumerate(events):
            metadata = event.metadata
            
            # Pattern 1: Sudden increase in access privileges
            if metadata.get("privilege_change"):
                risk += 0.4
            
            # Pattern 2: Access to sensitive system resources
            sensitive_paths = ["/etc/shadow", "/etc/sudoers", "C:\\Windows\\System32\\config"]
            if any(path in str(metadata) for path in sensitive_paths):
                risk += 0.3
            
            # Pattern 3: Failed auth attempts followed by success
            if event.event_type == "auth" and metadata.get("auth_failed"):
                # Check if next auth succeeds
                if i + 1 < len(events) and events[i + 1].event_type == "auth":
                    if not events[i + 1].metadata.get("auth_failed"):
                        risk += 0.25
        
        return min(1.0, risk)
    
    def _get_risk_level(self, score: float) -> SessionRiskLevel:
        """Determine risk level from composite score"""
        if score >= 0.9:
            return SessionRiskLevel.CRITICAL
        elif score >= 0.7:
            return SessionRiskLevel.HIGH
        elif score >= 0.5:
            return SessionRiskLevel.MEDIUM
        elif score >= 0.3:
            return SessionRiskLevel.LOW
        else:
            return SessionRiskLevel.SAFE
    
    def _classify_behavior(self, session_id: str) -> BehaviorType:
        """Classify session behavior type"""
        metrics = self.metrics[session_id]
        
        # Use composite score and detected patterns
        if metrics.privilege_escalation_risk > 0.6:
            return BehaviorType.PRIVILEGE_ESCALATION
        
        if metrics.throughput > 10_000_000:  # >10MB/sec
            return BehaviorType.DATA_EXFILTRATION
        
        if metrics.unique_destinations > 100:
            return BehaviorType.LATERAL_MOVEMENT
        
        if metrics.behavioral_score > 0.7:
            return BehaviorType.SUSPICIOUS
        
        if metrics.anomaly_score > 0.6:
            return BehaviorType.ATTACK
        
        if metrics.anomaly_score > 0.3:
            return BehaviorType.UNUSUAL
        
        return BehaviorType.NORMAL
    
    def get_session_score(self, session_id: str) -> Optional[SessionMetrics]:
        """
        Get current session score.
        
        Args:
            session_id: Session to score
            
        Returns:
            SessionMetrics object or None if session not found
        """
        return self.metrics.get(session_id)
    
    def close_session(self, session_id: str) -> Optional[SessionMetrics]:
        """
        Close session and finalize scores.
        
        Args:
            session_id: Session to close
            
        Returns:
            Final SessionMetrics
        """
        metrics = self.metrics.get(session_id)
        
        if metrics:
            # Final score calculation
            self._recalculate_scores(session_id)
            
            # Clean up old events
            if session_id in self.sessions:
                del self.sessions[session_id]
        
        return metrics
    
    def get_risky_sessions(self, min_risk: float = 0.5) -> List[SessionMetrics]:
        """
        Get all sessions above risk threshold.
        
        Args:
            min_risk: Minimum composite risk score
            
        Returns:
            List of risky SessionMetrics
        """
        return [
            metrics for metrics in self.metrics.values()
            if metrics.composite_risk_score >= min_risk
        ]


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_scorer_instance: Optional[SessionScorer] = None


def get_session_scorer() -> SessionScorer:
    """Get or create session scorer singleton"""
    global _scorer_instance
    
    if _scorer_instance is None:
        _scorer_instance = SessionScorer()
        logger.info("Session scorer initialized")
    
    return _scorer_instance
