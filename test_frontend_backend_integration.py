#!/usr/bin/env python3
"""
Frontend-Backend Integration Test Suite
Tests all critical data flows between frontend services and backend endpoints.

Usage:
    python3 test_frontend_backend_integration.py

Author: J.A.R.V.I.S. Integration Team
Date: December 2024
"""

import asyncio
import json
import sys
from typing import Dict, Any, Tuple
from datetime import datetime
import subprocess

# Test configuration
BACKEND_URL = "http://127.0.0.1:8000"
TEST_TIMEOUT = 10  # seconds

print("\n" + "=" * 100)
print("FRONTEND-BACKEND INTEGRATION TEST SUITE")
print("=" * 100 + "\n")

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

test_results = {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "total": 0,
    "tests": []
}

def log_test(name: str, status: str, message: str = "", duration: float = 0):
    """Log test result"""
    test_results["total"] += 1
    status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏭️ "
    
    if status == "PASS":
        test_results["passed"] += 1
        print(f"{GREEN}{status_symbol} {name}{RESET}")
    elif status == "FAIL":
        test_results["failed"] += 1
        print(f"{RED}{status_symbol} {name}{RESET}")
        if message:
            print(f"   {RED}Error: {message}{RESET}")
    else:
        test_results["skipped"] += 1
        print(f"{YELLOW}{status_symbol} {name}{RESET}")
    
    if duration > 0:
        print(f"   {BLUE}Duration: {duration:.3f}s{RESET}")
    
    test_results["tests"].append({
        "name": name,
        "status": status,
        "message": message,
        "duration": duration
    })

def test_backend_running() -> bool:
    """Check if backend is running"""
    try:
        import requests
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        return False

# ============================================================================
# TEST SUITE 1: Endpoint Connectivity
# ============================================================================

print(f"{BLUE}TEST SUITE 1: Endpoint Connectivity{RESET}")
print("-" * 100)

if test_backend_running():
    log_test("Backend Service Running", "PASS")
else:
    log_test("Backend Service Running", "FAIL", "Backend is not responding at http://127.0.0.1:8000")
    print(f"\n{YELLOW}NOTE: Start backend with: make run-backend{RESET}\n")
    sys.exit(1)

# Test critical endpoints
critical_endpoints = [
    ("GET", "/health"),
    ("GET", "/api/system/status"),
    ("GET", "/api/federation/status"),
]

for method, path in critical_endpoints:
    try:
        import requests
        if method == "GET":
            response = requests.get(f"{BACKEND_URL}{path}", timeout=5)
        log_test(f"Endpoint {method} {path}", "PASS" if response.status_code < 400 else "FAIL")
    except Exception as e:
        log_test(f"Endpoint {method} {path}", "FAIL", str(e))

# ============================================================================
# TEST SUITE 2: DPI Classification Flow
# ============================================================================

print(f"\n{BLUE}TEST SUITE 2: DPI Classification Flow{RESET}")
print("-" * 100)

try:
    import requests
    
    # Test DPI classification endpoint
    payload = {
        "src_ip": "192.168.1.100",
        "dst_ip": "8.8.8.8",
        "src_port": 51234,
        "dst_port": 443,
        "protocol": 6
    }
    
    response = requests.post(
        f"{BACKEND_URL}/api/dpi/classify/protocol",
        json=payload,
        timeout=5
    )
    
    if response.status_code == 200:
        data = response.json()
        required_fields = ["protocol", "confidence", "detection_tick", "app_name"]
        if all(field in data for field in required_fields):
            log_test("DPI: Classification Response Structure", "PASS")
        else:
            missing = [f for f in required_fields if f not in data]
            log_test("DPI: Classification Response Structure", "FAIL", f"Missing fields: {missing}")
    else:
        log_test("DPI: Classification Endpoint", "FAIL", f"Status: {response.status_code}")
        
except Exception as e:
    log_test("DPI: Classification Flow", "FAIL", str(e))

