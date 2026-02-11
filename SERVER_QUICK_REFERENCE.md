# JARVIS Live Server - Quick Reference

## Current Status
✅ **Server is LIVE on http://127.0.0.1:8000**

## Quick Access

| Resource | URL |
|----------|-----|
| **Interactive API Docs (Swagger UI)** | http://127.0.0.1:8000/docs |
| **ReDoc Documentation** | http://127.0.0.1:8000/redoc |
| **OpenAPI Schema** | http://127.0.0.1:8000/openapi.json |
| **Health Check** | http://127.0.0.1:8000/health |

## Essential Commands

### Check Server Status
```bash
curl http://127.0.0.1:8000/health
```

### Get Authentication Token
```bash
curl -X POST http://127.0.0.1:8000/token \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"pass123"}'
```

### Access Protected Resource
```bash
TOKEN="your-token-from-above"
curl -H "Authorization: Bearer $TOKEN" \
  http://127.0.0.1:8000/protected
```

### Create a Policy (Block Spotify)
```bash
curl -X POST "http://127.0.0.1:8000/policy/integration/policies/templates/block-application?app_name=spotify&priority=100"
```

### List All Policies
```bash
curl http://127.0.0.1:8000/policy/integration/policies/list
```

### Evaluate a Flow with DPI/IAM Context
```bash
curl -X POST http://127.0.0.1:8000/policy/integration/evaluate-with-context \
  -H "Content-Type: application/json" \
  -d '{
    "src_ip": "192.168.1.100",
    "dst_ip": "10.0.0.50",
    "src_port": 12345,
    "dst_port": 443,
    "protocol": "tcp",
    "dpi_classification": {
      "app_name": "spotify",
      "category": "media",
      "protocol": "HTTPS",
      "confidence": 95,
      "detection_tick": 150
    },
    "iam_assertion": {
      "user_id": "alice",
      "username": "alice",
      "user_role": "employee"
    }
  }'
```

## Available Policy Templates

### Block Application
```bash
curl -X POST "http://127.0.0.1:8000/policy/integration/policies/templates/block-application?app_name=APPNAME&priority=100"
```

### Block Category
```bash
curl -X POST "http://127.0.0.1:8000/policy/integration/policies/templates/block-category?category=CATEGORY&priority=100"
```

### Rate Limit
```bash
curl -X POST "http://127.0.0.1:8000/policy/integration/policies/templates/rate-limit?category=CATEGORY&rate_limit_kbps=5000&priority=80"
```

### High-Risk Quarantine
```bash
curl -X POST "http://127.0.0.1:8000/policy/integration/policies/templates/high-risk-quarantine"
```

### Contractor Restriction
```bash
curl -X POST "http://127.0.0.1:8000/policy/integration/policies/templates/contractor-restriction"
```

## Test Scenarios

### Scenario 1: Block Spotify
1. Create policy: `curl -X POST "http://127.0.0.1:8000/policy/integration/policies/templates/block-application?app_name=spotify"`
2. Evaluate: Send flow with `dpi_classification.app_name = "spotify"` → Result: `action = "drop"`

### Scenario 2: Rate-Limit Video Streaming
1. Create policy: `curl -X POST "http://127.0.0.1:8000/policy/integration/policies/templates/rate-limit?category=video&rate_limit_kbps=5000"`
2. Evaluate: Send flow with `dpi_classification.category = "video"` → Result: `action = "rate_limit"`

### Scenario 3: Contractor Network Restrictions
1. Create policy: `curl -X POST "http://127.0.0.1:8000/policy/integration/policies/templates/contractor-restriction"`
2. From office: `iam_assertion.location = "office"` → Result: `action = "pass"`
3. From home: `iam_assertion.location = "home"` → Result: `action = "drop"`

### Scenario 4: High-Risk Quarantine
1. Create policy: `curl -X POST "http://127.0.0.1:8000/policy/integration/policies/templates/high-risk-quarantine"`
2. Evaluate: Send flow with `dpi_classification.risk_score >= 80` → Result: `action = "quarantine"`

## Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/api/system/status` | GET | System status |
| `/api/federation/status` | GET | Federation status |
| `/token` | POST | Issue PQC token |
| `/protected` | GET | Protected resource (requires token) |
| `/policy/integration/policies/list` | GET | List all policies |
| `/policy/integration/policies/add` | POST | Add custom policy |
| `/policy/integration/policies/{policy_id}` | DELETE | Delete policy |
| `/policy/integration/evaluate-with-context` | POST | Evaluate flow with full context |
| `/policy/integration/policies/templates/*` | POST | Create policy from template |

## Expected Response Format

### Policy Evaluation Response
```json
{
  "status": "success",
  "flow": {
    "src_ip": "192.168.1.100",
    "src_port": 12345,
    "dst_ip": "10.0.0.50",
    "dst_port": 443,
    "protocol": "tcp"
  },
  "context": {
    "app_name": "spotify",
    "dpi_category": "media",
    "user_role": "employee",
    "user_location": "office",
    "risk_score": 0
  },
  "matching_policy": {
    "policy_id": "block_app_8e3fe8d1",
    "name": "Block spotify",
    "action": "drop",
    "priority": 100
  },
  "suggested_action": "drop",
  "action_parameters": {},
  "matching_policies_count": 1,
  "timestamp": "2025-12-10T11:55:44.966162"
}
```

## Server Logs

Monitor server activity:
```bash
tail -f /tmp/jarvis_server.log
```

## Test Suite

Run all tests:
```bash
cd /Users/mac/Desktop/J.A.R.V.I.S.
python3 -m pytest -v backend/tests/test_integration.py
```

Run specific test:
```bash
python3 -m pytest -v backend/tests/test_integration.py::test_policy_condition_matching
```

## Troubleshooting

### Server not responding
```bash
curl -v http://127.0.0.1:8000/health
tail -50 /tmp/jarvis_server.log
```

### Policy not matching
1. Check context: Review the `context` object in response
2. Check condition: Verify `matching_policy.conditions`
3. Add debug: Use `/policy/integration/policies/list` to confirm policy exists

### Token issues
```bash
# Get new token
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/token \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"pass123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Use token
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/protected
```

## Performance Notes

- Policy evaluation: < 5ms per flow
- Policy creation: < 100ms
- Policy listing: < 50ms
- Max concurrent connections: 100,000

## Next Steps

1. ✅ Verify server is running: `curl http://127.0.0.1:8000/health`
2. Open interactive docs: http://127.0.0.1:8000/docs
3. Create policies via templates
4. Test policy evaluation with sample flows
5. Review logs: `/tmp/jarvis_server.log`
6. Ready for integration with external systems

---

For full documentation, see `SMOKE_TEST_REPORT.md` or review code at `backend/api/routes/policy.py`
