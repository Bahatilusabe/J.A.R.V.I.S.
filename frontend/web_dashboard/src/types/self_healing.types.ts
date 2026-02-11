/**
 * Self-Healing Engine with Reinforcement Learning (RL)
 * Types for MARL (Multi-Agent Reinforcement Learning) simulation
 * Agent-based modeling with attackers vs defenders and reward optimization
 */

// ============================================================================
// AGENT TYPES
// ============================================================================

export type AgentType = 'attacker' | 'defender' | 'neutral';
export type AgentStatus = 'active' | 'disabled' | 'recovering' | 'compromised';
export type AgentStrategy = 'aggressive' | 'defensive' | 'evasive' | 'cooperative';

export interface Agent {
  id: string;
  type: AgentType;
  status: AgentStatus;
  strategy: AgentStrategy;
  x: number;
  y: number;
  energy: number;
  successRate: number;
  successCount: number;
  failureCount: number;
  lastActionTime: string;
  rewardAccumulated: number;
  policyVersion: string;
  targetId?: string;
}

export interface AgentMap {
  attackers: Agent[];
  defenders: Agent[];
  totalAgents: number;
  activeAgents: number;
  compromisedAgents: number;
  recoveryNeeded: number;
}

// ============================================================================
// REWARD FUNCTION TYPES
// ============================================================================

export type RewardMetric = 'total' | 'defense_success' | 'attack_prevention' | 'recovery_speed' | 'resource_efficiency';

export interface RewardDataPoint {
  tick: number;
  timestamp: string;
  totalReward: number;
  defenseReward: number;
  attackReward: number;
  recoveryReward: number;
  efficiency: number;
  trend: 'improving' | 'stable' | 'declining';
}

export interface RewardFunction {
  metric: RewardMetric;
  avgReward: number;
  maxReward: number;
  minReward: number;
  rewardHistory: RewardDataPoint[];
  convergenceRate: number;
  lastUpdate: string;
}

export interface RewardSnapshot {
  timestamp: string;
  tick: number;
  avgReward: number;
  attackers: number;
  defenders: number;
  policyVersion: string;
  convergenceStatus: 'converging' | 'oscillating' | 'diverging';
}

// ============================================================================
// POLICY TYPES
// ============================================================================

export type PolicyStatus = 'training' | 'validating' | 'deployed' | 'archived' | 'failed';
export type PolicyType = 'cooperative' | 'competitive' | 'hierarchical' | 'adaptive';

export interface PolicyVersion {
  version: string;
  semanticVersion: string;
  status: PolicyStatus;
  type: PolicyType;
  timestamp: string;
  trainingEpochs: number;
  finalReward: number;
  convergenceAchieved: boolean;
  convergenceMetric: number;
  accuracyMetrics: {
    defenseAccuracy: number;
    attackSuccessRate: number;
    recoverySuccess: number;
  };
  parentVersion?: string;
  childVersions: string[];
  updateCount: number;
  lastDeployed?: string;
  performanceScore: number;
}

export interface PolicyUpdate {
  tick: number;
  timestamp: string;
  previousVersion: string;
  newVersion: string;
  policyDelta: {
    agentCount: number;
    updatedAgents: number;
    rolloutStatus: 'pending' | 'in_progress' | 'complete' | 'failed';
  };
  performanceImprovement: number;
}

export interface PolicyTimeline {
  versions: PolicyVersion[];
  updates: PolicyUpdate[];
  currentVersion: string;
  deploymentHistory: Array<{
    version: string;
    deployedAt: string;
    metrics: {
      avgReward: number;
      successRate: number;
      convergenceRate: number;
    };
  }>;
}

// ============================================================================
// SIMULATION TYPES
// ============================================================================

export type SimulationStatus = 'idle' | 'running' | 'paused' | 'stopping' | 'stopped' | 'error';
export type SimulationMode = 'training' | 'evaluation' | 'attack_scenario' | 'recovery_test';

export interface SimulationConfig {
  mode: SimulationMode;
  initialAttackers: number;
  initialDefenders: number;
  gridWidth: number;
  gridHeight: number;
  tickInterval: number;
  maxEpisodes: number;
  maxStepsPerEpisode: number;
  learningRate: number;
  discountFactor: number;
  explorationRate: number;
  aggregationMethod: 'fedavg' | 'secure_aggregation' | 'gossip';
  privacyBudget: number;
}

export interface SimulationMetrics {
  currentTick: number;
  elapsedTime: number;
  attackers: number;
  defenders: number;
  compromised: number;
  recovered: number;
  avgReward: number;
  totalReward: number;
  policyVersion: string;
  convergenceProgress: number;
  estimatedCompletion?: string;
}

