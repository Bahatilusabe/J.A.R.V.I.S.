"""
IMMUNE SENSORY SYSTEM - Noise Suppression Engine
============================================
Filters noise and false positives from security signals, similar to:
- Sensory gating (inhibiting repetitive stimuli)
- Signal-to-noise filtering (focusing on salient threats)
- Habituation (adapting to baseline patterns)

Key Mechanisms:
1. Baseline Learning - What is normal behavior?
2. Noise Detection - What is repetitive/harmless?
3. Habituation - Gradually raise detection thresholds
4. Whitelist Management - Known-good behaviors
5. Temporal Filtering - Distinguish blips from trends
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
import numpy as np
from collections import defaultdict, deque
import json


class NoiseCategory(Enum):
    """Types of noise/false positives"""
    SCAN_NOISE = "scan_noise"                       # Regular scanners
    MAINTENANCE = "maintenance"                     # Scheduled activities
    WHITELIST_MATCH = "whitelist_match"             # Known-good behavior
    HABITUATED_PATTERN = "habituated_pattern"       # Seen many times
    STATISTICAL_FLUCTUATION = "stat_fluctuation"   # Normal variance
    SENSOR_ARTIFACT = "sensor_artifact"            # Measurement error
    BUSINESS_AS_USUAL = "business_as_usual"        # Expected operations


@dataclass
class NoiseSignature:
    """Profile of known noise/harmless activity"""
    signature_id: str
    category: NoiseCategory
    pattern_description: str
    
    # Matching criteria
    source_ips: Set[str] = field(default_factory=set)
    dest_ips: Set[str] = field(default_factory=set)
    protocols: Set[str] = field(default_factory=set)
    ports: Set[int] = field(default_factory=set)
    time_windows: List[Tuple[int, int]] = field(default_factory=list)  # (hour_start, hour_end)
    
    # Confidence
    is_approved: bool = False                       # Whitelisted?
    confidence: float = 0.5                         # How sure is this noise?
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_seen: Optional[datetime] = None
    occurrence_count: int = 0


@dataclass
class BaselineProfile:
    """Normal behavior baseline for a network segment"""
    segment_id: str
    
    # Traffic patterns
    avg_packets_per_hour: float = 0.0
    peak_packets_per_hour: float = 0.0
    traffic_stddev: float = 0.0
    
    # Known services
    expected_services: Set[str] = field(default_factory=set)
    expected_protocols: Set[str] = field(default_factory=set)
    
    # Known hosts
    expected_hosts: Set[str] = field(default_factory=set)
    
    # Temporal patterns
    traffic_by_hour: Dict[int, float] = field(default_factory=dict)
    traffic_by_day: Dict[str, float] = field(default_factory=dict)
    
    # Last updated
    last_updated: datetime = field(default_factory=datetime.now)
    samples_collected: int = 0


class NoiseSuppressionEngine:
    """
    Filters false positives and noise from security signals.
    
    Works like sensory gating in the nervous system:
    - Ignores irrelevant stimuli
    - Focuses on salient threats
    - Learns what is background noise
    - Prevents habituation to real threats
    """
    
    def __init__(self, learning_period_hours: int = 72):
        self.noise_signatures: Dict[str, NoiseSignature] = {}
        self.baselines: Dict[str, BaselineProfile] = {}
        self.whitelist: Dict[str, Dict[str, any]] = {}
        self.learning_period = learning_period_hours
        
        # Signal filtering
        self.signal_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.suppressed_count: Dict[str, int] = defaultdict(int)
        
        # Habituation tracking
        self.habituation_scores: Dict[str, float] = defaultdict(float)
        self.alert_fatigue_threshold = 100  # Suppress after N occurrences
        
    def add_noise_signature(
        self,
        signature_id: str,
        category: NoiseCategory,
        pattern_description: str,
        source_ips: Optional[Set[str]] = None,
        dest_ips: Optional[Set[str]] = None,
        protocols: Optional[Set[str]] = None,
        is_approved: bool = False,
        confidence: float = 0.8,
    ) -> NoiseSignature:
        """Register a known noise pattern"""
        sig = NoiseSignature(
            signature_id=signature_id,
            category=category,
            pattern_description=pattern_description,
            source_ips=source_ips or set(),
            dest_ips=dest_ips or set(),
            protocols=protocols or set(),
            is_approved=is_approved,
            confidence=confidence,
        )
        
        self.noise_signatures[signature_id] = sig
        return sig
    
    def add_whitelist_entry(
        self,
        entry_id: str,
        source_ip: Optional[str] = None,
        dest_ip: Optional[str] = None,
        protocol: Optional[str] = None,
        port: Optional[int] = None,
        reason: str = "manual_entry",
        expires_at: Optional[datetime] = None,
    ) -> None:
        """Add to whitelist"""
        self.whitelist[entry_id] = {
            "source_ip": source_ip,
            "dest_ip": dest_ip,
            "protocol": protocol,
            "port": port,
            "reason": reason,
            "created_at": datetime.now(),
            "expires_at": expires_at,
        }
    
    def learn_baseline(
        self,
        segment_id: str,
        historical_signals: List[Dict[str, any]],
    ) -> BaselineProfile:
        """
        Learn normal behavior from historical data.
        Extracts statistical baseline.
        """
        baseline = BaselineProfile(segment_id=segment_id)
        
        if not historical_signals:
            self.baselines[segment_id] = baseline
            return baseline
        
        # Extract traffic volumes per hour
        hourly_traffic = defaultdict(float)
        daily_traffic = defaultdict(float)
        services = set()
        hosts = set()
        protocols = set()
        
        for sig in historical_signals:
            hour = sig.get("timestamp", datetime.now()).hour
            day = sig.get("timestamp", datetime.now()).strftime("%A")
            
            hourly_traffic[hour] += sig.get("intensity", 0.5)
            daily_traffic[day] += sig.get("intensity", 0.5)
            services.add(sig.get("service", "unknown"))
            hosts.add(sig.get("host", "unknown"))
            protocols.add(sig.get("protocol", "unknown"))
        
        # Calculate statistics
        traffic_values = list(hourly_traffic.values())
        baseline.avg_packets_per_hour = np.mean(traffic_values) if traffic_values else 0
        baseline.peak_packets_per_hour = np.max(traffic_values) if traffic_values else 0
        baseline.traffic_stddev = np.std(traffic_values) if traffic_values else 0
        baseline.traffic_by_hour = dict(hourly_traffic)
        baseline.traffic_by_day = dict(daily_traffic)
        baseline.expected_services = services
        baseline.expected_hosts = hosts
        baseline.expected_protocols = protocols
        baseline.samples_collected = len(historical_signals)
        
        self.baselines[segment_id] = baseline
        return baseline
    
    def is_noise(
        self,
        signal: Dict[str, any],
        segment_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[str], float]:
        """
        Determine if signal is noise/false positive.
        
        Returns:
            (is_noise: bool, reason: str, confidence: float)
        """
        
        # 1. Check against whitelist
        if self._check_whitelist(signal):
            return True, NoiseCategory.WHITELIST_MATCH.value, 0.95
        
        # 2. Check against approved noise signatures
        for sig_id, sig in self.noise_signatures.items():
            if sig.is_approved and self._matches_signature(signal, sig):
                return True, sig.category.value, sig.confidence
        
        # 3. Check against baseline (if available)
        if segment_id and segment_id in self.baselines:
            baseline = self.baselines[segment_id]
            if self._is_within_baseline(signal, baseline):
                return True, NoiseCategory.BUSINESS_AS_USUAL.value, 0.7
        
        # 4. Check for habituation (repeated pattern)
        pattern_key = self._get_pattern_key(signal)
        if self.habituation_scores.get(pattern_key, 0) > 0.8:
            return True, NoiseCategory.HABITUATED_PATTERN.value, 0.6
        
        # 5. Check signal history for duplicates
        if self._is_repeated_signal(signal):
            return True, NoiseCategory.SCAN_NOISE.value, 0.5
        
        return False, None, 0.0
    
    def suppress_signal(
        self,
        signal_id: str,
        reason: NoiseCategory,
    ) -> None:
        """Record suppressed signal"""
        self.suppressed_count[signal_id] += 1
        
        # Update habituation
        pattern_key = self._get_pattern_key({"id": signal_id})
        self.habituation_scores[pattern_key] = min(
            self.habituation_scores[pattern_key] + 0.1,
            1.0
        )
    
    def get_noise_summary(self) -> Dict[str, any]:
        """Get noise suppression statistics"""
        total_suppressed = sum(self.suppressed_count.values())
        
        return {
            "total_signals_suppressed": total_suppressed,
            "noise_signatures_registered": len(self.noise_signatures),
            "approved_signatures": sum(
                1 for s in self.noise_signatures.values() if s.is_approved
            ),
            "whitelist_entries": len(self.whitelist),
            "baselines_learned": len(self.baselines),
            "top_suppressed_patterns": sorted(
                self.suppressed_count.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
        }
    
    def _check_whitelist(self, signal: Dict[str, any]) -> bool:
        """Check if signal matches whitelist"""
        for entry_id, entry in self.whitelist.items():
            # Check if entry has expired
            if entry.get("expires_at") and entry["expires_at"] < datetime.now():
                del self.whitelist[entry_id]
                continue
            
            # Check field matches
            if entry.get("source_ip") and signal.get("source_ip") != entry["source_ip"]:
                continue
            if entry.get("dest_ip") and signal.get("dest_ip") != entry["dest_ip"]:
                continue
            if entry.get("protocol") and signal.get("protocol") != entry["protocol"]:
                continue
            if entry.get("port") and signal.get("port") != entry["port"]:
                continue
            
            return True
        
        return False
    
    def _matches_signature(self, signal: Dict[str, any], sig: NoiseSignature) -> bool:
        """Check if signal matches noise signature"""
        # Check source IPs
        if sig.source_ips:
            source = signal.get("source_ip", "")
            if source not in sig.source_ips:
                # Check if source is in CIDR ranges (simplified)
                if not any(self._ip_in_range(source, cidr) for cidr in sig.source_ips):
                    return False
        
        # Check dest IPs
        if sig.dest_ips:
            dest = signal.get("dest_ip", "")
            if dest not in sig.dest_ips:
                if not any(self._ip_in_range(dest, cidr) for cidr in sig.dest_ips):
                    return False
        
        # Check protocols
        if sig.protocols and signal.get("protocol") not in sig.protocols:
            return False
        
        # Check time windows
        if sig.time_windows:
            current_hour = datetime.now().hour
            in_window = any(
                start <= current_hour < end
                for start, end in sig.time_windows
            )
            if not in_window:
                return False
        
        return True
    
    def _is_within_baseline(
        self,
        signal: Dict[str, any],
        baseline: BaselineProfile
    ) -> bool:
        """Check if signal is within baseline"""
        intensity = signal.get("intensity", 0.5)
        hour = datetime.now().hour
        
        # Check if intensity is within 2 standard deviations
        baseline_intensity = baseline.traffic_by_hour.get(hour, 0)
        deviation = abs(intensity - baseline_intensity)
        
        if baseline.traffic_stddev > 0:
            z_score = deviation / (baseline.traffic_stddev + 0.001)
            return z_score < 2.0  # Within 2 stddevs
        
        return False
    
    def _is_repeated_signal(self, signal: Dict[str, any]) -> bool:
        """Check if signal is repeated/duplicate"""
        pattern_key = self._get_pattern_key(signal)
        
        # Check history
        if pattern_key in self.signal_history:
            recent = list(self.signal_history[pattern_key])
            if len(recent) > 50:
                # If same pattern seen 50+ times recently, it's noise
                return True
        
        self.signal_history[pattern_key].append(datetime.now())
        return False
    
    def _get_pattern_key(self, signal: Dict[str, any]) -> str:
        """Extract pattern key from signal"""
        return f"{signal.get('source_ip', 'x')}:{signal.get('protocol', 'x')}:{signal.get('port', 0)}"
    
    def _ip_in_range(self, ip: str, cidr: str) -> bool:
        """Simple IP range check (simplified - would use ipaddress module)"""
        # Simplified implementation
        return ip.startswith(cidr.replace("/24", ""))


class AdaptiveNoiseThreshold:
    """
    Dynamically adjusts noise filtering thresholds based on:
    - Time of day
    - Day of week
    - Alert fatigue
    - Recent threat level
    """
    
    def __init__(self):
        self.base_threshold = 0.5
        self.alert_count_last_hour = deque(maxlen=60)
        self.alert_count_last_day = deque(maxlen=1440)
        
    def get_threshold(
        self,
        time_context: datetime,
        current_threat_level: float,
        fatigue_index: float,  # 0-1 how tired are operators?
    ) -> float:
        """
        Get current noise threshold.
        Higher threshold = more aggressive filtering = fewer alerts.
        """
        threshold = self.base_threshold
        
        # Time-of-day adjustment
        hour = time_context.hour
        if 22 <= hour or hour < 6:
            # Night hours - lower threshold (more sensitive)
            threshold *= 0.8
        elif 9 <= hour < 17:
            # Business hours - normal
            threshold *= 1.0
        else:
            # Off-peak - slightly higher threshold
            threshold *= 1.1
        
        # Day-of-week adjustment
        day_of_week = time_context.weekday()
        if day_of_week >= 5:  # Weekend
            threshold *= 0.85  # More sensitive
        
        # Threat level adjustment
        if current_threat_level > 0.8:
            threshold *= 0.5  # Urgent - less filtering
        elif current_threat_level > 0.5:
            threshold *= 0.75
        
        # Fatigue adjustment
        if fatigue_index > 0.8:
            threshold *= 1.3  # Reduce alert volume if tired
        
        return min(threshold, 0.95)  # Cap at 0.95
    
    def record_alert(self) -> None:
        """Record that an alert was sent"""
        self.alert_count_last_hour.append(datetime.now())
        self.alert_count_last_day.append(datetime.now())
    
    def get_alert_rate(self) -> Dict[str, float]:
        """Get alert statistics"""
        now = datetime.now()
        alerts_per_hour = len(self.alert_count_last_hour)
        alerts_per_day = len(self.alert_count_last_day)
        
        return {
            "alerts_last_hour": alerts_per_hour,
            "alerts_last_day": alerts_per_day,
            "average_per_hour": alerts_per_day / 24,
            "fatigue_index": min(alerts_per_hour / 50, 1.0),  # 50+ alerts = maximum fatigue
        }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    engine = NoiseSuppressionEngine()
    
    # Register known noise pattern (regular scanner)
    engine.add_noise_signature(
        signature_id="scanner_nessus",
        category=NoiseCategory.SCAN_NOISE,
        pattern_description="Nessus vulnerability scanner",
        source_ips={"192.168.1.50"},
        ports={80, 443, 22, 23, 25, 445},
        is_approved=True,
        confidence=0.95,
    )
    
    # Add to whitelist
    engine.add_whitelist_entry(
        entry_id="whitelist_maintenance",
        source_ip="10.0.0.1",
        protocol="SMTP",
        reason="Email backup server",
    )
    
    # Create baseline
    historical = [
        {"intensity": 0.3, "timestamp": datetime.now() - timedelta(hours=i), "service": "HTTP"}
        for i in range(24)
    ]
    baseline = engine.learn_baseline("segment_1", historical)
    print(f"Baseline learned: avg={baseline.avg_packets_per_hour:.2f}")
    
    # Test signal filtering
    test_signal = {
        "source_ip": "192.168.1.50",
        "dest_ip": "10.0.0.5",
        "protocol": "TCP",
        "port": 443,
        "intensity": 0.4,
    }
    
    is_noise, reason, confidence = engine.is_noise(test_signal, "segment_1")
    print(f"\nSignal is noise: {is_noise} (reason: {reason}, confidence: {confidence})")
    
    # Print summary
    print(f"\nNoise Summary:")
    print(json.dumps(engine.get_noise_summary(), indent=2, default=str))
