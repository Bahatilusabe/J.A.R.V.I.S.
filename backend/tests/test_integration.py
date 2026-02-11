"""
Integration Tests for DPI ↔ IAM ↔ Firewall

Test scenarios:
1. DPI classification matching
2. IAM identity-based access control
3. Multi-condition policy evaluation
4. Priority-based policy selection
5. Action enforcement with parameters
6. Context building from multiple sources
7. Policy suggestion for debugging

Author: J.A.R.V.I.S. Team
"""

import pytest
import logging
from datetime import datetime

# Import integration components
from backend.integrations.firewall_dpi_iam_integration import (
    FirewallDPIIAMIntegration,
    DPIClassification,
    IAMIdentityAssertion,
    AdminPolicy,
    PolicyCondition,
    PolicyMatchType,
    create_block_application_policy,
    create_block_category_policy,
    create_rate_limit_policy,
    create_high_risk_quarantine_policy,
    create_contractor_policy,
    create_restrict_by_role_policy,
)

logger = logging.getLogger(__name__)


class TestDPIClassification:
    """Test DPI classification data structures"""
    
    def test_create_dpi_classification(self):
        """Test creating DPI classification object"""
        dpi = DPIClassification(
            app_name="Spotify",
            category="Video Streaming",
            protocol="HTTPS",
            confidence=95,
            detection_tick=47,
            is_encrypted=True,
            risk_score=5,
        )
        
        assert dpi.app_name == "Spotify"
        assert dpi.category == "Video Streaming"
        assert dpi.confidence == 95
        assert dpi.is_encrypted is True
        assert dpi.risk_score == 5
    
    def test_dpi_classification_to_dict(self):
        """Test converting DPI classification to dictionary"""
        dpi = DPIClassification(
            app_name="BitTorrent",
            category="P2P",
            protocol="BitTorrent",
            confidence=92,
            detection_tick=150,
            detected_anomalies=["suspicious_pattern"],
        )
        
        dpi_dict = dpi.to_dict()
        
        assert dpi_dict["app_name"] == "BitTorrent"
        assert dpi_dict["category"] == "P2P"
        assert dpi_dict["detected_anomalies"] == ["suspicious_pattern"]


class TestIAMAssertion:
    """Test IAM identity assertion data structures"""
    
    def test_create_iam_assertion(self):
        """Test creating IAM assertion object"""
        iam = IAMIdentityAssertion(
            user_id="emp_123",
            username="alice.smith",
            user_role="employee",
            user_groups=["engineers"],
            location="office",
            device_type="laptop",
            is_mfa_verified=True,
            permission_level=60,
        )
        
        assert iam.user_id == "emp_123"
        assert iam.username == "alice.smith"
        assert iam.user_role == "employee"
        assert iam.is_mfa_verified is True
    
    def test_iam_assertion_to_dict(self):
        """Test converting IAM assertion to dictionary"""
        iam = IAMIdentityAssertion(
            user_id="ctr_001",
            username="bob.contractor",
            user_role="contractor",
            clearance_level="public",
        )
        
        iam_dict = iam.to_dict()
        
        assert iam_dict["user_id"] == "ctr_001"
        assert iam_dict["user_role"] == "contractor"
        assert iam_dict["clearance_level"] == "public"


