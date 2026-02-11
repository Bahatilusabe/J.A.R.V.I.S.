/**
 * XDR Federation + Blockchain Ledger Type Definitions
 * 
 * Complete type system for Federated Extended Detection & Response (XDR)
 * with model provenance tracking and immutable blockchain ledger
 */

// ============================================================================
// Federation Types
// ============================================================================

export type NodeStatus = 'online' | 'offline' | 'syncing' | 'error' | 'pending';
export type TrustLevel = 'full' | 'partial' | 'untrusted' | 'verifying';
export type SyncStatus = 'idle' | 'in_progress' | 'completed' | 'failed';

/**
 * Federation Node - represents a node in the federated network
 */
export interface FederationNode {
  nodeId: string;
  nodeName: string;
  region: string;
  ipAddress: string;
  publicKey: string;
  status: NodeStatus;
  trustLevel: TrustLevel;
  lastSyncTime: ISO8601;
  lastSyncDuration: number; // milliseconds
  syncStatus: SyncStatus;
  modelsContributed: number;
  eventsProcessed: number;
  threatDetectionRate: number; // 0-1
  responseTime: number; // milliseconds
  cpuUsage: number; // 0-100
  memoryUsage: number; // MB
  bandwidth: number; // bytes per second
  isLeader: boolean;
  certificateExpiry: ISO8601;
  capabilities: string[]; // ['voice_analysis', 'network_detection', 'threat_response']
  customAttributes: Record<string, string | number | boolean>;
}

/**
 * Sync Event - real-time event during federation sync
 */
export interface SyncEvent {
  eventId: string;
  nodeId: string;
  timestamp: ISO8601;
  type: 'sync_start' | 'model_transfer' | 'ledger_sync' | 'verification' | 'sync_complete' | 'sync_error';
  details: string;
  modelsTransferred?: number;
  entriesSynced?: number;
  duration?: number;
  error?: string;
}

/**
 * Federation Status Response
 */
export interface FederationStatus {
  totalNodes: number;
  onlineNodes: number;
  averageLatency: number; // milliseconds
  lastGlobalSync: ISO8601;
  nextScheduledSync: ISO8601;
  totalModels: number;
  totalEntries: number;
  syncHealth: number; // 0-100 percentage
  encryptionAlgorithm: string; // 'AES-256-GCM'
  consensusStatus: 'achieved' | 'pending' | 'failed';
  leaderNode: string; // nodeId
}

// ============================================================================
// Blockchain Ledger Types
// ============================================================================

export type LedgerEntryType = 'containment' | 'response' | 'forensics' | 'model_update' | 'audit' | 'threat_report' | 'training_complete' | 'policy_change' | 'attestation';
export type EntryStatus = 'pending' | 'confirmed' | 'finalized' | 'archived';

/**
 * Signature Data - cryptographic signature information
 */
export interface SignatureData {
  algorithm: string; // 'DILITHIUM', 'FALCON', 'SPHINCS+'
  signature: string; // hex-encoded
  publicKey: string; // hex-encoded
  timestamp: ISO8601;
  verificationStatus: 'verified' | 'unverified' | 'invalid';
  verifierNodeId?: string;
}

/**
 * Blockchain Ledger Entry - immutable transaction record
 */
export interface BlockchainLedgerEntry {
  txId: string; // tx-555 format
  blockHash: string; // block identifier
  blockHeight: number;
  timestamp: ISO8601;
  type: LedgerEntryType;
  actor: string; // JARVIS-NODE-7
  actorNodeId: string; // internal node ID
  action: string; // containment, response, etc.
  target: string; // IP, device ID, or entity
  targetType: 'ip_address' | 'device' | 'user' | 'model' | 'network';
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  description: string;
  metadata: Record<string, string | number | boolean | string[]>;
  signature: SignatureData;
  status: EntryStatus;
  parentTxId?: string; // link to previous entry
  forensicsId?: string; // reference to forensics data
  proofOfWork?: string; // hash proof
  gasUsed?: number; // computational cost
  confirmations: number; // number of confirmations
  children: string[]; // txIds of child entries
}

