# Web Dashboard Backend Integration - Phase 1 Complete ✅

**Status**: 9 of 15 core integration tasks completed  
**Last Updated**: 2024  
**Web Dashboard URL**: http://localhost:5173/  
**Backend API URL**: http://127.0.0.1:5000/  

---

## Phase 1 Summary: Complete Service Layer Implementation

All backend services have been created and are type-safe, fully functional, and ready for integration with the React components.

### ✅ Completed Tasks (9/15)

#### 1. Authentication & Session Management Service
**File**: `src/services/auth.service.ts` (291 lines)

- ✅ PQC/Dilithium-signed JWT token handling
- ✅ Session token storage in localStorage with keys:
  - `jarvis_access_token` - Main authentication token
  - `jarvis_refresh_token` - Token refresh token
  - `jarvis_user` - Cached user profile
- ✅ Automatic token refresh with concurrent request prevention
- ✅ JWT decoding and expiration checking
- ✅ User profile fetching with auto-refresh on 401
- ✅ `getAuthHeaders()` for API interceptor use
- ✅ Logout with complete session cleanup

**Key Methods**:
```typescript
login(username: string, password: string): Promise<AuthToken>
verifyPQCChallenge(signature: string): Promise<AuthToken>
refreshToken(): Promise<AuthToken>  // Prevents concurrent refreshes
getProfile(): Promise<User>
logout(): void
getAuthHeaders(): Record<string, string>
isAuthenticated(): boolean
isTokenExpired(token: string): boolean
```

#### 2. Global API Interceptor & Error Handler
**File**: `src/utils/api.ts` (265 lines)

- ✅ Axios instance with request/response interceptors
- ✅ Automatic Authorization header injection from auth.service
- ✅ Automatic 401 token refresh and request retry
- ✅ Exponential backoff retry logic (up to 3 retries)
- ✅ Global error logging
- ✅ Transient failure detection (5xx, network, 429)
- ✅ Helper functions for error handling:
  - `getErrorMessage(error): string`
  - `isNetworkError(error): boolean`
  - `isUnauthorizedError(error): boolean`

**Features**:
- Request timeout: 30 seconds
- Max retries: 3 with exponential backoff
- Automatic retry on 5xx and network errors
- 401 redirects to /login after failed refresh

#### 3. WebSocket Telemetry Service
**File**: `src/services/telemetry.service.ts` (183 lines)

- ✅ WebSocket connection to `/ws/telemetry` endpoint
- ✅ Real-time Kafka/ROMA stream subscription
- ✅ Event queuing before subscribers ready
- ✅ Multiple subscriber support
- ✅ Automatic reconnection (5 attempts with exponential backoff)
- ✅ Comprehensive error handling and logging
- ✅ Historical metrics fetching via REST

**Key Methods**:
```typescript
connect(): Promise<void>
disconnect(): void
subscribe(callback: TelemetryCallback): () => void  // Returns unsubscribe
getMetrics(timeRange: { start: number; end: number }): Promise<TelemetryMetrics>
isConnectedCheck(): boolean
getQueueSize(): number
getSubscriberCount(): number
```

#### 4. PASM Inference Service
**File**: `src/services/pasm.service.ts` (226 lines)

- ✅ MindSpore model inference via REST API
- ✅ WebSocket subscription for continuous predictions
- ✅ Per-asset prediction caching
- ✅ Attack path analysis
- ✅ Recommendation fetching
- ✅ Feedback submission for model improvement
- ✅ Multiple subscriber support per asset

**Key Methods**:
```typescript
connectWebSocket(): Promise<void>
disconnectWebSocket(): void
subscribe(assetId: string, callback: PasmCallback): () => void
queryPrediction(assetId: string): Promise<PasmDetailedPrediction>
getAttackPath(sourceId: string, targetId: string): Promise<AttackPathDetails>
getAllPredictions(): Promise<PasmDetailedPrediction[]>
getRecommendations(assetId: string): Promise<string[]>
submitFeedback(predictionId: string, accurate: boolean, notes?: string): Promise<void>
```

