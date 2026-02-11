import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type {
  Agent,
  AgentMap,
  RewardFunction,
  RewardMetric,
  PolicyTimeline,
  PolicyVersion,
  SimulationStatus,
  SimulationConfig,
  SimulationMetrics,
  SnapshotMetadata,
  SelfHealingState,
} from '@/types/self_healing.types';

// Default config for simulation
const defaultConfig: SimulationConfig = {
  mode: 'training',
  initialAttackers: 5,
  initialDefenders: 10,
  gridWidth: 100,
  gridHeight: 100,
  tickInterval: 500,
  maxEpisodes: 1000,
  maxStepsPerEpisode: 500,
  learningRate: 0.01,
  discountFactor: 0.99,
  explorationRate: 0.1,
  aggregationMethod: 'fedavg',
  privacyBudget: 10.0,
};

const initialState: SelfHealingState = {
  // Simulation
  simulationStatus: 'idle',
  currentJobId: undefined,
  simulationConfig: defaultConfig,
  startTime: undefined,

  // Agents
  agents: {
    attackers: [],
    defenders: [],
    totalAgents: 0,
    activeAgents: 0,
    compromisedAgents: 0,
    recoveryNeeded: 0, // Matches type definition
  },
  selectedAgentId: undefined,
  agentFilterType: undefined,

  // Rewards
  rewardFunction: {
    metric: 'total',
    avgReward: 0,
    maxReward: 0,
    minReward: 0,
    rewardHistory: [],
    convergenceRate: 0,
    lastUpdate: new Date().toISOString(),
  },
  rewardHistory: [],
  selectedRewardMetric: 'total',

  // Policies
  policyTimeline: {
    versions: [],
    updates: [],
    currentVersion: 'v1.0.0',
    deploymentHistory: [],
  },
  currentPolicyVersion: 'v1.0.0',
  selectedPolicyVersions: [],
  policyComparison: {},

  // Snapshots & Recovery
  snapshots: [],
  selectedSnapshotId: undefined,
  recoveryInProgress: false,

  // Metrics
  metrics: {
    currentTick: 0,
    elapsedTime: 0,
    attackers: 0,
    defenders: 0,
    compromised: 0,
    recovered: 0,
    avgReward: 0,
    totalReward: 0,
    policyVersion: 'v1.0.0',
    convergenceProgress: 0,
    estimatedCompletion: '',
  },
  lastUpdate: new Date().toISOString(),
  timelineSteps: [] as Array<{
    step: number;
    actions: Record<string, number>;
    rewards: Record<string, number>;
    infos: Record<string, Record<string, unknown>>;
    ts: string;
  }>,

  // WebSocket & Connection
  wsConnected: false,
  wsLatency: 0,

  // UI State
  activeTab: 'simulation',
  showSnapshotModal: false,
  showRecoveryLog: false,

  // Status & Errors
  error: undefined,
  warning: undefined,
  success: undefined,
  isLoading: false,
};