/**
 * Forensics Data - detailed evidence and proof documents
 */
export interface ForensicsData {
  forensicsId: string;
  txId: string; // reference to ledger entry
  timestamp: ISO8601;
  actor: string;
  evidence: ForensicsEvidence[];
  jsonPayload: Record<string, string | number | boolean | string[]>;
  signature: SignatureData;
  proofOfExecution: string; // neural contract execution proof
  encryptionKey: string; // reference to encryption key
}

/**
 * Forensics Evidence - individual piece of evidence
 */
export interface ForensicsEvidence {
  evidenceId: string;
  type: 'pcap' | 'log' | 'memory_dump' | 'process_tree' | 'timeline' | 'artifact';
  description: string;
  hash: string; // SHA-256
  size: number; // bytes
  timestamp: ISO8601;
  sourceNode: string;
}

// ============================================================================
// Model Provenance Types
// ============================================================================

export type ModelStatus = 'training' | 'validation' | 'deployed' | 'archived' | 'failed';
export type FrameworkType = 'pytorch' | 'tensorflow' | 'onnx' | 'qiskit' | 'jax';

/**
 * Model Hash - cryptographic hash of model
 */
export interface ModelHash {
  algorithm: string; // SHA-256, SHA-3
  hashValue: string; // hex
  computedAt: ISO8601;
  verificationStatus: 'verified' | 'unverified' | 'mismatched';
  verificationMethod: 'local' | 'federated' | 'consensus';
  verifierNodes: string[]; // nodeIds
}

/**
 * Training Configuration - parameters used in training
 */
export interface TrainingConfig {
  algorithm: string; // DRL, federated_averaging, etc.
  epochs: number;
  batchSize: number;
  learningRate: number;
  optimizer: string; // Adam, SGD, etc.
  lossFunction: string;
  regularization: number;
  dataSource: string;
  dataSamples: number;
  trainingSplitRatio: number; // 0-1
  validationSplitRatio: number; // 0-1
  hyperparameters: Record<string, string | number | boolean>;
}

/**
 * Model Performance - metrics from training/validation
 */
export interface ModelPerformance {
  accuracy: number; // 0-1
  precision: number; // 0-1
  recall: number; // 0-1
  f1Score: number; // 0-1
  rocAuc: number; // 0-1
  trainingLoss: number;
  validationLoss: number;
  inferenceLatency: number; // milliseconds
  throughput: number; // samples per second
  computeTime: number; // seconds
  customMetrics: Record<string, number>;
}

/**
 * Model Provenance Card - complete training history
 */
export interface ModelProvenanceCard {
  modelId: string;
  modelName: string;
  version: string; // semantic versioning
  status: ModelStatus;
  framework: FrameworkType;
  timestamp: ISO8601;
  owner: string; // nodeId
  ownerName: string;
  description: string;
  purpose: string; // 'threat_detection', 'anomaly_detection', etc.
  modelHash: ModelHash;
  parentModelId?: string; // previous version
  parentHash?: string;
  childModelIds: string[]; // versions derived from this
  trainingConfig: TrainingConfig;
  performance: ModelPerformance;
  dataProvenance: string; // federated data sources
  contributingNodes: string[]; // nodeIds
  trainingStartTime: ISO8601;
  trainingEndTime: ISO8601;
  trainingDuration: number; // seconds
  validationDate: ISO8601;
  deplomentDate?: ISO8601;
  retirementDate?: ISO8601;
  modelSize: number; // bytes
  inputShape: number[]; // tensor shape
  outputShape: number[];
  dependencies: string[]; // library versions
  containerImage?: string; // Docker image hash
  signature: SignatureData;
  auditTrail: AuditEntry[];
}

/**
 * Audit Entry - change log for model
 */