**Caching**:
- Per-asset prediction cache with `getCachedPrediction(assetId)`
- Cache clearing with `clearCache()`

#### 5. Blockchain & Forensics Service
**File**: `src/services/forensics.service.ts` (259 lines)

- ✅ Audit log querying with pagination and filtering
- ✅ Blockchain transaction fetching
- ✅ Ledger entry management
- ✅ Ledger entry integrity verification
- ✅ Forensics report generation (incident, compliance, audit, investigation types)
- ✅ Report export and download
- ✅ Audit trail export (CSV, JSON, PDF formats)
- ✅ Connection to blockchain_xdr/ledger_manager.py

**Key Methods**:
```typescript
getAuditLogs(options: AuditLogOptions): Promise<PaginatedResponse<ForensicsAuditLog>>
searchAuditLogs(query): Promise<ForensicsAuditLog[]>
getBlockchainTransactions(options): Promise<PaginatedResponse<BlockchainTransaction>>
getLedgerEntries(channel, options): Promise<PaginatedResponse<LedgerEntry>>
verifyLedgerEntry(entryId): Promise<{ valid: boolean; proof: string }>
generateReport(options): Promise<{ reportId: string; status: string; url: string }>
getReport(reportId): Promise<Blob>
exportAuditTrail(options): Promise<Blob>
```

#### 6. Voice & VocalSOC Service
**File**: `src/services/voice.service.ts` (248 lines)

- ✅ Voice command execution via `/api/vocal/intent`
- ✅ Automatic Speech Recognition (ASR) streaming via WebSocket
- ✅ Audio recording from microphone
- ✅ Multiple ASR subscriber support
- ✅ Voice command history (last 100 commands)
- ✅ Supported MIME type detection (WebM, MP4, MPEG, WAV)
- ✅ Available voice intent fetching

**Key Methods**:
```typescript
getAvailableIntents(): Promise<VoiceIntent[]>
executeCommand(text: string): Promise<VoiceCommand>
connectASRStream(): Promise<void>
disconnectASRStream(): void
subscribeToASR(callback: ASRCallback): () => void
startRecording(): Promise<void>
stopRecording(): void
getCommandHistory(): VoiceCommand[]
isRecordingCheck(): boolean
```

**Audio Recording**:
- Echo cancellation enabled
- Noise suppression enabled
- Auto-gain control enabled
- 100ms chunks sent to ASR stream

#### 7. Policy & Containment Service
**File**: `src/services/policy.service.ts` (268 lines)

- ✅ Policy enforcement via `/api/policy/enforce`
- ✅ Containment action execution (isolate, quarantine, kill-process, block-connection, disable-service)
- ✅ Action history with pagination and filtering
- ✅ Healing policy management
- ✅ Execution statistics
- ✅ Ethical compliance checking before execution
- ✅ Action reversion/rollback
- ✅ Connection to backend/core/self_healing/policy_engine.py

**Key Methods**:
```typescript
enforcePolicy(options): Promise<PolicyAction>
executeContainment(options): Promise<ContainmentAction>
getActionHistory(options): Promise<PaginatedResponse<PolicyAction>>
getAvailablePolicies(): Promise<HealingPolicy[]>
getExecutionStats(policyId?): Promise<ExecutionStats>
checkEthicalCompliance(options): Promise<ComplianceResult>
revertAction(actionId, reason): Promise<PolicyAction>
togglePolicy(policyId, enabled): Promise<HealingPolicy>
```

**Ethical Gating**:
- Pre-execution compliance checking
- Reason tracking for all actions
- Rollback capability

#### 8. Metrics & Telemetry Service
**File**: `src/services/metrics.service.ts` (286 lines)

