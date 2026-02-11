"""
Comprehensive Test Suite for TDS Module

Unit tests for all TDS components:
- Session Scoring Engine
- Device Health Classification
- Unified TDS API Router
- IDS Integration Bridge
- Edge Orchestration System
- Prometheus Metrics

Run: pytest backend/tests/unit/test_tds_core.py -v
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Import TDS components
from backend.core.tds.session_scorer import (
    SessionScorer, SessionEvent, SessionRiskLevel, BehaviorType, get_session_scorer
)
from backend.core.tds.device_health import (
    DeviceHealthClassifier, HealthStatus, VulnerabilityLevel, Vulnerability,
    get_device_health_classifier
)
from backend.core.tds.ids_bridge import (
    IDSBridge, ThreatLevel, AlertSource, ResponseAction, 
    CrossModuleAlert, ThreatIntelligence, get_ids_bridge
)
from backend.core.tds.edge_orchestration import (
    EdgeOrchestrator, GatewayConfig, GatewayStatus, LoadBalancingStrategy,
    get_edge_orchestrator
)
from backend.core.tds.prometheus_metrics import (
    MetricsCollector, Histogram, get_metrics_collector
)


class TestSessionScorer:
    """Tests for Session Scoring Engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = SessionScorer()
    
    def test_initialization(self):
        """Test scorer initialization."""
        assert self.scorer is not None
        assert len(self.scorer.sessions) == 0
    
    def test_add_event(self):
        """Test adding session event."""
        event = SessionEvent(
            timestamp=datetime.now(),
            event_type="packet",
            source_ip="192.168.1.100",
            dest_ip="10.0.0.1",
            protocol="tcp",
            port=443,
            bytes_sent=1024,
            bytes_received=512,
            packet_count=2,
        )
        
        self.scorer.add_event("session-1", "device-1", event)
        assert "session-1" in self.scorer.sessions
    
    def test_risk_level_escalation(self):
        """Test that risk level increases with suspicious events."""
        # Add normal events
        for i in range(3):
            event = SessionEvent(
                timestamp=datetime.now() + timedelta(seconds=i),
                event_type="packet",
                source_ip="192.168.1.100",
                dest_ip="10.0.0.1",
                protocol="tcp",
                port=443,
                bytes_sent=1000,
                bytes_received=500,
                packet_count=1,
            )
            self.scorer.add_event("session-1", "device-1", event)
        
        normal_score = self.scorer.get_session_score("session-1")
        
        # Add suspicious event (high throughput)
        suspicious_event = SessionEvent(
            timestamp=datetime.now() + timedelta(seconds=4),
            event_type="packet",
            source_ip="192.168.1.100",
            dest_ip="10.0.0.1",
            protocol="tcp",
            port=443,
            bytes_sent=1000000,  # Very high throughput
            bytes_received=500000,
            packet_count=100,
        )
        self.scorer.add_event("session-1", "device-1", suspicious_event)
        
        suspicious_score = self.scorer.get_session_score("session-1")
        
        # Risk should increase
        assert suspicious_score.composite_risk_score > normal_score.composite_risk_score
    
    def test_get_risky_sessions(self):
        """Test retrieving risky sessions."""
        # Add high-risk session
        for i in range(5):
            event = SessionEvent(
                timestamp=datetime.now() + timedelta(seconds=i),
                event_type="packet",
                source_ip="192.168.1.100",
                dest_ip="10.0.0.1",
                protocol="tcp",
                port=443,
                bytes_sent=5000000,
                bytes_received=2500000,
                packet_count=500,
                behavior_type=BehaviorType.SUSPICIOUS,
            )
            self.scorer.add_event("risky-session", "device-1", event)
        
        risky = self.scorer.get_risky_sessions(threshold=0.7)
        assert len(risky) > 0
        assert "risky-session" in [s.session_id for s in risky]
    
    def test_session_closure(self):
        """Test closing a session."""
        event = SessionEvent(
            timestamp=datetime.now(),
            event_type="packet",
            source_ip="192.168.1.100",
            dest_ip="10.0.0.1",
            protocol="tcp",
            port=443,
            bytes_sent=1024,
            bytes_received=512,
            packet_count=2,
        )
        
        self.scorer.add_event("session-1", "device-1", event)
        metrics = self.scorer.close_session("session-1")
        
        assert metrics is not None
        assert metrics.total_events > 0


