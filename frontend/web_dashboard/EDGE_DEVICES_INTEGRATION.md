# Edge Device Management Integration

## Overview

The Edge Devices page provides comprehensive management and monitoring of distributed trusted execution environment (TEE) edge devices across the J.A.R.V.I.S. network. This integration enables real-time monitoring, security auditing, and remote management of heterogeneous hardware platforms including Ascend/Atlas and HiSilicon architectures.

## Architecture

### Component Structure

```
EdgeDevices.tsx
├── Device Grid View (Multi-card layout with live metrics)
├── Device List View (Table-based overview)
└── Security View (TEE/TPM/Encryption compliance dashboard)
```

### Data Models

#### EdgeDevice Interface
```typescript
interface EdgeDevice {
  id: string                    // Unique device identifier
  name: string                  // Human-readable device name
  platform: 'atlas' | 'hisilicon' | 'unknown'
  status: 'online' | 'offline' | 'degraded'
  cpu_usage: number             // Percentage (0-100)
  memory_usage: number          // Percentage (0-100)
  temperature: number           // Celsius
  uptime: number                // Hours
  last_seen: string             // ISO timestamp
  firmware_version: string
  tee_enabled: boolean          // Trusted Execution Environment
  tpm_attestation: boolean      // TPM attestation status
  location: string              // Physical/logical location
  model: string                 // Hardware model
  cores: number                 // CPU core count
  memory_gb: number             // Total memory in GB
}
```

#### SecurityMetrics Interface
```typescript
interface SecurityMetrics {
  total_devices: number         // Total managed devices
  secure_devices: number        // Devices with TEE + TPM
  attestation_success: number   // Successful TPM attestations
  encryption_enabled: number    // Devices with encryption
  seal_status: string           // Key sealing status
  device_binding: number        // Percentage of bound devices
}
```

## Integration Points

### Backend API Endpoints (To Be Implemented)

```javascript
// Device Management
GET  /api/v1/edge/devices              // List all edge devices
GET  /api/v1/edge/devices/{id}         // Get device details
POST /api/v1/edge/devices/{id}/command // Execute remote command
GET  /api/v1/edge/devices/{id}/history // Get device history

// Metrics & Monitoring
GET  /api/v1/edge/metrics              // Get aggregated metrics
GET  /api/v1/edge/health               // System health status
GET  /api/v1/edge/alerts               // Active alerts

// Security & Attestation
GET  /api/v1/edge/security/attestation // TPM attestation status
GET  /api/v1/edge/security/compliance  // Compliance dashboard
POST /api/v1/edge/security/seal        // Manage key sealing
```

### Connection to Backend Services

The component integrates with:

1. **Hardware Integration Module** (`hardware_integration/`)
   - `platform_detector.py` - Platform detection and capability querying
   - `tee_manager.py` - Trusted Execution Environment management
   - `tpm_attestation.py` - TPM attestation workflows
   - `kunpeng_tee_adapter.py` - HiSilicon-specific adapters

2. **Co-processor Driver** (`co_processor_driver.cpp`)
   - Direct hardware interaction for performance metrics
   - Temperature and resource monitoring
   - Device state queries

3. **Backend API** (`backend/`)
   - Device state persistence
   - Historical data storage
   - Remote command execution

## Feature Details

### Grid View

**Purpose**: Visual overview of all edge devices with real-time metrics

**Key Components**:
- Device cards with status indicators
- Live CPU, Memory, Temperature metrics
- Security status (TEE/TPM indicators)
- Quick action buttons (Status, Reboot)
- Color-coded platform identification

**Performance Metrics Display**:
- CPU Usage: Cyan gradient bar
- Memory Usage: Blue gradient bar
- Temperature: Color-coded (green: normal, red: critical)
- Live updates every 5 seconds

**Device Selection**:
- Click any device card to view detailed metrics
- Historical performance charts in detail panel
- Extended specifications display

### List View

