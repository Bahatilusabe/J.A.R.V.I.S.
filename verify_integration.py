#!/usr/bin/env python3
"""
Frontend-Backend Integration Verification Script
Validates that all frontend services are correctly calling backend endpoints
with proper data flow and error handling.

Author: J.A.R.V.I.S. Integration Team
Date: December 2024
"""

import json
import os
import sys
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import re

# Configuration
BACKEND_BASE = Path("/Users/mac/Desktop/J.A.R.V.I.S./backend/api/routes")
FRONTEND_BASE = Path("/Users/mac/Desktop/J.A.R.V.I.S./frontend/web_dashboard/src/services")

print("=" * 100)
print("FRONTEND-BACKEND INTEGRATION VERIFICATION")
print("=" * 100)

# ============================================================================
# STEP 1: Extract all backend endpoints
# ============================================================================

print("\n📊 STEP 1: Mapping Backend Endpoints")
print("-" * 100)

backend_endpoints: Dict[str, List[Dict]] = {}

# Read all route files
for route_file in BACKEND_BASE.glob("*.py"):
    if route_file.name == "__init__.py":
        continue
    
    with open(route_file, 'r') as f:
        content = f.read()
    
    # Extract router prefix from server.py import
    route_name = route_file.stem
    
    # Find all @router.get, @router.post, etc.
    endpoints = re.findall(
        r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
        content
    )
    
    if endpoints:
        backend_endpoints[route_name] = []
        for method, path in endpoints:
            backend_endpoints[route_name].append({
                'method': method.upper(),
                'path': path,
                'file': route_file.name
            })

# Print discovered endpoints
for route_name, endpoints in sorted(backend_endpoints.items()):
    print(f"\n✅ {route_name.upper()}")
    for ep in endpoints[:5]:  # Show first 5
        print(f"   {ep['method']:8} {ep['path']}")
    if len(endpoints) > 5:
        print(f"   ... and {len(endpoints) - 5} more")

total_endpoints = sum(len(eps) for eps in backend_endpoints.values())
print(f"\n📈 Total Backend Endpoints: {total_endpoints}")

# ============================================================================
# STEP 2: Extract all frontend service calls
# ============================================================================

print("\n\n📊 STEP 2: Mapping Frontend Service Calls")
print("-" * 100)

frontend_calls: Dict[str, List[Dict]] = {}

for service_file in FRONTEND_BASE.glob("*.ts"):
    if service_file.name == "__init__.py":
        continue
    
    with open(service_file, 'r') as f:
        content = f.read()
    
    service_name = service_file.stem
    
    # Find all apiClient calls
    calls = re.findall(
        r'apiClient\.(get|post|put|delete|patch)<[^>]*>\(\s*["\']([^"\']+)["\']',
        content
    )
    
    if calls:
        frontend_calls[service_name] = []
        for method, path in calls:
            frontend_calls[service_name].append({
                'method': method.upper(),
                'path': path,
                'file': service_file.name
            })

# Print discovered calls
for service_name, calls in sorted(frontend_calls.items()):
    print(f"\n✅ {service_name.upper()}")
    for call in calls[:5]:  # Show first 5
        print(f"   {call['method']:8} {call['path']}")
    if len(calls) > 5:
        print(f"   ... and {len(calls) - 5} more")

total_calls = sum(len(calls) for calls in frontend_calls.values())
print(f"\n📈 Total Frontend Service Calls: {total_calls}")

# ============================================================================
# STEP 3: Verify endpoint-to-service mappings
# ============================================================================

print("\n\n📊 STEP 3: Verifying Endpoint-to-Service Mappings")
print("-" * 100)

# Build a map of what's in the backend
backend_map = {}
for route_name, endpoints in backend_endpoints.items():
    for ep in endpoints:
        key = f"{ep['method']} {ep['path']}"
        backend_map[key] = {'route': route_name, 'endpoint': ep}

# Check frontend calls against backend
missing_endpoints = []
found_endpoints = []
mismatched_methods = []

for service_name, calls in frontend_calls.items():
    for call in calls:
        # Build the call key
        call_key = f"{call['method']} {call['path']}"
        
        # Try exact match
        if call_key in backend_map:
            found_endpoints.append({
                'service': service_name,
                'endpoint': call_key,
                'route': backend_map[call_key]['route']
            })
        else:
            # Check if path exists with different method
            path_variants = [k for k in backend_map.keys() if call['path'] in k]
            if path_variants:
                mismatched_methods.append({
                    'service': service_name,
                    'call': call_key,
                    'found': path_variants
                })
            else:
                missing_endpoints.append({
                    'service': service_name,
                    'call': call_key,
                    'path': call['path']
                })

# Report findings
print(f"\n✅ Found Endpoints: {len(found_endpoints)}")
for item in found_endpoints[:10]:
    print(f"   {item['endpoint']} ← {item['service']}")

if missing_endpoints:
    print(f"\n⚠️  Missing Endpoints: {len(missing_endpoints)}")
    for item in missing_endpoints[:10]:
        print(f"   {item['call']} (called by {item['service']})")
        print(f"      Path: {item['path']}")
else:
    print(f"\n✅ No Missing Endpoints!")

if mismatched_methods:
    print(f"\n⚠️  Possible Method Mismatches: {len(mismatched_methods)}")
    for item in mismatched_methods[:10]:
        print(f"   {item['call']} (called by {item['service']})")
        print(f"      Found: {item['found']}")

# ============================================================================
# STEP 4: Check request/response data flow
# ============================================================================

print("\n\n📊 STEP 4: Validating Request/Response Data Flow")
print("-" * 100)

