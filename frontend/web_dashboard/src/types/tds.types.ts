/**
 * Tactical Defense Shield (TDS) Type Definitions
 * Firewall, DPI, VPN, Zero-Trust, and Network Security Types
 */

// ============================================================================
// TELEMETRY AND PACKET EVENTS
// ============================================================================

/**
 * Raw telemetry event from the network
 */
export interface TelemetryEvent {
  eventId: string
  timestamp: string
  type: 'packet' | 'flow' | 'alert' | 'session' | 'attestation'
  severity: 'info' | 'low' | 'medium' | 'high' | 'critical'
  source: string
  sourcePort?: number
  destination: string
  destPort?: number
  protocol?: string
  payload?: Record<string, string | number | boolean>
}

/**
 * Network packet with DPI analysis
 */
export interface PacketEvent extends TelemetryEvent {
  type: 'packet'
  src: string
  srcPort: number
  dst: string
  dstPort: number
  protocol: 'tcp' | 'udp' | 'icmp' | 'other'
  payloadSize: number
  flags?: string[]
  signature?: string
  riskScore: number // 0-1
  isBlocked: boolean
  isAnomalous: boolean
  threatType?: string
}

/**
 * Suspicious signature matched during DPI inspection
 */
export interface SuspiciousSignature {
  signatureId: string
  name: string
  pattern: string
  category: 'malware' | 'exploit' | 'reconnaissance' | 'command_control' | 'data_exfiltration' | 'anomaly'
  severity: 'low' | 'medium' | 'high' | 'critical'
  hitCount: number
  lastTriggered: string
  enabled: boolean
  description: string
  referenceUrl?: string
  cveId?: string[]
  threatActors?: string[]
}

/**
 * DPI Rule for pattern matching
 */
export interface DPIRule {
  ruleId: string
  name: string
  description: string
  signature: string
  category: 'malware' | 'exploit' | 'reconnaissance' | 'command_control' | 'data_exfiltration' | 'anomaly' | 'policy_violation'
  severity: 'info' | 'low' | 'medium' | 'high' | 'critical'
  enabled: boolean
  actions: ('alert' | 'block' | 'drop' | 'replace' | 'log')[]
  hitCount: number
  lastTriggered?: string
  createdAt: string
  updatedAt: string
  tags?: string[]
  cvss?: number
  threatLevel?: number
}

// ============================================================================
// VPN AND CONNECTIVITY
// ============================================================================

/**
 * Active VPN session
 */
export interface VPNSession {
  sessionId: string
  userId: string
  deviceId?: string
  deviceName?: string
  vpnGateway: string
  protocol: 'wireguard' | 'openvpn' | 'ipsec' | 'custom'
  encryptionAlgo: string
  connectedAt: string
  lastActivity: string
  bytesIn: number
  bytesOut: number
  packetsIn: number
  packetsOut: number
  latencyMs: number
  bandwidth: number
  publicIp?: string
  internalIp?: string
  isActive: boolean
  trustLevel: 'trusted' | 'unknown' | 'suspicious'
}

// ============================================================================
// ZERO TRUST AND ATTESTATION
// ============================================================================

/**
 * Device attestation claim
 */
export interface AttestationClaim {
  claimId: string
  claimType: 'tpm' | 'secure_boot' | 'disk_encryption' | 'antivirus' | 'firewall' | 'patch_level' | 'compliance_score'
  value: boolean | number | string
  verified: boolean
  verifiedAt?: string
  evidenceHash?: string
}

/**
 * Device attestation request
 */
export interface AttestationRequest {
  deviceId: string
  deviceName: string
  userId: string
  challenge: string
  claims: AttestationClaim[]
  signature?: string
  certificate?: string
}

/**
 * Device attestation response
 */
export interface AttestationResponse {
  attestationId: string
  deviceId: string
  deviceName: string
  userId: string
  timestamp: string
  verified: boolean
  trustScore: number // 0-1
  claims: AttestationClaim[]
  complianceStatus: 'compliant' | 'non_compliant' | 'unknown'
  recommendations?: string[]
  expiresAt: string
}

/**
 * Zero-trust attestation state
 */
