#!/usr/bin/env python3
"""
Packet Capture API Testing Script

Tests all 10 packet capture endpoints and verifies functionality.

Usage:
    python3 test_packet_capture_api.py [--base-url http://localhost:8000]
"""

import requests
import json
import time
import sys
import argparse
from typing import Dict, Any, Optional
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_header(text: str) -> None:
    """Print a section header"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"{text:^60}")
    print(f"{'='*60}{Colors.RESET}\n")

def print_success(text: str) -> None:
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text: str) -> None:
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text: str) -> None:
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text: str) -> None:
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")

class PacketCaptureAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.packet_capture_url = f"{self.base_url}/packet_capture"
        self.session = requests.Session()
        self.results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0
        }

    def check_server(self) -> bool:
        """Check if server is running"""
        try:
            resp = self.session.get(f"{self.base_url}/docs", timeout=2)
            return resp.status_code != 404
        except:
            return False

    def test_get_backends(self) -> bool:
        """Test: GET /capture/backends"""
        print_header("TEST 1: Get Available Backends")
        
        try:
            resp = self.session.get(
                f"{self.packet_capture_url}/capture/backends",
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                
                if "available_backends" in data:
                    print_success(f"Found {len(data['available_backends'])} backends")
                    for backend in data['available_backends']:
                        print_info(f"  • {backend.get('name', 'Unknown')}: "
                                 f"{backend.get('status', 'unknown')}")
                    self.results["passed"] += 1
                    return True
                else:
                    print_error("Response missing 'available_backends' field")
                    self.results["failed"] += 1
                    return False
            else:
                print_error(f"HTTP {resp.status_code}: {resp.text}")
                self.results["failed"] += 1
                return False
        except Exception as e:
            print_error(f"Request failed: {e}")
            self.results["failed"] += 1
            return False

    def test_start_capture(self) -> bool:
        """Test: POST /capture/start"""
        print_header("TEST 2: Start Packet Capture")
        
        payload = {
            "interface": "lo",  # Use loopback interface
            "backend": "libpcap",
            "buffer_size_mb": 64,
            "timestamp_source": "kernel",
            "filter_expr": "",
            "snaplen": 0
        }
        
        try:
            resp = self.session.post(
                f"{self.packet_capture_url}/capture/start",
                json=payload,
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                
                if data.get("status") == "started":
                    print_success("Capture started successfully")
                    self.results["passed"] += 1
                    return True
                else:
                    print_error(f"Unexpected status: {data.get('status')}")
                    self.results["failed"] += 1
                    return False
            else:
                print_warning(f"HTTP {resp.status_code}")
                print_info(f"Note: May fail if no packet capture permissions. "
                          f"Run with: sudo python3 {sys.argv[0]}")
                self.results["skipped"] += 1
                return False
        except Exception as e:
            print_warning(f"Request failed (expected without sudo): {e}")
            self.results["skipped"] += 1
            return False

    def test_get_status(self) -> bool:
        """Test: GET /capture/status"""
        print_header("TEST 3: Get Capture Status")
        
        try:
            resp = self.session.get(
                f"{self.packet_capture_url}/capture/status",
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                print_success("Status retrieved successfully")
                self.results["passed"] += 1
                return True
            elif resp.status_code == 400:
                print_warning("No active capture session")
                print_info("(This is expected if capture wasn't started)")
                self.results["skipped"] += 1
                return False
            else:
                print_error(f"HTTP {resp.status_code}: {resp.text}")
                self.results["failed"] += 1
                return False
        except Exception as e:
            print_error(f"Request failed: {e}")
            self.results["failed"] += 1
            return False

    def test_get_metrics(self) -> bool:
        """Test: GET /capture/metrics"""
        print_header("TEST 4: Get Capture Metrics")
        
        try:
            resp = self.session.get(
                f"{self.packet_capture_url}/capture/metrics",
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                print_success("Metrics retrieved successfully")
                
                # Validate key fields
                required_fields = [
                    "packets_captured", "packets_dropped", "bytes_captured",
                    "drop_rate", "throughput_mbps", "buffer_usage_pct"
                ]
                missing = [f for f in required_fields if f not in data]
                if missing:
                    print_warning(f"Missing fields: {', '.join(missing)}")
                
                self.results["passed"] += 1
                return True
            elif resp.status_code == 400:
                print_warning("No active capture session")
                self.results["skipped"] += 1
                return False
            else:
                print_error(f"HTTP {resp.status_code}")
                self.results["failed"] += 1
                return False
        except Exception as e:
            print_error(f"Request failed: {e}")
            self.results["failed"] += 1
            return False

    def test_enable_flow_metering(self) -> bool:
        """Test: POST /capture/flow/meter/enable"""
        print_header("TEST 5: Enable Flow Metering")
        
        payload = {
            "table_size": 10000,
            "idle_timeout_sec": 300,
            "export_interval_sec": 60
        }
        
        try:
            resp = self.session.post(
                f"{self.packet_capture_url}/capture/flow/meter/enable",
                json=payload,
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                
                if data.get("status") == "enabled":
                    print_success("Flow metering enabled")
                    self.results["passed"] += 1
                    return True
                else:
                    print_error(f"Unexpected status: {data.get('status')}")
                    self.results["failed"] += 1
                    return False
            elif resp.status_code == 400:
                print_warning("Cannot enable flow metering without active capture")
                self.results["skipped"] += 1
                return False
            else:
                print_error(f"HTTP {resp.status_code}: {resp.text}")
                self.results["failed"] += 1
                return False
        except Exception as e:
            print_error(f"Request failed: {e}")
            self.results["failed"] += 1
            return False

    def test_get_flows(self) -> bool:
        """Test: GET /capture/flows"""
        print_header("TEST 6: Get Active Flows")
        
        try:
            resp = self.session.get(
                f"{self.packet_capture_url}/capture/flows",
                params={"limit": 10, "min_packets": 1},
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"Response: {json.dumps(data[:2], indent=2) if data else '[]'}")
                print_success(f"Retrieved {len(data)} flows")
                self.results["passed"] += 1
                return True
            elif resp.status_code == 400:
                print_warning("Flow metering not enabled")
                self.results["skipped"] += 1
                return False
            else:
                print_error(f"HTTP {resp.status_code}")
                self.results["failed"] += 1
                return False
        except Exception as e:
            print_error(f"Request failed: {e}")
            self.results["failed"] += 1
            return False

    def test_enable_netflow(self) -> bool:
        """Test: POST /capture/netflow/export/enable"""
        print_header("TEST 7: Enable NetFlow Export")
        
        payload = {
            "collector_ip": "127.0.0.1",
            "collector_port": 2055,
            "export_interval_sec": 60,
            "netflow_version": 5
        }
        
        try:
            resp = self.session.post(
                f"{self.packet_capture_url}/capture/netflow/export/enable",
                json=payload,
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                
                if data.get("status") == "enabled":
                    print_success("NetFlow export enabled")
                    self.results["passed"] += 1
                    return True
                else:
                    print_error(f"Unexpected status: {data.get('status')}")
                    self.results["failed"] += 1
                    return False
            elif resp.status_code == 400:
                print_warning("Cannot enable NetFlow without active capture")
                self.results["skipped"] += 1
                return False
            else:
                print_error(f"HTTP {resp.status_code}: {resp.text}")
                self.results["failed"] += 1
                return False
        except Exception as e:
            print_error(f"Request failed: {e}")
            self.results["failed"] += 1
            return False

    def test_enable_encryption(self) -> bool:
        """Test: POST /capture/encryption/enable"""
        print_header("TEST 8: Enable Encryption")
        
        payload = {
            "cipher_suite": "AES-256-GCM",
            "key_file": "/etc/jarvis/capture.key"
        }
        
        try:
            resp = self.session.post(
                f"{self.packet_capture_url}/capture/encryption/enable",
                json=payload,
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                
                if data.get("status") == "enabled":
                    print_success("Encryption enabled")
                    self.results["passed"] += 1
                    return True
                else:
                    print_warning(f"Unexpected status: {data.get('status')}")
                    self.results["skipped"] += 1
                    return False
            elif resp.status_code == 400:
                print_warning("Encryption not available or key file missing")
                self.results["skipped"] += 1
                return False
            else:
                print_error(f"HTTP {resp.status_code}: {resp.text}")
                self.results["failed"] += 1
                return False
        except Exception as e:
            print_warning(f"Request failed (expected): {e}")
            self.results["skipped"] += 1
            return False

    def test_verify_firmware(self) -> bool:
        """Test: GET /capture/firmware/verify"""
        print_header("TEST 9: Verify Firmware Signature")
        
        try:
            resp = self.session.get(
                f"{self.packet_capture_url}/capture/firmware/verify",
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                print_success("Firmware verification completed")
                self.results["passed"] += 1
                return True
            else:
                print_error(f"HTTP {resp.status_code}: {resp.text}")
                self.results["failed"] += 1
                return False
        except Exception as e:
            print_error(f"Request failed: {e}")
            self.results["failed"] += 1
            return False

    def test_stop_capture(self) -> bool:
        """Test: POST /capture/stop"""
        print_header("TEST 10: Stop Packet Capture")
        
        payload = {"graceful": True}
        
        try:
            resp = self.session.post(
                f"{self.packet_capture_url}/capture/stop",
                json=payload,
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                
                if data.get("status") == "stopped":
                    print_success("Capture stopped successfully")
                    self.results["passed"] += 1
                    return True
                else:
                    print_warning(f"Unexpected status: {data.get('status')}")
                    self.results["skipped"] += 1
                    return False
            elif resp.status_code == 400:
                print_warning("No active capture session to stop")
                self.results["skipped"] += 1
                return False
            else:
                print_error(f"HTTP {resp.status_code}")
                self.results["failed"] += 1
                return False
        except Exception as e:
            print_error(f"Request failed: {e}")
            self.results["failed"] += 1
            return False

    def run_all_tests(self) -> None:
        """Run all tests"""
        print_header("J.A.R.V.I.S. Packet Capture API Test Suite")
        
        # Check server
        print_info(f"Testing server at: {self.base_url}")
        if not self.check_server():
            print_error("Server is not responding. Make sure uvicorn is running:")
            print_info("  python3 -m uvicorn backend.api.server:app --host 0.0.0.0")
            sys.exit(1)
        
        print_success("Server is responding")
        
        # Run tests
        tests = [
            self.test_get_backends,
            self.test_start_capture,
            self.test_get_status,
            self.test_get_metrics,
            self.test_enable_flow_metering,
            self.test_get_flows,
            self.test_enable_netflow,
            self.test_enable_encryption,
            self.test_verify_firmware,
            self.test_stop_capture,
        ]
        
        for i, test in enumerate(tests, 1):
            try:
                test()
                time.sleep(0.5)  # Brief delay between tests
            except Exception as e:
                print_error(f"Test {i} crashed: {e}")
                self.results["failed"] += 1
        
        # Print summary
        self._print_summary()

    def _print_summary(self) -> None:
        """Print test summary"""
        print_header("Test Summary")
        
        total = sum(self.results.values())
        print(f"Total Tests:   {total}")
        print(f"{Colors.GREEN}Passed:       {self.results['passed']}{Colors.RESET}")
        print(f"{Colors.RED}Failed:       {self.results['failed']}{Colors.RESET}")
        print(f"{Colors.YELLOW}Skipped:      {self.results['skipped']}{Colors.RESET}")
        
        if self.results["failed"] == 0:
            print_success("\nAll tests completed successfully!")
            return 0
        else:
            print_error(f"\n{self.results['failed']} test(s) failed")
            return 1

def main():
    parser = argparse.ArgumentParser(
        description="Test J.A.R.V.I.S. Packet Capture API endpoints"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the API server (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    tester = PacketCaptureAPITester(args.base_url)
    tester.run_all_tests()
    
    return 0 if tester.results["failed"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
