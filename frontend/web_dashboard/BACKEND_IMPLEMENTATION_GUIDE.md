# Edge Device Management - Backend Implementation Guide

## Overview

This guide provides implementation specifications for the backend Edge Device Management API. The backend must integrate with hardware abstraction layers, TEE managers, and TPM attestation services to provide a comprehensive edge device monitoring and management system.

## Backend Architecture

```
backend/
├── api/
│   └── edge/
│       ├── __init__.py
│       ├── routes.py           # API endpoint definitions
│       ├── handlers.py         # Request handlers
│       └── schemas.py          # Request/response schemas
├── core/
│   └── edge_manager.py         # Core business logic
├── integrations/
│   └── hardware/
│       ├── device_aggregator.py
│       ├── metrics_collector.py
│       └── command_executor.py
└── utils/
    └── edge_utils.py           # Utility functions
```

## Database Schema

### Devices Table

```sql
CREATE TABLE edge_devices (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    platform VARCHAR(32) NOT NULL,
    location VARCHAR(255),
    model VARCHAR(255),
    cores INTEGER,
    memory_gb INTEGER,
    firmware_version VARCHAR(255),
    tee_enabled BOOLEAN DEFAULT FALSE,
    tpm_enabled BOOLEAN DEFAULT FALSE,
    status VARCHAR(32) DEFAULT 'unknown',
    last_heartbeat TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_device_id (id),
    INDEX idx_platform (platform),
    INDEX idx_status (status),
    INDEX idx_location (location)
);
```

### Device Metrics Table

```sql
CREATE TABLE device_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(64) NOT NULL,
    cpu_usage FLOAT,
    memory_usage FLOAT,
    temperature FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES edge_devices(id),
    INDEX idx_device_id_timestamp (device_id, timestamp),
    INDEX idx_timestamp (timestamp)
);
```

### Device Attestation Table

```sql
CREATE TABLE device_attestations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(64) NOT NULL,
    tpm_version VARCHAR(32),
    pcr_hash VARCHAR(512),
    attestation_status VARCHAR(32),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES edge_devices(id),
    INDEX idx_device_id_timestamp (device_id, timestamp),
    INDEX idx_status (attestation_status)
);
```

### Device Commands Table

```sql
CREATE TABLE device_commands (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(64) NOT NULL,
    command VARCHAR(255) NOT NULL,
    parameters JSON,
    status VARCHAR(32),
    result JSON,
    executed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES edge_devices(id),
    INDEX idx_device_id_status (device_id, status),
    INDEX idx_created_at (created_at)
);
```

## API Endpoints

### Device Management

#### GET `/api/v1/edge/devices`

**Description**: List all edge devices

