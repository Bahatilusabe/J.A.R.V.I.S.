# DPI ↔ IAM ↔ Firewall Integration Guide

**Complete data flow showing how DPI classifications, IAM identity assertions, and admin policy definitions integrate with the Stateful Firewall & Policy Engine.**

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Input Sources](#input-sources)
3. [Integration Flow](#integration-flow)
4. [API Endpoints](#api-endpoints)
5. [Usage Examples](#usage-examples)
6. [Advanced Patterns](#advanced-patterns)
7. [Testing & Validation](#testing--validation)
8. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INCOMING NETWORK FLOW                        │
│               (Packet arrives at network interface)                 │
└─────────────────┬───────────────────────────────────────────────────┘
                  │
                  ├──────────────────────────────────────────┐
                  │                                          │
                  ▼                                          ▼
        ┌────────────────────┐                    ┌────────────────────┐
        │   [1] DPI Engine   │                    │  [2] IAM System    │
        │                    │                    │                    │
        │ Input: Packet data │                    │ Input: User ID     │
        │ Output: {          │                    │ Output: {          │
        │   app_name: "...",│                    │   username: "...", │
        │   category: "...",│                    │   user_role: "...",│
        │   protocol: "...",│                    │   groups: [...],   │
        │   confidence: 95, │                    │   location: "...", │
        │   risk_score: 10, │                    │   device_id: "...",│
        │   anomalies: [...]│                    │   mfa_verified: T, │
        │ }                  │                    │   clearance: "..." │
        │                    │                    │ }                  │
        └────────┬───────────┘                    └────────┬───────────┘
                 │                                         │
                 └──────────────────┬──────────────────────┘
                                    │
                                    ▼
                ┌───────────────────────────────────────┐
                │  [3] Policy Context Builder           │
                │                                       │
                │ Combines:                            │
                │ - Network layer (IP/port/protocol)   │
                │ - Application layer (DPI)            │
                │ - Identity layer (IAM)               │
                │                                       │
                │ Output: Comprehensive context dict   │
                └───────────────────┬───────────────────┘
                                    │
                                    ▼
                ┌───────────────────────────────────────┐
                │  [4] Admin Policy Engine              │
                │                                       │
                │ Evaluates policies in priority order:│
                │ - Policy A (priority 100)            │
                │ - Policy B (priority 90)             │
                │ - Policy C (priority 50)             │
                │                                       │
                │ Returns: First matching policy       │
                │ with suggested action                │
                └───────────────────┬───────────────────┘
                                    │
                                    ▼
                ┌───────────────────────────────────────┐
                │  [5] Firewall Engine                  │
                │                                       │
                │ Actions:                             │
                │ - PASS (allow)                       │
                │ - DROP (block)                       │
                │ - RATE_LIMIT                        │
                │ - REDIRECT                          │
                │ - QUARANTINE                        │
                │ - REJECT                            │
                │                                       │
                │ Optional enforcement:                │
                │ - NAT translation                    │
                │ - QoS marking                        │
                │ - Connection tracking                │
                │ - Logging/metrics                    │
                └───────────────────┬───────────────────┘
                                    │
                                    ▼
                        ┌───────────────────┐
                        │    NETWORK ACTION │
                        │ (Allow/Drop/etc.) │
                        └───────────────────┘
```

### Component Interactions

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   DPI Engine     │────▶│ Policy Context   │◀────│   IAM System     │
│  (Classification)│     │   (Integration)  │     │  (Assertions)    │
└──────────────────┘     └────────┬─────────┘     └──────────────────┘
                                  │
                                  ▼
                        ┌──────────────────┐
                        │  Admin Policies  │
                        │   (Evaluation)   │
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │ Firewall Engine  │
                        │  (Enforcement)   │
                        └──────────────────┘
```

---

## Input Sources

### 1. DPI Classifications (from DPI Engine)

**Purpose**: Provide Layer 7 application-level insight into traffic

**Data Structure** (`DPIClassification`):

```python
{
    "app_name": str,              # e.g., "Spotify", "Chrome", "BitTorrent"
    "category": str,              # e.g., "Video Streaming", "P2P", "Web Browsing"
    "protocol": str,              # e.g., "HTTP", "HTTPS", "DNS", "QUIC"
    "confidence": int,            # 0-100, how certain is this classification?
    "detection_tick": int,        # Packet number when detected
    "is_encrypted": bool,         # Whether traffic is encrypted
    "is_tunneled": bool,          # Whether traffic is tunneled/proxied
    "risk_score": int,            # 0-100, how risky is this traffic?
    "detected_anomalies": List[str],  # e.g., ["suspicious_pattern", "large_upload"]
}
```

**Example Classifications**:

```python
# Example 1: Spotify streaming
{
    "app_name": "Spotify",
    "category": "Video Streaming",
    "protocol": "QUIC",
    "confidence": 98,
    "detection_tick": 47,
    "is_encrypted": True,
    "risk_score": 5,
    "detected_anomalies": [],
}

# Example 2: Suspicious torrent traffic
{
    "app_name": "BitTorrent",
    "category": "P2P",
    "protocol": "BitTorrent",
    "confidence": 92,
    "detection_tick": 150,
    "is_encrypted": False,
    "risk_score": 75,
    "detected_anomalies": ["unusual_peer_distribution", "rapid_connection_attempts"],
}

# Example 3: DNS query with anomaly
{
    "app_name": "DNS Query",
    "category": "DNS",
    "protocol": "DNS",
    "confidence": 99,
    "detection_tick": 3,
    "is_encrypted": False,
    "risk_score": 40,
    "detected_anomalies": ["dns_tunneling_detected", "high_entropy_domain"],
}
```

**Where it comes from**: DPI Engine (`backend/dpi_engine_py.py`)

---

### 2. IAM Identity Assertions (from IAM System)

**Purpose**: Provide identity and authorization context for the user/device

**Data Structure** (`IAMIdentityAssertion`):

```python
{
    "user_id": str,                    # Unique identifier
    "username": str,                   # Human-readable username
    "user_role": str,                  # e.g., "admin", "employee", "contractor"
    "user_groups": List[str],          # e.g., ["engineers", "vpn_users"]
    "organization_unit": Optional[str], # e.g., "Engineering", "Finance"
    "location": Optional[str],         # e.g., "office", "remote", "branch_office"
    "device_id": Optional[str],        # Device identifier
    "device_type": Optional[str],      # e.g., "laptop", "phone", "tablet", "printer"
    "is_mfa_verified": bool,           # Whether MFA was completed
    "permission_level": int,           # 0-100, higher = more privileged
    "clearance_level": Optional[str],  # e.g., "public", "internal", "confidential", "secret"
    "restrictions": List[str],         # e.g., ["vpn_only", "office_hours_only"]
}
```

**Example Assertions**:

```python
# Example 1: Regular employee from office
{
    "user_id": "emp_12345",
    "username": "alice.smith",
    "user_role": "employee",
    "user_groups": ["engineers", "vpn_users"],
    "organization_unit": "Engineering",
    "location": "office",
    "device_id": "laptop_001",
    "device_type": "laptop",
    "is_mfa_verified": True,
    "permission_level": 60,
    "clearance_level": "internal",
    "restrictions": [],
}

# Example 2: Contractor from remote
{
    "user_id": "ctr_67890",
    "username": "bob.jones",
    "user_role": "contractor",
    "user_groups": ["external_partners"],
    "organization_unit": "Consulting",
    "location": "remote",
    "device_id": "laptop_ext_002",
    "device_type": "laptop",
    "is_mfa_verified": True,
    "permission_level": 30,
    "clearance_level": "public",
    "restrictions": ["vpn_only", "office_hours_only"],
}

# Example 3: Admin from office
{
    "user_id": "adm_11111",
    "username": "carol.admin",
    "user_role": "admin",
    "user_groups": ["admins", "security_team"],
    "organization_unit": "IT Security",
    "location": "office",
    "device_id": "laptop_admin_001",
    "device_type": "laptop",
    "is_mfa_verified": True,
    "permission_level": 95,
    "clearance_level": "confidential",
    "restrictions": [],
}
```

**Where it comes from**: IAM System / Zero-Trust Device (via `backend/core/tds.py`)

---

### 3. Admin Policy Definitions

**Purpose**: Define security policies that combine network, application, and identity contexts

**Data Structure** (`AdminPolicy`):

```python
{
    "policy_id": str,              # Unique identifier
    "name": str,                   # Human-readable name
    "description": str,            # Policy description
    "conditions": List[PolicyCondition],  # Rules to match
    "condition_logic": str,        # "ALL" (AND) or "ANY" (OR)
    "action": str,                 # "pass", "drop", "rate_limit", "quarantine", "redirect"
    "action_params": Dict[str, Any],     # Action-specific parameters
    "priority": int,               # 0-255, higher = evaluated first
    "enabled": bool,               # Whether policy is active
}
```

**Condition Structure** (`PolicyCondition`):

```python
{
    "match_type": str,   # "network", "application", "identity", "device", "location", "behavioral"
    "field": str,        # Field name to match (e.g., "dpi_category", "user_role")
    "operator": str,     # "eq", "ne", "contains", "in", "not_in", "gt", "gte", "lt", "lte", "regex"
    "value": Any,        # Value to match against
}
```

---

## Integration Flow

### Step-by-Step Flow

#### **Step 1: Network Packet Arrives**

A packet or flow tuple arrives at the firewall:

```
Source: 192.168.1.100:51234
Destination: 10.0.0.50:443
Protocol: TCP
```

#### **Step 2: DPI Classification**

The DPI engine classifies the packet/flow:

```http
GET /dpi/classify
Body: {packet_data, flow_tuple}

Returns:
{
    "app_name": "Spotify",
    "category": "Video Streaming",
    "protocol": "HTTPS",
    "confidence": 95,
    "detection_tick": 47,
    "risk_score": 5,
    ...
}
```

#### **Step 3: IAM Lookup**

The IAM system retrieves the user's identity:

```http
GET /auth/user/{user_id}

Returns:
{
    "user_id": "user123",
    "username": "alice.smith",
    "user_role": "employee",
    "user_groups": ["engineers"],
    "location": "office",
    "device_type": "laptop",
    "is_mfa_verified": true,
    ...
}
```

#### **Step 4: Context Building**

The integration engine builds a comprehensive context:

```python
context = {
    # Network layer
    "src_ip": "192.168.1.100",
    "src_port": 51234,
    "dst_ip": "10.0.0.50",
    "dst_port": 443,
    "protocol": "tcp",
    
    # DPI layer
    "app_name": "Spotify",
    "dpi_category": "Video Streaming",
    "dpi_confidence": 95,
    "risk_score": 5,
    
    # Identity layer
    "user_id": "user123",
    "username": "alice.smith",
    "user_role": "employee",
    "location": "office",
    "device_type": "laptop",
    "is_mfa_verified": True,
}
```

#### **Step 5: Policy Matching**

Policies are evaluated in priority order:

```
Rule 1 (Priority 100): Block P2P category
  - Condition: app_category == "P2P"
  - Match: NO (app is "Video Streaming")

Rule 2 (Priority 90): Rate-limit Video Streaming to 5 Mbps
  - Condition: app_category == "Video Streaming"
  - Match: YES ← SELECTED

Rule 3 (Priority 50): Allow office users
  - Condition: location == "office"
  - Not evaluated (Rule 2 already matched)
```

#### **Step 6: Action Enforcement**

The selected policy is enforced:

```
Action: "rate_limit"
Parameters: {"rate_limit_kbps": 5000}

Firewall enforces:
- Allow traffic
- Apply QoS marking
- Enforce rate limit at 5 Mbps
```

---

## API Endpoints

### 1. Flow Evaluation with Full Context

**POST** `/policy/integration/evaluate-with-context`

Evaluate a flow with DPI + IAM context and get the suggested policy decision.

**Request**:

```bash
curl -X POST http://localhost:8000/policy/integration/evaluate-with-context \
  -H "Content-Type: application/json" \
  -d '{
    "src_ip": "192.168.1.100",
    "dst_ip": "10.0.0.50",
    "src_port": 51234,
    "dst_port": 443,
    "protocol": "tcp",
    "dpi_classification": {
      "app_name": "Spotify",
      "category": "Video Streaming",
      "protocol": "HTTPS",
      "confidence": 95,
      "detection_tick": 47,
      "is_encrypted": true,
      "is_tunneled": false,
      "risk_score": 5,
      "detected_anomalies": []
    },
    "iam_assertion": {
      "user_id": "user123",
      "username": "alice.smith",
      "user_role": "employee",
      "user_groups": ["engineers"],
      "organization_unit": "Engineering",
      "location": "office",
      "device_id": "laptop001",
      "device_type": "laptop",
      "is_mfa_verified": true,
      "permission_level": 60,
      "clearance_level": "internal",
      "restrictions": []
    }
  }'
```

**Response** (200 OK):

```json
{
  "status": "success",
  "flow": {
    "src_ip": "192.168.1.100",
    "src_port": 51234,
    "dst_ip": "10.0.0.50",
    "dst_port": 443,
    "protocol": "tcp"
  },
  "context": {
    "src_ip": "192.168.1.100",
    "app_name": "Spotify",
    "user_role": "employee",
    "location": "office",
    ...
  },
  "matching_policy": {
    "policy_id": "rate_limit_abc123",
    "name": "Rate limit Video Streaming",
    "action": "rate_limit",
    "action_params": {"rate_limit_kbps": 5000},
    "priority": 90
  },
  "suggested_action": "rate_limit",
  "action_parameters": {"rate_limit_kbps": 5000},
  "matching_policies_count": 3,
  "timestamp": "2025-12-10T14:30:00.000000"
}
```

---

### 2. Add Admin Policy

**POST** `/policy/integration/policies/add`

Add a new policy to the integration engine.

**Request**:

```bash
curl -X POST http://localhost:8000/policy/integration/policies/add \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Block Torrent",
    "description": "Block all BitTorrent traffic by category",
    "conditions": [
      {
        "match_type": "application",
        "field": "dpi_category",
        "operator": "eq",
        "value": "P2P"
      },
      {
        "match_type": "application",
        "field": "app_name",
        "operator": "contains",
        "value": "Torrent"
      }
    ],
    "condition_logic": "ANY",
    "action": "drop",
    "priority": 100
  }'
```

**Response** (200 OK):

```json
{
  "status": "success",
  "policy_id": "policy_abc12345",
  "message": "Policy 'Block Torrent' added with priority 100",
  "policy": {
    "policy_id": "policy_abc12345",
    "name": "Block Torrent",
    "description": "Block all BitTorrent traffic by category",
    "conditions": [...],
    "condition_logic": "ANY",
    "action": "drop",
    "priority": 100,
    "enabled": true,
    "created_at": "2025-12-10T14:30:00"
  }
}
```

---

### 3. List Admin Policies

**GET** `/policy/integration/policies/list`

List all policies currently loaded, sorted by priority.

**Response** (200 OK):

```json
{
  "status": "success",
  "count": 5,
  "policies": [
    {
      "policy_id": "policy_100",
      "name": "Block Torrent",
      "priority": 100,
      "action": "drop",
      "enabled": true
    },
    {
      "policy_id": "policy_90",
      "name": "Rate limit Video Streaming",
      "priority": 90,
      "action": "rate_limit",
      "enabled": true
    },
    ...
  ]
}
```

---

### 4. Remove Admin Policy

**DELETE** `/policy/integration/policies/{policy_id}`

Remove a policy by ID.

```bash
curl -X DELETE http://localhost:8000/policy/integration/policies/policy_abc12345
```

**Response** (200 OK):

```json
{
  "status": "success",
  "message": "Policy policy_abc12345 removed"
}
```

---

### 5. Policy Templates

Quick-create common policies:

#### 5a. Block Application

**POST** `/policy/integration/policies/templates/block-application?app_name={app_name}`

```bash
curl -X POST "http://localhost:8000/policy/integration/policies/templates/block-application?app_name=Spotify"
```

#### 5b. Block Category

**POST** `/policy/integration/policies/templates/block-category?category={category}`

```bash
curl -X POST "http://localhost:8000/policy/integration/policies/templates/block-category?category=P2P"
```

#### 5c. Rate Limit

**POST** `/policy/integration/policies/templates/rate-limit?category={category}&rate_limit_kbps={rate_limit_kbps}`

```bash
curl -X POST "http://localhost:8000/policy/integration/policies/templates/rate-limit?category=Video%20Streaming&rate_limit_kbps=5000"
```

#### 5d. High-Risk Quarantine

**POST** `/policy/integration/policies/templates/high-risk-quarantine`

```bash
curl -X POST "http://localhost:8000/policy/integration/policies/templates/high-risk-quarantine"
```

#### 5e. Contractor Restriction

**POST** `/policy/integration/policies/templates/contractor-restriction`

```bash
curl -X POST "http://localhost:8000/policy/integration/policies/templates/contractor-restriction"
```

---

## Usage Examples

### Example 1: Block Torrent Traffic

**Scenario**: Block all BitTorrent traffic, but only for non-admin users

**Step 1: Create the policy**

```bash
curl -X POST http://localhost:8000/policy/integration/policies/add \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Block Torrent for non-admins",
    "description": "Block P2P/Torrent traffic except for admin users",
    "conditions": [
      {
        "match_type": "application",
        "field": "dpi_category",
        "operator": "eq",
        "value": "P2P"
      },
      {
        "match_type": "identity",
        "field": "user_role",
        "operator": "ne",
        "value": "admin"
      }
    ],
    "condition_logic": "ALL",
    "action": "drop",
    "priority": 100
  }'
```

**Step 2: Evaluate a torrent flow from a regular employee**

```bash
curl -X POST http://localhost:8000/policy/integration/evaluate-with-context \
  -H "Content-Type: application/json" \
  -d '{
    "src_ip": "192.168.1.100",
    "dst_ip": "10.0.0.1",
    "src_port": 51234,
    "dst_port": 6881,
    "protocol": "tcp",
    "dpi_classification": {
      "app_name": "BitTorrent",
      "category": "P2P",
      "protocol": "BitTorrent",
      "confidence": 95,
      "detection_tick": 150,
      "risk_score": 75
    },
    "iam_assertion": {
      "user_id": "user123",
      "username": "alice.smith",
      "user_role": "employee",
      "location": "office",
      "is_mfa_verified": true
    }
  }'
```

**Result**: Policy matches → Action: "drop" → Flow is blocked

**Step 3: Evaluate the same torrent flow from an admin**

```bash
# Same request, but with user_role: "admin"
```

**Result**: Policy does NOT match (user_role != ne admin) → Default action: "pass"

---

### Example 2: Rate Limit Video Streaming

**Scenario**: Allow video streaming during work hours, rate-limit it to 5 Mbps during off-hours

**Step 1: Create rate-limit policy**

```bash
curl -X POST http://localhost:8000/policy/integration/policies/templates/rate-limit \
  -X POST "http://localhost:8000/policy/integration/policies/templates/rate-limit?category=Video%20Streaming&rate_limit_kbps=5000"
```

**Step 2: Evaluate a video stream during work hours**

```bash
curl -X POST http://localhost:8000/policy/integration/evaluate-with-context \
  -H "Content-Type: application/json" \
  -d '{
    "src_ip": "192.168.1.100",
    "dst_ip": "streaming.example.com",
    "src_port": 54321,
    "dst_port": 443,
    "protocol": "tcp",
    "dpi_classification": {
      "app_name": "Netflix",
      "category": "Video Streaming",
      "confidence": 98,
      "risk_score": 5
    },
    "iam_assertion": {
      "user_id": "user123",
      "username": "alice.smith",
      "user_role": "employee"
    }
  }'
```

**Result**: 
- Policy matches
- Suggested action: "rate_limit" 
- Action parameters: {"rate_limit_kbps": 5000}
- Firewall will apply 5 Mbps rate limit to this flow

---

### Example 3: Contractor Access Restrictions

**Scenario**: Contractors can only access the network from the office VPN

**Step 1: Create contractor policy**

```bash
curl -X POST http://localhost:8000/policy/integration/policies/templates/contractor-restriction
```

**Step 2: Evaluate contractor from office VPN**

```bash
curl -X POST http://localhost:8000/policy/integration/evaluate-with-context \
  -H "Content-Type: application/json" \
  -d '{
    "src_ip": "10.200.0.50",
    "dst_ip": "192.168.100.50",
    "src_port": 443,
    "dst_port": 443,
    "iam_assertion": {
      "user_id": "ctr_001",
      "username": "bob.contractor",
      "user_role": "contractor",
      "location": "office"
    }
  }'
```

**Result**: Location is "office" → No match → Default action: "pass" → Allowed

**Step 3: Evaluate contractor from remote location**

```bash
# Same request, but with location: "remote"
```

**Result**: Role is "contractor" AND location != "office" → Policy matches → Action: "drop" → Blocked

---

### Example 4: Multi-Condition Policy

**Scenario**: Prevent data exfiltration: Block large uploads (>100MB) to external IPs from confidential data holders

```bash
curl -X POST http://localhost:8000/policy/integration/policies/add \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prevent data exfiltration",
    "description": "Block large uploads from classified data holders to external IPs",
    "conditions": [
      {
        "match_type": "application",
        "field": "app_name",
        "operator": "in",
        "value": ["FileTransfer", "SFTP", "S3Client", "Dropbox"]
      },
      {
        "match_type": "identity",
        "field": "clearance_level",
        "operator": "in",
        "value": ["confidential", "secret"]
      },
      {
        "match_type": "network",
        "field": "dst_ip",
        "operator": "regex",
        "value": "^(8|9|[0-9]{2,3})\\..*"
      }
    ],
    "condition_logic": "ALL",
    "action": "drop",
    "priority": 150
  }'
```

---

## Advanced Patterns

### Pattern 1: Risk-Based Quarantine

Automatically quarantine traffic with high anomaly scores:

```bash
curl -X POST http://localhost:8000/policy/integration/policies/add \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Auto-quarantine high-risk traffic",
    "conditions": [
      {
        "match_type": "behavioral",
        "field": "risk_score",
        "operator": "gte",
        "value": 80
      }
    ],
    "condition_logic": "ANY",
    "action": "quarantine",
    "priority": 200
  }'
```

### Pattern 2: Device-Type Restrictions

Allow cloud access only from managed laptops:

```bash
curl -X POST http://localhost:8000/policy/integration/policies/add \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cloud access from managed devices only",
    "conditions": [
      {
        "match_type": "application",
        "field": "app_name",
        "operator": "in",
        "value": ["AWS SDK", "Azure SDK", "GCP SDK"]
      },
      {
        "match_type": "device",
        "field": "device_type",
        "operator": "not_in",
        "value": ["laptop"]
      }
    ],
    "condition_logic": "ALL",
    "action": "drop",
    "priority": 120
  }'
```

### Pattern 3: Time-Aware Policies

Combine with application timestamp to create time-based restrictions:

```bash
# Policy: Block social media during business hours
# Condition: app_category == "Social Media" AND user_role == "employee"
# Implementation: Add timestamp check in your client code
```

---

## Testing & Validation

### Test Case 1: Basic DPI Classification Matching

```python
# backend/tests/test_integration.py

def test_dpi_application_blocking():
    """Test that DPI classification triggers policy matching"""
    integration = FirewallDPIIAMIntegration()
    
    # Add policy: Block Spotify
    policy = create_block_application_policy("Spotify")
    integration.add_admin_policy(policy)
    
    # Create DPI classification
    dpi = DPIClassification(
        app_name="Spotify",
        category="Video Streaming",
        protocol="HTTPS",
        confidence=95,
        detection_tick=50,
        risk_score=5,
    )
    
    # Build context
    context = integration.build_policy_context(
        src_ip="192.168.1.100",
        dst_ip="10.0.0.50",
        src_port=54321,
        dst_port=443,
        protocol="tcp",
        dpi_classification=dpi,
    )
    
    # Evaluate
    matching_policy, action, params = integration.evaluate_policies(context)
    
    # Assert
    assert matching_policy is not None
    assert matching_policy.name == "Block Spotify"
    assert action == "drop"
```

### Test Case 2: IAM-Based Access Control

```python
def test_contractor_office_restriction():
    """Test that IAM role + location restricts contractor access"""
    integration = FirewallDPIIAMIntegration()
    
    # Add policy
    policy = create_contractor_policy()
    integration.add_admin_policy(policy)
    
    # Create IAM assertion
    iam = IAMIdentityAssertion(
        user_id="ctr_001",
        username="contractor",
        user_role="contractor",
        location="remote",  # Not at office
    )
    
    # Build context
    context = integration.build_policy_context(
        src_ip="203.0.113.1",
        dst_ip="192.168.100.50",
        src_port=443,
        dst_port=443,
        protocol="tcp",
        iam_assertion=iam,
    )
    
    # Evaluate
    matching_policy, action, params = integration.evaluate_policies(context)
    
    # Assert
    assert matching_policy is not None
    assert action == "drop"
```

### Test Case 3: Multi-Condition Matching

```python
def test_multi_condition_policy():
    """Test policy with multiple conditions"""
    integration = FirewallDPIIAMIntegration()
    
    # Add multi-condition policy
    policy = AdminPolicy(
        policy_id="test_001",
        name="Block P2P from non-admins",
        conditions=[
            PolicyCondition(PolicyMatchType.APPLICATION, "dpi_category", "eq", "P2P"),
            PolicyCondition(PolicyMatchType.IDENTITY, "user_role", "ne", "admin"),
        ],
        condition_logic="ALL",
        action="drop",
        priority=100,
    )
    integration.add_admin_policy(policy)
    
    # Test 1: Non-admin with P2P → Should match
    dpi = DPIClassification(app_name="BitTorrent", category="P2P", ...)
    iam = IAMIdentityAssertion(user_role="employee", ...)
    context = integration.build_policy_context(..., dpi, iam)
    match, action, _ = integration.evaluate_policies(context)
    assert match is not None and action == "drop"
    
    # Test 2: Admin with P2P → Should NOT match
    iam = IAMIdentityAssertion(user_role="admin", ...)
    context = integration.build_policy_context(..., dpi, iam)
    match, action, _ = integration.evaluate_policies(context)
    assert match is None  # No policy matched
```

---

## Troubleshooting

### Issue: Policy Not Matching

**Symptoms**: You create a policy but it never gets triggered

**Diagnosis**:
1. Check policy is enabled: `GET /policy/integration/policies/list`
2. Verify conditions: Use `POST /policy/integration/evaluate-with-context` with same context
3. Check priority: Policy must be evaluated before higher-priority policies match

**Solution**:
```bash
# Debug: See all matching policies
curl -X POST http://localhost:8000/policy/integration/evaluate-with-context \
  -d '{your flow}' | jq '.matching_policies_count'

# If 0: No policies matched
# Debug context fields vs. condition fields
```

### Issue: Unexpected "Pass" Decision

**Symptoms**: Flow is allowed when you expected it to be blocked

**Diagnosis**:
1. DPI classification may not have arrived yet (async timing issue)
2. No policies in the engine
3. Policy conditions don't match the actual context

**Solution**:
```bash
# List current policies
curl http://localhost:8000/policy/integration/policies/list

# Ensure DPI/IAM data is being provided
# Check that field names match (e.g., "dpi_category" not "category")
```

### Issue: Integration Engine Not Available

**Symptoms**: 503 Error: "Integration engine not available"

**Diagnosis**:
1. `backend/integrations/firewall_dpi_iam_integration.py` not found
2. Import error in module
3. Integration not initialized

**Solution**:
```bash
# Check file exists
ls -la /Users/mac/Desktop/J.A.R.V.I.S./backend/integrations/firewall_dpi_iam_integration.py

# Check for import errors
python3 -c "from backend.integrations.firewall_dpi_iam_integration import *"

# Restart server
```

---

## Configuration

### Environment Variables

```bash
# Enable integration logging
LOGGING_LEVEL=DEBUG

# Max policies
MAX_ADMIN_POLICIES=1000

# Cache settings
DPI_CACHE_TTL_SECONDS=3600
IAM_CACHE_TTL_SECONDS=1800
```

### Performance Tuning

- **Policy Evaluation**: O(n) where n = number of policies
- **Condition Matching**: O(m) where m = number of conditions
- **Typical latency**: <10ms for policy decision (with <100 policies)

**Optimization**:
- Limit policies to high-priority ones (sort by usage)
- Cache frequently-evaluated contexts
- Use "ANY" logic to short-circuit evaluation

---

## Summary

The DPI ↔ IAM ↔ Firewall integration provides:

✅ **Multi-layer Policy Matching**: Combine network, application, identity, and behavioral contexts  
✅ **Flexible Condition System**: 10+ operators for precise matching  
✅ **Priority-Based Evaluation**: Deterministic policy selection  
✅ **Template Quick-Start**: Pre-built policies for common use cases  
✅ **REST API**: Full programmatic control  
✅ **Debugging Support**: Query matching policies and reasoning  

**Next Steps**:
1. Review `firewall_dpi_iam_integration.py` and `policy.py` integration endpoints
2. Test with your DPI engine classifications
3. Test with your IAM identity assertions
4. Create custom policies for your organization
5. Deploy to production with monitoring