**Purpose**: Tabular overview for efficient device management

**Columns**:
- Device Name (with platform icon)
- Platform (Atlas/Ascend or HiSilicon)
- Status (Online/Offline/Degraded)
- CPU Usage (%)
- Memory Usage (%)
- Temperature (°C)
- Security Status (TEE + TPM)

**Interactive Features**:
- Sortable columns
- Quick status checks
- Row highlighting on hover

### Security View

**Purpose**: Comprehensive security posture monitoring

**Security Domains**:

1. **Trusted Execution Environments**
   - Kunpeng TEE (ARM TrustZone) status
   - Ascend TEE integration
   - Key sealing mechanisms
   - Device binding percentages

2. **TPM & Attestation**
   - TPM 2.0 availability
   - PCR (Platform Configuration Register) measurement
   - Device attestation success rates
   - Secure Boot status

3. **Encryption & Privacy**
   - At-rest encryption status
   - In-transit TLS configuration
   - Key rotation schedules
   - Privacy compliance metrics

4. **Platform Compliance**
   - HuaweiCloud certification status
   - OpenEnclave compatibility
   - Hardware hardening levels
   - Security patch levels

## Device Filtering

### Filter Options

```typescript
filters: {
  platform: 'all' | 'atlas' | 'hisilicon' | 'unknown'
  status: 'all' | 'online' | 'offline' | 'degraded'
  teeEnabled: 'all' | 'enabled' | 'disabled'
}
```

### Search Functionality

Search bar enables real-time filtering by:
- Device name
- Device ID
- Model number
- Location

## Remote Command Execution

### Supported Commands

```javascript
// Device Management Commands
handleRemoteCommand(deviceId, 'status')       // Get device status
handleRemoteCommand(deviceId, 'reboot')       // Restart device
handleRemoteCommand(deviceId, 'halt')         // Shutdown device
handleRemoteCommand(deviceId, 'diagnose')     // Run diagnostics
handleRemoteCommand(deviceId, 'update')       // Push firmware update
```

### Command Execution Flow

1. User clicks action button
2. Command queued in `isRemoteCommand` state
3. API call to backend with device ID and command
4. Backend routes to hardware integration layer
5. Response displayed to user
6. State updated with execution result

## Real-time Updates

### Auto-refresh Mechanism

```typescript
useEffect(() => {
  loadEdgeDevices()
  const interval = setInterval(loadEdgeDevices, 5000) // 5-second refresh
  return () => clearInterval(interval)
}, [])
```

**Update Strategy**:
- Refreshes device list and metrics every 5 seconds
- Preserves selected device on refresh
- Updates device history for trend analysis
- Maintains filter state during updates

## Styling & Themes

### Color Scheme

| Element | Color | RGB |
|---------|-------|-----|
| Online Status | Green | `#22c55e` |
| Offline Status | Red | `#ef4444` |
| Degraded Status | Yellow | `#eab308` |
| Atlas Platform | Blue | `#3b82f6` |
| HiSilicon Platform | Purple | `#a855f7` |
| CPU Metric | Cyan | `#06b6d4` |
| Memory Metric | Blue | `#0ea5e9` |
| Accent Color | Cyan | `#06b6d4` |

### Responsive Design

- **Desktop**: 2-column grid, 3-column security metrics
- **Tablet**: 1-2 column grid, responsive tables
- **Mobile**: 1-column grid, stacked layout

## Error Handling

### Error States

```javascript
try {
  // API calls
} catch (error) {
  console.error('Failed to load edge devices:', error)
  // Display error toast/alert to user
  // Show fallback UI with cached data
}
```

### Fallback Behaviors

- Displays cached device data if API fails
- Shows error messages in user notifications
- Graceful degradation with limited functionality
- Retry mechanisms for transient failures

## Security Considerations

### Authentication & Authorization

- Requires authenticated user session
- RBAC (Role-Based Access Control) checks
- Device access permissions validated per user
- Command execution restricted to authorized roles