export interface ZeroTrustAttestation {
  attestationId: string
  deviceId: string
  deviceName: string
  osType: 'windows' | 'macos' | 'linux' | 'ios' | 'android'
  osVersion: string
  verified: boolean
  trustScore: number // 0-1
  complianceStatus: 'compliant' | 'non_compliant' | 'unknown'
  claimStatuses: Record<string, boolean>
  lastVerified: string
  lastActivity: string
  vulnerabilities: {
    count: number
    critical: number
    high: number
    medium: number
  }
  patchStatus: 'up_to_date' | 'pending_patches' | 'outdated'
  antivirus: {
    installed: boolean
    enabled: boolean
    lastSignatureUpdate: string
  }
  firewall: {
    enabled: boolean
    inboundRules: number
    outboundRules: number
  }
  diskEncryption: {
    enabled: boolean
    encryptionType?: string
  }
  secureBoot: boolean
  approvalRequired: boolean
  blockedReason?: string
}

// ============================================================================
// NETWORK TOPOLOGY AND MICRO-SEGMENTATION
// ============================================================================

/**
 * Network node in micro-segmentation map
 */
export interface MicroSegmentNode {
  nodeId: string
  name: string
  type: 'server' | 'workstation' | 'iot' | 'external' | 'gateway' | 'database'
  ipAddress: string
  zone: string // Zone/segment identifier
  trustLevel: 'high' | 'medium' | 'low' | 'untrusted'
  isIsolated: boolean
  lastSeen: string
  inboundConnections: number
  outboundConnections: number
  blockedConnections: number
  threatIndicators: string[]
  services: string[]
  position?: { x: number; y: number } // For canvas positioning
}

/**
 * Traffic flow between nodes
 */
export interface TrafficFlow {
  flowId: string
  source: string
  destination: string
  protocol: string
  packetsPerSec: number
  bytesPerSec: number
  isAllowed: boolean
  isBlocked: boolean
  riskScore: number
  anomalyDetected: boolean
}

/**
 * Micro-segmentation zone
 */
export interface SegmentationZone {
  zoneId: string
  name: string
  trustLevel: 'high' | 'medium' | 'low' | 'isolated'
  description: string
  ingressRules: number
  egressRules: number
  nodeCount: number
  inboundThreatCount: number
  outboundThreatCount: number
  isActive: boolean
}

// ============================================================================
// PACKET STREAM VISUALIZATION
// ============================================================================

/**
 * Particle for WebGL visualization
 */
export interface Particle {
  id: string
  x: number
  y: number
  vx: number // velocity x
  vy: number // velocity y
  size: number
  color: [number, number, number, number] // RGBA
  lifespan: number
  maxLifespan: number
  riskScore: number
  srcPort?: number
  dstPort?: number
}

/**
 * Packet stream data for visualization
 */
export interface PacketStreamData {
  packetId: string
  timestamp: string
  source: string
  sourcePort?: number
  destination: string
  destPort?: number
  protocol: string
  bytes: number
  riskScore: number // 0-1 (green < 0.3, yellow 0.3-0.7, red > 0.7)
  isBlocked: boolean
  isAnomalous: boolean
  signature?: string
  flowState: 'new' | 'established' | 'closing' | 'closed'
}

/**
 * WebGL canvas context data
 */
export interface CanvasContextData {
  particles: Particle[]
  srcClusters: Map<string, { x: number; y: number; count: number }>
  dstClusters: Map<string, { x: number; y: number; count: number }>
  blockingRate: number
  totalBandwidth: number
  anomalyRate: number
}

// ============================================================================
// ACTIONS AND ALERTS
// ============================================================================

/**
 * Alert from security system
 */
export interface SecurityAlert {
  alertId: string
  timestamp: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  title: string
  description: string
  source: string
  destination?: string
  signature?: string
  threatType?: string
  action: 'alert' | 'block' | 'isolate' | 'investigate'
  resolved: boolean
  resolvedAt?: string
  relatedEvents: string[]
}

/**
 * IP/endpoint blocking action
 */
export interface BlockAction {
  actionId: string
  timestamp: string
  ipAddress: string
  reason: string
  duration?: number // seconds, null = permanent
  blockedBy: string
  isActive: boolean
  expiresAt?: string
}

/**
 * Endpoint isolation action
 */
