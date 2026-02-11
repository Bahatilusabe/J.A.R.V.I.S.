import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import {
  TDSState,
  PacketEvent,
  DPIRule,
  VPNSession,
  ZeroTrustAttestation,
  SecurityAlert,
  PacketStreamData,
  SuspiciousSignature,
  MicroSegmentNode,
  TrafficFlow,
  EnforcementAction,
  BlockAction,
  IsolationAction,
} from '../../types/tds.types'

const initialState: TDSState = {
  packetStream: [],
  livePackets: [],
  packetStreamActive: false,
  latestPackets: [] as PacketStreamData[],
  anomalyRate: 0,
  blockingRate: 0,
  totalBandwidth: 0,

  rules: [],
  suspiciousSignatures: [],
  signatureMatches: new Map(),
  activeSignatures: [],
  rulesLoaded: false,

  vpnSessions: [],
  activeSessionCount: 0,
  vpnSessionsLoaded: false,

  attestationPending: false,
  attestationModalOpen: false,
  currentAttestation: null,
  deviceComplianceStatus: 'unknown',
  trustScore: 0,

  microSegmentNodes: [],
  trafficFlows: [],
  segmentationZones: [],
  topologyLoaded: false,
  isolatedEndpoints: [],

  alerts: [],
  blockActions: [],
  isolationActions: [],
  pendingEnforcements: [],
  recentAlerts: [],

  selectedPacket: null,
  selectedRule: null,
  selectedSession: null,
  filterCriteria: {},
  searchQuery: '',
  viewMode: 'grid',

  isOnline: true,
  wsConnected: false,
  telemetryLatency: 0,

  error: null,
  warning: null,
  lastUpdate: new Date().toISOString(),
}

