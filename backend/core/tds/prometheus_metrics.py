"""
Real-time Prometheus Metrics for TDS Module

Provides comprehensive observability and monitoring for TDS subsystem:
- Real-time performance metrics (latency, throughput)
- Detection and false positive rates
- Session and device health statistics
- SLA compliance monitoring
- Custom alert thresholds

Integration:
    TDS Components
    (Session Scorer, Device Health, IDS Bridge)
            ↓
    Metrics Collector
            ↓
    Prometheus Format
            ↓
    /metrics endpoint → Prometheus/Grafana
"""

import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Prometheus metric types."""
    COUNTER = "counter"              # Monotonically increasing
    GAUGE = "gauge"                  # Can increase or decrease
    HISTOGRAM = "histogram"           # Distribution (buckets)
    SUMMARY = "summary"              # Distribution (quantiles)


@dataclass
class Histogram:
    """Simple histogram implementation for distributions."""
    name: str
    buckets: List[float] = field(default_factory=lambda: [
        0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0
    ])
    bucket_counts: Dict[float, int] = field(default_factory=dict)
    sum_value: float = 0.0
    count_value: int = 0
    
    def __post_init__(self):
        """Initialize bucket counts."""
        for bucket in self.buckets:
            self.bucket_counts[bucket] = 0
    
    def observe(self, value: float) -> None:
        """Add observation to histogram."""
        for bucket in self.buckets:
            if value <= bucket:
                self.bucket_counts[bucket] += 1
        self.sum_value += value
        self.count_value += 1
    
    def get_mean(self) -> float:
        """Calculate mean value."""
        return self.sum_value / self.count_value if self.count_value > 0 else 0.0


@dataclass
class SLAThreshold:
    """SLA threshold definition."""
    metric_name: str
    max_value: Optional[float] = None
    min_value: Optional[float] = None
    warning_threshold: float = 0.8
    critical_threshold: float = 0.95


class MetricsCollector:
    """
    Collects and exports metrics in Prometheus format.
    
    Metrics tracked:
    - Session metrics: count, duration, risk distribution
    - Device metrics: health score distribution, device count by status
    - API latency: endpoint response times
    - Detection metrics: alerts per module, correlation rates
    - System metrics: CPU, memory, event processing rate
    - SLA metrics: detection latency, false positive rate
    """
    
    def __init__(self, retention_hours: int = 24):
        """
        Initialize metrics collector.
        
        Args:
            retention_hours: How long to keep detailed metrics
        """
        self.retention_hours = retention_hours
        
        # Counters
        self.counters: Dict[str, float] = defaultdict(float)
        
        # Gauges (current values)
        self.gauges: Dict[str, float] = defaultdict(float)
        
        # Histograms (distributions)
        self.histograms: Dict[str, Histogram] = {}
        
        # Time-series data for SLA tracking
        self.metric_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=500)  # Keep last 500 data points
        )
        
        # SLA definitions
        self.sla_thresholds: List[SLAThreshold] = self._init_sla_thresholds()
        
        # Lock for thread-safety
        self._lock = threading.RLock()
        
        # Metrics metadata
        self.metric_descriptions = {
            # Session metrics
            "tds_sessions_active": "Number of active VPN sessions",
            "tds_sessions_total": "Total sessions created (counter)",
            "tds_session_duration_seconds": "Session duration distribution",
            "tds_session_risk_distribution": "Distribution of session risk scores",
            
            # Device metrics
            "tds_devices_total": "Total devices seen",
            "tds_devices_healthy": "Devices with health > 0.8",
            "tds_devices_at_risk": "Devices with health < 0.4",
            "tds_device_health_distribution": "Distribution of device health scores",
            
            # Detection metrics
            "tds_alerts_total": "Total alerts generated",
            "tds_alerts_critical": "Critical severity alerts",
            "tds_alerts_high": "High severity alerts",
            "tds_correlations_total": "Total alert correlations detected",
            "tds_threat_intelligence_items": "Items in threat intelligence pool",
            
            # API metrics
            "tds_api_request_latency_seconds": "API endpoint response times",
            "tds_api_requests_total": "Total API requests",
            "tds_api_errors_total": "Total API errors",
            
            # Detection quality
            "tds_false_positive_rate": "False positive rate (0.0-1.0)",
            "tds_detection_latency_seconds": "Time from event to alert",
            "tds_threat_detection_rate": "Percentage of threats detected",
            
            # Processing metrics
            "tds_events_processed_total": "Total events processed",
            "tds_events_processing_rate": "Events processed per second",
            "tds_ml_model_inference_time_seconds": "ML model inference latency",
            
            # System metrics
            "tds_cpu_usage_percent": "TDS module CPU usage %",
            "tds_memory_usage_bytes": "TDS module memory usage",
            "tds_uptime_seconds": "Module uptime",
        }
        
        logger.info("Metrics collector initialized")
    
    def _init_sla_thresholds(self) -> List[SLAThreshold]:
        """Initialize SLA threshold definitions."""
        return [
            # Detection latency SLA: Alert within 5 seconds
            SLAThreshold(
                metric_name="tds_detection_latency_seconds",
                max_value=5.0,
                warning_threshold=3.0,
                critical_threshold=5.0,
            ),
            # False positive rate SLA: < 5%
            SLAThreshold(
                metric_name="tds_false_positive_rate",
                max_value=0.05,
                warning_threshold=0.03,
                critical_threshold=0.05,
            ),
            # API latency SLA: < 500ms
            SLAThreshold(
                metric_name="tds_api_request_latency_seconds",
                max_value=0.5,
                warning_threshold=0.3,
                critical_threshold=0.5,
            ),
            # Detection rate SLA: > 95%
            SLAThreshold(
                metric_name="tds_threat_detection_rate",
                min_value=0.95,
                warning_threshold=0.97,
                critical_threshold=0.95,
            ),
        ]
    
    def increment_counter(self, metric_name: str, value: float = 1.0) -> None:
        """Increment a counter metric."""
        with self._lock:
            self.counters[metric_name] += value
    
    def set_gauge(self, metric_name: str, value: float) -> None:
        """Set a gauge metric value."""
        with self._lock:
            self.gauges[metric_name] = value
            # Record in history for SLA tracking
            self.metric_history[metric_name].append({
                "timestamp": time.time(),
                "value": value,
            })
    
    def observe_histogram(self, metric_name: str, value: float) -> None:
        """Record a histogram observation."""
        with self._lock:
            if metric_name not in self.histograms:
                self.histograms[metric_name] = Histogram(metric_name)
            
            self.histograms[metric_name].observe(value)
            # Record in history
            self.metric_history[metric_name].append({
                "timestamp": time.time(),
                "value": value,
            })
    
    def record_api_latency(self, endpoint: str, latency_seconds: float) -> None:
        """Record API endpoint latency."""
        self.observe_histogram("tds_api_request_latency_seconds", latency_seconds)
        self.increment_counter("tds_api_requests_total")
    
    def record_api_error(self, endpoint: str, error_code: int) -> None:
        """Record API error."""
        self.increment_counter("tds_api_errors_total")
        self.increment_counter(f"tds_api_errors_{error_code}")
    
    def record_detection_event(
        self,
        threat_type: str,
        detection_latency_seconds: float,
        confidence: float = 1.0,
    ) -> None:
        """
        Record a threat detection event.
        
        Args:
            threat_type: Type of threat detected
            detection_latency_seconds: Time from event to detection
            confidence: Confidence score (0.0-1.0)
        """
        self.increment_counter("tds_alerts_total")
        self.increment_counter(f"tds_alerts_{threat_type}")
        self.observe_histogram("tds_detection_latency_seconds", detection_latency_seconds)
    
    def record_false_positive(self) -> None:
        """Record a false positive detection."""
        self.increment_counter("tds_false_positives_total")
    
    def record_session_created(self, risk_score: float, duration_seconds: float = 0) -> None:
        """Record new session creation."""
        self.increment_counter("tds_sessions_total")
        self.observe_histogram("tds_session_risk_distribution", risk_score)
        if duration_seconds > 0:
            self.observe_histogram("tds_session_duration_seconds", duration_seconds)
    
    def record_session_closed(self, duration_seconds: float) -> None:
        """Record session closure."""
        self.observe_histogram("tds_session_duration_seconds", duration_seconds)
    
    def update_active_sessions(self, count: int) -> None:
        """Update active session count."""
        self.set_gauge("tds_sessions_active", float(count))
    
    def update_device_health(self, device_id: str, health_score: float) -> None:
        """Record device health assessment."""
        self.observe_histogram("tds_device_health_distribution", health_score)
    
    def update_device_status(
        self,
        total: int,
        healthy: int,
        at_risk: int,
    ) -> None:
        """Update device statistics."""
        self.set_gauge("tds_devices_total", float(total))
        self.set_gauge("tds_devices_healthy", float(healthy))
        self.set_gauge("tds_devices_at_risk", float(at_risk))
    
    def record_ml_inference(self, latency_seconds: float, model_name: str = "default") -> None:
        """Record ML model inference latency."""
        self.observe_histogram("tds_ml_model_inference_time_seconds", latency_seconds)
    
    def record_event_processing(self, count: int = 1) -> None:
        """Record event processing."""
        self.increment_counter("tds_events_processed_total", count)
    
    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus text format.
        
        Returns:
            Prometheus-formatted metrics string
        """
        with self._lock:
            lines = []
            
            # Add HELP and TYPE comments
            for metric_name, description in self.metric_descriptions.items():
                lines.append(f"# HELP {metric_name} {description}")
            
            lines.append("")
            
            # Export counters
            for metric_name, value in self.counters.items():
                if metric_name in self.metric_descriptions:
                    lines.append(f"# TYPE {metric_name} counter")
                lines.append(f"{metric_name} {value}")
            
            # Export gauges
            for metric_name, value in self.gauges.items():
                if metric_name in self.metric_descriptions:
                    lines.append(f"# TYPE {metric_name} gauge")
                lines.append(f"{metric_name} {value}")
            
            # Export histograms
            for metric_name, histogram in self.histograms.items():
                lines.append(f"# TYPE {metric_name} histogram")
                
                # Add bucket data
                for bucket, count in sorted(histogram.bucket_counts.items()):
                    lines.append(f'{metric_name}_bucket{{le="{bucket}"}} {count}')
                
                # Add sum and count
                lines.append(f"{metric_name}_sum {histogram.sum_value}")
                lines.append(f"{metric_name}_count {histogram.count_value}")
            
            return "\n".join(lines)
    
    def check_sla_compliance(self) -> Dict[str, Any]:
        """
        Check SLA compliance for all thresholds.
        
        Returns:
            SLA status report
        """
        with self._lock:
            report = {
                "timestamp": datetime.now().isoformat(),
                "sla_compliant": True,
                "violations": [],
                "warnings": [],
                "details": {},
            }
            
            for sla in self.sla_thresholds:
                metric_name = sla.metric_name
                current_value = self.gauges.get(metric_name)
                
                if current_value is None:
                    # Try histogram mean
                    if metric_name in self.histograms:
                        current_value = self.histograms[metric_name].get_mean()
                
                if current_value is None:
                    continue
                
                status = {
                    "metric": metric_name,
                    "current_value": current_value,
                    "status": "OK",
                }
                
                # Check max threshold
                if sla.max_value is not None and current_value > sla.max_value:
                    status["status"] = "VIOLATION"
                    report["sla_compliant"] = False
                    report["violations"].append({
                        "metric": metric_name,
                        "current": current_value,
                        "threshold": sla.max_value,
                    })
                elif sla.max_value is not None and current_value > sla.critical_threshold:
                    status["status"] = "WARNING"
                    report["warnings"].append({
                        "metric": metric_name,
                        "current": current_value,
                        "threshold": sla.critical_threshold,
                    })
                
                # Check min threshold
                if sla.min_value is not None and current_value < sla.min_value:
                    status["status"] = "VIOLATION"
                    report["sla_compliant"] = False
                    report["violations"].append({
                        "metric": metric_name,
                        "current": current_value,
                        "threshold": sla.min_value,
                    })
                elif sla.min_value is not None and current_value < sla.warning_threshold:
                    status["status"] = "WARNING"
                    report["warnings"].append({
                        "metric": metric_name,
                        "current": current_value,
                        "threshold": sla.warning_threshold,
                    })
                
                report["details"][metric_name] = status
            
            return report
    
    def get_metric_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        with self._lock:
            return {
                "timestamp": datetime.now().isoformat(),
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {
                    name: {
                        "mean": hist.get_mean(),
                        "count": hist.count_value,
                        "sum": hist.sum_value,
                    }
                    for name, hist in self.histograms.items()
                },
            }
    
    def reset_metrics(self) -> None:
        """Reset all metrics (for testing)."""
        with self._lock:
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.metric_history.clear()


# Singleton instance
_metrics_collector_instance: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create metrics collector singleton."""
    global _metrics_collector_instance
    if _metrics_collector_instance is None:
        _metrics_collector_instance = MetricsCollector()
    return _metrics_collector_instance


def record_api_latency(endpoint: str, latency_seconds: float) -> None:
    """Helper to record API latency."""
    collector = get_metrics_collector()
    collector.record_api_latency(endpoint, latency_seconds)


def record_detection_event(
    threat_type: str,
    detection_latency_seconds: float,
    confidence: float = 1.0,
) -> None:
    """Helper to record detection event."""
    collector = get_metrics_collector()
    collector.record_detection_event(threat_type, detection_latency_seconds, confidence)


def record_session_created(risk_score: float, duration_seconds: float = 0) -> None:
    """Helper to record session creation."""
    collector = get_metrics_collector()
    collector.record_session_created(risk_score, duration_seconds)


def update_active_sessions(count: int) -> None:
    """Helper to update active sessions."""
    collector = get_metrics_collector()
    collector.update_active_sessions(count)
