"""
Firewall ↔ DPI ↔ IAM Integration Module

This module demonstrates and implements the complete data flow between:
1. DPI Engine (provides app/category classifications)
2. IAM System (provides user identity/role assertions)  
3. Firewall Policy Engine (enforces policies with multi-layer context)

The integration enables:
- Layer 7 policy enforcement based on DPI classifications
- Identity-based access control using IAM assertions
- Admin-defined policies that span all three systems
- End-to-end network policy enforcement

Architecture:
    Incoming Flow
         ↓
    [DPI Engine] → Classification (app, category, protocol, confidence)
         ↓
    [IAM Lookup] → Identity (user, role, groups, permissions)
         ↓
    [Firewall] → Policy Decision (PASS/DROP/RATE_LIMIT/etc.)
         ↓
    [Action] → NAT/QoS/Logging

Author: J.A.R.V.I.S. Team
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS FOR DPI CLASSIFICATIONS
# ============================================================================

@dataclass
class DPIClassification:
    """Output from DPI Engine - represents packet/flow classification"""
    
    app_name: str  # Application name (e.g., 'Chrome', 'Spotify', 'BitTorrent')
    category: str  # Application category (e.g., 'Video Streaming', 'P2P', 'Web Browsing')
    protocol: str  # Protocol detected (e.g., 'HTTP', 'HTTPS', 'DNS', 'QUIC')
    confidence: int  # Confidence level 0-100 for classification
    detection_tick: int  # Packet number when detection occurred
    is_encrypted: bool = field(default=False)  # Whether traffic is encrypted
    is_tunneled: bool = field(default=False)  # Whether traffic is tunneled/proxied
    risk_score: int = field(default=0)  # Risk score 0-100
    detected_anomalies: List[str] = field(default_factory=list)  # Detected anomalies
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'app_name': self.app_name,
            'category': self.category,
            'protocol': self.protocol,
            'confidence': self.confidence,
            'detection_tick': self.detection_tick,
            'is_encrypted': self.is_encrypted,
            'is_tunneled': self.is_tunneled,
            'risk_score': self.risk_score,
            'detected_anomalies': self.detected_anomalies,
        }


# ============================================================================
# DATA MODELS FOR IAM IDENTITY ASSERTIONS
# ============================================================================

@dataclass
class IAMIdentityAssertion:
    """Output from IAM System - represents user identity and permissions"""
    
    user_id: str  # Unique user identifier
    username: str  # Username
    user_role: str  # Primary role (e.g., 'admin', 'employee', 'contractor', 'guest')
    user_groups: List[str] = field(default_factory=list)  # User's security groups
    organization_unit: Optional[str] = field(default=None)  # Department or organizational unit
    location: Optional[str] = field(default=None)  # User's location/office
    device_id: Optional[str] = field(default=None)  # Device identifier
    device_type: Optional[str] = field(default=None)  # Device type (laptop, phone, tablet)
    is_mfa_verified: bool = field(default=False)  # Whether MFA has been verified
    permission_level: int = field(default=0)  # Permission level 0-100
    clearance_level: Optional[str] = field(default=None)  # Security clearance level
    restrictions: List[str] = field(default_factory=list)  # User restrictions/flags
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'user_role': self.user_role,
            'user_groups': self.user_groups,
            'organization_unit': self.organization_unit,
            'location': self.location,
            'device_id': self.device_id,
            'device_type': self.device_type,
            'is_mfa_verified': self.is_mfa_verified,
            'permission_level': self.permission_level,
            'clearance_level': self.clearance_level,
            'restrictions': self.restrictions,
        }


# ============================================================================
# ADMIN POLICY DEFINITIONS (Multi-Layer)
# ============================================================================

class PolicyMatchType(Enum):
    """Types of policy conditions that can be matched"""
    NETWORK = "network"          # L3/L4: IP/port/protocol
    APPLICATION = "application"  # L7: DPI app/category
    IDENTITY = "identity"        # User/role/group
    DEVICE = "device"           # Device type/id
    LOCATION = "location"       # Geographic/office location
    BEHAVIORAL = "behavioral"   # Risk/anomaly scores
    COMPOSITE = "composite"     # Multi-layer combination


@dataclass
class PolicyCondition:
    """Single condition in a policy rule"""
    match_type: PolicyMatchType
    field: str  # Field name to match on
    operator: str  # Operator: eq, contains, in, gt, lt, regex
    value: Any  # Value to match against
    
    def matches(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate if this condition matches the given context.
        
        Args:
            context: Dict with keys like 'app_name', 'user_role', etc.
            
        Returns:
            True if condition matches, False otherwise
        """
        field_value = context.get(self.field)
        
        if self.operator == "eq":
            return field_value == self.value
        elif self.operator == "ne":
            return field_value != self.value
        elif self.operator == "contains":
            # Check if value is contained in field_value (substring or list membership)
            if isinstance(field_value, list):
                # For lists, check if any element contains the value as substring
                return any(self.value in str(item) for item in field_value)
            elif isinstance(field_value, str):
                return self.value in field_value
            else:
                return False
        elif self.operator == "in":
            return field_value in self.value
        elif self.operator == "not_in":
            return field_value not in self.value
        elif self.operator == "gt":
            return field_value > self.value
        elif self.operator == "gte":
            return field_value >= self.value
        elif self.operator == "lt":
            return field_value < self.value
        elif self.operator == "lte":
            return field_value <= self.value
        elif self.operator == "regex":
            import re
            return re.match(self.value, str(field_value)) is not None
        else:
            logger.warning(f"Unknown operator: {self.operator}")
            return False


