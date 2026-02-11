# Edge Device Management - Complete Feature Guide

## 🎯 Overview

The Edge Device Management page is a sophisticated, real-time monitoring and control system for distributed trusted execution environment (TEE) edge devices. It provides comprehensive visibility into hardware status, security metrics, and enables remote management of heterogeneous computing platforms including Ascend/Atlas and HiSilicon architectures.

## 🚀 Quick Start

### For Frontend Developers

1. **Import the component**:
```typescript
import EdgeDevices from '@/pages/EdgeDevices'
```

2. **Add to routes**:
```typescript
{
  path: '/edge-devices',
  component: EdgeDevices,
  meta: { title: 'Edge Devices' }
}
```

3. **Ensure API service is configured**:
```typescript
// in edgeDeviceService.ts
const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000'
```

### For Backend Developers

1. **Implement API endpoints** in `backend/api/edge/routes.py`
2. **Integrate hardware services** from `hardware_integration/`
3. **Configure database schema** with provided SQL
4. **Set up authentication middleware**
5. **Deploy and test**

## 📁 File Structure

```
frontend/web_dashboard/
├── src/
│   ├── pages/
│   │   ├── EdgeDevices.tsx          # Main component (850+ lines)
│   │   └── EdgeDevices.css          # Styling (350+ lines)
│   ├── services/
│   │   └── edgeDeviceService.ts     # API integration (400+ lines)
│   └── components/
│       └── AppLayout.tsx             # Layout wrapper
├── EDGE_DEVICES_INTEGRATION.md       # Integration guide
└── BACKEND_IMPLEMENTATION_GUIDE.md   # Backend specs
```

## 🎨 UI Components

### Three View Modes

#### 1. Grid View (Default)
- **Best for**: Visual overview and quick status checks
- **Features**:
  - Multi-card device display
  - Live metric visualization
  - Color-coded status indicators
  - Quick action buttons
  - Device detail panel

#### 2. List View
- **Best for**: Bulk operations and comprehensive comparison
- **Features**:
  - Sortable table columns
  - Compact information display
  - Efficient scanning
  - Row highlighting

#### 3. Security View
- **Best for**: Compliance and security auditing
- **Features**:
  - TEE/TPM status dashboard
  - Security metric charts
  - Compliance scoring
  - Platform-specific compliance

### Filtering System

**Available Filters**:
- **Platform**: All, Atlas/Ascend, HiSilicon
- **Status**: All, Online, Offline, Degraded
- **TEE Status**: All, Enabled, Disabled

**Search Functionality**:
- Real-time search across device names, IDs, models, and locations

## 📊 Key Metrics

### Device Metrics

| Metric | Range | Color | Indicator |
|--------|-------|-------|-----------|
| CPU Usage | 0-100% | Cyan | Live bar chart |
| Memory Usage | 0-100% | Blue | Live bar chart |
| Temperature | 0-100°C | Green/Red | Gradient indicator |
| Uptime | Hours | Gray | Text display |

### Security Metrics

| Metric | Type | Calculation |
|--------|------|-------------|
| Secure Devices | Count | Devices with TEE + TPM |
| Attestation Success | % | Successful TPM verifications |
| Device Binding | % | Devices with key sealing |
| Encryption | Count | Devices with encryption enabled |

## 🔐 Security Features

### Trusted Execution Environment (TEE)

**Supported Platforms**:
- **Ascend/Atlas**: Proprietary TEE implementation
- **HiSilicon/Kunpeng**: ARM TrustZone

**Capabilities**:
- Secure key storage
- Protected code execution
- Hardware-backed encryption
- Attestation support

### TPM Attestation

**Features**:
- TPM 2.0 support
- Platform Configuration Register (PCR) measurement
- Secure boot verification
- Device identity binding

**Status Indicators**:
- ✅ Green: Attestation successful
- ⚠️ Yellow: Attestation pending
- ❌ Red: Attestation failed

### Encryption & Key Sealing

**Implementations**:
- At-rest encryption with device-specific keys
- In-transit TLS encryption
- Key sealing with PCR policies
- Automatic key rotation

## 🔄 Real-time Updates

### Auto-refresh Mechanism

