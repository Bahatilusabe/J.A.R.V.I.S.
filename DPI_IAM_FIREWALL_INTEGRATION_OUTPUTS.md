# DPI ↔ IAM ↔ Firewall Integration - Outputs Specification

## Overview

The DPI ↔ IAM ↔ Firewall integration produces three categories of outputs:

1. **Decisions** - Firewall actions (PASS, DROP, REJECT, RATE_LIMIT, QUARANTINE, REDIRECT)
2. **Logs** - Detailed event logs for auditing and troubleshooting
3. **Metrics** - Performance and policy statistics

---

## Part 1: Firewall Decisions

### Decision Types

#### 1. PASS
**Description**: Allow traffic to proceed without restrictions

```json
{
  "decision": "PASS",
  "policy_id": "allow_office_traffic",
  "policy_name": "Allow Office Users",
  "reason": "User is admin accessing approved application",
  "timestamp": "2025-12-10T14:30:45.123Z",
  "flow_id": "flow_12345",
  "src_ip": "192.168.1.100",
  "dst_ip": "10.0.0.1",
  "action_params": {}
}
```

**Use Cases**:
- Approved applications for role
- Administrative users accessing any app
- Whitelisted destinations
- Low-risk internal traffic

**Action**: Forward packet/flow to destination

---

#### 2. DROP
**Description**: Silently discard traffic without notifying source

```json
{
  "decision": "DROP",
  "policy_id": "block_p2p_employees",
  "policy_name": "Block P2P for Non-Admins",
  "reason": "P2P traffic denied for employee role",
  "timestamp": "2025-12-10T14:30:46.234Z",
  "flow_id": "flow_12346",
  "src_ip": "192.168.1.101",
  "dst_ip": "10.0.0.2",
  "app_detected": "BitTorrent",
  "risk_score": 85,
  "action_params": {
    "log_event": true,
    "alert_threshold": "high"
  }
}
```

**Use Cases**:
- Blocked applications for role
- High-risk traffic
- Policy violations
- Suspicious patterns

**Action**: Discard packet/flow silently (TCP RST for TCP, ICMP unreachable for UDP)

---

#### 3. REJECT
**Description**: Actively refuse connection and notify source

```json
{
  "decision": "REJECT",
  "policy_id": "block_malware",
  "policy_name": "Block Malware Traffic",
  "reason": "High-risk malware signature detected",
  "timestamp": "2025-12-10T14:30:47.345Z",
  "flow_id": "flow_12347",
  "src_ip": "192.168.1.102",
  "dst_ip": "10.0.0.3",
  "detected_anomalies": ["malware_signature_match", "c2_communication"],
  "risk_score": 95,
  "action_params": {
    "log_event": true,
    "alert_level": "critical",
    "notify_soc": true
  }
}
```

**Use Cases**:
- Malware or C2 detection
- Critical policy violations
- Security incidents
- Explicit blocking with notification

**Action**: Send TCP RST (reset connection) or ICMP unreachable + log

---

#### 4. RATE_LIMIT
**Description**: Allow traffic but limit bandwidth/connections

```json
{
  "decision": "RATE_LIMIT",
  "policy_id": "limit_streaming",
  "policy_name": "Rate Limit Video Streaming",
  "reason": "Video streaming bandwidth limited for employees",
  "timestamp": "2025-12-10T14:30:48.456Z",
  "flow_id": "flow_12348",
  "src_ip": "192.168.1.103",
  "dst_ip": "10.0.0.4",
  "app_detected": "Netflix",
  "category": "Video Streaming",
  "action_params": {
    "rate_limit_kbps": 5000,
    "rate_limit_pps": 10000,
    "burst_allowed_kbps": 7500,
    "burst_duration_ms": 100,
    "queue_strategy": "fair_queuing"
  }
}
```

**Use Cases**:
- Bandwidth management
- Preventing congestion
- Fair bandwidth allocation
- Business policy enforcement

**Action**: Queue/shape traffic to specified rate limit

**Rate Limiting Parameters**:
- `rate_limit_kbps` - Sustained rate in kilobits/sec
- `rate_limit_pps` - Sustained rate in packets/sec
- `burst_allowed_kbps` - Burst rate in kilobits/sec
- `burst_duration_ms` - Duration of burst in milliseconds
- `queue_strategy` - Algorithm: fair_queuing, priority, fifo