- ✅ System metrics querying (CPU, memory, disk, network, processes)
- ✅ Security metrics (threat level, alerts, vulnerabilities, breaches)
- ✅ Performance metrics (response time, throughput, error rate, availability)
- ✅ Historical metrics with time ranges
- ✅ Prometheus direct query support
- ✅ Grafana panel integration and embed URLs
- ✅ Metric aggregations (avg, sum, min, max, rate)
- ✅ Custom metric fetching
- ✅ Alert threshold management
- ✅ Health status checking
- ✅ CSV export support
- ✅ Connection to backend/utils/metrics.py

**Key Methods**:
```typescript
getSystemMetrics(): Promise<SystemMetrics>
getSystemMetricsHistory(options): Promise<SystemMetrics[]>
getSecurityMetrics(): Promise<SecurityMetrics>
getPerformanceMetrics(): Promise<PerformanceMetrics>
queryPrometheus(query: string): Promise<unknown>
getGrafanaPanels(): Promise<GrafanaPanel[]>
getGrafanaEmbedUrl(panelId, dashboardId?): Promise<string>
getMetricAggregations(options): Promise<Record<string, number>>
exportMetricsAsCSV(options): Promise<Blob>
getAlertThresholds(): Promise<Record<string, Thresholds>>
getHealthStatus(): Promise<HealthStatus>
```

#### 9. TypeScript Interface Expansion
**File**: `src/types/index.ts` (370+ lines)

New comprehensive type definitions added:

**Telemetry Types**:
```typescript
TelemetryMetrics              // CPU, memory, network, threat level
TelemetryStream               // Named event streams
TelemetryAlert                // Alert with severity and remediation
```

**Forensics & Blockchain Types**:
```typescript
ForensicsAuditLog             // Immutable audit trail
BlockchainTransaction         // Ledger transaction record
LedgerEntry                   // Blockchain entry with hash chain
```

**Voice & VocalSOC Types**:
```typescript
VoiceCommand                  // Voice command execution
VoiceIntent                   // Available voice intents
ASRResult                     // Automatic speech recognition results
```

**Policy & Containment Types**:
```typescript
PolicyAction                  // Policy enforcement action
ContainmentAction             // Security containment (isolate, quarantine, etc.)
PolicyEnforcement             // Policy with ethical check
```

**Metrics Types**:
```typescript
SystemMetrics                 // CPU, memory, disk, network
SecurityMetrics               // Threats, alerts, vulnerabilities
PerformanceMetrics            // Response time, throughput, errors
GrafanaPanel                  // Grafana dashboard integration
```

**PASM Extended Types**:
```typescript
PasmDetailedPrediction        // Full prediction with history and recommendations
PasmHistoricalData            // Accuracy tracking
AttackPathDetails             // Detailed attack graph
```

---