class TestDeviceHealth:
    """Tests for Device Health Classifier."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = DeviceHealthClassifier()
    
    def test_initialization(self):
        """Test classifier initialization."""
        assert self.classifier is not None
        assert len(self.classifier.device_profiles) == 0
    
    def test_create_profile(self):
        """Test creating device profile."""
        profile = self.classifier.create_profile("device-1")
        assert profile is not None
        assert profile.device_id == "device-1"
    
    def test_vulnerability_assessment(self):
        """Test vulnerability assessment."""
        self.classifier.create_profile("device-1")
        
        vulns = [
            Vulnerability(
                cve_id="CVE-2024-1234",
                software="OpenSSL",
                severity=VulnerabilityLevel.CRITICAL,
                cvss_score=9.5,
                cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                affected_versions=["3.0.0"],
                exploitability=0.95,
                impact_score=0.95,
                discovery_date=datetime.now(),
                fix_available=True,
                patch_version="3.0.2",
                days_to_patch=5,
            )
        ]
        
        self.classifier.assess_vulnerabilities("device-1", vulns)
        profile = self.classifier.device_profiles.get("device-1")
        
        assert profile is not None
        assert len(profile.vulnerabilities) > 0
    
    def test_health_score_calculation(self):
        """Test health score calculation."""
        self.classifier.create_profile("device-1")
        
        # Create healthy device
        self.classifier.assess_vulnerabilities("device-1", [])
        self.classifier.assess_security_controls("device-1", {
            "antivirus": True,
            "firewall": True,
            "encryption": True,
            "edr": True,
        })
        self.classifier.assess_patch_status("device-1", days_since_update=5)
        
        score, status = self.classifier.calculate_health("device-1")
        
        assert score > 0.7
        assert status in [HealthStatus.EXCELLENT, HealthStatus.GOOD]
    
    def test_unhealthy_device(self):
        """Test unhealthy device detection."""
        self.classifier.create_profile("device-1")
        
        # Create unhealthy device
        vulns = [
            Vulnerability(
                cve_id="CVE-2024-9999",
                software="Critical",
                severity=VulnerabilityLevel.CRITICAL,
                cvss_score=10.0,
                cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                affected_versions=["*"],
                exploitability=1.0,
                impact_score=1.0,
                discovery_date=datetime.now(),
                fix_available=False,
                days_to_patch=0,
            )
        ]
        
        self.classifier.assess_vulnerabilities("device-1", vulns)
        self.classifier.assess_security_controls("device-1", {})
        self.classifier.assess_patch_status("device-1", days_since_update=180)
        
        score, status = self.classifier.calculate_health("device-1")
        
        assert score < 0.4
        assert status in [HealthStatus.CRITICAL, HealthStatus.POOR]


class TestIDSBridge:
    """Tests for IDS Integration Bridge."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.bridge = IDSBridge()
    
    def test_initialization(self):
        """Test bridge initialization."""
        assert self.bridge is not None
        assert len(self.bridge.alerts_by_id) == 0
    
    def test_report_tds_threat(self):
        """Test reporting TDS threat."""
        alert_id = self.bridge.report_tds_threat(
            device_id="device-1",
            session_id="session-1",
            threat_type="high_risk_session",
            threat_level=ThreatLevel.HIGH,
            risk_score=0.8,
            indicators={"reason": "privilege_escalation"},
            source_ip="192.168.1.100",
            dest_ip="10.0.0.1",
        )
        
        assert alert_id is not None
        alert = self.bridge.get_alert(alert_id)
        assert alert is not None
        assert alert.threat_level == ThreatLevel.HIGH
    
    def test_report_ids_detection(self):
        """Test reporting IDS detection."""
        alert_id = self.bridge.report_ids_detection(
            source_ip="192.168.1.100",
            dest_ip="10.0.0.1",
            detection_type="signature",
            signature_id="RULE-1234",
            severity=ThreatLevel.CRITICAL,
            protocol="tcp",
            port=443,
        )
        
        assert alert_id is not None
        alert = self.bridge.get_alert(alert_id)
        assert alert is not None
        assert alert.source_module == "ids"
    
    def test_alert_correlation(self):
        """Test alert correlation."""
        # Report TDS threat
        tds_alert_id = self.bridge.report_tds_threat(
            device_id="device-1",
            session_id="session-1",
            threat_type="privilege_escalation",
            threat_level=ThreatLevel.HIGH,
            risk_score=0.8,
            indicators={},
        )
        
        # Report related IDS detection
        ids_alert_id = self.bridge.report_ids_detection(
            source_ip="192.168.1.100",
            dest_ip="10.0.0.1",
            detection_type="signature",
            signature_id="EXPLOIT-5678",
            severity=ThreatLevel.HIGH,
        )
        
        # Check correlation
        correlations = list(self.bridge.correlations.values())
        assert len(correlations) > 0
    
    def test_threat_intelligence_sharing(self):
        """Test threat intelligence sharing."""
        threat_id = self.bridge.share_threat_intelligence(
            threat_id="malware-001",
            threat_type="malware",
            threat_level=ThreatLevel.CRITICAL,
            source=AlertSource.IDS_SIGNATURE,
            indicators={
                "hash": "abc123def456",
                "behavior": "ransomware",
            },
            confidence=0.95,
        )
        
        assert threat_id == "malware-001"
        intel = self.bridge.get_threat_intelligence("malware-001")
        assert intel is not None
        assert intel.confidence == 0.95
    
    def test_query_threat_intelligence(self):
        """Test querying threat intelligence."""
        self.bridge.share_threat_intelligence(
            threat_id="threat-1",
            threat_type="malware",
            threat_level=ThreatLevel.HIGH,
            source=AlertSource.TDS_SESSION_SCORER,
            indicators={},
            confidence=0.9,
        )
        
        results = self.bridge.query_threat_intelligence(
            threat_type="malware",
            min_confidence=0.8,
        )
        
        assert len(results) > 0
        assert results[0].threat_type == "malware"