export interface SimulationState {
  status: SimulationStatus;
  config: SimulationConfig;
  metrics: SimulationMetrics;
  agents: AgentMap;
  rewardFunction: RewardFunction;
  policyTimeline: PolicyTimeline;
  startTime: string;
  lastUpdate: string;
}

export interface SimulationSnapshot {
  id: string;
  timestamp: string;
  tick: number;
  mode: SimulationMode;
  agentCount: number;
  avgReward: number;
  policyVersion: string;
  metrics: SimulationMetrics;
  agentStates: Agent[];
  description: string;
  automated: boolean;
  autoRecovery?: {
    enabled: boolean;
    triggers: string[];
    status: 'success' | 'pending' | 'failed';
  };
}

// ============================================================================
// ACTION & EVENT TYPES
// ============================================================================

export type ActionType = 'attack' | 'defend' | 'isolate' | 'recover' | 'observe' | 'coordinate' | 'adapt';
export type EventType = 'agent_action' | 'breach_detected' | 'recovery_initiated' | 'policy_updated' | 'convergence_achieved' | 'system_metric_change';

export interface RLAction {
  agentId: string;
  actionType: ActionType;
  targetId?: string;
  parameters: Record<string, number | string | boolean>;
  probability: number;
  timestamp: string;
}

export interface RLEvent {
  id: string;
  type: EventType;
  tick: number;
  timestamp: string;
  agentId?: string;
  description: string;
  severity: 'info' | 'warning' | 'critical';
  metadata: Record<string, string | number | boolean | string[]>;
}

export interface ActionLog {
  timestamp: string;
  tick: number;
  actions: RLAction[];
  events: RLEvent[];
  averageReward: number;
  policyVersion: string;
}

// ============================================================================
// RECOVERY & SNAPSHOT TYPES
// ============================================================================

export type SnapshotStatus = 'available' | 'restoring' | 'failed' | 'archived';
export type RecoveryStatus = 'pending' | 'in_progress' | 'success' | 'failed' | 'rollback';

export interface RecoveryAction {
  id: string;
  snapshotId: string;
  timestamp: string;
  recoveryType: 'full' | 'partial' | 'differential';
  targetTick: number;
  affectedAgents: string[];
  status: RecoveryStatus;
  restoreTime?: number;
  errorMessage?: string;
  rollbackAvailable: boolean;
}

export interface SnapshotMetadata {
  id: string;
  name: string;
  description: string;
  createdAt: string;
  tick: number;
  size: number;
  metrics: {
    avgReward: number;
    defenseSuccess: number;
    convergenceRate: number;
  };
  status: SnapshotStatus;
  agentCount: number;
  policyVersion: string;
  automated: boolean;
  retentionDays: number;
  encryption: 'AES-256-GCM' | 'PALISADE_HE';
  location: 'local' | 'backup' | 'replicated';
}

export interface RecoveryLog {
  id: string;
  timestamp: string;
  recoveryAction: RecoveryAction;
  duration: number;
  agentsRestored: number;
  agentsFailed: number;
  dataIntegrityCheck: {
    passed: boolean;
    checksum: string;
    verifyTime: number;
  };
  logs: string[];
}

// ============================================================================
// WEBSOCKET MESSAGE TYPES
// ============================================================================

export type WSMessageType = 'agent_update' | 'reward_update' | 'policy_update' | 'action_event' | 'snapshot_trigger' | 'simulation_control' | 'metrics_update' | 'error';

export interface AgentUpdateMessage {
  type: 'agent_update';
  tick: number;
  agents: Agent[];
  agentCount: {
    attackers: number;
    defenders: number;
    compromised: number;
  };
}

export interface RewardUpdateMessage {
  type: 'reward_update';
  tick: number;
  timestamp: string;
  avgReward: number;
  totalReward: number;
  rewardDelta: number;
  convergenceProgress: number;
  rewardTrend: 'improving' | 'stable' | 'declining';
}

export interface PolicyUpdateMessage {
  type: 'policy_update';
  tick: number;
  timestamp: string;
  previousVersion: string;
  newVersion: string;
  updateScope: 'all_agents' | 'subset' | 'rollout';
  performanceImprovement: number;
}

export interface ActionEventMessage {
  type: 'action_event';
  tick: number;
  timestamp: string;
  action: RLAction;
  result: {
    success: boolean;
    rewardDelta: number;
    description: string;
  };
  agentRewardUpdate: number;
}

export interface SnapshotTriggerMessage {
  type: 'snapshot_trigger';
  timestamp: string;
  snapshotId: string;
  reason: 'convergence' | 'recovery' | 'scheduled' | 'threshold' | 'manual';
  tick: number;
  metrics: SimulationMetrics;
}