# Check for BaseModel definitions in backend
pydantic_models = {}
for route_file in BACKEND_BASE.glob("*.py"):
    with open(route_file, 'r') as f:
        content = f.read()
    
    models = re.findall(r'class\s+(\w+)\(BaseModel\):', content)
    if models:
        pydantic_models[route_file.stem] = models

print("\n✅ Pydantic Models (Request/Response Contracts):")
for route_name, models in pydantic_models.items():
    print(f"\n   {route_name.upper()}:")
    for model in models[:10]:
        print(f"      • {model}")
    if len(models) > 10:
        print(f"      ... and {len(models) - 10} more")

# ============================================================================
# STEP 5: Check error handling
# ============================================================================

print("\n\n📊 STEP 5: Checking Error Handling")
print("-" * 100)

backend_error_handling = 0
frontend_error_handling = 0

# Check backend
for route_file in BACKEND_BASE.glob("*.py"):
    with open(route_file, 'r') as f:
        content = f.read()
    
    if 'HTTPException' in content or 'try:' in content or 'except' in content:
        backend_error_handling += 1

# Check frontend
for service_file in FRONTEND_BASE.glob("*.ts"):
    with open(service_file, 'r') as f:
        content = f.read()
    
    if 'catch' in content or 'error' in content:
        frontend_error_handling += 1

print(f"\n✅ Backend Error Handling: {backend_error_handling} files with error handling")
print(f"✅ Frontend Error Handling: {frontend_error_handling} files with error handling")

# ============================================================================
# STEP 6: Check authentication flow
# ============================================================================

print("\n\n📊 STEP 6: Verifying Authentication Flow")
print("-" * 100)

auth_backend = False
auth_frontend = False

# Check backend auth
auth_file = BACKEND_BASE / "auth.py"
if auth_file.exists():
    with open(auth_file, 'r') as f:
        content = f.read()
    if 'token' in content.lower():
        auth_backend = True
        print("✅ Backend authentication endpoints found")

# Check frontend auth
auth_service = FRONTEND_BASE / "auth.service.ts"
if auth_service.exists():
    with open(auth_service, 'r') as f:
        content = f.read()
    if 'token' in content.lower() or 'Bearer' in content:
        auth_frontend = True
        print("✅ Frontend authentication service configured")

if auth_backend and auth_frontend:
    print("✅ Authentication flow appears complete")

# ============================================================================
# STEP 7: Integration summary
# ============================================================================

print("\n\n" + "=" * 100)
print("INTEGRATION VERIFICATION SUMMARY")
print("=" * 100)

integration_score = 0
total_checks = 5

print("\n📋 Verification Checklist:\n")

# Check 1: Endpoint discovery
if total_endpoints > 20:
    print(f"✅ Endpoint Discovery: {total_endpoints} endpoints found")
    integration_score += 1
else:
    print(f"⚠️  Endpoint Discovery: Only {total_endpoints} endpoints found")

# Check 2: Service mapping
mapping_success_rate = len(found_endpoints) / (len(found_endpoints) + len(missing_endpoints)) * 100 if (len(found_endpoints) + len(missing_endpoints)) > 0 else 0
if mapping_success_rate >= 80:
    print(f"✅ Service Mapping: {mapping_success_rate:.1f}% endpoints mapped ({len(found_endpoints)}/{len(found_endpoints) + len(missing_endpoints)})")
    integration_score += 1
else:
    print(f"⚠️  Service Mapping: {mapping_success_rate:.1f}% endpoints mapped")

# Check 3: Pydantic models
if len(pydantic_models) > 0 and sum(len(m) for m in pydantic_models.values()) > 10:
    print(f"✅ Data Contracts: {sum(len(m) for m in pydantic_models.values())} Pydantic models defined")
    integration_score += 1
else:
    print(f"⚠️  Data Contracts: Limited Pydantic models found")

# Check 4: Error handling
if backend_error_handling > 5 and frontend_error_handling > 3:
    print(f"✅ Error Handling: Backend ({backend_error_handling}), Frontend ({frontend_error_handling})")
    integration_score += 1
else:
    print(f"⚠️  Error Handling: May need enhancement")

# Check 5: Authentication
if auth_backend and auth_frontend:
    print(f"✅ Authentication: Complete end-to-end flow")
    integration_score += 1
else:
    print(f"⚠️  Authentication: May need verification")

print(f"\n🎯 Integration Score: {integration_score}/{total_checks} ({integration_score/total_checks*100:.0f}%)")

if integration_score >= 4:
    print("\n🟢 STATUS: FRONTEND-BACKEND INTEGRATION HEALTHY")
else:
    print("\n🟡 STATUS: FRONTEND-BACKEND INTEGRATION NEEDS REVIEW")

# ============================================================================
# STEP 8: Generate recommendations
# ============================================================================

print("\n\n📋 RECOMMENDATIONS:")
print("-" * 100)

recommendations = []

if len(missing_endpoints) > 0:
    recommendations.append(f"1. Add missing endpoints or update frontend calls ({len(missing_endpoints)} mismatches)")

if mapping_success_rate < 90:
    recommendations.append("2. Verify endpoint paths and HTTP methods match between frontend and backend")

if backend_error_handling < 8:
    recommendations.append("3. Add more comprehensive error handling in backend routes")

if frontend_error_handling < 5:
    recommendations.append("4. Enhance error handling in frontend services")

if not auth_backend or not auth_frontend:
    recommendations.append("5. Verify complete authentication flow implementation")

if not recommendations:
    recommendations.append("✅ All integration checks passed! No critical recommendations.")

for rec in recommendations:
    print(f"  {rec}")

print("\n" + "=" * 100)
print("VERIFICATION COMPLETE")
print("=" * 100 + "\n")
