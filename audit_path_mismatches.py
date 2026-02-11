#!/usr/bin/env python3
"""
Path Mismatch Audit Script

Systematically audits all frontend service calls against backend endpoints
to identify and document path, method, and parameter mismatches.

Usage:
    python3 audit_path_mismatches.py

Author: J.A.R.V.I.S. Integration Team
Date: December 2024
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def extract_backend_endpoints() -> Dict[str, List[Dict]]:
    """Extract all backend endpoints from route files

    This attempts two strategies:
      1) Detect router prefix inside each route file (APIRouter(prefix="/..."))
      2) Parse backend/api/server.py for app.include_router(var.router, prefix="/api/...")

    The server.py mapping takes precedence if present so the audit reflects the
    actual registered API paths seen by the frontend.
    """
    endpoints = defaultdict(list)
    routes_dir = Path("/Users/mac/Desktop/J.A.R.V.I.S./backend/api/routes")
    server_py = Path("/Users/mac/Desktop/J.A.R.V.I.S./backend/api/server.py")

    # Patterns to match FastAPI decorators
    decorator_pattern = r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
    router_prefix_pattern = r"router\s*=\s*APIRouter\s*\(.*?prefix\s*=\s*[\"']([^\"']+)[\"']"

    # Parse server.py include_router mappings: var_name -> prefix
    include_router_map: Dict[str, str] = {}
    try:
        if server_py.exists():
            srv_text = server_py.read_text()
            include_pattern = re.compile(r"app\.include_router\(\s*([a-zA-Z0-9_]+)\.router\s*,\s*prefix\s*=\s*[\"']([^\"']+)[\"']")
            for m in include_pattern.finditer(srv_text):
                include_router_map[m.group(1)] = m.group(2)
    except Exception:
        # best-effort: continue without server mapping
        include_router_map = {}

    for route_file in routes_dir.glob("*.py"):
        if route_file.name == "__pycache__":
            continue

        try:
            content = route_file.read_text()

            # try to detect router prefix (APIRouter(prefix="/dpi") style)
            prefix_match = re.search(router_prefix_pattern, content, flags=re.S)
            if prefix_match:
                router_prefix = prefix_match.group(1)
            else:
                # fallback: if server.py included this module with a prefix, use it
                module_var = route_file.stem
                if module_var in include_router_map:
                    router_prefix = include_router_map[module_var]
                else:
                    # fallback to module name as used previously
                    router_prefix = f"/{route_file.stem}"

            matches = re.finditer(decorator_pattern, content)
            for match in matches:
                method = match.group(1).upper()
                path = match.group(2)
                # normalize path join
                full = router_prefix.rstrip('/') + ('/' + path.lstrip('/')) if path else router_prefix

                module = route_file.stem
                full_path = f"/api{full}" if not str(full).startswith('/api') else full
                endpoints[module].append({
                    "method": method,
                    "path": path,
                    "full_path": full_path
                })
        except Exception as e:
            print(f"Error reading {route_file}: {e}")

    return dict(endpoints)

def extract_frontend_service_calls() -> Dict[str, List[Dict]]:
    """Extract all API calls from frontend services"""
    calls = defaultdict(list)
    services_dir = Path("/Users/mac/Desktop/J.A.R.V.I.S./frontend/web_dashboard/src/services")
    
    # Patterns for API calls
    patterns = [
        r'this\.api\.(?:get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
        r'\.(?:get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
        r'fetch\s*\(\s*["\']([^"\']+)["\']',
    ]
    
    for service_file in services_dir.glob("*.ts"):
        if service_file.name == "__pycache__":
            continue
            
        try:
            with open(service_file, 'r') as f:
                content = f.read()
                service_name = service_file.stem
                
                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        endpoint = match.group(1)
                        # Extract method from context
                        start = max(0, match.start() - 50)
                        context = content[start:match.end()]
                        method = "GET"  # Default
                        if "post" in context.lower():
                            method = "POST"
                        elif "put" in context.lower():
                            method = "PUT"
                        elif "delete" in context.lower():
                            method = "DELETE"
                        
                        calls[service_name].append({
                            "method": method,
                            "endpoint": endpoint,
                            "line": content[:match.start()].count('\n') + 1
                        })
        except Exception as e:
            print(f"Error reading {service_file}: {e}")
    
    return dict(calls)

def audit_endpoints():
    """Perform comprehensive audit"""
    print("\n" + "=" * 120)
    print("FRONTEND-BACKEND ENDPOINT AUDIT")
    print("=" * 120 + "\n")
    
    # Extract endpoints and calls
    backend_endpoints = extract_backend_endpoints()
    frontend_calls = extract_frontend_service_calls()
    
    # Build lookup tables
    all_backend_paths = set()
    for module, endpoints in backend_endpoints.items():
        for ep in endpoints:
            all_backend_paths.add(ep["full_path"])
    
    # Count statistics
    total_backend = sum(len(eps) for eps in backend_endpoints.values())
    total_frontend = sum(len(calls) for calls in frontend_calls.values())
    
    print(f"{BLUE}Summary:{RESET}")
    print(f"  Backend Endpoints:   {total_backend}")
    print(f"  Frontend API Calls:  {total_frontend}")
    print()
    
    # Audit by backend module
    print(f"{BLUE}Backend Endpoints by Module:{RESET}")
    print("-" * 120)
    
    for module in sorted(backend_endpoints.keys()):
        endpoints = backend_endpoints[module]
        print(f"\n{YELLOW}{module}:{RESET} ({len(endpoints)} endpoints)")
        
        for ep in sorted(endpoints, key=lambda x: x["path"]):
            print(f"  {ep['method']:6s} {ep['full_path']}")
    
    # Audit by frontend service
    print(f"\n{BLUE}Frontend Service Calls:{RESET}")
    print("-" * 120)
    
    matched = 0
    mismatched = 0
    
    for service in sorted(frontend_calls.keys()):
        calls = frontend_calls[service]
        print(f"\n{YELLOW}{service}:{RESET} ({len(calls)} calls)")
        
        for call in sorted(calls, key=lambda x: x["endpoint"]):
            endpoint = call["endpoint"]
            method = call["method"]
            
            # Check if endpoint exists
            is_match = False
            for path in all_backend_paths:
                if endpoint in path or path in endpoint:
                    is_match = True
                    break
            
            if is_match:
                print(f"  {GREEN}✓{RESET} {method:6s} {endpoint}")
                matched += 1
            else:
                print(f"  {RED}✗{RESET} {method:6s} {endpoint}")
                mismatched += 1
    
    # Summary
    print("\n" + "=" * 120)
    print(f"{BLUE}Audit Results:{RESET}")
    print(f"  Matched:    {matched} endpoints")
    print(f"  Mismatched: {mismatched} endpoints")
    if total_frontend > 0:
        match_rate = (matched / total_frontend) * 100
        print(f"  Match Rate: {match_rate:.1f}%")
    print("=" * 120 + "\n")

if __name__ == "__main__":
    audit_endpoints()