export interface AuditEntry {
  entryId: string;
  timestamp: ISO8601;
  actor: string;
  action: 'created' | 'trained' | 'validated' | 'deployed' | 'modified' | 'retired' | 'exported' | 'imported';
  details: string;
  changes?: Record<string, string | number | boolean | string[]>;
  signature?: SignatureData;
}

/**
 * Model Hash Verification - proof of model integrity
 */
export interface ModelHashVerification {
  modelId: string;
  originalHash: string;
  currentHash: string;
  verified: boolean;
  verificationNodes: string[]; // consensus verifiers
  verificationScore: number; // 0-1
  lastVerified: ISO8601;
  issues: string[]; // mismatch details
  proofOfVerification: string; // signed proof
}

// ============================================================================
// Training + Federation Integration
// ============================================================================

/**
 * Federated Training Job
 */
export interface FederatedTrainingJob {
  jobId: string;
  jobName: string;
  modelId: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  startTime: ISO8601;
  endTime?: ISO8601;
  estimatedEndTime?: ISO8601;
  participatingNodes: string[]; // nodeIds
  nodeCount: number;
  roundNumber: number;
  totalRounds: number;
  globalAggregator: string; // nodeId of leader
  trainingConfig: TrainingConfig;
  currentPerformance: ModelPerformance;
  convergenceMetric: number; // 0-1
  dataDistribution: Record<string, number>; // nodeId -> sample count
  communicationCost: number; // bytes exchanged
  computationCost: number; // total CPU-seconds
  privacyBudget: number; // differential privacy epsilon
  encryptionStatus: 'plaintext' | 'encrypted' | 'federated_secret_sharing';
  aggregationMethod: 'fedavg' | 'secure_aggregation' | 'gossip' | 'parameter_server';
  progress: number; // 0-100
  nextUpdateTime?: ISO8601;
}

/**
 * Training Result
 */
export interface TrainingResult {
  jobId: string;
  modelId: string;
  success: boolean;
  finalModelHash: string;
  finalPerformance: ModelPerformance;
  convergenceAchieved: boolean;
  totalRoundsCompleted: number;
  trainingDuration: number; // seconds
  nodeFailures: number;
  communalDataUsed: number; // samples
  privacyMetrics: {
    epsilonUsed: number;
    deltaUsed: number;
    dpMechanism: string;
  };
  forensicsId?: string; // reference to proof
  signedResult: SignatureData;
}

// ============================================================================
// Real-time Events
// ============================================================================

/**
 * Federation Sync Event - WebSocket message type
 */
export interface FederationSyncEvent {
  eventId: string;
  timestamp: ISO8601;
  nodeId: string;
  eventType: 'node_online' | 'node_offline' | 'sync_start' | 'sync_progress' | 'sync_complete' | 'model_received' | 'verification' | 'error';
  details: Record<string, string | number | boolean | string[]>;
  severity: 'info' | 'warning' | 'error';
}

/**
 * Ledger Subscription Event - WebSocket message type
 */
export interface LedgerSubscriptionEvent {
  eventId: string;
  timestamp: ISO8601;
  entryType: LedgerEntryType;
  action: 'entry_created' | 'entry_confirmed' | 'entry_finalized' | 'verification_complete';
  ledgerEntry: BlockchainLedgerEntry;
}

/**
 * WebSocket Message Union Type
 */
export type XDRWSMessage = 
  | { type: 'federation_sync'; payload: FederationSyncEvent }
  | { type: 'ledger_entry'; payload: LedgerSubscriptionEvent }
  | { type: 'node_status'; payload: { nodeId: string; status: NodeStatus; timestamp: ISO8601 } }
  | { type: 'model_update'; payload: { modelId: string; status: ModelStatus; timestamp: ISO8601 } }
  | { type: 'error'; payload: { message: string; code: string; timestamp: ISO8601 } }
  | { type: 'ping'; payload: { timestamp: ISO8601 } };

// ============================================================================
// UI State + Redux
// ============================================================================

/**
 * Federation Ring State - visualization state
 */