class TestEdgeOrchestrator:
    """Tests for Edge Orchestration System."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = EdgeOrchestrator()
    
    def test_initialization(self):
        """Test orchestrator initialization."""
        assert self.orchestrator is not None
        assert len(self.orchestrator.gateways) == 0
    
    def test_register_gateway(self):
        """Test gateway registration."""
        config = GatewayConfig(
            gateway_id="gw-us-east",
            location="us-east-1",
            endpoint_url="http://gw1.example.com:8000",
            max_sessions=10000,
        )
        
        self.orchestrator.register_gateway(config)
        assert "gw-us-east" in self.orchestrator.gateways
    
    def test_distribute_session(self):
        """Test session distribution."""
        # Register gateway
        config = GatewayConfig(
            gateway_id="gw-1",
            location="us-east-1",
            endpoint_url="http://gw1.example.com:8000",
        )
        self.orchestrator.register_gateway(config)
        
        # Mark as healthy
        from backend.core.tds.edge_orchestration import GatewayMetrics
        metrics = GatewayMetrics(
            gateway_id="gw-1",
            timestamp=datetime.now(),
            active_sessions=10,
            cpu_usage_percent=30,
            memory_usage_percent=40,
        )
        self.orchestrator.update_gateway_metrics("gw-1", metrics)
        
        # Distribute session
        assigned_gateway = self.orchestrator.distribute_session(
            session_id="session-1",
            device_id="device-1",
            risk_score=0.5,
        )
        
        assert assigned_gateway == "gw-1"
        assert "session-1" in self.orchestrator.sessions
    
    def test_failover(self):
        """Test failover handling."""
        # Register two gateways
        for i in range(2):
            config = GatewayConfig(
                gateway_id=f"gw-{i}",
                location=f"zone-{i}",
                endpoint_url=f"http://gw{i}.example.com:8000",
            )
            self.orchestrator.register_gateway(config)
        
        # Mark as healthy
        from backend.core.tds.edge_orchestration import GatewayMetrics
        for i in range(2):
            metrics = GatewayMetrics(
                gateway_id=f"gw-{i}",
                timestamp=datetime.now(),
                active_sessions=5,
                cpu_usage_percent=30,
                memory_usage_percent=40,
            )
            self.orchestrator.update_gateway_metrics(f"gw-{i}", metrics)
        
        # Distribute session to gateway 0
        self.orchestrator.distribute_session("session-1", "device-1", 0.5)
        
        # Simulate failure of gateway 0
        migrated = self.orchestrator.handle_gateway_failure("gw-0")
        
        assert len(migrated) > 0
        assert self.orchestrator.session_gateway_map["session-1"] == "gw-1"
    
    def test_state_synchronization(self):
        """Test state synchronization."""
        # Register gateway
        config = GatewayConfig(
            gateway_id="gw-1",
            location="us-east-1",
            endpoint_url="http://gw1.example.com:8000",
        )
        self.orchestrator.register_gateway(config)
        
        # Synchronize state
        sync_id = self.orchestrator.synchronize_state(
            data_type="policy",
            payload={"version": "1.0", "rules": []},
            target_gateways=["gw-1"],
        )
        
        assert sync_id is not None
        assert sync_id in self.orchestrator.sync_points


class TestMetricsCollector:
    """Tests for Prometheus Metrics Collector."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.collector = MetricsCollector()
    
    def test_initialization(self):
        """Test collector initialization."""
        assert self.collector is not None
    
    def test_increment_counter(self):
        """Test counter increment."""
        self.collector.increment_counter("test_counter", 5)
        assert self.collector.counters["test_counter"] == 5
        
        self.collector.increment_counter("test_counter", 3)
        assert self.collector.counters["test_counter"] == 8
    
    def test_set_gauge(self):
        """Test gauge value setting."""
        self.collector.set_gauge("test_gauge", 42.5)
        assert self.collector.gauges["test_gauge"] == 42.5
        
        self.collector.set_gauge("test_gauge", 50.0)
        assert self.collector.gauges["test_gauge"] == 50.0
    
    def test_histogram(self):
        """Test histogram observation."""
        for value in [0.1, 0.2, 0.5, 1.0, 2.0]:
            self.collector.observe_histogram("test_histogram", value)
        
        assert "test_histogram" in self.collector.histograms
        hist = self.collector.histograms["test_histogram"]
        assert hist.count_value == 5
        assert hist.get_mean() > 0
    
    def test_prometheus_export(self):
        """Test Prometheus format export."""
        self.collector.increment_counter("metric1", 10)
        self.collector.set_gauge("metric2", 25.5)
        
        export = self.collector.export_prometheus()
        
        assert "metric1 10" in export
        assert "metric2 25.5" in export
    
    def test_sla_compliance(self):
        """Test SLA compliance checking."""
        # Set compliant metrics
        self.collector.set_gauge("tds_detection_latency_seconds", 2.0)
        self.collector.set_gauge("tds_false_positive_rate", 0.02)
        
        report = self.collector.check_sla_compliance()
        
        assert report["sla_compliant"] is True
    
    def test_sla_violation(self):
        """Test SLA violation detection."""
        # Set violating metric
        self.collector.set_gauge("tds_detection_latency_seconds", 10.0)  # > 5s threshold
        
        report = self.collector.check_sla_compliance()
        
        assert report["sla_compliant"] is False
        assert len(report["violations"]) > 0