export interface SimulationControlMessage {
  type: 'simulation_control';
  command: 'start' | 'pause' | 'resume' | 'stop' | 'checkpoint' | 'recover';
  timestamp: string;
  parameters?: Record<string, string | number | boolean>;
}

export interface MetricsUpdateMessage {
  type: 'metrics_update';
  tick: number;
  timestamp: string;
  metrics: SimulationMetrics;
  systemHealth: {
    cpuUsage: number;
    memoryUsage: number;
    networkLatency: number;
  };
}

export interface ErrorMessage {
  type: 'error';
  timestamp: string;
  code: string;
  message: string;
  severity: 'warning' | 'error' | 'critical';
  recoverySuggestion?: string;
}

export type SelfHealingWSMessage = 
  | AgentUpdateMessage 
  | RewardUpdateMessage 
  | PolicyUpdateMessage 
  | ActionEventMessage 
  | SnapshotTriggerMessage 
  | SimulationControlMessage 
  | MetricsUpdateMessage 
  | ErrorMessage;

// ============================================================================
// API RESPONSE TYPES
// ============================================================================

export interface SimulationStartRequest {
  mode: SimulationMode;
  initialAttackers: number;
  initialDefenders: number;
  config?: Partial<SimulationConfig>;
}

export interface SimulationStartResponse {
  jobId: string;
  status: 'started' | 'error';
  message: string;
  timestamp: string;
}

export interface MetricsResponse {
  jobId: string;
  metrics: SimulationMetrics;
  rewardHistory: RewardDataPoint[];
  agents: AgentMap;
  policyVersion: string;
  timestamp: string;
}

export interface RecoveryRequest {
  snapshotId: string;
  recoveryType: 'full' | 'partial' | 'differential';
  targetTick?: number;
}

export interface RecoveryResponse {
  jobId: string;
  recoveryId: string;
  status: RecoveryStatus;
  estimatedDuration: number;
  message: string;
  timestamp: string;
}

// ============================================================================
// REDUX STATE SHAPE
// ============================================================================

export interface SelfHealingState {
  // Simulation
  simulationStatus: SimulationStatus;
  currentJobId?: string;
  simulationConfig: SimulationConfig;
  startTime?: string;

  // Agents
  agents: AgentMap;
  selectedAgentId?: string;
  agentFilterType?: AgentType;

  // Rewards
  rewardFunction: RewardFunction;
  rewardHistory: RewardDataPoint[];
  selectedRewardMetric: RewardMetric;

  // Policies
  policyTimeline: PolicyTimeline;
  currentPolicyVersion: string;
  selectedPolicyVersions: string[];
  policyComparison: {
    version1?: PolicyVersion;
    version2?: PolicyVersion;
    differences?: Record<string, string | number | boolean>;
  };

  // Snapshots
  snapshots: SnapshotMetadata[];
  selectedSnapshotId?: string;
  recoveryInProgress: boolean;

  // Metrics
  metrics: SimulationMetrics;
  lastUpdate: string;
  timelineSteps: Array<{
    step: number;
    actions: Record<string, number>;
    rewards: Record<string, number>;
    infos: Record<string, Record<string, unknown>>;
    ts: string;
  }>;

  // WebSocket
  wsConnected: boolean;
  wsLatency: number;

  // UI
  activeTab: 'simulation' | 'rewards' | 'policies' | 'recovery' | 'metrics';
  showSnapshotModal: boolean;
  showRecoveryLog: boolean;

  // Status
  error?: string;
  warning?: string;
  success?: string;
  isLoading: boolean;
}

// ============================================================================
// HELPER TYPES
// ============================================================================

export interface SimulationProgress {
  currentTick: number;
  maxTicks: number;
  percentage: number;
  estimatedTimeRemaining: number;
  convergenceProgress: number;
}

export interface AgentStatistics {
  totalAgents: number;
  activeCount: number;
  compromisedCount: number;
  recoveryNeeded: number;
  avgEnergy: number;
  avgSuccessRate: number;
  totalRewardAccumulated: number;
}

export interface PolicyComparisonMetrics {
  version1: string;
  version2: string;
  rewardDifference: number;
  convergenceSpeedDifference: number;
  accuracyDifference: {
    defense: number;
    attack: number;
    recovery: number;
  };
  agentCountDifference: number;
  deploymentTimeDifference: number;
}

export interface SystemHealth {
  simulationHealth: number;
  agentHealth: number;
  convergenceHealth: number;
  recoveryReadiness: number;
  overallHealth: number;
}