export interface FederationRingState {
  nodes: FederationNode[];
  selectedNodeId: string | null;
  highlightedNodeId: string | null;
  syncAnimation: boolean;
  rotationEnabled: boolean;
  showLabels: boolean;
  zoomLevel: number; // 1-10
}

/**
 * Ledger Filter Criteria
 */
export interface LedgerFilterCriteria {
  entryTypes: LedgerEntryType[];
  severities: Array<'critical' | 'high' | 'medium' | 'low' | 'info'>;
  actors: string[];
  dateRange: {
    startDate: ISO8601;
    endDate: ISO8601;
  };
  status: EntryStatus[];
  searchQuery: string;
}

/**
 * Ledger Timeline State
 */
export interface LedgerTimelineState {
  entries: BlockchainLedgerEntry[];
  filteredEntries: BlockchainLedgerEntry[];
  expandedEntryIds: string[];
  selectedEntryId: string | null;
  totalEntries: number;
  pageIndex: number;
  pageSize: number;
  sortOrder: 'descending' | 'ascending';
  filterCriteria: LedgerFilterCriteria;
}

/**
 * Model Provenance State
 */
export interface ModelProvenanceState {
  models: ModelProvenanceCard[];
  selectedModelId: string | null;
  expandedModelIds: string[];
  verifications: Record<string, ModelHashVerification>; // modelId -> verification
  filters: {
    status: ModelStatus[];
    framework: FrameworkType[];
    owner: string[];
  };
}

/**
 * Main XDR Federation Redux State
 */
export interface XDRFederationState {
  // Federation Data
  federationNodes: FederationNode[];
  federationStatus: FederationStatus | null;
  syncEvents: FederationSyncEvent[];
  federationRingState: FederationRingState;
  
  // Ledger Data
  ledgerEntries: BlockchainLedgerEntry[];
  ledgerTimeline: LedgerTimelineState;
  forensicsData: Record<string, ForensicsData>; // forensicsId -> data
  
  // Model Provenance
  modelProvenance: ModelProvenanceState;
  trainingJobs: FederatedTrainingJob[];
  
  // UI State
  selectedNodeId: string | null;
  selectedEntryId: string | null;
  selectedModelId: string | null;
  activeTab: 'federation' | 'ledger' | 'models' | 'training';
  searchQuery: string;
  filterCriteria: {
    nodes: Record<string, string | number | boolean>;
    entries: LedgerFilterCriteria;
    models: Record<string, string | number | boolean>;
  };
  
  // Real-time State
  wsConnected: boolean;
  wsLatency: number; // milliseconds
  isLoading: boolean;
  isRefreshing: boolean;
  lastUpdate: ISO8601;
  
  // Status
  error: string | null;
  warning: string | null;
  successMessage: string | null;
}

// ============================================================================
// Type Aliases
// ============================================================================

type ISO8601 = string; // YYYY-MM-DDTHH:mm:ssZ

// ============================================================================
// Response Types
// ============================================================================

/**
 * API Response for federation status
 */
export interface FederationStatusResponse {
  status: FederationStatus;
  nodes: FederationNode[];
  lastUpdated: ISO8601;
}

/**
 * API Response for ledger entries
 */
export interface LedgerEntriesResponse {
  entries: BlockchainLedgerEntry[];
  totalCount: number;
  pageIndex: number;
  pageSize: number;
  hasMore: boolean;
  lastUpdated: ISO8601;
}

/**
 * API Response for model provenance
 */
export interface ModelProvenanceResponse {
  models: ModelProvenanceCard[];
  totalCount: number;
  lastUpdated: ISO8601;
}

/**
 * API Response for forensics download
 */
export interface ForensicsResponse {
  forensics: ForensicsData;
  signedData: string; // JSON stringified and signed
  signature: string; // cryptographic signature
  verifiable: boolean;
}

/**
 * API Response for training status
 */
export interface TrainingStatusResponse {
  jobs: FederatedTrainingJob[];
  results: TrainingResult[];
  totalJobs: number;
  completedJobs: number;
}