---

#### 5. QUARANTINE
**Description**: Redirect traffic to isolated monitoring/analysis

```json
{
  "decision": "QUARANTINE",
  "policy_id": "quarantine_high_risk",
  "policy_name": "High-Risk Traffic Quarantine",
  "reason": "Suspicious traffic detected - moved to quarantine for analysis",
  "timestamp": "2025-12-10T14:30:49.567Z",
  "flow_id": "flow_12349",
  "src_ip": "192.168.1.104",
  "dst_ip": "10.0.0.5",
  "detected_anomalies": ["protocol_deviation", "traffic_pattern_abnormal"],
  "risk_score": 78,
  "action_params": {
    "quarantine_queue": "medium_risk_queue",
    "allow_inspection": true,
    "capture_payload": true,
    "max_duration_minutes": 60,
    "analysis_required": ["malware_scan", "behavioral_analysis"],
    "notify_soc": true,
    "soc_notification_method": "email,syslog"
  }
}
```

**Use Cases**:
- Suspicious traffic patterns
- Potential security incidents
- Protocol anomalies
- Behavioral red flags

**Action**: Redirect to quarantine system for detailed inspection

**Quarantine Parameters**:
- `quarantine_queue` - Queue name (low/medium/high_risk_queue)
- `allow_inspection` - Enable payload inspection
- `capture_payload` - Save traffic for analysis
- `max_duration_minutes` - Quarantine timeout
- `analysis_required` - List of analyses to perform
- `notify_soc` - Alert SOC team
- `soc_notification_method` - Notification channels

---

#### 6. REDIRECT
**Description**: Forward traffic to alternate destination

```json
{
  "decision": "REDIRECT",
  "policy_id": "redirect_http_to_proxy",
  "policy_name": "Force HTTP Through Proxy",
  "reason": "HTTP traffic redirected to corporate proxy",
  "timestamp": "2025-12-10T14:30:50.678Z",
  "flow_id": "flow_12350",
  "src_ip": "192.168.1.105",
  "dst_ip": "10.0.0.6",
  "original_dst_ip": "8.8.8.8",
  "original_dst_port": 80,
  "action_params": {
    "redirect_type": "dnat",
    "new_destination_ip": "10.10.10.10",
    "new_destination_port": 8080,
    "preserve_source_ip": false,
    "log_redirect": true
  }
}
```

**Use Cases**:
- Force proxy inspection
- Redirect to captive portal
- Load balancing
- Traffic interception for analysis

**Action**: Modify packet destination (DNAT) and forward

---

### Decision Output Structure

**Complete Decision Object**:

```json
{
  "decision_id": "decision_uuid_12345",
  "decision": "DROP|PASS|REJECT|RATE_LIMIT|QUARANTINE|REDIRECT",
  "policy_id": "policy_unique_id",
  "policy_name": "Human-readable policy name",
  "priority": 100,
  "timestamp": "2025-12-10T14:30:45.123Z",
  "flow_id": "unique_flow_identifier",
  
  "reason": "Detailed reason for decision",
  "matched_conditions": [
    {
      "condition": "dpi_category eq P2P",
      "result": true
    },
    {
      "condition": "user_role ne admin",
      "result": true
    }
  ],
  
  "network_context": {
    "src_ip": "192.168.1.100",
    "src_port": 51234,
    "dst_ip": "10.0.0.1",
    "dst_port": 6881,
    "protocol": "tcp"
  },
  
  "dpi_context": {
    "app_name": "BitTorrent",
    "category": "P2P",
    "dpi_protocol": "TCP",
    "confidence": 95,
    "is_encrypted": false,
    "is_tunneled": false,
    "risk_score": 85,
    "detected_anomalies": ["high_bandwidth_usage", "known_p2p_signature"]
  },
  
  "iam_context": {
    "user_id": "user123",
    "username": "alice.smith",
    "user_role": "employee",
    "user_groups": ["employees", "sales"],
    "location": "office",
    "device_type": "laptop",
    "is_mfa_verified": true,
    "clearance_level": "level_1"
  },
  
  "action_params": {
    "rate_limit_kbps": 5000
  },
  
  "enforcement_target": {
    "enforcement_point": "firewall_egress",
    "enforcement_device": "fw-main-01",
    "enforcement_interface": "ge-0/0/1"
  }
}
```