class TestPolicyCondition:
    """Test policy condition matching"""
    
    def test_condition_equals_operator(self):
        """Test equality operator"""
        cond = PolicyCondition(
            match_type=PolicyMatchType.APPLICATION,
            field="dpi_category",
            operator="eq",
            value="P2P",
        )
        
        context = {"dpi_category": "P2P"}
        assert cond.matches(context) is True
        
        context = {"dpi_category": "Video Streaming"}
        assert cond.matches(context) is False
    
    def test_condition_contains_operator(self):
        """Test contains operator"""
        cond = PolicyCondition(
            match_type=PolicyMatchType.APPLICATION,
            field="app_name",
            operator="contains",
            value="Torrent",
        )
        
        context = {"app_name": "BitTorrent Client"}
        assert cond.matches(context) is True
        
        context = {"app_name": "Spotify"}
        assert cond.matches(context) is False
    
    def test_condition_in_operator(self):
        """Test 'in' operator"""
        cond = PolicyCondition(
            match_type=PolicyMatchType.IDENTITY,
            field="user_role",
            operator="in",
            value=["admin", "ops"],
        )
        
        context = {"user_role": "admin"}
        assert cond.matches(context) is True
        
        context = {"user_role": "employee"}
        assert cond.matches(context) is False
    
    def test_condition_not_in_operator(self):
        """Test 'not_in' operator"""
        cond = PolicyCondition(
            match_type=PolicyMatchType.IDENTITY,
            field="user_role",
            operator="not_in",
            value=["contractor", "guest"],
        )
        
        context = {"user_role": "employee"}
        assert cond.matches(context) is True
        
        context = {"user_role": "contractor"}
        assert cond.matches(context) is False
    
    def test_condition_gt_operator(self):
        """Test greater-than operator"""
        cond = PolicyCondition(
            match_type=PolicyMatchType.BEHAVIORAL,
            field="risk_score",
            operator="gt",
            value=50,
        )
        
        context = {"risk_score": 75}
        assert cond.matches(context) is True
        
        context = {"risk_score": 30}
        assert cond.matches(context) is False
    
    def test_condition_gte_operator(self):
        """Test greater-than-or-equal operator"""
        cond = PolicyCondition(
            match_type=PolicyMatchType.BEHAVIORAL,
            field="risk_score",
            operator="gte",
            value=80,
        )
        
        context = {"risk_score": 80}
        assert cond.matches(context) is True
        
        context = {"risk_score": 79}
        assert cond.matches(context) is False
    
    def test_condition_regex_operator(self):
        """Test regex operator"""
        cond = PolicyCondition(
            match_type=PolicyMatchType.NETWORK,
            field="dst_ip",
            operator="regex",
            value="^10\\..*",
        )
        
        context = {"dst_ip": "10.0.0.50"}
        assert cond.matches(context) is True
        
        context = {"dst_ip": "192.168.1.1"}
        assert cond.matches(context) is False


class TestAdminPolicy:
    """Test admin policy evaluation"""
    
    def test_policy_single_condition_match(self):
        """Test policy with single condition"""
        policy = AdminPolicy(
            policy_id="test_001",
            name="Block P2P",
            description="Block P2P traffic",
            conditions=[
                PolicyCondition(PolicyMatchType.APPLICATION, "dpi_category", "eq", "P2P"),
            ],
            condition_logic="ALL",
            action="drop",
        )
        
        context = {"dpi_category": "P2P"}
        assert policy.evaluate(context) is True
        
        context = {"dpi_category": "Video Streaming"}
        assert policy.evaluate(context) is False
    
    def test_policy_all_conditions_required(self):
        """Test policy with ALL logic (AND)"""
        policy = AdminPolicy(
            policy_id="test_002",
            name="Block P2P from non-admins",
            description="Block P2P for non-admin users",
            conditions=[
                PolicyCondition(PolicyMatchType.APPLICATION, "dpi_category", "eq", "P2P"),
                PolicyCondition(PolicyMatchType.IDENTITY, "user_role", "ne", "admin"),
            ],
            condition_logic="ALL",
            action="drop",
        )
        
        # Both conditions true → Match
        context = {"dpi_category": "P2P", "user_role": "employee"}
        assert policy.evaluate(context) is True
        
        # First true, second false → No match
        context = {"dpi_category": "P2P", "user_role": "admin"}
        assert policy.evaluate(context) is False
        
        # Both false → No match
        context = {"dpi_category": "Video Streaming", "user_role": "employee"}
        assert policy.evaluate(context) is False
    
    def test_policy_any_condition_required(self):
        """Test policy with ANY logic (OR)"""
        policy = AdminPolicy(
            policy_id="test_003",
            name="Block high-risk or anomalies",
            description="Block high-risk flows or malware",
            conditions=[
                PolicyCondition(PolicyMatchType.BEHAVIORAL, "risk_score", "gte", 80),
                PolicyCondition(PolicyMatchType.BEHAVIORAL, "detected_anomalies", "contains", "malware"),
            ],
            condition_logic="ANY",
            action="drop",
        )
        
        # First condition true → Match
        context = {"risk_score": 85, "detected_anomalies": []}
        assert policy.evaluate(context) is True
        
        # Second condition true → Match
        context = {"risk_score": 20, "detected_anomalies": ["malware_detected"]}
        assert policy.evaluate(context) is True
        
        # Both conditions false → No match
        context = {"risk_score": 20, "detected_anomalies": []}
        assert policy.evaluate(context) is False
    
    def test_policy_disabled(self):
        """Test that disabled policies don't match"""
        policy = AdminPolicy(
            policy_id="test_004",
            name="Disabled policy",
            description="This policy is disabled",
            conditions=[
                PolicyCondition(PolicyMatchType.APPLICATION, "dpi_category", "eq", "P2P"),
            ],
            condition_logic="ALL",
            action="drop",
            enabled=False,
        )
        
        context = {"dpi_category": "P2P"}
        assert policy.evaluate(context) is False
    
    def test_policy_to_dict(self):
        """Test converting policy to dictionary"""
        policy = AdminPolicy(
            policy_id="test_005",
            name="Test policy",
            description="Test description",
            conditions=[
                PolicyCondition(PolicyMatchType.APPLICATION, "app_name", "eq", "Spotify"),
            ],
            condition_logic="ALL",
            action="rate_limit",
            action_params={"rate_limit_kbps": 5000},
            priority=100,
        )
        
        policy_dict = policy.to_dict()
        
        assert policy_dict["policy_id"] == "test_005"
        assert policy_dict["name"] == "Test policy"
        assert policy_dict["action"] == "rate_limit"
        assert policy_dict["priority"] == 100


