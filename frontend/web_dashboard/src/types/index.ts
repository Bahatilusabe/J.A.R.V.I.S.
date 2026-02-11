// API Response types
export interface ApiResponse<T> {
  success: boolean
  data: T
  error?: string
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  hasMore: boolean
}

// Authentication types
export interface AuthToken {
  accessToken: string
  refreshToken: string
  expiresIn: number
  tokenType: 'Bearer' | 'PQC'
  pqcEnabled: boolean
}

export interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'analyst' | 'viewer'
  permissions: string[]
  createdAt: string
  lastLogin?: string
}

export interface AuthState {
  user: User | null
  token: AuthToken | null
  isAuthenticated: boolean
  isLoading: boolean
  error?: string
}

// PASM types
export interface AttackPath {
  id: string
  nodes: string[]
  score: number
  risk: 'critical' | 'high' | 'medium' | 'low'
  description: string
  exploits: Exploit[]
  timestamp: string
}

export interface Exploit {
  cveId: string
  title: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  cvss: number
  description: string
}

export interface PasmPrediction {
  nodeId: string
  riskScore: number
  uncertainty: number
  paths: AttackPath[]
  recommendations: string[]
  timestamp: string
}

export interface GraphNode {
  id: string
  label?: string
  type: 'asset' | 'service' | 'network' | 'process' | 'web' | 'app' | 'db' | 'firewall' | 'vpn'
  risk: number
  metadata?: Record<string, unknown>
}

export interface GraphEdge {
  id?: string
  source: string
  target: string
  weight: number
  label?: string
  vuln?: string
}

export interface Graph {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

// Telemetry types
export interface TelemetryEvent {
  id: string
  type: 'alert' | 'metric' | 'log' | 'trace'
  timestamp: string
  source: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  message: string
  metadata?: Record<string, unknown>
}

export interface MetricData {
  name: string
  value: number
  unit: string
  timestamp: string
  threshold?: number
}

export interface TelemetryMetrics {
  cpuUsage: number
  memoryUsage: number
  networkLatency: number
  threatLevel: 'critical' | 'high' | 'medium' | 'low'
  activeAlerts: number
  systemHealth: number
  timestamp: string
}

export interface TelemetryStream {
  id: string
  name: string
  source: string
  events: TelemetryEvent[]
  lastUpdate: string
}

export interface TelemetryAlert {
  id: string
  timestamp: string
  source: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  title: string
  description: string
  affectedAssets: string[]
  remediation?: string
  acknowledged: boolean
}

// Self-healing types
export interface HealingAction {
  id: string
  type: string
  status: 'pending' | 'executing' | 'completed' | 'failed'
  target: string
  description: string
  createdAt: string
  executedAt?: string
}

export interface HealingPolicy {
  id: string
  name: string
  description: string
  conditions: string[]
  actions: string[]
  enabled: boolean
}

// CED types
export interface CedReport {
  id: string
  name: string
  description: string
  createdAt: string
  updatedAt: string
  findings: CedFinding[]
  status: 'draft' | 'published' | 'archived'
}

export interface CedFinding {
  id: string
  title: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  description: string
  remediation: string
  status: 'open' | 'in-progress' | 'resolved'
}

// Real-time types
export interface WebSocketMessage<T = unknown> {
  type: string
  payload: T
  timestamp: string
  clientId?: string
}

export interface ConnectionStatus {
  isConnected: boolean
  lastConnected?: string
  reconnectAttempts: number
  lastError?: string
}

// UI types
export interface NotificationMessage {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  duration?: number
  action?: {
    label: string
    onClick: () => void
  }
}

export interface LoadingState {
  isLoading: boolean
  error?: string
  data?: unknown
}

// Forensics & Blockchain types
export interface ForensicsAuditLog {
  id: string
  timestamp: string
  actor: string
  action: 'read' | 'write' | 'delete' | 'modify'
  resource: string
  status: 'success' | 'failed'
  details: string
}

export interface BlockchainTransaction {
  id: string
  hash: string
  timestamp: string
  source: string
  destination: string
  amount?: number
  status: 'pending' | 'confirmed' | 'failed'
  signature: string
}

export interface LedgerEntry {
  id: string
  timestamp: string
  data: Record<string, unknown>
  hash: string
  previousHash: string
  sequenceNumber: number
}

// Voice & VocalSOC types
export interface VoiceCommand {
  id: string
  timestamp: string
  audio?: string
  text: string
  intent: string
  confidence: number
  parameters: Record<string, unknown>
  status: 'pending' | 'executing' | 'completed' | 'failed'
  result?: string
}

export interface VoiceIntent {
  name: string
  description: string
  parameters: string[]
  actions: string[]
}

export interface ASRResult {
  id: string
  timestamp: string
  text: string
  confidence: number
  alternatives: string[]
}

// Policy & Containment types
export interface PolicyAction {
  id: string
  timestamp: string
  type: string
  target: string
  status: 'pending' | 'executing' | 'completed' | 'failed'
  description: string
  ethicalCheck: {
    passed: boolean
    reason?: string
  }
  executedAt?: string
  result?: Record<string, unknown>
}

export interface PolicyEnforcement {
  id: string
  policy: string
  action: PolicyAction
  triggered: boolean
  timestamp: string
}

export interface ContainmentAction {
  id: string
  type: 'isolate' | 'quarantine' | 'kill-process' | 'block-connection' | 'disable-service'
  target: string
  status: 'pending' | 'executing' | 'completed' | 'failed' | 'reverted'
  reason: string
  timestamp: string
  duration?: number
}

// Metrics types
export interface SystemMetrics {
  cpuUsage: number
  memoryUsage: number
  diskUsage: number
  networkBandwidth: number
  processCount: number
  connectionCount: number
  timestamp: string
}

export interface SecurityMetrics {
  threatLevel: 'critical' | 'high' | 'medium' | 'low'
  alertCount: number
  vulnerabilityCount: number
  unhealtedSystemCount: number
  breachAttempts: number
  successfulBreaches: number
  timestamp: string
}

export interface PerformanceMetrics {
  responseTime: number
  throughput: number
  errorRate: number
  availability: number
  timestamp: string
}

export interface GrafanaPanel {
  id: number
  title: string
  url: string
  height: number
}

// PASM Extended types
export interface PasmDetailedPrediction {
  id: string
  nodeId: string
  assetName: string
  riskScore: number
  uncertainty: number
  confidence: number
  likelihood: number
  impact: number
  exploitability: number
  paths: AttackPath[]
  recommendations: string[]
  historicalData: PasmHistoricalData[]
  timestamp: string
}

export interface PasmHistoricalData {
  timestamp: string
  riskScore: number
  uncertainty: number
  actualBreached: boolean
}

export interface AttackPathDetails {
  id: string
  nodes: Array<{
    id: string
    type: string
    name: string
    riskScore: number
  }>
  edges: Array<{
    source: string
    target: string
    attackMethod: string
    difficulty: number
  }>
  totalRisk: number
  pathLength: number
}

// CED (Causal Explanation & Disinformation) types
export interface CEDNarrative {
  id: string
  narrative: string
  probability: number
  confidence: number
  counterfactuals: string[]
  factors: string[]
  timestamp: string
  eventId?: string
  predictionId?: string
}

export interface CEDExplanation {
  eventId: string
  narrative: CEDNarrative
  relatedEvents: string[]
  suggestedActions: string[]
}