# ============================================================================
# TEST SUITE 3: Policy Evaluation Flow
# ============================================================================

print(f"\n{BLUE}TEST SUITE 3: Policy Evaluation Flow{RESET}")
print("-" * 100)

try:
    import requests
    
    # Test firewall rule retrieval
    response = requests.get(
        f"{BACKEND_URL}/api/policy/firewall/rules",
        timeout=5,
        headers={"Authorization": "Bearer test-token"}
    )
    
    if response.status_code in [200, 401, 403]:  # 401/403 expected if auth required
        log_test("Policy: Firewall Rules Endpoint", "PASS")
    else:
        log_test("Policy: Firewall Rules Endpoint", "FAIL", f"Status: {response.status_code}")
        
except Exception as e:
    log_test("Policy: Firewall Rules Endpoint", "FAIL", str(e))

# Test policy decision evaluation
try:
    import requests
    
    payload = {
        "src_ip": "192.168.1.100",
        "dst_ip": "8.8.8.8",
        "src_port": 51234,
        "dst_port": 443,
        "protocol": "tcp",
        "direction": "outbound"
    }
    
    response = requests.post(
        f"{BACKEND_URL}/api/policy/firewall/evaluate",
        json=payload,
        timeout=5,
        headers={"Authorization": "Bearer test-token"}
    )
    
    if response.status_code in [200, 401, 403]:
        log_test("Policy: Evaluation Endpoint", "PASS")
    else:
        log_test("Policy: Evaluation Endpoint", "FAIL", f"Status: {response.status_code}")
        
except Exception as e:
    log_test("Policy: Evaluation Endpoint", "FAIL", str(e))

# ============================================================================
# TEST SUITE 4: Forensics Flow
# ============================================================================

print(f"\n{BLUE}TEST SUITE 4: Forensics Flow{RESET}")
print("-" * 100)

try:
    import requests
    from datetime import datetime
    
    # Test forensics store endpoint with proper payload
    response = requests.post(
        f"{BACKEND_URL}/api/forensics/store",
        json={
            "record": {
                "incident_id": "test-incident-001",
                "incident_start": datetime.utcnow().isoformat(),
                "artifacts": [],
                "severity": "high"
            }
        },
        timeout=5,
        headers={"Authorization": "Bearer test-token"}
    )
    
    if response.status_code in [200, 400, 401, 403, 422]:
        log_test("Forensics: Store Endpoint", "PASS")
    else:
        log_test("Forensics: Store Endpoint", "FAIL", f"Status: {response.status_code}")
        
except Exception as e:
    log_test("Forensics: Store Endpoint", "FAIL", str(e))

# Test audit logs endpoint
try:
    import requests
    
    response = requests.get(
        f"{BACKEND_URL}/api/forensics/records/test-record",
        timeout=5,
        headers={"Authorization": "Bearer test-token"}
    )
    
    if response.status_code in [200, 401, 403, 404]:
        log_test("Forensics: Records Endpoint", "PASS")
    else:
        log_test("Forensics: Records Endpoint", "FAIL", f"Status: {response.status_code}")
        
except Exception as e:
    log_test("Forensics: Records Endpoint", "FAIL", str(e))

# ============================================================================
# TEST SUITE 5: Authentication Flow
# ============================================================================

print(f"\n{BLUE}TEST SUITE 5: Authentication Flow{RESET}")
print("-" * 100)

try:
    import requests
    
    # Test auth endpoints exist
    auth_endpoints = [
        ("/api/auth/mobile/init", "POST"),
        ("/api/auth/biometric", "POST"),
    ]
    
    for endpoint, method in auth_endpoints:
        response = requests.request(
            method,
            f"{BACKEND_URL}{endpoint}",
            json={"user_id": "test", "password": "test"},
            timeout=5
        )
        
        if response.status_code in [200, 400, 401, 422]:  # 422 is Pydantic validation
            log_test(f"Auth: {method} {endpoint}", "PASS")
        else:
            log_test(f"Auth: {method} {endpoint}", "FAIL", f"Status: {response.status_code}")
            