---

## Part 2: Logs

### Log Levels

| Level | Usage | Frequency |
|-------|-------|-----------|
| DEBUG | Detailed condition evaluation | High in testing |
| INFO | Policy matches and decisions | Normal operations |
| WARN | Policy violations, anomalies | Moderate |
| ERROR | System errors, failures | Rare |
| CRITICAL | Security incidents, malware | Very rare |

### Log Events

#### 2.1 Policy Evaluation Log

```json
{
  "timestamp": "2025-12-10T14:30:45.123Z",
  "log_level": "INFO",
  "event_type": "POLICY_EVALUATION",
  "flow_id": "flow_12345",
  "message": "Evaluating 5 policies against flow context",
  "details": {
    "policies_evaluated": 5,
    "policies_matched": 1,
    "first_match_policy_id": "block_p2p_employees",
    "evaluation_time_ms": 0.234,
    "src_ip": "192.168.1.100",
    "app_detected": "BitTorrent"
  }
}
```

**Fields**:
- `flow_id` - Unique flow identifier
- `policies_evaluated` - Count of policies checked
- `policies_matched` - Count of matching policies
- `first_match_policy_id` - First matching policy
- `evaluation_time_ms` - Time to evaluate (for performance monitoring)

---

#### 2.2 Decision Log

```json
{
  "timestamp": "2025-12-10T14:30:45.234Z",
  "log_level": "INFO",
  "event_type": "DECISION_MADE",
  "flow_id": "flow_12345",
  "message": "Policy decision made: DROP",
  "details": {
    "decision": "DROP",
    "policy_id": "block_p2p_employees",
    "policy_name": "Block P2P for Non-Admins",
    "reason": "P2P traffic denied for employee role",
    "src_ip": "192.168.1.100",
    "dst_ip": "10.0.0.1",
    "app_name": "BitTorrent",
    "user_id": "user123",
    "user_role": "employee",
    "risk_score": 85,
    "conditions_met": 2,
    "total_conditions": 2
  }
}
```

**Fields**:
- `decision` - Final decision made
- `policy_id` / `policy_name` - Applied policy
- `reason` - Decision rationale
- `conditions_met` / `total_conditions` - Condition matching status

---

#### 2.3 Policy Match Log

```json
{
  "timestamp": "2025-12-10T14:30:45.245Z",
  "log_level": "DEBUG",
  "event_type": "POLICY_MATCH",
  "flow_id": "flow_12345",
  "message": "Policy matched: Block P2P for Non-Admins",
  "details": {
    "policy_id": "block_p2p_employees",
    "policy_name": "Block P2P for Non-Admins",
    "priority": 100,
    "condition_count": 2,
    "condition_logic": "ALL",
    "conditions": [
      {
        "field": "dpi_category",
        "operator": "eq",
        "value": "P2P",
        "matched": true,
        "actual_value": "P2P"
      },
      {
        "field": "user_role",
        "operator": "ne",
        "value": "admin",
        "matched": true,
        "actual_value": "employee"
      }
    ],
    "match_result": true
  }
}
```

**Fields**:
- `policy_id` / `policy_name` - Matched policy
- `condition_count` - Number of conditions
- `condition_logic` - AND/OR logic
- `conditions[]` - Array of condition evaluations

---

#### 2.4 Anomaly Detection Log

```json
{
  "timestamp": "2025-12-10T14:30:45.300Z",
  "log_level": "WARN",
  "event_type": "ANOMALY_DETECTED",
  "flow_id": "flow_12346",
  "message": "Traffic anomaly detected",
  "details": {
    "anomalies": [
      {
        "anomaly_type": "malware_signature_match",
        "confidence": 0.98,
        "severity": "critical",
        "signature_id": "sig_c2_beacon_001"
      },
      {
        "anomaly_type": "protocol_deviation",
        "confidence": 0.85,
        "severity": "high",
        "description": "Unexpected packet sequence detected"
      }
    ],
    "combined_risk_score": 92,
    "recommended_action": "REJECT",
    "src_ip": "192.168.1.150",
    "dst_ip": "malicious.example.com"
  }
}
```

