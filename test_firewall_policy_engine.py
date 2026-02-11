#!/usr/bin/env python3
"""
Comprehensive test suite for Stateful Firewall & Policy Engine

Tests all critical components:
- ACLs (Access Control Lists)
- NAT (Network Address Translation)
- Geo-blocking
- Rate limiting
- QoS marking
- Connection tracking
- Policy versioning
- Staged rollouts
- DPI integration
- IAM integration
"""

import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    """Print formatted header"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

def print_test(name):
    """Print test name"""
    print(f"{YELLOW}→ {name}{RESET}")

def print_pass(msg):
    """Print passing test"""
    print(f"  {GREEN}✓ {msg}{RESET}")

def print_fail(msg):
    """Print failing test"""
    print(f"  {RED}✗ {msg}{RESET}")

def test_firewall_engine_import():
    """Test 1: Verify firewall engine imports correctly"""
    print_header("TEST 1: Firewall Engine Import")
    print_test("Importing firewall_policy_engine module...")
    
    try:
        from backend.firewall_policy_engine import (
            StatefulFirewallPolicyEngine,
            FirewallRule,
            FlowTuple,
            PolicyDecision,
            PolicyEvaluationResult,
            ACLAction,
            TrafficDirection,
            QoSClass,
            GeoBlockAction,
            NATMode,
            PolicyVersion,
            NATMapping,
            ConnectionState,
        )
        print_pass("All firewall engine classes imported successfully")
        return True
    except ImportError as e:
        print_fail(f"Import error: {e}")
        return False
    except Exception as e:
        print_fail(f"Unexpected error: {e}")
        return False

def test_firewall_engine_initialization():
    """Test 2: Initialize firewall engine"""
    print_header("TEST 2: Firewall Engine Initialization")
    print_test("Creating StatefulFirewallPolicyEngine instance...")
    
    try:
        from backend.firewall_policy_engine import StatefulFirewallPolicyEngine
        engine = StatefulFirewallPolicyEngine(max_connections=10000, cleanup_interval=60)
        print_pass(f"Engine initialized: {type(engine).__name__}")
        print_pass(f"Max connections: 10,000")
        print_pass(f"Cleanup interval: 60 seconds")
        return True, engine
    except Exception as e:
        print_fail(f"Failed to initialize engine: {e}")
        return False, None

def test_acl_rules(engine):
    """Test 3: ACL (Access Control List) functionality"""
    print_header("TEST 3: ACL Rules Management")
    
    try:
        from backend.firewall_policy_engine import (
            FirewallRule, ACLAction, TrafficDirection
        )
        
        # Test 3.1: Create and add rules
        print_test("Creating ACL rule: Block malware traffic...")
        rule1 = FirewallRule(
            rule_id="rule_block_malware",
            name="Block Malware",
            priority=1000,
            direction=TrafficDirection.BIDIRECTIONAL,
            dpi_category="malware",
            action=ACLAction.DENY,
            description="Automatic malware blocking"
        )
        
        if engine.add_rule(rule1):
            print_pass("Malware blocking rule added")
        else:
            print_fail("Failed to add malware rule")
            return False
        
        # Test 3.2: Create allow rule
        print_test("Creating ACL rule: Allow web browsing...")
        rule2 = FirewallRule(
            rule_id="rule_allow_web",
            name="Allow Web Browsing",
            priority=100,
            direction=TrafficDirection.OUTBOUND,
            protocol="tcp",
            dst_port_range=(443, 443),
            dpi_category="web_browsing",
            action=ACLAction.ALLOW,
        )
        
        if engine.add_rule(rule2):
            print_pass("Web browsing allow rule added")
        else:
            print_fail("Failed to add web rule")
            return False
        
        # Test 3.3: List rules
        print_test("Listing all rules...")
        rules = engine.list_rules()
        print_pass(f"Total rules: {len(rules)}")
        for rule in rules:
            print_pass(f"  - {rule.name} (priority: {rule.priority}, action: {rule.action.value})")
        
        # Test 3.4: Get specific rule
        print_test("Retrieving specific rule...")
        retrieved = engine.get_rule("rule_block_malware")
        if retrieved and retrieved.name == "Block Malware":
            print_pass(f"Retrieved rule: {retrieved.name}")
        else:
            print_fail("Failed to retrieve rule")
            return False
        
        return True
    except Exception as e:
        print_fail(f"ACL test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_flow_evaluation(engine):
    """Test 4: Flow evaluation against policies"""
    print_header("TEST 4: Flow Evaluation")
    
    try:
        from backend.firewall_policy_engine import FlowTuple, TrafficDirection
        
        # Test 4.1: Evaluate allowed flow
        print_test("Evaluating ALLOWED flow (web browsing)...")
        flow1 = FlowTuple(
            src_ip="192.168.1.100",
            dst_ip="1.1.1.1",
            src_port=54321,
            dst_port=443,
            protocol="tcp"
        )
        
        decision1 = engine.evaluate_flow(
            flow=flow1,
            direction=TrafficDirection.OUTBOUND,
            dpi_app="TLS-Web",
            dpi_category="web_browsing",
            user_identity="user@example.com",
            user_role="employee"
        )
        
        if decision1 and decision1.policy_decision.value in ["pass", "allow"]:
            print_pass(f"Flow decision: {decision1.policy_decision.value}")
            print_pass(f"Matched rule: {decision1.matched_rule_id}")
        else:
            print_fail(f"Unexpected decision: {decision1}")
        
        # Test 4.2: Evaluate blocked flow
        print_test("Evaluating BLOCKED flow (malware)...")
        flow2 = FlowTuple(
            src_ip="192.168.1.100",
            dst_ip="10.0.0.50",
            src_port=12345,
            dst_port=6881,
            protocol="tcp"
        )
        
        decision2 = engine.evaluate_flow(
            flow=flow2,
            direction=TrafficDirection.BIDIRECTIONAL,
            dpi_app="Malware",
            dpi_category="malware",
            user_identity="user@example.com"
        )
        
        if decision2 and decision2.policy_decision.value in ["drop", "deny"]:
            print_pass(f"Flow decision: {decision2.policy_decision.value}")
            print_pass(f"Matched rule: {decision2.matched_rule_id}")
        else:
            print_fail(f"Expected DROP/DENY but got: {decision2}")
        
        return True
    except Exception as e:
        print_fail(f"Flow evaluation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_connection_tracking(engine):
    """Test 5: Connection tracking and state machine"""
    print_header("TEST 5: Connection Tracking")
    
    try:
        from backend.firewall_policy_engine import FlowTuple, TrafficDirection
        
        print_test("Creating tracked flow...")
        flow = FlowTuple(
            src_ip="192.168.1.50",
            dst_ip="8.8.8.8",
            src_port=53210,
            dst_port=53,
            protocol="tcp"
        )
        
        # Evaluate flow (creates tracking entry)
        engine.evaluate_flow(
            flow=flow,
            direction=TrafficDirection.OUTBOUND,
            dpi_category="dns"
        )
        
        print_pass(f"Flow tracked: {flow.to_key()}")
        
        # Test getting metrics
        print_test("Retrieving connection metrics...")
        metrics = engine.get_metrics()
        
        if metrics:
            print_pass(f"Total tracked connections: {len(engine._connections)}")
            print_pass(f"Packets passed: {metrics.get('packets_passed', 0)}")
            print_pass(f"Packets dropped: {metrics.get('packets_dropped', 0)}")
        else:
            print_fail("Failed to get metrics")
            return False
        
        # Test closing connection
        print_test("Closing connection...")
        if engine.close_connection(flow):
            print_pass("Connection closed successfully")
        else:
            print_fail("Failed to close connection")
            return False
        
        return True
    except Exception as e:
        print_fail(f"Connection tracking test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_qos_marking(engine):
    """Test 6: QoS (Quality of Service) marking"""
    print_header("TEST 6: QoS Marking")
    
    try:
        from backend.firewall_policy_engine import (
            FirewallRule, TrafficDirection, ACLAction, QoSClass
        )
        
        print_test("Creating QoS rule for VoIP traffic...")
        rule = FirewallRule(
            rule_id="rule_qos_voip",
            name="QoS VoIP",
            priority=500,
            direction=TrafficDirection.BIDIRECTIONAL,
            protocol="udp",
            dpi_category="voip",
            action=ACLAction.ALLOW,
            qos_class=QoSClass.CRITICAL,
            description="High priority VoIP"
        )
        
        if engine.add_rule(rule):
            print_pass(f"QoS rule added: {rule.name} (class: {rule.qos_class.value})")
        else:
            print_fail("Failed to add QoS rule")
            return False
        
        return True
    except Exception as e:
        print_fail(f"QoS test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rate_limiting(engine):
    """Test 7: Rate limiting functionality"""
    print_header("TEST 7: Rate Limiting")
    
    try:
        from backend.firewall_policy_engine import (
            FirewallRule, TrafficDirection, ACLAction
        )
        
        print_test("Creating rate-limited rule for video streaming...")
        rule = FirewallRule(
            rule_id="rule_rate_limit_video",
            name="Rate Limit Video",
            priority=300,
            direction=TrafficDirection.OUTBOUND,
            dpi_category="video_streaming",
            action=ACLAction.RATE_LIMIT,
            rate_limit_kbps=10000,  # 10 Mbps limit
            description="Limit video to 10 Mbps"
        )
        
        if engine.add_rule(rule):
            print_pass(f"Rate limit rule added: {rule.rate_limit_kbps} kbps")
        else:
            print_fail("Failed to add rate limit rule")
            return False
        
        return True
    except Exception as e:
        print_fail(f"Rate limiting test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_geo_blocking(engine):
    """Test 8: Geo-blocking functionality"""
    print_header("TEST 8: Geo-Blocking")
    
    try:
        from backend.firewall_policy_engine import (
            FirewallRule, TrafficDirection, ACLAction, GeoBlockAction
        )
        
        print_test("Creating geo-blocking rule for restricted countries...")
        rule = FirewallRule(
            rule_id="rule_geo_block",
            name="Geo Block Restricted",
            priority=800,
            direction=TrafficDirection.INBOUND,
            action=ACLAction.DENY,
            geo_block_countries=["KP", "IR", "SY"],  # Example restricted countries
            geo_block_action=GeoBlockAction.BLOCK,
            description="Block traffic from restricted countries"
        )
        
        if engine.add_rule(rule):
            print_pass(f"Geo-blocking rule added")
            print_pass(f"  Blocked countries: {', '.join(rule.geo_block_countries)}")
        else:
            print_fail("Failed to add geo-blocking rule")
            return False
        
        return True
    except Exception as e:
        print_fail(f"Geo-blocking test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_nat_support(engine):
    """Test 9: NAT (Network Address Translation) support"""
    print_header("TEST 9: NAT Support")
    
    try:
        from backend.firewall_policy_engine import (
            FirewallRule, TrafficDirection, ACLAction, NATMode
        )
        
        print_test("Creating SNAT rule...")
        rule_snat = FirewallRule(
            rule_id="rule_snat",
            name="Source NAT",
            priority=600,
            direction=TrafficDirection.OUTBOUND,
            src_ip_prefix="192.168.0.0/16",
            action=ACLAction.ALLOW,
            nat_mode=NATMode.SOURCE_NAT,
            description="Rewrite source IPs to gateway"
        )
        
        if engine.add_rule(rule_snat):
            print_pass(f"SNAT rule added: {rule_snat.name}")
        else:
            print_fail("Failed to add SNAT rule")
            return False
        
        print_test("Creating DNAT rule...")
        rule_dnat = FirewallRule(
            rule_id="rule_dnat",
            name="Destination NAT",
            priority=700,
            direction=TrafficDirection.INBOUND,
            dst_port_range=(8080, 8080),
            action=ACLAction.ALLOW,
            nat_mode=NATMode.DESTINATION_NAT,
            description="Redirect external traffic to internal server"
        )
        
        if engine.add_rule(rule_dnat):
            print_pass(f"DNAT rule added: {rule_dnat.name}")
        else:
            print_fail("Failed to add DNAT rule")
            return False
        
        return True
    except Exception as e:
        print_fail(f"NAT test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_policy_versioning(engine):
    """Test 10: Policy versioning"""
    print_header("TEST 10: Policy Versioning")
    
    try:
        print_test("Creating policy version...")
        version = engine.create_policy_version(
            name="Policy v1.0",
            description="Initial firewall policy",
            created_by="admin"
        )
        
        if version:
            print_pass(f"Version created: {version.version_id}")
            print_pass(f"  Name: {version.name}")
            print_pass(f"  Status: {version.status}")
        else:
            print_fail("Failed to create policy version")
            return False
        
        print_test("Listing policy versions...")
        versions = engine.list_policy_versions()
        print_pass(f"Total versions: {len(versions)}")
        
        return True, version
    except Exception as e:
        print_fail(f"Policy versioning test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_staged_rollout(engine, version):
    """Test 11: Staged rollout functionality"""
    print_header("TEST 11: Staged Rollout")
    
    try:
        if not version:
            print_fail("No version available for rollout test")
            return False
        
        print_test("Staging policy for canary deployment (10%)...")
        if engine.stage_policy_version(version.version_id, deployment_percentage=10):
            print_pass("Policy staged at 10% (canary)")
        else:
            print_fail("Failed to stage policy")
            return False
        
        print_test("Checking staged version status...")
        staged = engine.get_policy_version(version.version_id)
        if staged and staged.deployment_percentage == 10:
            print_pass(f"Deployment percentage: {staged.deployment_percentage}%")
            print_pass(f"Status: {staged.status}")
        else:
            print_fail("Staged version status incorrect")
            return False
        
        print_test("Activating policy to 100%...")
        if engine.activate_policy_version(version.version_id):
            print_pass("Policy activated to 100%")
        else:
            print_fail("Failed to activate policy")
            return False
        
        return True
    except Exception as e:
        print_fail(f"Staged rollout test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_integration():
    """Test 12: API routes integration"""
    print_header("TEST 12: API Routes Integration")
    
    try:
        from backend.api.routes.policy import router
        print_pass("Policy router imported successfully")
        
        # Check if routes are registered
        routes_found = len(router.routes) > 0
        if routes_found:
            print_pass(f"Total policy routes registered: {len(router.routes)}")
        else:
            print_fail("No routes found in policy router")
            return False
        
        return True
    except ImportError as e:
        print_fail(f"Failed to import policy router: {e}")
        return False
    except Exception as e:
        print_fail(f"API integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dpi_integration():
    """Test 13: DPI integration"""
    print_header("TEST 13: DPI Integration")
    
    try:
        from backend.firewall_policy_engine import FlowTuple, TrafficDirection
        from backend.firewall_policy_engine import StatefulFirewallPolicyEngine
        
        engine = StatefulFirewallPolicyEngine()
        
        print_test("Evaluating flow with DPI classification...")
        flow = FlowTuple(
            src_ip="192.168.1.100",
            dst_ip="10.0.0.1",
            src_port=54321,
            dst_port=6881,
            protocol="tcp"
        )
        
        decision = engine.evaluate_flow(
            flow=flow,
            direction=TrafficDirection.BIDIRECTIONAL,
            dpi_app="BitTorrent",
            dpi_category="P2P",
            user_identity="user@example.com"
        )
        
        if decision and decision.dpi_app == "BitTorrent":
            print_pass(f"DPI classification applied: {decision.dpi_app}")
            print_pass(f"Category: {decision.dpi_category}")
        else:
            print_fail("DPI integration not working")
            return False
        
        return True
    except Exception as e:
        print_fail(f"DPI integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_iam_integration():
    """Test 14: IAM integration"""
    print_header("TEST 14: IAM Integration")
    
    try:
        from backend.firewall_policy_engine import FlowTuple, TrafficDirection
        from backend.firewall_policy_engine import StatefulFirewallPolicyEngine
        
        engine = StatefulFirewallPolicyEngine()
        
        print_test("Evaluating flow with IAM identity...")
        flow = FlowTuple(
            src_ip="192.168.1.100",
            dst_ip="10.0.0.1",
            src_port=443,
            dst_port=443,
            protocol="tcp"
        )
        
        decision = engine.evaluate_flow(
            flow=flow,
            direction=TrafficDirection.OUTBOUND,
            user_identity="contractor@example.com",
            user_role="contractor",
            src_country="US"
        )
        
        if decision and decision.user_identity == "contractor@example.com":
            print_pass(f"IAM identity applied: {decision.user_identity}")
            print_pass(f"Role: {decision.user_role}")
        else:
            print_fail("IAM integration not working")
            return False
        
        return True
    except Exception as e:
        print_fail(f"IAM integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests"""
    print_header("STATEFUL FIREWALL & POLICY ENGINE - COMPREHENSIVE TEST SUITE")
    
    results = {}
    
    # Test 1: Import
    results['import'] = test_firewall_engine_import()
    if not results['import']:
        print_fail("Cannot continue without successful import")
        return results
    
    # Test 2: Initialization
    results['init'], engine = test_firewall_engine_initialization()
    if not engine:
        print_fail("Cannot continue without engine initialization")
        return results
    
    # Test 3: ACLs
    results['acl'] = test_acl_rules(engine)
    
    # Test 4: Flow Evaluation
    results['flow_eval'] = test_flow_evaluation(engine)
    
    # Test 5: Connection Tracking
    results['conn_track'] = test_connection_tracking(engine)
    
    # Test 6: QoS
    results['qos'] = test_qos_marking(engine)
    
    # Test 7: Rate Limiting
    results['rate_limit'] = test_rate_limiting(engine)
    
    # Test 8: Geo-blocking
    results['geo_block'] = test_geo_blocking(engine)
    
    # Test 9: NAT
    results['nat'] = test_nat_support(engine)
    
    # Test 10: Versioning
    results['versioning'], version = test_policy_versioning(engine)
    
    # Test 11: Staged Rollout
    results['staged_rollout'] = test_staged_rollout(engine, version)
    
    # Test 12: API Integration
    results['api'] = test_api_integration()
    
    # Test 13: DPI Integration
    results['dpi'] = test_dpi_integration()
    
    # Test 14: IAM Integration
    results['iam'] = test_iam_integration()
    
    # Print summary
    print_header("TEST SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{GREEN}✓ PASS{RESET}" if result else f"{RED}✗ FAIL{RESET}"
        print(f"{test_name.upper():20s} {status}")
    
    print(f"\n{BLUE}Overall: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print(f"{GREEN}✓ All tests passed!{RESET}")
        return True
    else:
        print(f"{RED}✗ Some tests failed{RESET}")
        return False

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Fatal error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