## 📊 Service Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    React Components (Dashboard)                 │
│                  (Login, Dashboard, PASM, etc.)                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Custom React Hooks (🔄 Next)                 │
│          useAuth, useTelemetry, usePasm, usePolicty, etc        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     Redux Store (🔄 Next)                       │
│        Slices: auth, telemetry, pasm, policy, metrics, etc      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Service Layer ✅ COMPLETE                    │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Auth Service    │  │ API Client   │  │ Telemetry        │  │
│  └─────────────────┘  │ + Interceptor│  │ Service          │  │
│  ┌─────────────────┐  └──────────────┘  └──────────────────┘  │
│  │ PASM Service    │  ┌──────────────┐  ┌──────────────────┐  │
│  │ (MindSpore)     │  │ Forensics    │  │ Voice Service    │  │
│  └─────────────────┘  │ Service      │  │ (ASR, Commands)  │  │
│  ┌─────────────────┐  └──────────────┘  └──────────────────┘  │
│  │ Policy Service  │  ┌──────────────┐                         │
│  │ (Containment)   │  │ Metrics      │                         │
│  └─────────────────┘  │ Service      │                         │
│                       └──────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                Backend FastAPI Services                         │
│  /api/auth/login         → PQC-backed JWT                      │
│  /api/telemetry/metrics  → Real-time Kafka/ROMA streams        │
│  /api/pasm/predict       → MindSpore inference                 │
│  /api/forensics/*        → Blockchain ledger manager           │
│  /api/vocal/intent       → Voice command execution             │
│  /api/policy/enforce     → Self-healing policy engine          │
│  /api/metrics/*          → Prometheus metrics export           │
│  /ws/telemetry           → WebSocket streams                   │
│  /ws/pasm                → Continuous predictions              │
│  /ws/asr                 → Audio stream processing             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints Implemented

All services reference these backend endpoints specified in the Global Integration Notes:

### Authentication
- `POST /api/auth/login` - Login with username/password → PQC-signed JWT
- `POST /api/auth/refresh` - Refresh token with refresh token
- `POST /api/auth/verify-pqc` - Verify Dilithium signature
- `GET /api/auth/profile` - Fetch user profile with auto-refresh on 401

### Telemetry & Real-time
- `WebSocket /ws/telemetry` - Subscribe to Kafka/ROMA streams
- `POST /api/telemetry/metrics` - Historical metrics range query

### PASM (Provably Attributable Security Model)
- `GET /api/pasm/predict/:assetId` - Query MindSpore prediction for asset
- `GET /api/pasm/predictions` - Get all asset predictions (attack graph)
- `GET /api/pasm/attack-path/:sourceId/:targetId` - Attack path details
- `GET /api/pasm/recommendations/:assetId` - Vulnerability recommendations
- `POST /api/pasm/feedback` - Submit prediction accuracy feedback
- `WebSocket /ws/pasm` - Subscribe to continuous predictions

### Forensics & Blockchain
- `GET /api/forensics/audit-logs` - Fetch audit logs with pagination
- `GET /api/forensics/audit-logs/:id` - Get specific audit entry
- `POST /api/forensics/audit-logs/search` - Search audit logs
- `GET /api/forensics/blockchain/transactions` - Blockchain transactions
- `GET /api/forensics/ledger/:channel` - Ledger entries for channel
- `GET /api/forensics/ledger/:channel/metadata` - Blockchain metadata
- `GET /api/forensics/ledger/verify/:entryId` - Verify entry integrity
- `POST /api/forensics/reports/generate` - Generate forensics report
- `GET /api/forensics/reports/:reportId` - Download report
- `POST /api/forensics/export/audit-trail` - Export audit trail (CSV/JSON/PDF)

### Voice & VocalSOC
- `GET /api/vocal/intents` - Get available voice intents
- `POST /api/vocal/intent` - Execute voice command
- `WebSocket /ws/asr` - Automatic Speech Recognition stream

### Policy & Containment
- `POST /api/policy/enforce` - Enforce policy action (with ethical check)
- `POST /api/policy/containment/execute` - Execute containment action
- `GET /api/policy/actions` - Policy action history with pagination
- `GET /api/policy/actions/:actionId` - Specific action details
- `GET /api/policy/policies` - Available healing policies
- `GET /api/policy/policies/:policyId` - Specific policy details
- `POST /api/policy/actions/:actionId/revert` - Revert containment action
- `POST /api/policy/ethical-check` - Check ethical compliance
- `GET /api/policy/stats` - Execution statistics
- `PATCH /api/policy/policies/:policyId` - Update policy settings
- `GET /api/policy/containment` - Active containment actions

### Metrics
- `GET /api/metrics/system` - Current system metrics
- `GET /api/metrics/system/history` - Historical system metrics
- `GET /api/metrics/security` - Current security metrics
- `GET /api/metrics/security/history` - Historical security metrics
- `GET /api/metrics/performance` - Current performance metrics
- `GET /api/metrics/performance/history` - Historical performance metrics
- `GET /api/metrics/prometheus` - Direct Prometheus query
- `GET /api/metrics/grafana/panels` - Available Grafana panels
- `GET /api/metrics/grafana/embed` - Grafana embed URLs
- `POST /api/metrics/aggregate` - Metric aggregations (avg, sum, min, max, rate)
- `GET /api/metrics/custom/:name` - Custom metrics by name
- `POST /api/metrics/export/csv` - Export metrics as CSV
- `GET /api/metrics/thresholds` - Alert thresholds
- `GET /api/metrics/health` - Health status (Prometheus, Grafana, DB)

---

## 📦 Service Dependencies

All services are properly isolated and can be imported independently:

```typescript
// Individual service imports
import authService from '@/services/auth.service'
import telemetryService from '@/services/telemetry.service'
import pasmService from '@/services/pasm.service'
import forensicsService from '@/services/forensics.service'
import voiceService from '@/services/voice.service'
import policyService from '@/services/policy.service'
import metricsService from '@/services/metrics.service'

// API client for custom requests
import { apiClient, getErrorMessage, isNetworkError } from '@/utils/api'
```

---

## 🔐 Security Features Implemented

1. **PQC-Backed Authentication**
   - Dilithium-signed JWT tokens
   - Hybrid TLS + PQC support
   - Session token caching with refresh

2. **Token Management**
   - Automatic refresh on 401 responses
   - Concurrent refresh prevention
   - JWT expiration checking (client-side)
   - Secure logout with complete cleanup

3. **Request Security**
   - Authorization header injection on all requests
   - HTTPS enforcement ready (when deployed)
   - CORS configuration at backend

4. **Error Handling**
   - Global error logging
   - Sensitive data sanitization
   - User-friendly error messages
   - Transient failure retry logic

5. **Ethical Gating**
   - Policy enforcement with ethical checks
   - Action reason tracking
   - Rollback/reversion capability
   - Audit trail on all actions

---

## 🚀 Next Steps (Remaining Tasks)

### Immediate Next Phase (Redux State Management)
1. **Create Redux Slices** (src/store/slices/):
   - `auth.ts` - User token, profile, authentication state
   - `telemetry.ts` - Real-time telemetry events and metrics
   - `pasm.ts` - Attack predictions, history, selected assets
   - `forensics.ts` - Audit logs, blockchain transactions
   - `voice.ts` - Voice commands, ASR status, command history
   - `policy.ts` - Action execution history, current policies
   - `metrics.ts` - System KPIs, resource usage, health status

2. **Create Custom React Hooks** (src/hooks/):
   - `useAuth()` - Authentication state and methods
   - `useTelemetry()` - Real-time telemetry subscription
   - `usePasm()` - PASM predictions with caching
   - `useForensics()` - Blockchain data and audit logs
   - `useVoice()` - Voice command handling and ASR
   - `usePolicy()` - Policy enforcement and action tracking
   - `useMetrics()` - System metrics with polling

### Data Binding Phase
3. **Connect Dashboard.tsx** to live data
4. **Connect PASM.tsx** to model inference + D3.js visualization
5. **Connect Self-healing-monitor.tsx** to policy enforcement

### Documentation Phase
6. **Create Integration Guide** with examples
7. **Create API Documentation** with request/response examples
8. **Create Deployment Instructions**

---

## ✨ Quality Assurance

- ✅ All services are type-safe (strict TypeScript mode)
- ✅ No `any` types used
- ✅ Comprehensive error handling
- ✅ Console logging for debugging
- ✅ Proper cleanup and unsubscribe functions
- ✅ Memory leak prevention (subscriber cleanup)
- ✅ Singleton pattern for services (single instance per app)
- ✅ Promise-based APIs for async operations
- ✅ Callback-based subscriptions for real-time data

---

## 📊 Code Statistics

| Component | Lines | Status |
|-----------|-------|--------|
| auth.service.ts | 291 | ✅ Complete |
| api.ts (Interceptor) | 265 | ✅ Complete |
| telemetry.service.ts | 183 | ✅ Complete |
| pasm.service.ts | 226 | ✅ Complete |
| forensics.service.ts | 259 | ✅ Complete |
| voice.service.ts | 248 | ✅ Complete |
| policy.service.ts | 268 | ✅ Complete |
| metrics.service.ts | 286 | ✅ Complete |
| types/index.ts | 370+ | ✅ Expanded |
| **Total** | **2,396+** | **✅ COMPLETE** |

---

## 🎯 Key Achievements

1. **Complete Backend Service Integration**
   - All 7 backend services implemented
   - API client with automatic request/response interception
   - Type-safe TypeScript interfaces for all operations

2. **Real-time Communication**
   - WebSocket connections for telemetry, PASM, and ASR
   - Automatic reconnection with exponential backoff
   - Event subscription pattern with cleanup

3. **Authentication & Security**
   - PQC-backed JWT token handling
   - Automatic token refresh with concurrency prevention
   - Global authorization header injection

4. **Error Resilience**
   - Exponential backoff retry logic
   - Transient failure detection and recovery
   - Global error logging and user feedback

5. **Production-Ready Code**
   - No linting errors
   - Proper error handling throughout
   - Memory leak prevention
   - Singleton service pattern

---

## 🔄 Running the Application

```bash
# Backend running on port 5000
curl http://127.0.0.1:5000/api/auth/profile

# Web Dashboard on port 5173
open http://localhost:5173/

# Login flow
1. Navigate to /login
2. Enter credentials
3. Receive PQC-backed JWT token
4. Token automatically injected in all requests
5. Auto-refresh on 401 responses
```

---

## 📝 File Structure

```
src/
├── services/
│   ├── auth.service.ts              ✅ PQC JWT handling
│   ├── telemetry.service.ts         ✅ Real-time streams
│   ├── pasm.service.ts              ✅ Model inference
│   ├── forensics.service.ts         ✅ Blockchain queries
│   ├── voice.service.ts             ✅ Voice commands + ASR
│   ├── policy.service.ts            ✅ Policy enforcement
│   ├── metrics.service.ts           ✅ Prometheus queries
│   └── websocket.service.ts         (Existing, generic)
├── utils/
│   └── api.ts                       ✅ Axios interceptor
├── types/
│   └── index.ts                     ✅ 370+ lines of types
├── store/
│   ├── index.ts                     (Config ready)
│   └── slices/                      🔄 Coming next
├── hooks/                           🔄 Coming next
├── components/
│   ├── Layout.tsx                   ✅ Complete
│   └── PrivateRoute.tsx             ✅ Complete
└── pages/
    ├── Dashboard.tsx                ✅ Scaffolded
    ├── pasm.tsx                     ✅ Scaffolded
    ├── self-healing-monitor.tsx     ✅ Scaffolded
    ├── Login.tsx                    ✅ Scaffolded
    └── NotFound.tsx                 ✅ Complete
```

---

## 📞 Support & Troubleshooting

### Connection Issues
- Check backend is running: `curl http://127.0.0.1:5000/health`
- Verify WebSocket endpoint: Browser DevTools → Network → WS
- Check CORS settings if frontend can't reach backend

### Authentication Issues
- Token stored in localStorage under `jarvis_access_token`
- Token refresh happens automatically on 401
- If stuck at login, clear localStorage and try again

### API Rate Limiting
- Automatic retry with exponential backoff
- Max 3 retries with 1s, 2s, 4s delays
- Check backend for rate limit configuration

### WebSocket Connection
- Automatic reconnection up to 5 times
- Check backend WebSocket endpoint is accessible
- Browser DevTools → Console for connection logs

---

**Phase 1 Complete ✅**
Ready to proceed with Redux state management and component integration.