const tdsSlice = createSlice({
  name: 'tds',
  initialState,
  reducers: {
    setPacketStream: (state, action: PayloadAction<PacketStreamData[]>) => {
      state.packetStream = action.payload
      state.latestPackets = action.payload.slice(-50)
      state.lastUpdate = new Date().toISOString()
    },

    addPacket: (state, action: PayloadAction<PacketEvent>) => {
      state.livePackets.unshift(action.payload)
      state.livePackets = state.livePackets.slice(0, 100)
      state.lastUpdate = new Date().toISOString()
    },

    setRules: (state, action: PayloadAction<DPIRule[]>) => {
      state.rules = action.payload
      state.rulesLoaded = true
    },

    toggleRule: (state, action: PayloadAction<{ ruleId: string; enabled: boolean }>) => {
      const rule = state.rules.find((r) => r.ruleId === action.payload.ruleId)
      if (rule) {
        rule.enabled = action.payload.enabled
      }
    },

    setSuspiciousSignatures: (state, action: PayloadAction<SuspiciousSignature[]>) => {
      state.suspiciousSignatures = action.payload
      state.activeSignatures = action.payload.filter((s) => s.enabled)
    },

    addSignatureMatch: (state, action: PayloadAction<SuspiciousSignature>) => {
      const sig = action.payload
      const count = state.signatureMatches.get(sig.signatureId) || 0
      state.signatureMatches.set(sig.signatureId, count + 1)
    },

    setVPNSessions: (state, action: PayloadAction<VPNSession[]>) => {
      state.vpnSessions = action.payload
      state.activeSessionCount = action.payload.filter((s) => s.isActive).length
      state.vpnSessionsLoaded = true
    },

    removeVPNSession: (state, action: PayloadAction<string>) => {
      state.vpnSessions = state.vpnSessions.filter((s) => s.sessionId !== action.payload)
    },

    setAttestation: (state, action: PayloadAction<ZeroTrustAttestation>) => {
      state.currentAttestation = action.payload
      state.trustScore = action.payload.trustScore
      state.deviceComplianceStatus = action.payload.complianceStatus
    },

    setAttestationModalOpen: (state, action: PayloadAction<boolean>) => {
      state.attestationModalOpen = action.payload
    },

    setAttestationPending: (state, action: PayloadAction<boolean>) => {
      state.attestationPending = action.payload
    },

    setMicroSegmentNodes: (state, action: PayloadAction<MicroSegmentNode[]>) => {
      state.microSegmentNodes = action.payload
      state.topologyLoaded = true
    },

    setTrafficFlows: (state, action: PayloadAction<TrafficFlow[]>) => {
      state.trafficFlows = action.payload
    },

    addAlert: (state, action: PayloadAction<SecurityAlert>) => {
      state.alerts.unshift(action.payload)
      state.recentAlerts.unshift(action.payload)
      state.recentAlerts = state.recentAlerts.slice(0, 20)
    },

    resolveAlert: (state, action: PayloadAction<string>) => {
      const alert = state.alerts.find((a) => a.alertId === action.payload)
      if (alert) {
        alert.resolved = true
        alert.resolvedAt = new Date().toISOString()
      }
    },

    blockIP: (state, action: PayloadAction<BlockAction>) => {
      state.blockActions.push(action.payload)
    },

    isolateEndpoint: (state, action: PayloadAction<IsolationAction>) => {
      state.isolationActions.push(action.payload)
      state.isolatedEndpoints.push(action.payload.deviceId)
    },

    addPendingEnforcement: (state, action: PayloadAction<EnforcementAction>) => {
      state.pendingEnforcements.push(action.payload)
    },

    approveEnforcement: (state, action: PayloadAction<string>) => {
      const enforcement = state.pendingEnforcements.find((e) => e.actionId === action.payload)
      if (enforcement) {
        enforcement.status = 'approved'
        enforcement.confirmed = true
        enforcement.confirmedAt = new Date().toISOString()
      }
    },

    rejectEnforcement: (state, action: PayloadAction<string>) => {
      const enforcement = state.pendingEnforcements.find((e) => e.actionId === action.payload)
      if (enforcement) {
        enforcement.status = 'rejected'
      }
    },

    setPacketStreamActive: (state, action: PayloadAction<boolean>) => {
      state.packetStreamActive = action.payload
    },

    setAnomalyRate: (state, action: PayloadAction<number>) => {
      state.anomalyRate = Math.max(0, Math.min(1, action.payload))
    },

    setBlockingRate: (state, action: PayloadAction<number>) => {
      state.blockingRate = Math.max(0, Math.min(1, action.payload))
    },

    setTotalBandwidth: (state, action: PayloadAction<number>) => {
      state.totalBandwidth = action.payload
    },

    selectPacket: (state, action: PayloadAction<PacketEvent | null>) => {
      state.selectedPacket = action.payload
    },

    selectRule: (state, action: PayloadAction<DPIRule | null>) => {
      state.selectedRule = action.payload
    },

    selectSession: (state, action: PayloadAction<VPNSession | null>) => {
      state.selectedSession = action.payload
    },

    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload
    },

    setFilterCriteria: (state, action: PayloadAction<Partial<typeof state.filterCriteria>>) => {
      state.filterCriteria = { ...state.filterCriteria, ...action.payload }
    },

    setViewMode: (state, action: PayloadAction<'grid' | 'list' | 'topology'>) => {
      state.viewMode = action.payload
    },

    setWSConnected: (state, action: PayloadAction<boolean>) => {
      state.wsConnected = action.payload
    },

    setTelemetryLatency: (state, action: PayloadAction<number>) => {
      state.telemetryLatency = action.payload
    },

    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },

    setWarning: (state, action: PayloadAction<string | null>) => {
      state.warning = action.payload
    },

    resetTDS: () => initialState,
  },
})

export const {
  setPacketStream,
  addPacket,
  setRules,
  toggleRule,
  setSuspiciousSignatures,
  addSignatureMatch,
  setVPNSessions,
  removeVPNSession,
  setAttestation,
  setAttestationModalOpen,
  setAttestationPending,
  setMicroSegmentNodes,
  setTrafficFlows,
  addAlert,
  resolveAlert,
  blockIP,
  isolateEndpoint,
  addPendingEnforcement,
  approveEnforcement,
  rejectEnforcement,
  setPacketStreamActive,
  setAnomalyRate,
  setBlockingRate,
  setTotalBandwidth,
  selectPacket,
  selectRule,
  selectSession,
  setSearchQuery,
  setFilterCriteria,
  setViewMode,
  setWSConnected,
  setTelemetryLatency,
  setError,
  setWarning,
  resetTDS,
} = tdsSlice.actions

export default tdsSlice.reducer