**Fields**:
- `anomalies[]` - Array of detected anomalies
- `anomaly_type` - Type of anomaly
- `confidence` - Confidence level (0-1)
- `severity` - critical/high/medium/low
- `combined_risk_score` - Overall risk score

---

#### 2.5 Cache Event Log

```json
{
  "timestamp": "2025-12-10T14:30:45.350Z",
  "log_level": "DEBUG",
  "event_type": "CACHE_EVENT",
  "message": "DPI classification cached",
  "details": {
    "cache_type": "dpi_classification",
    "flow_key": "192.168.1.100:51234->10.0.0.1:6881:tcp",
    "cache_action": "put",
    "ttl_seconds": 300,
    "app_name": "BitTorrent",
    "category": "P2P"
  }
}
```

**Fields**:
- `cache_type` - dpi_classification, iam_assertion
- `cache_action` - put, get, hit, miss, expire
- `ttl_seconds` - Time-to-live for cache entry

---

#### 2.6 Error Log

```json
{
  "timestamp": "2025-12-10T14:30:45.400Z",
  "log_level": "ERROR",
  "event_type": "EVALUATION_ERROR",
  "flow_id": "flow_12347",
  "message": "Error during policy evaluation",
  "details": {
    "error_type": "PolicyEvaluationException",
    "error_message": "Invalid operator in condition: 'unknown_op'",
    "policy_id": "policy_invalid_001",
    "condition_index": 1,
    "recovery_action": "PASS_DEFAULT",
    "fallback_policy_used": "default_allow_policy"
  }
}
```

**Fields**:
- `error_type` - Exception type
- `error_message` - Error description
- `recovery_action` - How system recovered
- `fallback_policy_used` - Default policy applied

---

#### 2.7 Audit Log

```json
{
  "timestamp": "2025-12-10T14:30:45.450Z",
  "log_level": "INFO",
  "event_type": "AUDIT_LOG",
  "message": "Security-relevant event",
  "details": {
    "audit_type": "POLICY_VIOLATION",
    "severity": "high",
    "user_id": "user123",
    "username": "alice.smith",
    "action_attempted": "access_blocked_application",
    "blocked_resource": "P2P Application (BitTorrent)",
    "violation_policy": "block_p2p_employees",
    "enforcement_decision": "DROP",
    "timestamp_utc": "2025-12-10T14:30:45Z",
    "session_id": "session_abc123",
    "source_ip": "192.168.1.100",
    "destination_ip": "10.0.0.1"
  }
}
```

---

### Log Output Formats

#### Syslog Format
```
<Priority>Timestamp Hostname Tag[PID]: Message
<134>Dec 10 14:30:45 fw-main-01 dpi-iam-fw[12345]: POLICY_EVALUATION - Policy matched: Block P2P for Non-Admins
```

#### JSON Format
```json
{
  "timestamp": "2025-12-10T14:30:45.123Z",
  "level": "INFO",
  "component": "dpi-iam-fw",
  "message": "POLICY_EVALUATION",
  "data": { ... }
}
```

#### CSV Format
```csv
timestamp,level,event_type,flow_id,src_ip,dst_ip,decision,policy_id,app_name,user_role
2025-12-10T14:30:45.123Z,INFO,DECISION_MADE,flow_12345,192.168.1.100,10.0.0.1,DROP,block_p2p_employees,BitTorrent,employee
```

---

## Part 3: Metrics

### 3.1 Real-Time Metrics

#### Policy Evaluation Metrics

```json
{
  "timestamp": "2025-12-10T14:30:45.000Z",
  "metric_type": "POLICY_EVALUATION",
  "metrics": {
    "evaluations_total": 150432,
    "evaluations_per_second": 2507,
    "average_evaluation_time_ms": 0.156,
    "p50_evaluation_time_ms": 0.120,
    "p95_evaluation_time_ms": 0.340,
    "p99_evaluation_time_ms": 0.521,
    "max_evaluation_time_ms": 2.340,
    "policies_count": 42,
    "policies_matched_total": 89234,
    "first_match_rate": 0.593
  }
}
```

**Metrics**:
- `evaluations_total` - Total evaluations since start
- `evaluations_per_second` - Current throughput
- `average_evaluation_time_ms` - Mean latency
- `p50/p95/p99_evaluation_time_ms` - Percentiles for SLA monitoring
- `first_match_rate` - % of flows matching first policy