class TestIntegrationEngine:
    """Test the integration engine"""
    
    def test_add_and_remove_policy(self):
        """Test adding and removing policies"""
        integration = FirewallDPIIAMIntegration()
        
        policy = create_block_application_policy("Spotify")
        integration.add_admin_policy(policy)
        assert len(integration.admin_policies) == 1
        
        integration.remove_admin_policy(policy.policy_id)
        assert len(integration.admin_policies) == 0
    
    def test_policy_priority_sorting(self):
        """Test that policies are sorted by priority (highest first)"""
        integration = FirewallDPIIAMIntegration()
        
        policy_50 = AdminPolicy(policy_id="p50", name="50", description="desc50", priority=50, action="drop", conditions=[])
        policy_100 = AdminPolicy(policy_id="p100", name="100", description="desc100", priority=100, action="drop", conditions=[])
        policy_75 = AdminPolicy(policy_id="p75", name="75", description="desc75", priority=75, action="drop", conditions=[])
        
        integration.add_admin_policy(policy_50)
        integration.add_admin_policy(policy_100)
        integration.add_admin_policy(policy_75)
        
        # Should be sorted: 100, 75, 50
        priorities = [p.priority for p in integration.admin_policies]
        assert priorities == [100, 75, 50]
    
    def test_build_policy_context(self):
        """Test building comprehensive policy context"""
        integration = FirewallDPIIAMIntegration()
        
        dpi = DPIClassification(
            app_name="Spotify",
            category="Video Streaming",
            protocol="HTTPS",
            confidence=95,
            detection_tick=47,
            risk_score=5,
        )
        
        iam = IAMIdentityAssertion(
            user_id="user123",
            username="alice.smith",
            user_role="employee",
            location="office",
        )
        
        context = integration.build_policy_context(
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            src_port=54321,
            dst_port=443,
            protocol="tcp",
            dpi_classification=dpi,
            iam_assertion=iam,
        )
        
        # Verify context has all fields
        assert context["src_ip"] == "192.168.1.100"
        assert context["app_name"] == "Spotify"
        assert context["user_role"] == "employee"
        assert context["user_location"] == "office"
    
    def test_evaluate_policies_first_match(self):
        """Test that first matching policy is returned"""
        integration = FirewallDPIIAMIntegration()
        
        # Add policies
        policy_100 = AdminPolicy(
            policy_id="p100",
            name="Priority 100",
            description="High priority P2P block",
            priority=100,
            conditions=[PolicyCondition(PolicyMatchType.APPLICATION, "dpi_category", "eq", "P2P")],
            condition_logic="ALL",
            action="drop",
        )
        policy_50 = AdminPolicy(
            policy_id="p50",
            name="Priority 50",
            description="Low priority P2P rate limit",
            priority=50,
            conditions=[PolicyCondition(PolicyMatchType.APPLICATION, "dpi_category", "eq", "P2P")],
            condition_logic="ALL",
            action="rate_limit",
        )
        
        integration.add_admin_policy(policy_100)
        integration.add_admin_policy(policy_50)
        
        # Evaluate
        context = {"dpi_category": "P2P"}
        matched_policy, action, params = integration.evaluate_policies(context)
        
        # First (highest priority) should win
        assert matched_policy.policy_id == "p100"
        assert action == "drop"
    
    def test_get_policy_suggestions(self):
        """Test getting all matching policies for debugging"""
        integration = FirewallDPIIAMIntegration()
        
        policy1 = create_block_category_policy("P2P", priority=100)
        policy2 = AdminPolicy(
            policy_id="p_002",
            name="Alternative P2P block",
            description="Alternative P2P rate limit",
            priority=50,
            conditions=[PolicyCondition(PolicyMatchType.APPLICATION, "dpi_category", "eq", "P2P")],
            condition_logic="ALL",
            action="rate_limit",
        )
        
        integration.add_admin_policy(policy1)
        integration.add_admin_policy(policy2)
        
        context = {"dpi_category": "P2P"}
        suggestions = integration.get_policy_suggestions(context)
        
        assert len(suggestions) == 2