### Data Protection

- Device metrics encrypted in transit (TLS)
- Sensitive data (keys, attestation) redacted in UI
- Audit logs for all remote commands
- TPM attestation verification before command execution

### Hardware Security Integration

- Direct integration with TEE for secure operations
- TPM attestation validation for device trust
- Secure key sealing for sensitive operations
- Hardware-backed attestation reporting

## Performance Optimization

### Rendering Optimization

- Memoized device list components
- Virtualized rendering for large device counts
- Debounced search and filter operations
- Efficient state management with React hooks

### Network Optimization

- Batch device queries where possible
- Cached device history data
- Pagination for large result sets
- Incremental updates for metric changes

## Testing Strategy

### Unit Tests

```typescript
// Test device filtering
test('filters devices by platform', () => {
  // Test filtering logic
})

// Test status color mapping
test('returns correct status color', () => {
  // Test color mapping function
})

// Test metric calculations
test('calculates security metrics correctly', () => {
  // Test metrics aggregation
})
```

### Integration Tests

```typescript
// Test API integration
test('loads edge devices from API', async () => {
  // Mock API and test data loading
})

// Test remote command execution
test('executes remote command and updates state', async () => {
  // Mock command execution
})
```

### E2E Tests

```typescript
// Test complete user workflows
test('user can filter, select, and reboot device', async () => {
  // Full workflow testing
})
```

## Deployment Checklist

- [ ] Backend API endpoints implemented and tested
- [ ] Hardware integration modules functional
- [ ] TPM attestation working for all platform types
- [ ] Real-time metrics collection configured
- [ ] Authentication middleware in place
- [ ] Error handling and logging configured
- [ ] Performance monitoring enabled
- [ ] Security audit completed
- [ ] Documentation updated
- [ ] Team trained on feature usage

## Future Enhancements

1. **Advanced Scheduling**
   - Schedule maintenance windows
   - Automated firmware update scheduling
   - Bulk device operations

2. **ML-Based Anomaly Detection**
   - Predict device failures
   - Detect security threats
   - Optimize resource allocation

3. **Enhanced Visualization**
   - 3D device topology view
   - Network flow visualization
   - Geographic distribution mapping

4. **Automation & Orchestration**
   - Auto-healing workflows
   - Self-optimizing resource allocation
   - Automated incident response

5. **Advanced Analytics**
   - Predictive maintenance
   - TCO analysis
   - Performance trending

## References

### Related Documentation

- [Hardware Integration Guide](../../docs/architecture_diagram.drawio)
- [TEE/TPM Architecture](../../docs/security_compliance.md)
- [Backend API Reference](../../docs/API_reference.md)
- [HiSilicon/Kunpeng Documentation](../../docs/MODELARTS.md)

### Backend Services

- Platform Detection: `hardware_integration/platform_detector.py`
- TEE Management: `hardware_integration/tee_manager.py`
- TPM Attestation: `hardware_integration/tpm_attestation.py`
- Co-processor Driver: `hardware_integration/co_processor_driver.cpp`

### External References

- OpenEnclave: https://openenclave.io/
- TEE Standards: https://www.globalplatform.org/
- TPM Specifications: https://trusted computing.org/
- ARM TrustZone: https://developer.arm.com/

## Support & Troubleshooting

### Common Issues

**Issue**: Devices showing offline despite being powered on
- Check network connectivity
- Verify device agent is running
- Check firewall rules
- Review API connectivity logs

**Issue**: TPM attestation failing
- Verify TPM hardware enabled in BIOS
- Check TPM firmware version
- Validate hardware certificates
- Review TPM logs

**Issue**: Metrics not updating
- Check auto-refresh interval settings
- Verify API response times
- Check for network timeouts
- Review backend service status

### Support Contacts

- Hardware Integration: @hardware-team
- Backend API: @backend-team
- Frontend Issues: @frontend-team
- Security/Attestation: @security-team