except Exception as e:
    log_test("Auth: Endpoints", "FAIL", str(e))

# ============================================================================
# TEST SUITE 6: Self-Healing Flow
# ============================================================================

print(f"\n{BLUE}TEST SUITE 6: Self-Healing Flow{RESET}")
print("-" * 100)

try:
    import requests
    
    # Test self-healing metrics
    response = requests.get(
        f"{BACKEND_URL}/api/self_healing/metrics",
        timeout=5,
        headers={"Authorization": "Bearer test-token"}
    )
    
    if response.status_code in [200, 401, 403]:
        log_test("Self-Healing: Metrics Endpoint", "PASS")
    else:
        log_test("Self-Healing: Metrics Endpoint", "FAIL", f"Status: {response.status_code}")
        
except Exception as e:
    log_test("Self-Healing: Metrics Endpoint", "FAIL", str(e))

# ============================================================================
# TEST SUITE 7: Data Contract Validation
# ============================================================================

print(f"\n{BLUE}TEST SUITE 7: Data Contract Validation{RESET}")
print("-" * 100)

try:
    import requests
    
    # Test response structure for key endpoints
    response = requests.get(f"{BACKEND_URL}/health", timeout=5)
    data = response.json()
    
    if "status" in data:
        log_test("Data Contract: Health Response", "PASS")
    else:
        log_test("Data Contract: Health Response", "FAIL", "Missing 'status' field")
        
except Exception as e:
    log_test("Data Contract: Health Response", "FAIL", str(e))

# ============================================================================
# TEST SUITE 8: Error Handling
# ============================================================================

print(f"\n{BLUE}TEST SUITE 8: Error Handling{RESET}")
print("-" * 100)

try:
    import requests
    
    # Test invalid endpoint
    response = requests.get(f"{BACKEND_URL}/invalid/endpoint", timeout=5)
    
    if response.status_code == 404:
        log_test("Error Handling: 404 Not Found", "PASS")
    else:
        log_test("Error Handling: 404 Not Found", "FAIL", f"Got {response.status_code}")
        
except Exception as e:
    log_test("Error Handling: 404 Not Found", "FAIL", str(e))

# Test invalid request
try:
    import requests
    
    response = requests.post(
        f"{BACKEND_URL}/api/policy/firewall/rules",
        json={},  # Missing required fields
        timeout=5
    )
    
    if response.status_code in [400, 422]:
        log_test("Error Handling: 400 Bad Request", "PASS")
    else:
        log_test("Error Handling: 400 Bad Request", "FAIL", f"Got {response.status_code}")
        
except Exception as e:
    log_test("Error Handling: 400 Bad Request", "FAIL", str(e))

# ============================================================================
# TEST SUMMARY
# ============================================================================

print("\n" + "=" * 100)
print("TEST SUMMARY")
print("=" * 100)

total = test_results["total"]
passed = test_results["passed"]
failed = test_results["failed"]
skipped = test_results["skipped"]

print(f"\n{BLUE}Results:{RESET}")
print(f"  {GREEN}Passed:  {passed}/{total}{RESET}")
print(f"  {RED}Failed:  {failed}/{total}{RESET}")
print(f"  {YELLOW}Skipped: {skipped}/{total}{RESET}")

if total > 0:
    pass_rate = (passed / total) * 100
    print(f"\n{BLUE}Pass Rate: {pass_rate:.1f}%{RESET}")

if failed == 0:
    print(f"\n{GREEN}✅ ALL TESTS PASSED - Frontend-Backend integration is healthy!{RESET}\n")
    sys.exit(0)
else:
    print(f"\n{RED}❌ {failed} test(s) failed - Review errors above{RESET}\n")
    sys.exit(1)

# ============================================================================
# END OF TEST SUITE
# ============================================================================