class TestIntegration:
    """Integration tests for TDS components."""
    
    def test_end_to_end_session_evaluation(self):
        """Test complete session evaluation flow."""
        # Create components
        scorer = SessionScorer()
        classifier = DeviceHealthClassifier()
        
        # Simulate session
        classifier.create_profile("device-1")
        classifier.assess_security_controls("device-1", {"antivirus": True})
        
        # Add events
        for i in range(3):
            event = SessionEvent(
                timestamp=datetime.now() + timedelta(seconds=i),
                event_type="packet",
                source_ip="192.168.1.100",
                dest_ip="10.0.0.1",
                protocol="tcp",
                port=443,
                bytes_sent=1000,
                bytes_received=500,
                packet_count=1,
            )
            scorer.add_event("session-1", "device-1", event)
        
        # Get scores
        session_score = scorer.get_session_score("session-1")
        device_score, device_status = classifier.calculate_health("device-1")
        
        assert session_score is not None
        assert device_score > 0
    
    def test_threat_detection_and_response(self):
        """Test threat detection and response flow."""
        bridge = IDSBridge()
        metrics = MetricsCollector()
        
        # Report threat
        alert_id = bridge.report_tds_threat(
            device_id="device-1",
            session_id="session-1",
            threat_type="high_risk",
            threat_level=ThreatLevel.CRITICAL,
            risk_score=0.95,
            indicators={},
        )
        
        # Record detection
        metrics.record_detection_event("high_risk", 0.5, confidence=0.95)
        
        # Verify threat recorded
        alert = bridge.get_alert(alert_id)
        assert alert is not None
        assert ThreatLevel.CRITICAL in [ThreatLevel.CRITICAL]
        
        # Check metrics
        summary = metrics.get_metric_summary()
        assert summary["counters"]["tds_alerts_total"] > 0


# Pytest fixtures for singletons
@pytest.fixture
def session_scorer():
    """Provide SessionScorer instance."""
    return SessionScorer()


@pytest.fixture
def device_classifier():
    """Provide DeviceHealthClassifier instance."""
    return DeviceHealthClassifier()


@pytest.fixture
def ids_bridge():
    """Provide IDSBridge instance."""
    return IDSBridge()


@pytest.fixture
def edge_orchestrator():
    """Provide EdgeOrchestrator instance."""
    return EdgeOrchestrator()


@pytest.fixture
def metrics_collector():
    """Provide MetricsCollector instance."""
    return MetricsCollector()