export interface IsolationAction {
  actionId: string
  timestamp: string
  deviceId: string
  deviceName: string
  reason: string
  networkAccess: 'none' | 'internal_only' | 'whitelist'
  whitelistedIps?: string[]
  isolatedBy: string
  isActive: boolean
  duration?: number
  expiresAt?: string
}

/**
 * Enforcement action (block IP, isolate endpoint)
 */
export interface EnforcementAction {
  actionId: string
  timestamp: string
  actionType: 'block_ip' | 'isolate_endpoint' | 'drop_traffic' | 'redirect' | 'alert'
  target: string
  reason: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  duration?: number
  confirmed: boolean
  confirmedBy?: string
  confirmedAt?: string
  status: 'pending' | 'approved' | 'rejected' | 'active' | 'expired'
}

// ============================================================================
// REDUX STATE
// ============================================================================

/**
 * Complete TDS Redux state
 */
export interface TDSState {
  // Packet stream and telemetry
  packetStream: PacketStreamData[]
  livePackets: PacketEvent[]
  packetStreamActive: boolean
  latestPackets: PacketStreamData[] // Last 50 packets
  anomalyRate: number // 0-1
  blockingRate: number // 0-1
  totalBandwidth: number // bytes/sec

  // DPI rules and signatures
  rules: DPIRule[]
  suspiciousSignatures: SuspiciousSignature[]
  signatureMatches: Map<string, number> // signature -> hit count
  activeSignatures: SuspiciousSignature[]
  rulesLoaded: boolean

  // VPN sessions
  vpnSessions: VPNSession[]
  activeSessionCount: number
  vpnSessionsLoaded: boolean

  // Zero-trust and attestation
  attestationPending: boolean
  attestationModalOpen: boolean
  currentAttestation: ZeroTrustAttestation | null
  deviceComplianceStatus: 'compliant' | 'non_compliant' | 'unknown'
  trustScore: number // 0-1

  // Network topology
  microSegmentNodes: MicroSegmentNode[]
  trafficFlows: TrafficFlow[]
  segmentationZones: SegmentationZone[]
  topologyLoaded: boolean
  isolatedEndpoints: string[]

  // Alerts and actions
  alerts: SecurityAlert[]
  blockActions: BlockAction[]
  isolationActions: IsolationAction[]
  pendingEnforcements: EnforcementAction[]
  recentAlerts: SecurityAlert[]

  // UI state
  selectedPacket: PacketEvent | null
  selectedRule: DPIRule | null
  selectedSession: VPNSession | null
  filterCriteria: {
    protocol?: string
    severity?: string
    riskMin?: number
    riskMax?: number
    source?: string
    destination?: string
  }
  searchQuery: string
  viewMode: 'grid' | 'list' | 'topology'

  // Connectivity
  isOnline: boolean
  wsConnected: boolean
  telemetryLatency: number // ms

  // Error handling
  error: string | null
  warning: string | null
  lastUpdate: string
}

// ============================================================================
// WebSocket Message Types
// ============================================================================

export type WSMessage =
  | { type: 'telemetry_event'; payload: TelemetryEvent }
  | { type: 'packet_event'; payload: PacketEvent }
  | { type: 'signature_match'; payload: SuspiciousSignature & { matchedAt: string; packetId: string } }
  | { type: 'security_alert'; payload: SecurityAlert }
  | { type: 'anomaly_detected'; payload: { packetId: string; anomalyScore: number; description: string } }
  | { type: 'connection_state'; payload: { status: 'connected' | 'connecting' | 'disconnected'; message: string } }
  | { type: 'rate_update'; payload: { blockingRate: number; anomalyRate: number; timestamp: string } }
  | { type: 'error'; payload: { message: string; code: string; timestamp: string } }

// ============================================================================
// API Request/Response Types
// ============================================================================

/**
 * DPI rules list response
 */
export interface DPIRulesResponse {
  rules: DPIRule[]
  totalCount: number
  activeCount: number
  lastUpdated: string
}

/**
 * VPN sessions response
 */
export interface VPNSessionsResponse {
  sessions: VPNSession[]
  totalCount: number
  activeCount: number
  totalBandwidth: number
  lastUpdated: string
}

/**
 * Policy enforcement response
 */
export interface PolicyEnforcementResponse {
  actionId: string
  status: 'pending' | 'approved' | 'rejected' | 'active'
  message: string
  executedAt?: string
  requiresApproval: boolean
}
