"""
Device Health Classification Engine
====================================

Comprehensive device health assessment beyond simple pass/fail scoring.
Evaluates vulnerability exposure, security posture, compliance status,
and provides detailed health classification.

Features:
---------
- Vulnerability assessment and CVSS scoring
- Antivirus/Endpoint protection evaluation
- Firewall and network policy compliance
- OS patch level and update status
- Software compliance and license tracking
- Device behavior baseline profiling
- Health classification into categories
- Remediation recommendations

Author: J.A.R.V.I.S. Security Team
Date: December 2025
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import logging
import hashlib

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class HealthStatus(Enum):
    """Overall device health classification"""
    CRITICAL = "critical"      # Score: 0.0-0.2   - Major threats, immediate remediation
    POOR = "poor"              # Score: 0.2-0.4   - Significant issues
    FAIR = "fair"              # Score: 0.4-0.6   - Some concerns
    GOOD = "good"              # Score: 0.6-0.8   - Minor issues only
    EXCELLENT = "excellent"    # Score: 0.8-1.0   - Healthy device


class VulnerabilityLevel(Enum):
    """Vulnerability severity"""
    CRITICAL = "critical"      # CVSS 9.0-10.0 - Exploitable remotely
    HIGH = "high"              # CVSS 7.0-8.9  - Easily exploitable
    MEDIUM = "medium"          # CVSS 4.0-6.9  - Requires auth/interaction
    LOW = "low"                # CVSS 0.1-3.9  - Difficult to exploit
    NONE = "none"              # No vulnerabilities


class ComplianceStatus(Enum):
    """Compliance assessment"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNKNOWN = "unknown"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Vulnerability:
    """Identified vulnerability"""
    cve_id: str
    software: str
    severity: VulnerabilityLevel
    cvss_score: float  # 0.0-10.0
    cvss_vector: str  # CVSS vector string
    affected_versions: List[str]
    exploitability: float  # 0.0-1.0
    impact_score: float  # 0.0-1.0
    discovery_date: datetime
    fix_available: bool
    patch_version: Optional[str] = None
    days_to_patch: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "cve_id": self.cve_id,
            "software": self.software,
            "severity": self.severity.value,
            "cvss_score": self.cvss_score,
            "cvss_vector": self.cvss_vector,
            "exploitability": self.exploitability,
            "impact_score": self.impact_score,
            "discovery_date": self.discovery_date.isoformat(),
            "fix_available": self.fix_available,
            "patch_version": self.patch_version,
            "days_to_patch": self.days_to_patch,
        }


@dataclass
class SecurityControl:
    """Security control evaluation"""
    name: str  # e.g., "antivirus", "firewall", "encryption"
    status: str  # "enabled", "disabled", "misconfigured", "unknown"
    last_update: Optional[datetime] = None
    health: float = 0.5  # 0.0-1.0 health score for this control
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "status": self.status,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "health": round(self.health, 3),
            "metadata": self.metadata,
        }


@dataclass
class DeviceHealthProfile:
    """Complete device health profile"""
    device_id: str
    last_assessment: datetime
    
    # Core health components
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    critical_vulns: int = 0
    high_vulns: int = 0
    medium_vulns: int = 0
    low_vulns: int = 0
    
    # Security controls
    security_controls: Dict[str, SecurityControl] = field(default_factory=dict)
    antivirus_enabled: bool = False
    antivirus_updated: bool = False
    firewall_enabled: bool = False
    encryption_enabled: bool = False
    
    # OS and patch status
    os_type: str = "unknown"
    os_version: str = "unknown"
    kernel_version: str = "unknown"
    last_patch_date: Optional[datetime] = None
    patches_available: int = 0
    days_since_update: int = 0
    
    # Compliance
    compliance_status: ComplianceStatus = ComplianceStatus.UNKNOWN
    policy_violations: int = 0
    
    # Behavioral
    suspicious_processes: int = 0
    network_anomalies: int = 0
    failed_login_attempts: int = 0
    privileged_operations: int = 0
    
    # Scores
    vulnerability_score: float = 0.5  # 0.0 (safe) to 1.0 (critical)
    control_score: float = 0.5  # 0.0 (poor) to 1.0 (excellent)
    compliance_score: float = 0.5  # 0.0 (non-compliant) to 1.0 (compliant)
    patch_score: float = 0.5  # 0.0 (unpatched) to 1.0 (fully patched)
    behavioral_score: float = 0.5  # 0.0 (suspicious) to 1.0 (normal)
    
    # Overall health
    composite_health_score: float = 0.5  # 0.0-1.0
    health_status: HealthStatus = HealthStatus.FAIR
    trust_level: float = 0.5  # 0.0-1.0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "device_id": self.device_id,
            "last_assessment": self.last_assessment.isoformat(),
            "vulnerabilities": {
                "total": len(self.vulnerabilities),
                "critical": self.critical_vulns,
                "high": self.high_vulns,
                "medium": self.medium_vulns,
                "low": self.low_vulns,
                "details": [v.to_dict() for v in self.vulnerabilities[:10]],  # Top 10
            },
            "security_controls": {
                name: control.to_dict()
                for name, control in self.security_controls.items()
            },
            "os_and_patches": {
                "os_type": self.os_type,
                "os_version": self.os_version,
                "kernel_version": self.kernel_version,
                "last_patch_date": self.last_patch_date.isoformat() if self.last_patch_date else None,
                "patches_available": self.patches_available,
                "days_since_update": self.days_since_update,
            },
            "compliance": {
                "status": self.compliance_status.value,
                "violations": self.policy_violations,
            },
            "behavioral": {
                "suspicious_processes": self.suspicious_processes,
                "network_anomalies": self.network_anomalies,
                "failed_logins": self.failed_login_attempts,
                "privileged_operations": self.privileged_operations,
            },
            "scores": {
                "vulnerability": round(self.vulnerability_score, 3),
                "control": round(self.control_score, 3),
                "compliance": round(self.compliance_score, 3),
                "patch": round(self.patch_score, 3),
                "behavioral": round(self.behavioral_score, 3),
            },
            "health": {
                "composite_score": round(self.composite_health_score, 3),
                "status": self.health_status.value,
                "trust_level": round(self.trust_level, 3),
            },
        }