@dataclass
class AdminPolicy:
    """
    Admin-defined policy combining multiple layers.
    
    Example usage:
    ```python
    policy = AdminPolicy(
        name="Block Torrent",
        description="Block all BitTorrent traffic regardless of user",
        conditions=[
            PolicyCondition(PolicyMatchType.APPLICATION, "category", "eq", "P2P"),
            PolicyCondition(PolicyMatchType.APPLICATION, "app_name", "contains", "Torrent"),
        ],
        condition_logic="ANY",  # Match if ANY condition is true
        action="drop",
        priority=100,
    )
    ```
    """
    policy_id: str  # Unique policy identifier
    name: str  # Human-readable policy name
    description: str  # Policy description
    conditions: List[PolicyCondition]  # List of conditions to match
    action: str = field(default="pass")  # Action: pass, drop, rate_limit, redirect, quarantine
    condition_logic: str = field(default="ALL")  # ALL or ANY conditions must match
    action_params: Dict[str, Any] = field(default_factory=dict)  # Action parameters
    priority: int = field(default=50)  # Policy priority (higher = evaluated first)
    enabled: bool = field(default=True)  # Whether policy is enabled
    created_at: datetime = field(default_factory=datetime.utcnow)  # Creation timestamp
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate if this policy matches the given context.
        
        Args:
            context: Dict with DPI classifications, IAM assertions, and flow info
            
        Returns:
            True if policy conditions are met, False otherwise
        """
        if not self.enabled:
            return False
        
        if not self.conditions:
            return True
        
        results = [cond.matches(context) for cond in self.conditions]
        
        if self.condition_logic == "ALL":
            return all(results)
        elif self.condition_logic == "ANY":
            return any(results)
        else:
            logger.warning(f"Unknown condition_logic: {self.condition_logic}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'policy_id': self.policy_id,
            'name': self.name,
            'description': self.description,
            'conditions': [
                {
                    'match_type': c.match_type.value,
                    'field': c.field,
                    'operator': c.operator,
                    'value': c.value,
                }
                for c in self.conditions
            ],
            'condition_logic': self.condition_logic,
            'action': self.action,
            'action_params': self.action_params,
            'priority': self.priority,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat(),
        }


# ============================================================================
# INTEGRATION ENGINE
# ============================================================================

class FirewallDPIIAMIntegration:
    """
    Main integration engine that coordinates DPI classifications, IAM assertions,
    and policy evaluation through the firewall engine.
    """
    
    def __init__(self):
        self.admin_policies: List[AdminPolicy] = []
        self.dpi_classifications_cache: Dict[str, DPIClassification] = {}
        self.iam_assertions_cache: Dict[str, IAMIdentityAssertion] = {}
        logger.info("FirewallDPIIAMIntegration initialized")
    
    def add_admin_policy(self, policy: AdminPolicy) -> None:
        """Register an admin policy"""
        self.admin_policies.append(policy)
        self.admin_policies.sort(key=lambda p: p.priority, reverse=True)
        logger.info(f"Added policy: {policy.name}")
    
    def remove_admin_policy(self, policy_id: str) -> bool:
        """Remove a policy by ID"""
        initial_len = len(self.admin_policies)
        self.admin_policies = [p for p in self.admin_policies if p.policy_id != policy_id]
        removed = len(self.admin_policies) < initial_len
        if removed:
            logger.info(f"Removed policy: {policy_id}")
        return removed
    
    def cache_dpi_classification(self, flow_key: str, classification: DPIClassification) -> None:
        """Cache DPI classification result"""
        self.dpi_classifications_cache[flow_key] = classification
        logger.debug(f"Cached DPI classification for {flow_key}: {classification.app_name}")
    
    def cache_iam_assertion(self, user_id: str, assertion: IAMIdentityAssertion) -> None:
        """Cache IAM identity assertion"""
        self.iam_assertions_cache[user_id] = assertion
        logger.debug(f"Cached IAM assertion for {user_id}: {assertion.username}")
    
    def build_policy_context(
        self,
        src_ip: str,
        dst_ip: str,
        src_port: int,
        dst_port: int,
        protocol: str,
        dpi_classification: Optional[DPIClassification] = None,
        iam_assertion: Optional[IAMIdentityAssertion] = None,
    ) -> Dict[str, Any]:
        """
        Build comprehensive policy context from all available sources.
        
        This context is used for matching against admin policies and
        making firewall decisions.
        
        Args:
            src_ip: Source IP address
            dst_ip: Destination IP address
            src_port: Source port
            dst_port: Destination port
            protocol: Protocol (tcp/udp/icmp)
            dpi_classification: Optional DPI classification
            iam_assertion: Optional IAM identity assertion
            
        Returns:
            Dict with complete policy context
        """
        context = {
            # Network layer
            'src_ip': src_ip,
            'dst_ip': dst_ip,
            'src_port': src_port,
            'dst_port': dst_port,
            'protocol': protocol,
            
            # DPI layer
            'app_name': dpi_classification.app_name if dpi_classification else None,
            'dpi_category': dpi_classification.category if dpi_classification else None,
            'dpi_protocol': dpi_classification.protocol if dpi_classification else None,
            'dpi_confidence': dpi_classification.confidence if dpi_classification else 0,
            'is_encrypted': dpi_classification.is_encrypted if dpi_classification else False,
            'is_tunneled': dpi_classification.is_tunneled if dpi_classification else False,
            'risk_score': dpi_classification.risk_score if dpi_classification else 0,
            'detected_anomalies': dpi_classification.detected_anomalies if dpi_classification else [],
            
            # Identity layer
            'user_id': iam_assertion.user_id if iam_assertion else None,
            'username': iam_assertion.username if iam_assertion else None,
            'user_role': iam_assertion.user_role if iam_assertion else None,
            'user_groups': iam_assertion.user_groups if iam_assertion else [],
            'organization_unit': iam_assertion.organization_unit if iam_assertion else None,
            'user_location': iam_assertion.location if iam_assertion else None,
            'device_id': iam_assertion.device_id if iam_assertion else None,
            'device_type': iam_assertion.device_type if iam_assertion else None,
            'is_mfa_verified': iam_assertion.is_mfa_verified if iam_assertion else False,
            'permission_level': iam_assertion.permission_level if iam_assertion else 0,
            'clearance_level': iam_assertion.clearance_level if iam_assertion else None,
            'user_restrictions': iam_assertion.restrictions if iam_assertion else [],
        }
        
        return context
    
    def evaluate_policies(self, context: Dict[str, Any]) -> Tuple[Optional[AdminPolicy], str, Dict[str, Any]]:
        """
        Evaluate all admin policies against the given context.
        Returns the first matching policy and its action.
        
        Args:
            context: Policy context built from build_policy_context()
            
        Returns:
            Tuple of (matching_policy, action, action_params) or (None, None, {}) if no match
        """
        for policy in self.admin_policies:
            if policy.evaluate(context):
                logger.info(f"Policy matched: {policy.name}")
                return policy, policy.action, policy.action_params
        
        logger.debug("No policies matched")
        return None, None, {}
    
    def get_policy_suggestions(self, context: Dict[str, Any]) -> List[AdminPolicy]:
        """
        Get list of all policies that would match this context.
        Useful for debugging and auditing.
        """
        return [p for p in self.admin_policies if p.evaluate(context)]


# ============================================================================
# HELPER FUNCTIONS FOR COMMON POLICY PATTERNS
# ============================================================================

def create_block_application_policy(
    app_name: str,
    policy_id: str = None,
    priority: int = 100,
) -> AdminPolicy:
    """
    Create a policy that blocks a specific application.
    
    Example:
        policy = create_block_application_policy("Spotify")
    """
    if not policy_id:
        import uuid
        policy_id = f"block_app_{uuid.uuid4().hex[:8]}"
    
    return AdminPolicy(
        policy_id=policy_id,
        name=f"Block {app_name}",
        description=f"Block all {app_name} traffic",
        conditions=[
            PolicyCondition(PolicyMatchType.APPLICATION, "app_name", "eq", app_name),
        ],
        condition_logic="ALL",
        action="drop",
        priority=priority,
    )


def create_block_category_policy(
    category: str,
    policy_id: str = None,
    priority: int = 100,
) -> AdminPolicy:
    """
    Create a policy that blocks a traffic category.
    
    Example:
        policy = create_block_category_policy("P2P")
    """
    if not policy_id:
        import uuid
        policy_id = f"block_cat_{uuid.uuid4().hex[:8]}"
    
    return AdminPolicy(
        policy_id=policy_id,
        name=f"Block {category}",
        description=f"Block all {category} traffic",
        conditions=[
            PolicyCondition(PolicyMatchType.APPLICATION, "dpi_category", "eq", category),
        ],
        condition_logic="ALL",
        action="drop",
        priority=priority,
    )


def create_restrict_by_role_policy(
    app_name: str,
    allowed_roles: List[str],
    policy_id: str = None,
    priority: int = 90,
) -> AdminPolicy:
    """
    Create a policy that restricts an application by user role.
    
    Example:
        policy = create_restrict_by_role_policy("AWS Console", allowed_roles=["admin", "ops"])
    """
    if not policy_id:
        import uuid
        policy_id = f"role_restrict_{uuid.uuid4().hex[:8]}"
    
    return AdminPolicy(
        policy_id=policy_id,
        name=f"Restrict {app_name} to roles",
        description=f"Allow {app_name} only for specific roles",
        conditions=[
            PolicyCondition(PolicyMatchType.APPLICATION, "app_name", "eq", app_name),
            PolicyCondition(PolicyMatchType.IDENTITY, "user_role", "not_in", allowed_roles),
        ],
        condition_logic="ALL",  # Block if app is used AND user role is NOT in allowed list
        action="drop",
        priority=priority,
    )


def create_rate_limit_policy(
    category: str,
    rate_limit_kbps: int,
    policy_id: str = None,
    priority: int = 80,
) -> AdminPolicy:
    """
    Create a policy that rate limits a traffic category.
    
    Example:
        policy = create_rate_limit_policy("Video Streaming", rate_limit_kbps=5000)
    """
    if not policy_id:
        import uuid
        policy_id = f"rate_limit_{uuid.uuid4().hex[:8]}"
    
    return AdminPolicy(
        policy_id=policy_id,
        name=f"Rate limit {category}",
        description=f"Rate limit {category} to {rate_limit_kbps} kbps",
        conditions=[
            PolicyCondition(PolicyMatchType.APPLICATION, "dpi_category", "eq", category),
        ],
        condition_logic="ALL",
        action="rate_limit",
        action_params={'rate_limit_kbps': rate_limit_kbps},
        priority=priority,
    )


def create_high_risk_quarantine_policy(
    policy_id: str = None,
    priority: int = 200,  # Very high priority
) -> AdminPolicy:
    """
    Create a policy that quarantines high-risk traffic.
    
    Example:
        policy = create_high_risk_quarantine_policy()
    """
    if not policy_id:
        import uuid
        policy_id = f"quarantine_{uuid.uuid4().hex[:8]}"
    
    return AdminPolicy(
        policy_id=policy_id,
        name="Quarantine high-risk traffic",
        description="Quarantine any traffic with high risk score or detected anomalies",
        conditions=[
            PolicyCondition(PolicyMatchType.BEHAVIORAL, "risk_score", "gte", 80),
        ],
        condition_logic="ANY",  # Match if risk is high OR anomalies detected
        action="quarantine",
        priority=priority,
    )


def create_contractor_policy(
    policy_id: str = None,
    priority: int = 75,
) -> AdminPolicy:
    """
    Create a policy that restricts contractor access.
    
    Example:
        policy = create_contractor_policy()
    """
    if not policy_id:
        import uuid
        policy_id = f"contractor_{uuid.uuid4().hex[:8]}"
    
    return AdminPolicy(
        policy_id=policy_id,
        name="Contractor network restrictions",
        description="Restrict contractors to office network only",
        conditions=[
            PolicyCondition(PolicyMatchType.IDENTITY, "user_role", "eq", "contractor"),
            PolicyCondition(PolicyMatchType.LOCATION, "user_location", "ne", "office"),
        ],
        condition_logic="ALL",
        action="drop",
        priority=priority,
    )


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def example_integration_flow():
    """
    Complete example showing DPI → IAM → Firewall integration.
    """
    
    # Step 1: Initialize integration engine
    integration = FirewallDPIIAMIntegration()
    
    # Step 2: Add admin policies
    integration.add_admin_policy(create_block_category_policy("P2P"))
    integration.add_admin_policy(create_rate_limit_policy("Video Streaming", 10000))
    integration.add_admin_policy(create_high_risk_quarantine_policy())
    integration.add_admin_policy(create_contractor_policy())
    
    # Step 3: Simulate incoming flow
    src_ip = "192.168.1.100"
    dst_ip = "10.0.0.50"
    src_port = 51234
    dst_port = 6881
    protocol = "tcp"
    
    # Step 4: Get DPI classification (simulated)
    dpi_classification = DPIClassification(
        app_name="BitTorrent",
        category="P2P",
        protocol="BitTorrent",
        confidence=95,
        detection_tick=150,
        is_encrypted=False,
        is_tunneled=False,
        risk_score=75,
        detected_anomalies=["suspicious_packet_pattern"],
    )
    
    # Step 5: Get IAM assertion (simulated)
    iam_assertion = IAMIdentityAssertion(
        user_id="user123",
        username="john.doe",
        user_role="employee",
        user_groups=["engineers", "vpn_users"],
        organization_unit="Engineering",
        location="office",
        device_id="laptop001",
        device_type="laptop",
        is_mfa_verified=True,
        permission_level=60,
        clearance_level="standard",
    )
    
    # Step 6: Build policy context
    context = integration.build_policy_context(
        src_ip=src_ip,
        dst_ip=dst_ip,
        src_port=src_port,
        dst_port=dst_port,
        protocol=protocol,
        dpi_classification=dpi_classification,
        iam_assertion=iam_assertion,
    )
    
    # Step 7: Evaluate policies
    matching_policy, action, action_params = integration.evaluate_policies(context)
    
    # Step 8: Log results
    print(f"\n=== Integration Flow Example ===")
    print(f"Source: {src_ip}:{src_port}")
    print(f"Destination: {dst_ip}:{dst_port}")
    print(f"Protocol: {protocol}")
    print(f"\nDPI Classification:")
    print(f"  App: {dpi_classification.app_name}")
    print(f"  Category: {dpi_classification.category}")
    print(f"  Risk Score: {dpi_classification.risk_score}")
    print(f"\nIAM Assertion:")
    print(f"  User: {iam_assertion.username}")
    print(f"  Role: {iam_assertion.user_role}")
    print(f"  Location: {iam_assertion.location}")
    print(f"\nPolicy Matching:")
    if matching_policy:
        print(f"  Matched Policy: {matching_policy.name}")
        print(f"  Action: {action}")
        print(f"  Parameters: {action_params}")
    else:
        print(f"  No policies matched - default action: PASS")
    
    # Step 9: Get suggestions for debugging
    suggestions = integration.get_policy_suggestions(context)
    print(f"\nPolicy Suggestions ({len(suggestions)} matching):")
    for policy in suggestions:
        print(f"  - {policy.name}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    example_integration_flow()
