"""
IDS Integration Bridge for TDS Module

Provides bidirectional integration between TDS (Trusted Device Services) and IDS (Intrusion Detection System):
- TDS threats trigger IDS rule generation and alert escalation
- IDS detections enhance TDS risk scoring and device health assessment
- Cross-module threat intelligence sharing
- Coordinated response actions (block, quarantine, investigate)
- Alert correlation and deduplication

Architecture:
    TDS Module                          IDS Module
    (Session Scoring, Device Health)    (Threat Detection, Rules)
            ↓                                 ↓
    +-------+-------+
    |               |
    | IDS Bridge    |
    |               |
    +-------+-------+
            ↓
    Threat Intelligence Pool
    (Shared threat data, rules, patterns)
"""

import logging
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import queue

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat severity levels for cross-module communication."""
    CRITICAL = "critical"      # Immediate action required
    HIGH = "high"              # Urgent investigation needed
    MEDIUM = "medium"          # Monitor and investigate
    LOW = "low"                # Log and monitor
    INFO = "info"              # Informational only


class AlertSource(Enum):
    """Source of alert generation."""
    TDS_SESSION_SCORER = "tds_session_scorer"
    TDS_DEVICE_HEALTH = "tds_device_health"
    IDS_SIGNATURE = "ids_signature"
    IDS_ANOMALY = "ids_anomaly"
    IDS_BEHAVIORAL = "ids_behavioral"
    IDS_PROTOCOL = "ids_protocol"


class ResponseAction(Enum):
    """Coordinated response actions."""
    BLOCK = "block"                    # Block traffic
    QUARANTINE = "quarantine"          # Isolate device
    INVESTIGATE = "investigate"        # Deep inspection
    LOG = "log"                        # Log and monitor
    ALERT = "alert"                    # Send alert
    REVOKE_SESSION = "revoke_session"  # End VPN session
    UPDATE_POLICY = "update_policy"    # Update device policy


@dataclass
class ThreatIntelligence:
    """Shared threat intelligence across TDS and IDS."""
    threat_id: str
    threat_type: str                   # "malware", "attack_pattern", "vulnerability", etc.
    threat_level: ThreatLevel
    source: AlertSource
    timestamp: datetime
    source_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    device_id: Optional[str] = None
    session_id: Optional[str] = None
    process_name: Optional[str] = None
    signature_id: Optional[str] = None
    
    # Details
    description: str = ""
    indicators: Dict[str, Any] = field(default_factory=dict)  # IOCs, patterns, etc.
    confidence: float = 0.8             # 0.0-1.0 confidence score
    
    # Recommended actions
    suggested_actions: List[ResponseAction] = field(default_factory=lambda: [ResponseAction.LOG])
    
    # Cross-module metadata
    related_alerts: List[str] = field(default_factory=list)
    mitigated: bool = False
    mitigation_action: Optional[ResponseAction] = None


@dataclass
class CrossModuleAlert:
    """Alert structure for bidirectional communication."""
    alert_id: str
    alert_type: str                    # "session_risk", "device_health", "intrusion", etc.
    threat_level: ThreatLevel
    source_module: str                 # "tds" or "ids"
    timestamp: datetime
    
    # Context
    device_id: Optional[str] = None
    session_id: Optional[str] = None
    source_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    
    # Details
    message: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    # Response tracking
    actions_taken: List[ResponseAction] = field(default_factory=list)
    resolved: bool = False


@dataclass
class AlertCorrelation:
    """Correlation between related TDS and IDS alerts."""
    correlation_id: str
    related_alert_ids: List[str]
    correlation_score: float           # 0.0-1.0 likelihood of correlation
    threat_level: ThreatLevel
    timestamp: datetime
    
    # Pattern metadata
    attack_pattern: Optional[str] = None
    attack_phase: Optional[str] = None  # reconnaissance, weaponization, delivery, etc.
    root_cause: Optional[str] = None


class IDSBridge:
    """
    Bidirectional bridge between TDS and IDS modules.
    
    Responsibilities:
    - Listen to TDS threat events (high-risk sessions, device health alerts)
    - Listen to IDS detection events (signatures, anomalies, behavioral)
    - Generate cross-module alerts
    - Correlate and deduplicate alerts
    - Recommend coordinated response actions
    - Share threat intelligence
    """
    
    def __init__(self, max_alert_history: int = 10000, correlation_window: int = 300):
        """
        Initialize IDS Bridge.
        
        Args:
            max_alert_history: Maximum alerts to keep in memory
            correlation_window: Time window (seconds) for alert correlation
        """
        self.max_alert_history = max_alert_history
        self.correlation_window = correlation_window
        
        # Alert queues (would connect to actual IDS/TDS modules)
        self.tds_alert_queue: queue.Queue = queue.Queue()
        self.ids_alert_queue: queue.Queue = queue.Queue()
        
        # Alert storage
        self.alerts_by_id: Dict[str, CrossModuleAlert] = {}
        self.alerts_timeline: List[str] = []  # Alert IDs in chronological order
        
        # Threat intelligence pool
        self.threat_pool: Dict[str, ThreatIntelligence] = {}
        
        # Alert correlations
        self.correlations: Dict[str, AlertCorrelation] = {}
        
        # High-risk patterns for correlation
        self.known_attack_patterns: Dict[str, Dict[str, Any]] = self._init_attack_patterns()
        
        # Metrics
        self.metrics = {
            "total_alerts": 0,
            "tds_alerts": 0,
            "ids_alerts": 0,
            "correlations": 0,
            "actions_taken": defaultdict(int),
        }
        
        # Lock for thread-safe operations
        self._lock = threading.RLock()
        
        logger.info("IDS Bridge initialized")
    
    def _init_attack_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize known attack patterns for correlation."""
        return {
            "privilege_escalation_attack": {
                "phases": ["reconnaissance", "exploitation", "privilege_escalation"],
                "tds_indicators": ["privilege_escalation_risk", "unusual_process"],
                "ids_indicators": ["local_exploit", "kernel_module_load"],
                "threat_level": ThreatLevel.CRITICAL,
            },
            "data_exfiltration": {
                "phases": ["reconnaissance", "weaponization", "delivery", "exfiltration"],
                "tds_indicators": ["data_exfiltration_detected", "high_throughput"],
                "ids_indicators": ["large_outbound_transfer", "suspicious_protocol"],
                "threat_level": ThreatLevel.HIGH,
            },
            "lateral_movement": {
                "phases": ["lateral_movement"],
                "tds_indicators": ["lateral_movement_detected", "multiple_destinations"],
                "ids_indicators": ["port_scan", "service_enumeration"],
                "threat_level": ThreatLevel.HIGH,
            },
            "ddos_attack": {
                "phases": ["attack"],
                "tds_indicators": ["high_packet_rate", "protocol_anomaly"],
                "ids_indicators": ["flooding_attack", "traffic_anomaly"],
                "threat_level": ThreatLevel.CRITICAL,
            },
        }
    
    def report_tds_threat(
        self,
        device_id: str,
        session_id: Optional[str],
        threat_type: str,
        threat_level: ThreatLevel,
        risk_score: float,
        indicators: Dict[str, Any],
        source_ip: Optional[str] = None,
        dest_ip: Optional[str] = None,
    ) -> str:
        """
        Report a threat detected by TDS module.
        
        Args:
            device_id: Device identifier
            session_id: VPN session ID
            threat_type: Type of threat ("high_risk_session", "device_health", etc.)
            threat_level: Severity level
            risk_score: Numerical risk score (0.0-1.0)
            indicators: Detailed indicators/metrics
            source_ip: Source IP address
            dest_ip: Destination IP address
            
        Returns:
            Alert ID
        """
        alert_id = f"tds-{datetime.now().timestamp()}"
        
        alert = CrossModuleAlert(
            alert_id=alert_id,
            alert_type=threat_type,
            threat_level=threat_level,
            source_module="tds",
            timestamp=datetime.now(),
            device_id=device_id,
            session_id=session_id,
            source_ip=source_ip,
            dest_ip=dest_ip,
            message=f"TDS detected {threat_type}: risk_score={risk_score:.2f}",
            raw_data={
                "risk_score": risk_score,
                "indicators": indicators,
            },
        )
        
        with self._lock:
            self._store_alert(alert)
            self._correlate_alert(alert)
            self._recommend_actions(alert)
        
        logger.info(f"TDS threat reported: {alert_id} ({threat_level.value})")
        self.metrics["tds_alerts"] += 1
        self.metrics["total_alerts"] += 1
        
        return alert_id
    
    def report_ids_detection(
        self,
        source_ip: str,
        dest_ip: str,
        detection_type: str,
        signature_id: Optional[str],
        severity: ThreatLevel,
        protocol: Optional[str] = None,
        port: Optional[int] = None,
        indicators: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Report a detection from IDS module.
        
        Args:
            source_ip: Source IP
            dest_ip: Destination IP
            detection_type: Type of detection ("signature", "anomaly", "behavioral")
            signature_id: IDS signature ID
            severity: Alert severity
            protocol: Protocol (tcp, udp, icmp, etc.)
            port: Destination port
            indicators: Additional indicators
            
        Returns:
            Alert ID
        """
        alert_id = f"ids-{datetime.now().timestamp()}"
        
        alert = CrossModuleAlert(
            alert_id=alert_id,
            alert_type=detection_type,
            threat_level=severity,
            source_module="ids",
            timestamp=datetime.now(),
            source_ip=source_ip,
            dest_ip=dest_ip,
            message=f"IDS detection: {detection_type}",
            raw_data={
                "signature_id": signature_id,
                "protocol": protocol,
                "port": port,
                "indicators": indicators or {},
            },
        )
        
        with self._lock:
            self._store_alert(alert)
            self._correlate_alert(alert)
            self._recommend_actions(alert)
        
        logger.info(f"IDS detection reported: {alert_id} ({severity.value})")
        self.metrics["ids_alerts"] += 1
        self.metrics["total_alerts"] += 1
        
        return alert_id
    
    def _store_alert(self, alert: CrossModuleAlert) -> None:
        """Store alert in memory with cleanup of old alerts."""
        self.alerts_by_id[alert.alert_id] = alert
        self.alerts_timeline.append(alert.alert_id)
        
        # Cleanup old alerts if over limit
        if len(self.alerts_timeline) > self.max_alert_history:
            old_alert_id = self.alerts_timeline.pop(0)
            del self.alerts_by_id[old_alert_id]
    
    def _correlate_alert(self, alert: CrossModuleAlert) -> Optional[str]:
        """
        Correlate alert with existing alerts to identify coordinated attacks.
        
        Returns:
            Correlation ID if correlated, None otherwise
        """
        correlated_alerts = []
        current_time = alert.timestamp
        
        # Look for related alerts within correlation window
        for alert_id in self.alerts_timeline:
            if alert_id == alert.alert_id:
                continue
            
            stored_alert = self.alerts_by_id.get(alert_id)
            if not stored_alert:
                continue
            
            # Check time window
            time_diff = (current_time - stored_alert.timestamp).total_seconds()
            if time_diff > self.correlation_window:
                continue
            
            # Check for common attributes (same device, IP pair, etc.)
            if self._is_related_alert(alert, stored_alert):
                correlated_alerts.append(alert_id)
        
        if correlated_alerts:
            correlation_id = f"corr-{datetime.now().timestamp()}"
            correlated_alerts.append(alert.alert_id)
            
            # Detect attack pattern
            attack_pattern, confidence = self._detect_attack_pattern(
                [self.alerts_by_id[aid] for aid in correlated_alerts]
            )
            
            # Determine correlation threat level
            threat_level = max(
                (self.alerts_by_id[aid].threat_level for aid in correlated_alerts),
                key=lambda x: self._threat_level_rank(x)
            )
            
            correlation = AlertCorrelation(
                correlation_id=correlation_id,
                related_alert_ids=correlated_alerts,
                correlation_score=confidence,
                threat_level=threat_level,
                timestamp=current_time,
                attack_pattern=attack_pattern,
                attack_phase=self._estimate_attack_phase(attack_pattern, correlated_alerts),
            )
            
            self.correlations[correlation_id] = correlation
            self.metrics["correlations"] += 1
            
            logger.warning(
                f"Alert correlation detected: {correlation_id} "
                f"(pattern={attack_pattern}, confidence={confidence:.2f})"
            )
            
            return correlation_id
        
        return None
    
    def _is_related_alert(self, alert1: CrossModuleAlert, alert2: CrossModuleAlert) -> bool:
        """Check if two alerts are likely related."""
        # Same device
        if alert1.device_id and alert2.device_id and alert1.device_id == alert2.device_id:
            return True
        
        # Same IP pair
        if (alert1.source_ip == alert2.source_ip and 
            alert1.dest_ip == alert2.dest_ip):
            return True
        
        # Same session
        if (alert1.session_id and alert2.session_id and 
            alert1.session_id == alert2.session_id):
            return True
        
        return False
    
    def _detect_attack_pattern(
        self,
        alerts: List[CrossModuleAlert],
    ) -> Tuple[Optional[str], float]:
        """
        Detect known attack patterns from alert sequence.
        
        Returns:
            (pattern_name, confidence_score)
        """
        # Analyze alert types and sources
        alert_types = [alert.alert_type for alert in alerts]
        sources = [alert.source_module for alert in alerts]
        
        # Check for privilege escalation pattern
        if any("privilege" in t.lower() for t in alert_types) and "tds" in sources and "ids" in sources:
            return "privilege_escalation_attack", 0.85
        
        # Check for exfiltration pattern
        if any("exfiltration" in t.lower() or "throughput" in t.lower() for t in alert_types):
            return "data_exfiltration", 0.75
        
        # Check for lateral movement
        if any("lateral" in t.lower() for t in alert_types):
            return "lateral_movement", 0.80
        
        # Check for DDoS pattern
        if any("flood" in t.lower() or "packet" in t.lower() for t in alert_types):
            return "ddos_attack", 0.70
        
        return None, 0.0
    
    def _estimate_attack_phase(
        self,
        attack_pattern: Optional[str],
        alert_ids: List[str],
    ) -> Optional[str]:
        """Estimate current phase of attack based on pattern and alerts."""
        if not attack_pattern:
            return None
        
        pattern_def = self.known_attack_patterns.get(attack_pattern, {})
        phases = pattern_def.get("phases", [])
        
        if not phases:
            return None
        
        # Simple heuristic: estimate phase based on number of alerts
        phase_index = min(len(alert_ids) - 1, len(phases) - 1)
        return phases[phase_index]
    
    def _threat_level_rank(self, threat_level: ThreatLevel) -> int:
        """Get numeric rank of threat level for comparison."""
        ranking = {
            ThreatLevel.CRITICAL: 4,
            ThreatLevel.HIGH: 3,
            ThreatLevel.MEDIUM: 2,
            ThreatLevel.LOW: 1,
            ThreatLevel.INFO: 0,
        }
        return ranking.get(threat_level, -1)
    
    def _recommend_actions(self, alert: CrossModuleAlert) -> List[ResponseAction]:
        """
        Recommend response actions based on alert.
        
        Returns:
            List of recommended actions
        """
        actions = []
        
        # Critical threats: immediate block
        if alert.threat_level == ThreatLevel.CRITICAL:
            actions.extend([
                ResponseAction.BLOCK,
                ResponseAction.INVESTIGATE,
                ResponseAction.ALERT,
            ])
            if alert.session_id:
                actions.append(ResponseAction.REVOKE_SESSION)
        
        # High threats: investigate and monitor
        elif alert.threat_level == ThreatLevel.HIGH:
            actions.extend([
                ResponseAction.INVESTIGATE,
                ResponseAction.LOG,
                ResponseAction.ALERT,
            ])
        
        # Medium: monitor
        elif alert.threat_level == ThreatLevel.MEDIUM:
            actions.extend([
                ResponseAction.LOG,
                ResponseAction.ALERT,
            ])
        
        # Low/Info: just log
        else:
            actions.append(ResponseAction.LOG)
        
        alert.suggested_actions = actions
        for action in actions:
            self.metrics["actions_taken"][action.value] += 1
        
        return actions
    
    def share_threat_intelligence(
        self,
        threat_id: str,
        threat_type: str,
        threat_level: ThreatLevel,
        source: AlertSource,
        indicators: Dict[str, Any],
        confidence: float = 0.8,
    ) -> ThreatIntelligence:
        """
        Share threat intelligence across TDS and IDS modules.
        
        Args:
            threat_id: Unique threat identifier
            threat_type: Category of threat
            threat_level: Severity level
            source: Which module detected this
            indicators: IOCs, patterns, signatures, etc.
            confidence: Confidence in threat assessment (0.0-1.0)
            
        Returns:
            ThreatIntelligence object
        """
        threat_intel = ThreatIntelligence(
            threat_id=threat_id,
            threat_type=threat_type,
            threat_level=threat_level,
            source=source,
            timestamp=datetime.now(),
            indicators=indicators,
            confidence=confidence,
        )
        
        with self._lock:
            self.threat_pool[threat_id] = threat_intel
        
        logger.info(
            f"Threat intelligence shared: {threat_id} "
            f"({threat_type}, confidence={confidence:.2f})"
        )
        
        return threat_intel
    
    def get_threat_intelligence(self, threat_id: str) -> Optional[ThreatIntelligence]:
        """Retrieve threat intelligence by ID."""
        return self.threat_pool.get(threat_id)
    
    def query_threat_intelligence(
        self,
        threat_type: Optional[str] = None,
        min_confidence: float = 0.5,
        min_threat_level: Optional[ThreatLevel] = None,
    ) -> List[ThreatIntelligence]:
        """
        Query threat intelligence pool.
        
        Args:
            threat_type: Filter by type
            min_confidence: Minimum confidence threshold
            min_threat_level: Minimum threat level
            
        Returns:
            Matching threat intelligence records
        """
        results = []
        min_level_rank = (
            self._threat_level_rank(min_threat_level) if min_threat_level else -1
        )
        
        for intel in self.threat_pool.values():
            if threat_type and intel.threat_type != threat_type:
                continue
            
            if intel.confidence < min_confidence:
                continue
            
            if self._threat_level_rank(intel.threat_level) < min_level_rank:
                continue
            
            results.append(intel)
        
        return results
    
    def get_alert(self, alert_id: str) -> Optional[CrossModuleAlert]:
        """Retrieve an alert by ID."""
        return self.alerts_by_id.get(alert_id)
    
    def get_recent_alerts(
        self,
        hours: int = 1,
        threat_level: Optional[ThreatLevel] = None,
        source_module: Optional[str] = None,
    ) -> List[CrossModuleAlert]:
        """
        Get recent alerts with optional filtering.
        
        Args:
            hours: Time window
            threat_level: Filter by severity
            source_module: Filter by module ("tds" or "ids")
            
        Returns:
            Matching alerts in reverse chronological order
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        results = []
        
        for alert_id in reversed(self.alerts_timeline):
            alert = self.alerts_by_id.get(alert_id)
            if not alert:
                continue
            
            if alert.timestamp < cutoff_time:
                break
            
            if threat_level and alert.threat_level != threat_level:
                continue
            
            if source_module and alert.source_module != source_module:
                continue
            
            results.append(alert)
        
        return results
    
    def get_correlation(self, correlation_id: str) -> Optional[AlertCorrelation]:
        """Retrieve alert correlation by ID."""
        return self.correlations.get(correlation_id)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get bridge metrics and statistics."""
        with self._lock:
            return {
                **self.metrics,
                "alerts_in_memory": len(self.alerts_by_id),
                "threat_intel_items": len(self.threat_pool),
                "correlations": len(self.correlations),
                "timeline_size": len(self.alerts_timeline),
            }


# Singleton instance
_ids_bridge_instance: Optional[IDSBridge] = None


def get_ids_bridge() -> IDSBridge:
    """Get or create IDS Bridge singleton."""
    global _ids_bridge_instance
    if _ids_bridge_instance is None:
        _ids_bridge_instance = IDSBridge()
    return _ids_bridge_instance


def report_tds_threat(
    device_id: str,
    session_id: Optional[str],
    threat_type: str,
    threat_level: ThreatLevel,
    risk_score: float,
    indicators: Dict[str, Any],
    source_ip: Optional[str] = None,
    dest_ip: Optional[str] = None,
) -> str:
    """Helper function to report TDS threat through bridge."""
    bridge = get_ids_bridge()
    return bridge.report_tds_threat(
        device_id=device_id,
        session_id=session_id,
        threat_type=threat_type,
        threat_level=threat_level,
        risk_score=risk_score,
        indicators=indicators,
        source_ip=source_ip,
        dest_ip=dest_ip,
    )


def report_ids_detection(
    source_ip: str,
    dest_ip: str,
    detection_type: str,
    signature_id: Optional[str],
    severity: ThreatLevel,
    protocol: Optional[str] = None,
    port: Optional[int] = None,
    indicators: Optional[Dict[str, Any]] = None,
) -> str:
    """Helper function to report IDS detection through bridge."""
    bridge = get_ids_bridge()
    return bridge.report_ids_detection(
        source_ip=source_ip,
        dest_ip=dest_ip,
        detection_type=detection_type,
        signature_id=signature_id,
        severity=severity,
        protocol=protocol,
        port=port,
        indicators=indicators,
    )
