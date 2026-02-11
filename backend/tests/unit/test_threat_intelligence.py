"""
Dark Web Threat Intelligence Fusion - Integration Test Examples

Demonstrates the usage and capabilities of the threat intelligence engine.
Run this file to verify the implementation works correctly.

Usage:
  python -m pytest backend/tests/test_threat_intelligence.py -v
"""

import pytest
from datetime import datetime
from typing import List

# Import the threat intelligence engine
from backend.core.deception.threat_intelligence_fusion import (
    ThreatIntelligenceFusionEngine,
    ThreatSeverity,
    ThreatType,
    ThreatSignal,
    ThreatIndicator,
    ThreatCorrelation,
)


class TestThreatIntelligenceFusionEngine:
    """Test suite for threat intelligence engine"""
    
    @pytest.fixture
    def engine(self):
        """Initialize threat intelligence engine"""
        return ThreatIntelligenceFusionEngine()
    
    # ========================================================================
    # ENTITY EXTRACTION TESTS
    # ========================================================================
    
    def test_cve_extraction(self, engine):
        """Test CVE pattern extraction"""
        text = "Critical vulnerability CVE-2025-1234 discovered in Apache"
        indicators = engine.extract_threat_entities(text)
        
        cve_indicators = [i for i in indicators if i.ioc_type == "cve"]
        assert len(cve_indicators) > 0
        assert cve_indicators[0].ioc_value == "CVE-2025-1234"
        assert cve_indicators[0].confidence == 0.95
    
    def test_ip_extraction(self, engine):
        """Test IP address extraction"""
        text = "Command and control server at 192.168.1.100 and 10.0.0.1"
        indicators = engine.extract_threat_entities(text)
        
        ip_indicators = [i for i in indicators if i.ioc_type == "ip"]
        assert len(ip_indicators) > 0
        assert any(i.ioc_value == "10.0.0.1" for i in ip_indicators)
    
    def test_domain_extraction(self, engine):
        """Test domain extraction"""
        text = "Phishing domain detected: malicious.com and evil.org"
        indicators = engine.extract_threat_entities(text)
        
        domain_indicators = [i for i in indicators if i.ioc_type == "domain"]
        assert len(domain_indicators) > 0
        assert any("malicious" in i.ioc_value for i in domain_indicators)
    
    def test_email_extraction(self, engine):
        """Test email address extraction"""
        text = "Contact attacker@example.com or hacker@evil.org"
        indicators = engine.extract_threat_entities(text)
        
        email_indicators = [i for i in indicators if i.ioc_type == "email"]
        assert len(email_indicators) > 0
        assert any("attacker@" in i.ioc_value for i in email_indicators)
    
    def test_malware_extraction(self, engine):
        """Test malware name extraction"""
        text = "Emotet trojan and TrickBot detected spreading via email"
        indicators = engine.extract_threat_entities(text)
        
        malware_indicators = [i for i in indicators if i.ioc_type == "malware"]
        assert len(malware_indicators) > 0
        malware_values = [i.ioc_value for i in malware_indicators]
        assert "EMOTET" in malware_values or "TROJAN" in malware_values
    
    def test_threat_actor_extraction(self, engine):
        """Test threat actor extraction"""
        text = "APT28 attributed to Russian government, also known as Fancy Bear"
        indicators = engine.extract_threat_entities(text)
        
        actor_indicators = [i for i in indicators if i.ioc_type == "threat_actor"]
        assert len(actor_indicators) > 0
    
    # ========================================================================
    # THREAT CLASSIFICATION TESTS
    # ========================================================================
    
    def test_ransomware_classification(self, engine):
        """Test ransomware threat classification"""
        text = "New ransomware variant encrypting files and demanding ransom payment"
        indicators = engine.extract_threat_entities(text)
        threat_type, severity, confidence = engine.classify_threat(text, indicators)
        
        assert threat_type == ThreatType.RANSOMWARE
        assert severity == ThreatSeverity.HIGH
        assert confidence >= 0.75
    
    def test_exploit_classification(self, engine):
        """Test exploit threat classification"""
        text = "RCE exploit for CVE-2025-1234 allows remote code execution"
        indicators = engine.extract_threat_entities(text)
        threat_type, severity, confidence = engine.classify_threat(text, indicators)
        
        assert threat_type == ThreatType.EXPLOIT
        assert severity == ThreatSeverity.HIGH
        assert confidence >= 0.80
    
    def test_zero_day_classification(self, engine):
        """Test zero-day classification"""
        text = "Unpatched zero-day vulnerability discovered in Windows"
        indicators = engine.extract_threat_entities(text)
        threat_type, severity, confidence = engine.classify_threat(text, indicators)
        
        assert threat_type == ThreatType.VULNERABILITY
        assert severity == ThreatSeverity.CRITICAL
        assert confidence >= 0.90
    
    def test_credential_classification(self, engine):
        """Test credential breach classification"""
        text = "Database dump containing 1M user credentials and passwords"
        indicators = engine.extract_threat_entities(text)
        threat_type, severity, confidence = engine.classify_threat(text, indicators)
        
        assert threat_type == ThreatType.CREDENTIAL
        assert severity == ThreatSeverity.HIGH
        assert confidence >= 0.75
    
    # ========================================================================
    # THREAT SCORING TESTS
    # ========================================================================
    
    def test_threat_score_calculation(self, engine):
        """Test threat score calculation"""
        indicators = [
            ThreatIndicator("cve", "CVE-2025-1234", 0.95),
            ThreatIndicator("malware", "EMOTET", 0.85),
        ]
        
        score = engine.calculate_threat_score(
            ThreatType.MALWARE,
            ThreatSeverity.HIGH,
            indicators,
            1000  # 1000 char text
        )
        
        assert 0.0 <= score <= 1.0
        assert score > 0.75  # Should be high for HIGH severity + good indicators
    
    def test_critical_threat_score(self, engine):
        """Test critical threat gets high score"""
        indicators = [
            ThreatIndicator("cve", "CVE-2025-1234", 0.95),
            ThreatIndicator("threat_actor", "APT28", 0.90),
        ]
        
        score = engine.calculate_threat_score(
            ThreatType.EXPLOIT,
            ThreatSeverity.CRITICAL,
            indicators,
            500
        )
        
        assert score > 0.90
    
    def test_info_threat_low_score(self, engine):
        """Test informational threat gets low score"""
        indicators = []
        
        score = engine.calculate_threat_score(
            ThreatType.MALWARE,
            ThreatSeverity.INFO,
            indicators,
            100
        )
        
        assert score < 0.5
    
    # ========================================================================
    # THREAT SIGNAL PROCESSING TESTS
    # ========================================================================
    
    def test_process_dark_web_text(self, engine):
        """Test full dark web text processing pipeline"""
        text = """
        Critical RCE vulnerability CVE-2025-1234 discovered in Apache Web Server.
        CVSS score 9.8. Exploited by APT28 in the wild.
        Affects versions 2.4.0 to 2.4.52.
        Attack infrastructure: malicious.com, 192.168.1.100
        """
        
        signal = engine.process_dark_web_text(text, source_url="https://example.com")
        
        assert isinstance(signal, ThreatSignal)
        assert signal.threat_type == ThreatType.VULNERABILITY
        assert signal.severity == ThreatSeverity.CRITICAL
        assert signal.confidence_score > 0.85
        assert len(signal.indicators) > 0
        assert "APT28" in signal.threat_actors
    
    def test_marketplace_listing_processing(self, engine):
        """Test marketplace listing processing"""
        signal = engine.process_marketplace_listing(
            listing_title="CVE-2025-1234 Working Exploit",
            listing_description="Full RCE exploit code, tested and working",
            marketplace="darkfox",
            price=5000.0,
            vendor="threat_actor"
        )
        
        assert isinstance(signal, ThreatSignal)
        assert signal.marketplace == "darkfox"
        assert signal.threat_type == ThreatType.EXPLOIT or signal.threat_type == ThreatType.VULNERABILITY
    
    def test_leak_dump_processing(self, engine):
        """Test leak dump processing"""
        signal = engine.process_leak_dump(
            dump_name="2025_corporate_breach",
            entries_sample="user1@corp.com:password123\nuser2@corp.com:secret456"
        )
        
        assert isinstance(signal, ThreatSignal)
        assert signal.threat_type == ThreatType.DATA_BREACH
        assert signal.severity == ThreatSeverity.HIGH
        assert len(signal.indicators) > 0
    
    # ========================================================================
    # CORRELATION ANALYSIS TESTS
    # ========================================================================
    
    def test_find_similar_signals(self, engine):
        """Test finding similar threat signals"""
        text1 = "LockBit ransomware variant with CVE-2025-1234 discovered"
        text2 = "LockBit gang claims healthcare breach using same CVE"
        
        signal1 = engine.process_dark_web_text(text1)
        signal2 = engine.process_dark_web_text(text2)
        
        similar = engine.find_similar_signals(signal1, threshold=0.5)
        
        # Should find signal2 as similar
        similar_ids = [s[0] for s in similar]
        assert signal2.signal_id in similar_ids
    
    def test_create_correlation(self, engine):
        """Test creating correlation between signals"""
        text1 = "APT28 attacking US government agencies"
        text2 = "Fancy Bear (APT28) breach confirmed at State Department"
        
        signal1 = engine.process_dark_web_text(text1)
        signal2 = engine.process_dark_web_text(text2)
        
        correlation = engine.create_correlation(signal1.signal_id, signal2.signal_id)
        
        assert isinstance(correlation, ThreatCorrelation)
        assert correlation.correlation_score > 0.5
        assert len(correlation.signal_ids) == 2
    
    def test_invalid_correlation(self, engine):
        """Test correlation with non-existent signal"""
        signal = engine.process_dark_web_text("Test threat")
        
        correlation = engine.create_correlation(signal.signal_id, "invalid_id")
        
        assert correlation is None
    
    # ========================================================================
    # REPORTING AND ALERTING TESTS
    # ========================================================================
    
    def test_threat_summary(self, engine):
        """Test threat summary generation"""
        # Add multiple threats
        engine.process_dark_web_text("CVE-2025-1234 ransomware attack")
        engine.process_dark_web_text("APT28 phishing campaign")
        engine.process_dark_web_text("Emotet trojan distribution")
        
        summary = engine.get_threat_summary()
        
        assert summary["total_threats"] == 3
        assert "threats_by_severity" in summary
        assert "threats_by_type" in summary
        assert "known_indicators" in summary
    
    def test_top_threats(self, engine):
        """Test getting top threats by score"""
        engine.process_dark_web_text("Low priority info")
        engine.process_dark_web_text("CVE-2025-1234 CRITICAL RCE by APT28")
        engine.process_dark_web_text("Medium priority threat")
        
        top_5 = engine.get_top_threats(limit=5)
        
        assert len(top_5) <= 5
        assert top_5[0].confidence_score >= top_5[-1].confidence_score
    
    def test_keyword_alert(self, engine):
        """Test keyword alerting"""
        engine.process_dark_web_text("LockBit ransomware attacking hospitals")
        engine.process_dark_web_text("LockBit gang demands $10M ransom")
        engine.process_dark_web_text("Other unrelated threat")
        
        alert = engine.generate_keyword_alert("lockbit")
        
        assert alert["matched_signals"] == 2
        assert len(alert["signals"]) == 2
    
    # ========================================================================
    # END-TO-END TESTS
    # ========================================================================
    
    def test_full_processing_pipeline(self, engine):
        """Test complete processing pipeline end-to-end"""
        # 1. Add multiple threats
        threat1_text = "CVE-2025-1234 RCE in Apache, exploited by APT28, affects thousands"
        threat2_text = "Same CVE-2025-1234 being weaponized by Fancy Bear threat group"
        threat3_text = "New LockBit ransomware variant spreading via RDP"
        
        signal1 = engine.process_dark_web_text(threat1_text, marketplace="darkfox")
        signal2 = engine.process_dark_web_text(threat2_text, marketplace="marketplace")
        signal3 = engine.process_dark_web_text(threat3_text)
        
        # 2. Verify signals created
        assert len(engine.threat_signals) == 3
        
        # 3. Check correlations
        correlations = list(engine.correlations.values())
        assert len(correlations) > 0
        
        # 4. Test summary
        summary = engine.get_threat_summary()
        assert summary["total_threats"] == 3
        assert summary["total_correlations"] > 0
        
        # 5. Test top threats
        top = engine.get_top_threats(limit=3)
        assert len(top) == 3
        
        # 6. Test keyword search
        apt_alert = engine.generate_keyword_alert("APT")
        assert apt_alert["matched_signals"] >= 1
        
        lockbit_alert = engine.generate_keyword_alert("LockBit")
        assert lockbit_alert["matched_signals"] >= 1
        
        # 7. Test indicators tracking
        indicators = engine.known_indicators
        assert len(indicators["cve"]) > 0
        assert "CVE-2025-1234" in indicators["cve"]
    
    def test_multi_language_threat_extraction(self, engine):
        """Test extraction with English text patterns"""
        text = "Zahlreiche Unternehmen von Ransomware CVE-2025-1234 betroffen"
        indicators = engine.extract_threat_entities(text)
        
        # Should still extract CVE even with German text
        cve_found = any(i.ioc_type == "cve" for i in indicators)
        assert cve_found
    
    def test_performance_batch_processing(self, engine):
        """Test processing performance with batch"""
        import time
        
        texts = [
            f"Threat number {i}: CVE-2025-{1234+i} discovered"
            for i in range(10)
        ]
        
        start = time.time()
        for text in texts:
            engine.process_dark_web_text(text)
        elapsed = time.time() - start
        
        # Should process 10 threats in reasonable time (< 1 second)
        assert elapsed < 1.0
        assert len(engine.threat_signals) == 10