---

#### Decision Distribution Metrics

```json
{
  "timestamp": "2025-12-10T14:30:45.000Z",
  "metric_type": "DECISION_DISTRIBUTION",
  "time_window_seconds": 300,
  "metrics": {
    "total_decisions": 12543,
    "decisions": {
      "PASS": {
        "count": 7234,
        "percentage": 57.6,
        "rate_per_second": 24.1
      },
      "DROP": {
        "count": 3892,
        "percentage": 31.0,
        "rate_per_second": 13.0
      },
      "RATE_LIMIT": {
        "count": 890,
        "percentage": 7.1,
        "rate_per_second": 2.97
      },
      "QUARANTINE": {
        "count": 398,
        "percentage": 3.2,
        "rate_per_second": 1.33
      },
      "REJECT": {
        "count": 89,
        "percentage": 0.7,
        "rate_per_second": 0.30
      },
      "REDIRECT": {
        "count": 40,
        "percentage": 0.3,
        "rate_per_second": 0.13
      }
    }
  }
}
```

---

#### Policy Matching Metrics

```json
{
  "timestamp": "2025-12-10T14:30:45.000Z",
  "metric_type": "POLICY_STATISTICS",
  "metrics": {
    "policies_total": 42,
    "policies_enabled": 40,
    "policies_disabled": 2,
    "policy_breakdown": [
      {
        "policy_id": "block_p2p_employees",
        "policy_name": "Block P2P for Non-Admins",
        "matches_total": 12340,
        "matches_per_second": 41.1,
        "last_match_timestamp": "2025-12-10T14:30:44.987Z",
        "first_match_rate": 0.812,
        "average_conditions_checked": 2.3,
        "enabled": true,
        "priority": 100
      },
      {
        "policy_id": "limit_streaming",
        "policy_name": "Rate Limit Video Streaming",
        "matches_total": 3421,
        "matches_per_second": 11.4,
        "last_match_timestamp": "2025-12-10T14:30:44.965Z",
        "first_match_rate": 0.234,
        "average_conditions_checked": 1.8,
        "enabled": true,
        "priority": 75
      }
    ]
  }
}
```

---

#### Application Detection Metrics

```json
{
  "timestamp": "2025-12-10T14:30:45.000Z",
  "metric_type": "APPLICATION_DETECTION",
  "time_window_seconds": 300,
  "metrics": {
    "applications_detected_unique": 187,
    "top_applications": [
      {
        "app_name": "Chrome",
        "category": "Web Browsing",
        "flows_detected": 24532,
        "percentage_of_traffic": 35.2,
        "bytes_total": 5234123456,
        "average_risk_score": 5
      },
      {
        "app_name": "Microsoft Teams",
        "category": "Collaboration",
        "flows_detected": 8923,
        "percentage_of_traffic": 12.8,
        "bytes_total": 2123456789,
        "average_risk_score": 3
      },
      {
        "app_name": "Netflix",
        "category": "Video Streaming",
        "flows_detected": 3456,
        "percentage_of_traffic": 4.9,
        "bytes_total": 8234567890,
        "average_risk_score": 2
      }
    ],
    "categories_detected": {
      "Web Browsing": {
        "flows": 28900,
        "percentage": 41.4,
        "bytes": 6234567890
      },
      "Collaboration": {
        "flows": 12340,
        "percentage": 17.7,
        "bytes": 2567890123
      },
      "P2P": {
        "flows": 4532,
        "percentage": 6.5,
        "bytes": 987654321
      }
    }
  }
}
```

---

#### Risk Assessment Metrics

```json
{
  "timestamp": "2025-12-10T14:30:45.000Z",
  "metric_type": "RISK_ASSESSMENT",
  "time_window_seconds": 300,
  "metrics": {
    "flows_analyzed": 69823,
    "risk_distribution": {
      "low_risk": {
        "count": 52345,
        "percentage": 74.9
      },
      "medium_risk": {
        "count": 12543,
        "percentage": 18.0
      },
      "high_risk": {
        "count": 3892,
        "percentage": 5.6
      },
      "critical_risk": {
        "count": 1043,
        "percentage": 1.5
      }
    },
    "anomalies_detected": 4567,
    "anomaly_types": {
      "malware_signature": 234,
      "c2_communication": 89,
      "protocol_deviation": 567,
      "behavioral_anomaly": 3677
    }
  }
}
```