class TestTemplateHelpers:
    """Test template helper functions"""
    
    def test_block_application_policy(self):
        """Test block application template"""
        policy = create_block_application_policy("Spotify")
        
        assert policy.name == "Block Spotify"
        assert policy.action == "drop"
        assert len(policy.conditions) == 1
        
        context = {"app_name": "Spotify"}
        assert policy.evaluate(context) is True
    
    def test_block_category_policy(self):
        """Test block category template"""
        policy = create_block_category_policy("P2P")
        
        assert policy.name == "Block P2P"
        assert policy.action == "drop"
        
        context = {"dpi_category": "P2P"}
        assert policy.evaluate(context) is True
    
    def test_rate_limit_policy(self):
        """Test rate limit template"""
        policy = create_rate_limit_policy("Video Streaming", 5000)
        
        assert policy.action == "rate_limit"
        assert policy.action_params["rate_limit_kbps"] == 5000
    
    def test_high_risk_quarantine_policy(self):
        """Test high-risk quarantine template"""
        policy = create_high_risk_quarantine_policy()
        
        assert policy.action == "quarantine"
        assert policy.priority == 200  # Very high priority
    
    def test_contractor_policy(self):
        """Test contractor restriction template"""
        policy = create_contractor_policy()
        
        assert policy.action == "drop"
        
        # Contractor from remote → Should match
        context = {"user_role": "contractor", "user_location": "remote"}
        assert policy.evaluate(context) is True
        
        # Contractor from office → Should not match
        context = {"user_role": "contractor", "user_location": "office"}
        assert policy.evaluate(context) is False
        
        # Employee from remote → Should not match
        context = {"user_role": "employee", "user_location": "remote"}
        assert policy.evaluate(context) is False
    
    def test_restrict_by_role_policy(self):
        """Test restrict by role template"""
        policy = create_restrict_by_role_policy("AWS Console", ["admin", "ops"])
        
        # Non-allowed role trying to access → Should block
        context = {"app_name": "AWS Console", "user_role": "employee"}
        assert policy.evaluate(context) is True
        
        # Allowed role → Should not block
        context = {"app_name": "AWS Console", "user_role": "admin"}
        assert policy.evaluate(context) is False