# ============================================================================
# DEVICE HEALTH CLASSIFIER
# ============================================================================

class DeviceHealthClassifier:
    """Device health assessment and classification engine"""
    
    def __init__(self):
        """Initialize classifier"""
        self.profiles: Dict[str, DeviceHealthProfile] = {}
        self.vulnerability_db: Dict[str, Vulnerability] = {}
        
        # Scoring weights
        self.weights = {
            "vulnerability": 0.35,
            "control": 0.30,
            "compliance": 0.15,
            "patch": 0.15,
            "behavioral": 0.05,
        }
    
    def create_profile(self, device_id: str) -> DeviceHealthProfile:
        """
        Create new device health profile.
        
        Args:
            device_id: Unique device identifier
            
        Returns:
            New DeviceHealthProfile
        """
        profile = DeviceHealthProfile(
            device_id=device_id,
            last_assessment=datetime.now(),
        )
        
        self.profiles[device_id] = profile
        return profile
    
    def get_profile(self, device_id: str) -> Optional[DeviceHealthProfile]:
        """Get device health profile"""
        return self.profiles.get(device_id)
    
    def assess_vulnerabilities(
        self,
        device_id: str,
        vulnerabilities: List[Vulnerability]
    ) -> float:
        """
        Assess device vulnerability exposure.
        
        Args:
            device_id: Device to assess
            vulnerabilities: List of identified vulnerabilities
            
        Returns:
            Vulnerability score (0.0 safe to 1.0 critical)
        """
        profile = self.profiles.get(device_id)
        if not profile:
            profile = self.create_profile(device_id)
        
        profile.vulnerabilities = vulnerabilities
        
        # Count by severity
        profile.critical_vulns = sum(1 for v in vulnerabilities if v.severity == VulnerabilityLevel.CRITICAL)
        profile.high_vulns = sum(1 for v in vulnerabilities if v.severity == VulnerabilityLevel.HIGH)
        profile.medium_vulns = sum(1 for v in vulnerabilities if v.severity == VulnerabilityLevel.MEDIUM)
        profile.low_vulns = sum(1 for v in vulnerabilities if v.severity == VulnerabilityLevel.LOW)
        
        # Calculate vulnerability score
        # Critical vulns: 0.8-1.0, High: 0.5-0.8, Medium: 0.3-0.5, Low: 0.1-0.3
        score = 0.0
        
        for vuln in vulnerabilities:
            if vuln.severity == VulnerabilityLevel.CRITICAL:
                score += 0.8
            elif vuln.severity == VulnerabilityLevel.HIGH:
                score += 0.5
            elif vuln.severity == VulnerabilityLevel.MEDIUM:
                score += 0.3
            elif vuln.severity == VulnerabilityLevel.LOW:
                score += 0.1
        
        # Normalize by vulnerability count
        if vulnerabilities:
            score = score / len(vulnerabilities)
        
        # Factor in unpatched days
        for vuln in vulnerabilities:
            if vuln.fix_available and vuln.days_to_patch:
                if vuln.days_to_patch > 30:
                    score += 0.1  # Extra penalty for unpatched vulnerability
        
        profile.vulnerability_score = min(1.0, score)
        return profile.vulnerability_score
    
    def assess_security_controls(
        self,
        device_id: str,
        controls: Dict[str, SecurityControl]
    ) -> float:
        """
        Assess installed security controls.
        
        Args:
            device_id: Device to assess
            controls: Dict of control name -> SecurityControl
            
        Returns:
            Control score (0.0 poor to 1.0 excellent)
        """
        profile = self.profiles.get(device_id)
        if not profile:
            profile = self.create_profile(device_id)
        
        profile.security_controls = controls
        
        # Evaluate critical controls
        antivirus = controls.get("antivirus", SecurityControl("antivirus", "disabled"))
        firewall = controls.get("firewall", SecurityControl("firewall", "disabled"))
        encryption = controls.get("encryption", SecurityControl("encryption", "disabled"))
        edr = controls.get("edr", SecurityControl("edr", "disabled"))
        
        profile.antivirus_enabled = antivirus.status == "enabled"
        profile.firewall_enabled = firewall.status == "enabled"
        profile.encryption_enabled = encryption.status == "enabled"
        
        # Calculate score
        score = 0.0
        weights = {
            "antivirus": 0.35,
            "firewall": 0.30,
            "encryption": 0.20,
            "edr": 0.15,
        }
        
        control_scores = {
            "antivirus": antivirus.health,
            "firewall": firewall.health,
            "encryption": encryption.health,
            "edr": edr.health,
        }
        
        for control_name, weight in weights.items():
            score += control_scores[control_name] * weight
        
        profile.control_score = min(1.0, max(0.0, score))
        return profile.control_score
    
    def assess_patch_status(
        self,
        device_id: str,
        last_patch: Optional[datetime] = None,
        patches_available: int = 0,
        os_version: str = "unknown"
    ) -> float:
        """
        Assess OS and software patch compliance.
        
        Args:
            device_id: Device to assess
            last_patch: Last time patches were applied
            patches_available: Number of available patches
            os_version: OS version/build
            
        Returns:
            Patch score (0.0 unpatched to 1.0 fully patched)
        """
        profile = self.profiles.get(device_id)
        if not profile:
            profile = self.create_profile(device_id)
        
        profile.last_patch_date = last_patch
        profile.patches_available = patches_available
        profile.os_version = os_version
        
        # Calculate days since update
        if last_patch:
            profile.days_since_update = (datetime.now() - last_patch).days
        
        # Scoring logic
        score = 1.0
        
        # Penalty for available patches
        if patches_available > 0:
            score -= min(0.3, patches_available * 0.01)
        
        # Penalty for time since update
        if profile.days_since_update > 0:
            if profile.days_since_update > 90:
                score -= 0.4
            elif profile.days_since_update > 60:
                score -= 0.3
            elif profile.days_since_update > 30:
                score -= 0.2
            elif profile.days_since_update > 14:
                score -= 0.1
        
        profile.patch_score = max(0.0, min(1.0, score))
        return profile.patch_score
    
    def assess_compliance(
        self,
        device_id: str,
        compliance_status: ComplianceStatus,
        violations: int = 0
    ) -> float:
        """
        Assess policy compliance status.
        
        Args:
            device_id: Device to assess
            compliance_status: Overall compliance status
            violations: Number of policy violations
            
        Returns:
            Compliance score (0.0 non-compliant to 1.0 compliant)
        """
        profile = self.profiles.get(device_id)
        if not profile:
            profile = self.create_profile(device_id)
        
        profile.compliance_status = compliance_status
        profile.policy_violations = violations
        
        # Scoring
        if compliance_status == ComplianceStatus.COMPLIANT:
            score = 1.0
        elif compliance_status == ComplianceStatus.PARTIALLY_COMPLIANT:
            score = 0.6 - (violations * 0.05)
        elif compliance_status == ComplianceStatus.NON_COMPLIANT:
            score = 0.2
        else:  # UNKNOWN
            score = 0.5
        
        profile.compliance_score = max(0.0, min(1.0, score))
        return profile.compliance_score
    
    def assess_behavioral(
        self,
        device_id: str,
        suspicious_processes: int = 0,
        network_anomalies: int = 0,
        failed_logins: int = 0,
        privileged_operations: int = 0
    ) -> float:
        """
        Assess behavioral indicators.
        
        Args:
            device_id: Device to assess
            suspicious_processes: Number of suspicious processes detected
            network_anomalies: Number of network anomalies
            failed_logins: Failed login attempts
            privileged_operations: Suspicious privilege escalation
            
        Returns:
            Behavioral score (0.0 suspicious to 1.0 normal)
        """
        profile = self.profiles.get(device_id)
        if not profile:
            profile = self.create_profile(device_id)
        
        profile.suspicious_processes = suspicious_processes
        profile.network_anomalies = network_anomalies
        profile.failed_login_attempts = failed_logins
        profile.privileged_operations = privileged_operations
        
        # Scoring (inverse - higher indicators = lower score)
        score = 1.0
        
        # Suspicious processes
        if suspicious_processes > 10:
            score -= 0.4
        elif suspicious_processes > 5:
            score -= 0.2
        elif suspicious_processes > 0:
            score -= 0.1
        
        # Network anomalies
        if network_anomalies > 20:
            score -= 0.3
        elif network_anomalies > 10:
            score -= 0.15
        elif network_anomalies > 0:
            score -= 0.05
        
        # Failed logins
        if failed_logins > 100:
            score -= 0.2
        elif failed_logins > 20:
            score -= 0.1
        
        # Privilege operations
        if privileged_operations > 50:
            score -= 0.15
        elif privileged_operations > 20:
            score -= 0.08
        
        profile.behavioral_score = max(0.0, min(1.0, score))
        return profile.behavioral_score
    
    def calculate_health(self, device_id: str) -> Tuple[float, HealthStatus]:
        """
        Calculate overall device health.
        
        Args:
            device_id: Device to assess
            
        Returns:
            Tuple of (composite_score, health_status)
        """
        profile = self.profiles.get(device_id)
        if not profile:
            return 0.5, HealthStatus.FAIR
        
        # Composite score (inverse vulnerability to get health)
        profile.composite_health_score = (
            (1.0 - profile.vulnerability_score) * self.weights["vulnerability"] +
            profile.control_score * self.weights["control"] +
            profile.compliance_score * self.weights["compliance"] +
            profile.patch_score * self.weights["patch"] +
            profile.behavioral_score * self.weights["behavioral"]
        )
        
        # Calculate trust level (same as composite)
        profile.trust_level = profile.composite_health_score
        
        # Determine health status
        score = profile.composite_health_score
        if score < 0.2:
            profile.health_status = HealthStatus.CRITICAL
        elif score < 0.4:
            profile.health_status = HealthStatus.POOR
        elif score < 0.6:
            profile.health_status = HealthStatus.FAIR
        elif score < 0.8:
            profile.health_status = HealthStatus.GOOD
        else:
            profile.health_status = HealthStatus.EXCELLENT
        
        profile.last_assessment = datetime.now()
        
        return profile.composite_health_score, profile.health_status
    
    def get_remediation_recommendations(self, device_id: str) -> List[str]:
        """
        Generate remediation recommendations.
        
        Args:
            device_id: Device to analyze
            
        Returns:
            List of actionable recommendations
        """
        profile = self.profiles.get(device_id)
        if not profile:
            return []
        
        recommendations = []
        
        # Vulnerability remediation
        if profile.critical_vulns > 0:
            recommendations.append(f"CRITICAL: Patch {profile.critical_vulns} critical vulnerabilities immediately")
        
        if profile.high_vulns > 0:
            recommendations.append(f"HIGH: Apply patches for {profile.high_vulns} high-severity vulnerabilities")
        
        # Control recommendations
        if not profile.antivirus_enabled:
            recommendations.append("Enable and update antivirus software")
        
        if not profile.firewall_enabled:
            recommendations.append("Enable host firewall")
        
        if not profile.encryption_enabled:
            recommendations.append("Enable disk/data encryption")
        
        # Patch recommendations
        if profile.patches_available > 0:
            recommendations.append(f"Install {profile.patches_available} available system updates")
        
        if profile.days_since_update > 90:
            recommendations.append("Schedule system updates (>90 days overdue)")
        
        # Compliance recommendations
        if profile.policy_violations > 0:
            recommendations.append(f"Resolve {profile.policy_violations} policy violations")
        
        # Behavioral recommendations
        if profile.suspicious_processes > 0:
            recommendations.append(f"Investigate and remove {profile.suspicious_processes} suspicious processes")
        
        if profile.failed_login_attempts > 20:
            recommendations.append("Review and remediate failed login attempts")
        
        return recommendations


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_classifier_instance: Optional[DeviceHealthClassifier] = None


def get_device_health_classifier() -> DeviceHealthClassifier:
    """Get or create device health classifier singleton"""
    global _classifier_instance
    
    if _classifier_instance is None:
        _classifier_instance = DeviceHealthClassifier()
        logger.info("Device health classifier initialized")
    
    return _classifier_instance