class TestThreatIntelligenceDataModels:
    """Test data model functionality"""
    
    def test_threat_indicator_creation(self):
        """Test threat indicator creation"""
        indicator = ThreatIndicator(
            ioc_type="cve",
            ioc_value="CVE-2025-1234",
            confidence=0.95,
            source_text="Found in...",
        )
        
        assert indicator.ioc_type == "cve"
        assert indicator.confidence == 0.95
        
        # Test dict conversion
        data = indicator.to_dict()
        assert isinstance(data, dict)
        assert data["ioc_value"] == "CVE-2025-1234"
    
    def test_threat_signal_metadata(self):
        """Test threat signal metadata handling"""
        indicators = [
            ThreatIndicator("cve", "CVE-2025-1234", 0.95),
        ]
        
        signal = ThreatSignal(
            signal_id="test123",
            title="Test Threat",
            description="Test description",
            threat_type=ThreatType.VULNERABILITY,
            severity=ThreatSeverity.HIGH,
            confidence_score=0.85,
            indicators=indicators,
            threat_actors=["APT28"],
            affected_products=["Apache"],
            extraction_method="nlp",
        )
        
        # Verify timestamps created
        assert signal.created_at
        assert signal.updated_at
        
        # Verify dict conversion
        data = signal.to_dict()
        assert data["threat_type"] == "vulnerability"
        assert data["severity"] == "high"
        assert len(data["indicators"]) == 1


if __name__ == "__main__":
    """Run tests directly"""
    pytest.main([__file__, "-v"])