class TestRealWorldScenarios:
    """Test realistic scenarios"""
    
    def test_scenario_block_torrent_for_employees(self):
        """Scenario: Block torrent for regular employees but allow for admins"""
        integration = FirewallDPIIAMIntegration()
        
        # Add policy
        policy = AdminPolicy(
            policy_id="scenario_001",
            name="Block P2P for non-admins",
            description="Block P2P for non-admin users",
            conditions=[
                PolicyCondition(PolicyMatchType.APPLICATION, "dpi_category", "eq", "P2P"),
                PolicyCondition(PolicyMatchType.IDENTITY, "user_role", "ne", "admin"),
            ],
            condition_logic="ALL",
            action="drop",
            priority=100,
        )
        integration.add_admin_policy(policy)
        
        dpi_p2p = DPIClassification(
            app_name="BitTorrent",
            category="P2P",
            protocol="TCP",
            confidence=95,
            detection_tick=150
        )
        
        # Test 1: Employee with P2P → Should block
        iam_emp = IAMIdentityAssertion(user_id="user1", username="alice", user_role="employee")
        context = integration.build_policy_context(
            "192.168.1.1", "10.0.0.1", 51234, 6881, "tcp",
            dpi_p2p, iam_emp
        )
        matched, action, _ = integration.evaluate_policies(context)
        assert matched is not None and action == "drop"
        
        # Test 2: Admin with P2P → Should allow (no match)
        iam_admin = IAMIdentityAssertion(user_id="user2", username="bob", user_role="admin")
        context = integration.build_policy_context(
            "192.168.1.2", "10.0.0.1", 51235, 6881, "tcp",
            dpi_p2p, iam_admin
        )
        matched, action, _ = integration.evaluate_policies(context)
        assert matched is None  # No policies matched
    
    def test_scenario_rate_limit_video_streaming(self):
        """Scenario: Rate limit video streaming"""
        integration = FirewallDPIIAMIntegration()
        
        policy = create_rate_limit_policy("Video Streaming", 5000)
        integration.add_admin_policy(policy)
        
        dpi_video = DPIClassification(
            app_name="Netflix",
            category="Video Streaming",
            protocol="HTTPS",
            confidence=98,
            detection_tick=50,
        )
        
        context = integration.build_policy_context(
            "192.168.1.100", "streaming.example.com", 54321, 443, "tcp",
            dpi_classification=dpi_video,
        )
        
        matched, action, params = integration.evaluate_policies(context)
        
        assert matched is not None
        assert action == "rate_limit"
        assert params["rate_limit_kbps"] == 5000
    
    def test_scenario_contractor_restrictions(self):
        """Scenario: Contractor can only access from office VPN"""
        integration = FirewallDPIIAMIntegration()
        
        policy = create_contractor_policy()
        integration.add_admin_policy(policy)
        
        # Test 1: Contractor from office → Allow
        iam_office = IAMIdentityAssertion(
            user_id="contractor1",
            username="contractor1",
            user_role="contractor",
            location="office",
        )
        context = integration.build_policy_context(
            "10.200.0.1", "192.168.100.50", 443, 443, "tcp",
            iam_assertion=iam_office,
        )
        matched, action, _ = integration.evaluate_policies(context)
        assert matched is None  # No restriction
        
        # Test 2: Contractor from remote → Block
        iam_remote = IAMIdentityAssertion(
            user_id="contractor1",
            username="contractor1",
            user_role="contractor",
            location="remote",
        )
        context = integration.build_policy_context(
            "203.0.113.1", "192.168.100.50", 443, 443, "tcp",
            iam_assertion=iam_remote,
        )
        matched, action, _ = integration.evaluate_policies(context)
        assert matched is not None and action == "drop"
    
    def test_scenario_high_risk_quarantine(self):
        """Scenario: Quarantine high-risk traffic"""
        integration = FirewallDPIIAMIntegration()
        
        policy = create_high_risk_quarantine_policy()
        integration.add_admin_policy(policy)
        
        # High-risk DPI classification
        dpi_malware = DPIClassification(
            app_name="Unknown",
            category="Malware",
            protocol="TCP",
            confidence=85,
            detection_tick=200,
            risk_score=95,
            detected_anomalies=["malware_signature_match", "c2_communication"],
        )
        
        context = integration.build_policy_context(
            "192.168.1.150", "10.0.0.1", 49152, 443, "tcp",
            dpi_classification=dpi_malware,
        )
        
        matched, action, _ = integration.evaluate_policies(context)
        
        assert matched is not None
        assert action == "quarantine"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