- **Default Interval**: 5 seconds
- **Configurable**: Via environment variables
- **State Preservation**: Filters and selections maintained
- **Error Handling**: Graceful fallback with cached data

### Live Metrics Collection

```typescript
// Automatic refresh every 5 seconds
useEffect(() => {
  loadEdgeDevices()
  const interval = setInterval(loadEdgeDevices, 5000)
  return () => clearInterval(interval)
}, [])
```

## 🎛️ Remote Commands

### Supported Operations

**Device Management**:
- `status`: Get current device status
- `reboot`: Restart the device
- `halt`: Graceful shutdown
- `update`: Push firmware update
- `diagnose`: Run system diagnostics

**Security Operations**:
- `attestate`: Trigger TPM attestation
- `seal-keys`: Initiate key sealing
- `verify-seal`: Verify sealed keys
- `update-tee`: Update TEE firmware

**Bulk Operations**:
- Execute same command on multiple devices
- Batch firmware updates
- Coordinated maintenance windows

## 🔌 API Integration

### Service Layer (`edgeDeviceService.ts`)

**Available Methods**:
```typescript
// Device operations
getDevices()
getDevice(deviceId)
getDeviceHistory(deviceId, options)
executeRemoteCommand(deviceId, command, parameters)

// Security operations
getAttestationStatus(deviceId)
triggerAttestation(deviceId)
getComplianceStatus(deviceId)
sealKeys(deviceId, options)

// Metrics and monitoring
getSecurityMetrics()
getHealthStatus()
getAlerts(options)
getDeviceMetrics(deviceId, options)

// Platform information
getPlatformInfo(platform)
setDeviceConfig(deviceId, config)
getDeviceLogs(deviceId, options)
```

### Authentication

- **Method**: Bearer token JWT
- **Header**: `Authorization: Bearer <token>`
- **Stored in**: LocalStorage as `auth_token`

## 🛠️ Configuration

### Environment Variables

```bash
# API Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_API_TIMEOUT=30000

# Feature Flags
REACT_APP_ENABLE_TEE_MANAGEMENT=true
REACT_APP_ENABLE_TPM_ATTESTATION=true
REACT_APP_ENABLE_BULK_OPERATIONS=true

# Update Intervals
REACT_APP_DEVICE_UPDATE_INTERVAL=5000
REACT_APP_METRICS_UPDATE_INTERVAL=10000
```

### Theme Customization

Modify colors in `EdgeDevices.css`:
```css
:root {
  --color-status-online: #22c55e;
  --color-status-offline: #ef4444;
  --color-platform-atlas: #3b82f6;
  --color-platform-hisilicon: #a855f7;
  --color-accent-primary: #06b6d4;
}
```

## 📈 Performance Optimization

### Rendering

- **Memoization**: Device components memoized to prevent unnecessary re-renders
- **Virtualization**: For large device lists (100+ devices)
- **Lazy Loading**: Detail panels loaded on demand

### Network

- **Caching**: Device data cached for 30 seconds
- **Batch Requests**: Multiple device queries batched
- **Pagination**: Large result sets paginated (default: 20 items)

### Queries

```typescript
// Efficient device query
const devices = await edgeDeviceService.getDevices()

// Filtered query on backend
const filtered = await edgeDeviceService.searchDevices({
  platform: 'atlas',
  status: 'online',
  location: 'us-east-1'
})
```

## 🧪 Testing

### Unit Tests

```bash
npm run test -- EdgeDevices.test.tsx
npm run test -- edgeDeviceService.test.ts
```

### Integration Tests

```bash
npm run test:integration -- edge-devices
```

### E2E Tests

```bash
npm run test:e2e -- edge-devices.spec.ts
```

### Test Coverage Goals

- **Statements**: 85%+
- **Branches**: 80%+
- **Functions**: 85%+
- **Lines**: 85%+

## 🚀 Deployment

### Prerequisites

- Node.js 16+
- React 18+
- Backend API running
- Database configured
- Hardware integration modules available

### Build

```bash
npm run build:edge-devices
# or
npm run build
```

### Docker Deployment

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Health Checks