**Query Parameters**:
- `platform` (optional): Filter by platform (atlas, hisilicon)
- `status` (optional): Filter by status (online, offline, degraded)
- `location` (optional): Filter by location
- `limit` (optional): Results per page (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response**:
```json
{
  "devices": [
    {
      "id": "edge-001",
      "name": "Atlas-500-East",
      "platform": "atlas",
      "status": "online",
      "cpu_usage": 45,
      "memory_usage": 62,
      "temperature": 52,
      "uptime": 328,
      "last_seen": "2024-01-15T10:30:00Z",
      "firmware_version": "2.1.0",
      "tee_enabled": true,
      "tpm_attestation": true,
      "location": "DataCenter-US-East",
      "model": "Atlas 500",
      "cores": 64,
      "memory_gb": 256
    }
  ],
  "total": 4,
  "limit": 20,
  "offset": 0
}
```

#### GET `/api/v1/edge/devices/{id}`

**Description**: Get specific device details

**Response**:
```json
{
  "id": "edge-001",
  "name": "Atlas-500-East",
  "platform": "atlas",
  "status": "online",
  "metrics": {
    "cpu_usage": 45,
    "memory_usage": 62,
    "temperature": 52
  },
  "security": {
    "tee_enabled": true,
    "tee_type": "Ascend TEE",
    "tpm_version": "2.0",
    "tpm_attestation": true,
    "seal_status": "active"
  },
  "hardware": {
    "cores": 64,
    "memory_gb": 256,
    "model": "Atlas 500"
  }
}
```

#### POST `/api/v1/edge/devices/{id}/command`

**Description**: Execute remote command on device

**Request Body**:
```json
{
  "command": "reboot|status|update|diagnose|halt",
  "parameters": {
    "timeout": 30,
    "force": false
  }
}
```

**Response**:
```json
{
  "success": true,
  "device_id": "edge-001",
  "command": "reboot",
  "result": "Device rebooting...",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET `/api/v1/edge/devices/{id}/history`

**Description**: Get device historical data

**Query Parameters**:
- `limit` (optional): Number of records (default: 100)
- `offset` (optional): Pagination offset
- `start_time` (optional): ISO timestamp
- `end_time` (optional): ISO timestamp

**Response**:
```json
{
  "device_id": "edge-001",
  "history": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "cpu_usage": 45,
      "memory_usage": 62,
      "temperature": 52,
      "status": "online"
    }
  ]
}
```

### Security & Attestation

#### GET `/api/v1/edge/metrics`

**Description**: Get aggregated security metrics

**Response**:
```json
{
  "total_devices": 4,
  "secure_devices": 4,
  "attestation_success": 3,
  "encryption_enabled": 4,
  "seal_status": "active",
  "device_binding": 100
}
```

#### GET `/api/v1/edge/devices/{id}/attestation`

**Description**: Get TPM attestation status

**Response**:
```json
{
  "device_id": "edge-001",
  "tpm_version": "2.0",
  "pcr_values": {
    "pcr_0": "0x123456...",
    "pcr_1": "0x789abc...",
    "pcr_7": "0xdef012..."
  },
  "attestation_status": "success",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### POST `/api/v1/edge/devices/{id}/attestation/verify`

**Description**: Trigger TPM attestation verification

**Response**:
```json
{
  "device_id": "edge-001",
  "tpm_version": "2.0",
  "pcr_values": {
    "pcr_0": "0x123456..."
  },
  "attestation_status": "success",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET `/api/v1/edge/security/compliance`

**Description**: Get compliance status

**Response**:
```json
{
  "devices": [
    {
      "device_id": "edge-001",
      "tee_status": "enabled",
      "tpm_status": "active",
      "encryption_status": "enabled",
      "compliance_score": 95,
      "last_check": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### POST `/api/v1/edge/security/seal`

**Description**: Seal keys on device

**Request Body**:
```json
{
  "device_id": "edge-001",
  "key_id": "master_key_001",
  "policy": "pcr_0,pcr_1,pcr_7",
  "pcr_values": ["0x123456...", "0x789abc...", "0xdef012..."]
}
```

**Response**:
```json
{
  "success": true,
  "device_id": "edge-001",
  "key_id": "master_key_001",
  "sealed_data": "0xsealed_blob_...",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Health & Status

#### GET `/api/v1/edge/health`

**Description**: Get system health status

**Response**:
```json
{
  "overall_status": "healthy",
  "devices_online": 4,
  "devices_offline": 0,
  "alerts": [],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET `/api/v1/edge/alerts`

**Description**: Get active alerts

**Query Parameters**:
- `severity` (optional): critical, warning, info
- `device_id` (optional): Filter by device
- `limit` (optional): Number of alerts

**Response**:
```json
{
  "alerts": [
    {
      "id": "alert-001",
      "device_id": "edge-004",
      "severity": "warning",
      "message": "High CPU usage detected",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ]
}
```

## Implementation Examples

### Python Backend Implementation

```python
# backend/api/edge/routes.py
from flask import Blueprint, request, jsonify
from backend.core.edge_manager import EdgeManager
from backend.api.edge.schemas import DeviceSchema, CommandSchema

edge_bp = Blueprint('edge', __name__, url_prefix='/api/v1/edge')
edge_manager = EdgeManager()
device_schema = DeviceSchema()

@edge_bp.route('/devices', methods=['GET'])
def list_devices():
    """List all edge devices"""
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    platform = request.args.get('platform')
    status = request.args.get('status')
    
    devices = edge_manager.get_devices(
        limit=limit,
        offset=offset,
        platform=platform,
        status=status
    )
    
    return jsonify({
        'devices': device_schema.dump(devices, many=True),
        'total': len(devices),
        'limit': limit,
        'offset': offset
    })

@edge_bp.route('/devices/<device_id>', methods=['GET'])
def get_device(device_id):
    """Get specific device details"""
    device = edge_manager.get_device(device_id)
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    return jsonify(device_schema.dump(device))

@edge_bp.route('/devices/<device_id>/command', methods=['POST'])
def execute_command(device_id):
    """Execute remote command on device"""
    data = request.get_json()
    command = data.get('command')
    parameters = data.get('parameters', {})
    
    result = edge_manager.execute_device_command(
        device_id=device_id,
        command=command,
        parameters=parameters
    )
    
    return jsonify(result)

@edge_bp.route('/devices/<device_id>/attestation/verify', methods=['POST'])
def verify_attestation(device_id):
    """Trigger TPM attestation"""
    result = edge_manager.verify_tpm_attestation(device_id)
    return jsonify(result)
```

### Hardware Integration

```python
# backend/integrations/hardware/device_aggregator.py
from hardware_integration.platform_detector import PlatformDetector
from hardware_integration.tee_manager import TEEManager
from hardware_integration.tpm_attestation import TPMAttestationManager

class DeviceAggregator:
    def __init__(self):
        self.platform_detector = PlatformDetector()
        self.tee_manager = TEEManager()
        self.tpm_manager = TPMAttestationManager()
    
    def get_device_metrics(self, device_id):
        """Collect metrics from device"""
        platform = self.platform_detector.detect_platform(device_id)
        
        if platform == 'atlas':
            return self._get_atlas_metrics(device_id)
        elif platform == 'hisilicon':
            return self._get_hisilicon_metrics(device_id)
    
    def verify_device_attestation(self, device_id):
        """Verify TPM attestation"""
        return self.tpm_manager.verify_attestation(device_id)
    
    def execute_tee_operation(self, device_id, operation, params):
        """Execute operation in TEE"""
        return self.tee_manager.execute_operation(
            device_id=device_id,
            operation=operation,
            parameters=params
        )
```

## Integration with Hardware Services

### Platform Detection

```python
# Usage in device aggregator
from hardware_integration.platform_detector import PlatformDetector

detector = PlatformDetector()
platform_info = detector.detect_platform(device_id)
# Returns: {'platform': 'atlas', 'tee_type': 'Ascend TEE', 'capabilities': {...}}
```

### TEE Management

```python
# Usage for secure operations
from hardware_integration.tee_manager import TEEManager

tee_mgr = TEEManager()
result = tee_mgr.seal_key(
    device_id=device_id,
    key_id='master_key_001',
    pcr_values=[pcr_0, pcr_1, pcr_7]
)
```

### TPM Attestation

```python
# Usage for attestation
from hardware_integration.tpm_attestation import TPMAttestationManager

tpm_mgr = TPMAttestationManager()
attestation_result = tpm_mgr.verify_attestation(device_id)
# Returns PCR values and attestation status
```

## Error Handling

### Standard Error Responses

```json
{
  "error": "Device not found",
  "code": "DEVICE_NOT_FOUND",
  "status": 404
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|------------|-------------|
| DEVICE_NOT_FOUND | 404 | Device does not exist |
| INVALID_COMMAND | 400 | Command is not supported |
| TEE_NOT_AVAILABLE | 503 | TEE service unavailable |
| ATTESTATION_FAILED | 400 | TPM attestation failed |
| UNAUTHORIZED | 401 | User not authorized |
| INTERNAL_ERROR | 500 | Internal server error |

## Authentication & Authorization

### Required Headers

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### RBAC Roles

- `admin`: Full access to all devices and commands
- `operator`: Can view devices and execute safe commands
- `viewer`: Read-only access to device information
- `auditor`: Access to logs and compliance data

## Performance Optimization

### Caching Strategy

```python
# Cache device list for 30 seconds
@cache.cached(timeout=30, key_prefix='devices_list')
def get_devices():
    pass

# Cache attestation status for 5 minutes
@cache.cached(timeout=300, key_prefix='attestation_%s', args=device_id)
def get_attestation_status(device_id):
    pass
```

### Batch Operations

```python
# Support bulk device operations
@edge_bp.route('/devices/bulk', methods=['POST'])
def bulk_operation():
    data = request.get_json()
    device_ids = data.get('device_ids')
    operation = data.get('operation')
    
    results = edge_manager.bulk_execute(
        device_ids=device_ids,
        operation=operation
    )
    
    return jsonify(results)
```

## Testing

### Unit Tests

```python
# tests/test_edge_manager.py
import pytest
from backend.core.edge_manager import EdgeManager

@pytest.fixture
def edge_manager():
    return EdgeManager()

def test_get_devices(edge_manager):
    devices = edge_manager.get_devices()
    assert len(devices) > 0

def test_execute_command(edge_manager):
    result = edge_manager.execute_device_command(
        device_id='edge-001',
        command='status'
    )
    assert result['success'] is True
```

### Integration Tests

```python
# tests/test_edge_api.py
def test_list_devices_api(client):
    response = client.get('/api/v1/edge/devices')
    assert response.status_code == 200
    assert 'devices' in response.json

def test_execute_command_api(client):
    response = client.post(
        '/api/v1/edge/devices/edge-001/command',
        json={'command': 'reboot'}
    )
    assert response.status_code == 200
```

## Deployment Checklist

- [ ] Database schema created and migrated
- [ ] API endpoints implemented and tested
- [ ] Hardware integration modules integrated
- [ ] Authentication middleware configured
- [ ] Error handling and logging configured
- [ ] Cache layer implemented
- [ ] Performance testing completed
- [ ] Security audit performed
- [ ] Documentation completed
- [ ] Team trained on deployment

## Monitoring & Logging

### Key Metrics to Monitor

- Device uptime percentage
- API response times
- Attestation success rates
- Command execution success rate
- TPM operation latency
- Memory usage on devices

### Logging Strategy

```python
import logging

logger = logging.getLogger('edge_device_service')

logger.info(f'Device {device_id} status check initiated')
logger.warning(f'Device {device_id} temperature critical: {temp}°C')
logger.error(f'Failed to execute command on {device_id}: {error}')
```

## Future Enhancements

1. WebSocket support for real-time updates
2. GraphQL API alternative
3. Device provisioning automation
4. Advanced scheduling for batch operations
5. ML-based anomaly detection