---

#### User/Role Metrics

```json
{
  "timestamp": "2025-12-10T14:30:45.000Z",
  "metric_type": "USER_ROLE_STATISTICS",
  "time_window_seconds": 300,
  "metrics": {
    "users_active": 287,
    "by_role": {
      "admin": {
        "users": 12,
        "flows": 8923,
        "blocked_flows": 45,
        "block_rate": 0.005,
        "average_risk_score": 3.2
      },
      "employee": {
        "users": 245,
        "flows": 45234,
        "blocked_flows": 3892,
        "block_rate": 0.086,
        "average_risk_score": 28.5
      },
      "contractor": {
        "users": 18,
        "flows": 5234,
        "blocked_flows": 1203,
        "block_rate": 0.230,
        "average_risk_score": 42.1
      },
      "guest": {
        "users": 12,
        "flows": 10432,
        "blocked_flows": 8932,
        "block_rate": 0.856,
        "average_risk_score": 68.9
      }
    }
  }
}
```

---

#### Location-Based Metrics

```json
{
  "timestamp": "2025-12-10T14:30:45.000Z",
  "metric_type": "LOCATION_STATISTICS",
  "metrics": {
    "locations_active": 15,
    "by_location": {
      "office": {
        "users": 187,
        "flows": 42345,
        "dropped_flows": 2345,
        "drop_rate": 0.055,
        "quarantined_flows": 234,
        "average_risk_score": 15.3
      },
      "home": {
        "users": 67,
        "flows": 18902,
        "dropped_flows": 1892,
        "drop_rate": 0.100,
        "quarantined_flows": 456,
        "average_risk_score": 35.7
      },
      "remote": {
        "users": 33,
        "flows": 8576,
        "dropped_flows": 3204,
        "drop_rate": 0.374,
        "quarantined_flows": 678,
        "average_risk_score": 52.1
      }
    }
  }
}
```

---

### 3.2 Aggregated Metrics (Daily/Weekly/Monthly)

```json
{
  "timestamp": "2025-12-10T23:59:59.999Z",
  "metric_type": "DAILY_SUMMARY",
  "period": "day",
  "period_start": "2025-12-10T00:00:00Z",
  "period_end": "2025-12-10T23:59:59Z",
  "metrics": {
    "total_flows": 6234567890,
    "total_bytes_analyzed": 1234567890123,
    "total_decisions": 6234567890,
    
    "decision_summary": {
      "PASS": {
        "count": 3583892345,
        "percentage": 57.5,
        "bytes": 742341234567
      },
      "DROP": {
        "count": 1931456234,
        "percentage": 31.0,
        "bytes": 234567891234
      },
      "RATE_LIMIT": {
        "count": 442893123,
        "percentage": 7.1,
        "bytes": 142356789012
      },
      "QUARANTINE": {
        "count": 199234567,
        "percentage": 3.2,
        "bytes": 89234567123
      },
      "REJECT": {
        "count": 43678123,
        "percentage": 0.7,
        "bytes": 12345678901
      },
      "REDIRECT": {
        "count": 18702898,
        "percentage": 0.3,
        "bytes": 13789012345
      }
    },
    
    "top_violations": [
      {
        "policy_id": "block_p2p_employees",
        "violation_count": 342890,
        "blocked_bytes": 123456789
      },
      {
        "policy_id": "limit_streaming",
        "violation_count": 156234,
        "limited_bytes": 987654321
      }
    ],
    
    "security_incidents": {
      "malware_detected": 234,
      "c2_communications": 45,
      "ddos_attempts": 12,
      "intrusion_attempts": 89
    },
    
    "cache_statistics": {
      "dpi_cache_hits": 4892345,
      "dpi_cache_misses": 234567,
      "dpi_cache_hit_rate": 0.954,
      "iam_cache_hits": 2341234,
      "iam_cache_misses": 89234,
      "iam_cache_hit_rate": 0.963
    },
    
    "performance": {
      "average_evaluation_time_ms": 0.154,
      "p99_evaluation_time_ms": 0.432,
      "max_evaluation_time_ms": 12.343,
      "evaluations_per_second_peak": 2843,
      "evaluations_per_second_average": 1852
    }
  }
}
```