```bash
# Verify API connectivity
curl http://localhost:3000/api/v1/edge/health

# Check device count
curl http://localhost:3000/api/v1/edge/devices
```

## 📊 Monitoring & Observability

### Key Metrics to Monitor

- **Device Health**: Percentage online/offline/degraded
- **API Performance**: Response times and error rates
- **Security Status**: Attestation success rate
- **Resource Utilization**: Average CPU, memory, temperature

### Logging

**Log Levels**:
- `DEBUG`: Detailed component lifecycle
- `INFO`: API calls and device updates
- `WARN`: Performance warnings, attestation issues
- `ERROR`: API failures, command execution errors

**Structured Logging**:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "edge-device-management",
  "device_id": "edge-001",
  "action": "device_status_update",
  "status": "online",
  "duration_ms": 245
}
```

## 🐛 Troubleshooting

### Common Issues

**Issue**: Devices showing as offline
- **Solution**: Check API connectivity, verify device agents running
- **Debug**: Check network tab in DevTools, review backend logs

**Issue**: Metrics not updating
- **Solution**: Verify auto-refresh interval, check API response times
- **Debug**: Set `REACT_APP_DEBUG=true` in env, review component logs

**Issue**: TPM attestation failing
- **Solution**: Check TPM hardware enabled, verify firmware version
- **Debug**: Review hardware integration logs, check TPM availability

**Issue**: High memory usage
- **Solution**: Implement pagination, reduce update frequency
- **Debug**: Profile with React DevTools, check for memory leaks

## 📚 Additional Resources

### Documentation

- [Edge Devices Integration Guide](./EDGE_DEVICES_INTEGRATION.md)
- [Backend Implementation Guide](./BACKEND_IMPLEMENTATION_GUIDE.md)
- [Architecture Diagram](../../docs/architecture_diagram.drawio)
- [Security Compliance](../../docs/security_compliance.md)

### Related Components

- **Hardware Integration**: `hardware_integration/`
- **TPM Attestation**: `hardware_integration/tpm_attestation.py`
- **TEE Manager**: `hardware_integration/tee_manager.py`
- **Platform Detector**: `hardware_integration/platform_detector.py`

### External References

- [OpenEnclave SDK](https://openenclave.io/)
- [TEE Standards](https://www.globalplatform.org/)
- [TPM 2.0 Specification](https://trustedcomputinggroup.org/)
- [Ascend Hardware Documentation](https://www.huaweicloud.com/intl/en-us/ascend.html)
- [HiSilicon Kunpeng](https://www.hisilicon.com/)

## 👥 Support & Contribution

### Getting Help

- **Issues**: Create GitHub issue with reproduction steps
- **Questions**: Post in project discussions
- **Security**: Report vulnerabilities to security@jarvis.dev

### Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/edge-device-enhancement`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature/edge-device-enhancement`
5. Submit pull request

### Code Style

- Follow ESLint configuration
- Use TypeScript strict mode
- Document complex logic with comments
- Add tests for new features

## 📝 Changelog

### Version 1.0.0 (2024-01-15)

**Features**:
- ✅ Grid, List, and Security view modes
- ✅ Real-time device metrics collection
- ✅ TPM attestation support
- ✅ TEE management integration
- ✅ Remote command execution
- ✅ Advanced filtering and search
- ✅ Security compliance dashboard
- ✅ Historical data tracking

**Improvements**:
- Performance optimizations for large device counts
- Enhanced error handling and user feedback
- Comprehensive documentation

**Fixed**:
- Edge cases in device status updates
- CSS rendering issues on mobile
- API error handling consistency

### Future Roadmap

- [ ] WebSocket real-time updates (v1.1)
- [ ] GraphQL API support (v1.1)
- [ ] ML-based anomaly detection (v1.2)
- [ ] Device provisioning automation (v1.2)
- [ ] Advanced analytics dashboard (v1.3)
- [ ] Mobile app support (v2.0)

## 📄 License

This component is part of the J.A.R.V.I.S. project and is licensed under the project's main license. See LICENSE file for details.

---

**Last Updated**: January 15, 2024
**Maintained by**: Frontend & Backend Teams
**Status**: Production Ready ✅