export const selfHealingSlice = createSlice({
  name: 'selfHealing',
  initialState,
  reducers: {
    // Simulation actions
    setSimulationStatus: (state, action: PayloadAction<SimulationStatus>) => {
      state.simulationStatus = action.payload;
    },

    setSimulationConfig: (state, action: PayloadAction<Partial<SimulationConfig>>) => {
      state.simulationConfig = { ...state.simulationConfig, ...action.payload };
    },

    setCurrentJobId: (state, action: PayloadAction<string>) => {
      state.currentJobId = action.payload;
    },

    setStartTime: (state) => {
      state.startTime = new Date().toISOString();
    },

    // Agent actions
    setAgents: (state, action: PayloadAction<Partial<AgentMap>>) => {
      state.agents = { ...state.agents, ...action.payload };
    },

    updateAgent: (state, action: PayloadAction<Agent>) => {
      const agentId = action.payload.id;
      if (action.payload.type === 'attacker') {
        const idx = state.agents.attackers.findIndex((a) => a.id === agentId);
        if (idx >= 0) {
          state.agents.attackers[idx] = action.payload;
        }
      } else if (action.payload.type === 'defender') {
        const idx = state.agents.defenders.findIndex((a) => a.id === agentId);
        if (idx >= 0) {
          state.agents.defenders[idx] = action.payload;
        }
      }
    },

    selectAgent: (state, action: PayloadAction<string | undefined>) => {
      state.selectedAgentId = action.payload;
    },

    // Reward actions
    setRewardFunction: (state, action: PayloadAction<Partial<RewardFunction>>) => {
      state.rewardFunction = { ...state.rewardFunction, ...action.payload };
    },

    addRewardDataPoint: (state, action: PayloadAction<Record<string, number | string>>) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      state.rewardHistory.push(action.payload as any);
      // Keep only last 1000 points for performance
      if (state.rewardHistory.length > 1000) {
        state.rewardHistory.shift();
      }
    },

    selectRewardMetric: (state, action: PayloadAction<RewardMetric>) => {
      state.selectedRewardMetric = action.payload;
    },

    // Policy actions
    setPolicyTimeline: (state, action: PayloadAction<Partial<PolicyTimeline>>) => {
      state.policyTimeline = { ...state.policyTimeline, ...action.payload };
    },

    setCurrentPolicy: (state, action: PayloadAction<string>) => {
      state.currentPolicyVersion = action.payload;
    },

    addPolicyVersion: (state, action: PayloadAction<PolicyVersion>) => {
      state.policyTimeline.versions.push(action.payload);
    },

    selectPolicyVersions: (state, action: PayloadAction<string[]>) => {
      state.selectedPolicyVersions = action.payload;
    },

    // Snapshot actions
    setSnapshots: (state, action: PayloadAction<SnapshotMetadata[]>) => {
      state.snapshots = action.payload;
    },

    addSnapshot: (state, action: PayloadAction<SnapshotMetadata>) => {
      state.snapshots.push(action.payload);
      // Keep only last 50 snapshots
      if (state.snapshots.length > 50) {
        state.snapshots.shift();
      }
    },

    selectSnapshot: (state, action: PayloadAction<string>) => {
      state.selectedSnapshotId = action.payload;
    },

    // Recovery actions
    setRecoveryInProgress: (state, action: PayloadAction<boolean>) => {
      state.recoveryInProgress = action.payload;
    },

    // Metrics actions
    setMetrics: (state, action: PayloadAction<SimulationMetrics>) => {
      state.metrics = action.payload;
      state.lastUpdate = new Date().toISOString();
    },

    setTimelineSteps: (state, action: PayloadAction<Array<{
      step: number;
      actions: Record<string, number>;
      rewards: Record<string, number>;
      infos: Record<string, Record<string, unknown>>;
      ts: string;
    }>>) => {
      state.timelineSteps = action.payload;
    },

    // WebSocket actions
    setWebSocketConnected: (state, action: PayloadAction<boolean>) => {
      state.wsConnected = action.payload;
    },

    setWebSocketLatency: (state, action: PayloadAction<number>) => {
      state.wsLatency = action.payload;
    },

    // UI actions
    setActiveTab: (
      state,
      action: PayloadAction<'simulation' | 'rewards' | 'policies' | 'recovery' | 'metrics'>
    ) => {
      state.activeTab = action.payload;
    },

    openSnapshotModal: (state) => {
      state.showSnapshotModal = true;
    },

    closeSnapshotModal: (state) => {
      state.showSnapshotModal = false;
    },

    openRecoveryLog: (state) => {
      state.showRecoveryLog = true;
    },

    closeRecoveryLog: (state) => {
      state.showRecoveryLog = false;
    },

    // Error/Status actions
    setError: (state, action: PayloadAction<string | undefined>) => {
      state.error = action.payload;
    },

    setWarning: (state, action: PayloadAction<string | undefined>) => {
      state.warning = action.payload;
    },

    setSuccess: (state, action: PayloadAction<string | undefined>) => {
      state.success = action.payload;
    },

    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },

    // Reset actions
    resetSelfHealing: () => initialState,

    resetErrors: (state) => {
      state.error = undefined;
      state.warning = undefined;
      state.success = undefined;
    },
  },
});

// Export actions
export const {
  setSimulationStatus,
  setSimulationConfig,
  setCurrentJobId,
  setStartTime,
  setAgents,
  updateAgent,
  selectAgent,
  setRewardFunction,
  addRewardDataPoint,
  selectRewardMetric,
  setPolicyTimeline,
  setCurrentPolicy,
  addPolicyVersion,
  selectPolicyVersions,
  setSnapshots,
  addSnapshot,
  selectSnapshot,
  setRecoveryInProgress,
  setMetrics,
  setTimelineSteps,
  setWebSocketConnected,
  setWebSocketLatency,
  setActiveTab,
  openSnapshotModal,
  closeSnapshotModal,
  openRecoveryLog,
  closeRecoveryLog,
  setError,
  setWarning,
  setSuccess,
  setLoading,
  resetSelfHealing,
  resetErrors,
} = selfHealingSlice.actions;

// Export reducer
export default selfHealingSlice.reducer;