---

### 3.3 Metric Export Formats

#### Prometheus Format

```
# HELP dpi_iam_fw_evaluations_total Total policy evaluations
# TYPE dpi_iam_fw_evaluations_total counter
dpi_iam_fw_evaluations_total 150432

# HELP dpi_iam_fw_evaluation_time_ms Policy evaluation latency
# TYPE dpi_iam_fw_evaluation_time_ms histogram
dpi_iam_fw_evaluation_time_ms_bucket{le="0.1"} 45234
dpi_iam_fw_evaluation_time_ms_bucket{le="0.5"} 98234
dpi_iam_fw_evaluation_time_ms_bucket{le="1.0"} 143234
dpi_iam_fw_evaluation_time_ms_bucket{le="+Inf"} 150432

# HELP dpi_iam_fw_decisions Decision counts by type
# TYPE dpi_iam_fw_decisions counter
dpi_iam_fw_decisions{decision="PASS"} 87234
dpi_iam_fw_decisions{decision="DROP"} 38923
dpi_iam_fw_decisions{decision="RATE_LIMIT"} 8900
```

#### InfluxDB Format

```
policy_evaluation,policy_id=block_p2p_employees matches_total=12340i,matches_per_second=41.1 1702241445000
policy_evaluation,policy_id=limit_streaming matches_total=3421i,matches_per_second=11.4 1702241445000
decision_distribution,decision_type=PASS count=7234i,percentage=57.6 1702241445000
decision_distribution,decision_type=DROP count=3892i,percentage=31.0 1702241445000
```

---

## Part 4: Integration Output Points

### 4.1 REST API Response

```json
POST /policy/integration/evaluate-with-context

Response 200 OK:
{
  "status": "success",
  "decision_id": "dec_uuid_12345",
  "decision": "DROP",
  "policy_id": "block_p2p_employees",
  "policy_name": "Block P2P for Non-Admins",
  "reason": "P2P traffic denied for employee role",
  "action_params": {},
  "matched_conditions": 2,
  "evaluation_time_ms": 0.234,
  "timestamp": "2025-12-10T14:30:45.123Z"
}
```

---

### 4.2 Event Stream (Kafka/AMQP)

```json
Topic: security.decisions
{
  "event_id": "evt_12345",
  "event_type": "POLICY_DECISION",
  "decision": "DROP",
  "policy_id": "block_p2p_employees",
  "flow_id": "flow_12345",
  "timestamp": "2025-12-10T14:30:45.123Z",
  "src_ip": "192.168.1.100",
  "app_detected": "BitTorrent"
}
```

---

### 4.3 Database Storage

**Table: policy_decisions**
```sql
CREATE TABLE policy_decisions (
  decision_id VARCHAR(36) PRIMARY KEY,
  flow_id VARCHAR(36),
  decision VARCHAR(20),
  policy_id VARCHAR(100),
  policy_name VARCHAR(255),
  src_ip VARCHAR(45),
  dst_ip VARCHAR(45),
  app_name VARCHAR(100),
  user_id VARCHAR(100),
  user_role VARCHAR(50),
  timestamp TIMESTAMP,
  evaluation_time_ms FLOAT,
  INDEX idx_flow_id (flow_id),
  INDEX idx_timestamp (timestamp),
  INDEX idx_policy_id (policy_id)
);
```

---

## Summary

The integration produces three comprehensive output categories:

| Output Type | Purpose | Frequency | Consumers |
|-----------|---------|-----------|-----------|
| **Decisions** | Firewall enforcement | Per-flow (real-time) | Firewall engines, policy enforcement |
| **Logs** | Auditing & troubleshooting | Per-decision | SIEM, ELK, Splunk, file storage |
| **Metrics** | Performance monitoring | Real-time + aggregated | Prometheus, Grafana, dashboards |

All outputs are:
- ✅ Timestamped for correlation
- ✅ Detailed for analysis
- ✅ Scalable for high-throughput
- ✅ Standards-compliant (JSON, Syslog, Prometheus)
- ✅ Production-ready

---

**End of Outputs Specification**
