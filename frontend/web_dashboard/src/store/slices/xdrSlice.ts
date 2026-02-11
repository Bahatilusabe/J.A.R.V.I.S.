import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import {
  XDRFederationState,
  FederationNode,
  BlockchainLedgerEntry,
  ModelProvenanceCard,
  FederationSyncEvent,
  LedgerFilterCriteria,
} from '../../types/xdr.types';

const initialState: XDRFederationState = {
  federationNodes: [],
  federationStatus: null,
  syncEvents: [],
  federationRingState: {
    nodes: [],
    selectedNodeId: null,
    highlightedNodeId: null,
    syncAnimation: true,
    rotationEnabled: true,
    showLabels: true,
    zoomLevel: 1,
  },
  ledgerEntries: [],
  ledgerTimeline: {
    entries: [],
    filteredEntries: [],
    expandedEntryIds: [],
    selectedEntryId: null,
    totalEntries: 0,
    pageIndex: 0,
    pageSize: 50,
    sortOrder: 'descending',
    filterCriteria: {
      entryTypes: [],
      severities: [],
      actors: [],
      dateRange: {
        startDate: new Date(Date.now() - 86400000).toISOString(),
        endDate: new Date().toISOString(),
      },
      status: [],
      searchQuery: '',
    },
  },
  forensicsData: {},
  modelProvenance: {
    models: [],
    selectedModelId: null,
    expandedModelIds: [],
    verifications: {},
    filters: {
      status: [],
      framework: [],
      owner: [],
    },
  },
  trainingJobs: [],
  selectedNodeId: null,
  selectedEntryId: null,
  selectedModelId: null,
  activeTab: 'federation',
  searchQuery: '',
  filterCriteria: {
    nodes: {},
    entries: {
      entryTypes: [],
      severities: [],
      actors: [],
      dateRange: {
        startDate: new Date(Date.now() - 86400000).toISOString(),
        endDate: new Date().toISOString(),
      },
      status: [],
      searchQuery: '',
    },
    models: {},
  },
  wsConnected: false,
  wsLatency: 0,
  isLoading: false,
  isRefreshing: false,
  lastUpdate: new Date().toISOString(),
  error: null,
  warning: null,
  successMessage: null,
};

const xdrSlice = createSlice({
  name: 'xdr',
  initialState,
  reducers: {
    // Federation
    setFederationNodes: (state, action: PayloadAction<FederationNode[]>) => {
      state.federationNodes = action.payload;
      state.federationRingState.nodes = action.payload;
      state.lastUpdate = new Date().toISOString();
    },
    updateFederationNode: (state, action: PayloadAction<FederationNode>) => {
      const idx = state.federationNodes.findIndex((n) => n.nodeId === action.payload.nodeId);
      if (idx >= 0) {
        state.federationNodes[idx] = action.payload;
      }
    },
    selectFederationNode: (state, action: PayloadAction<string | null>) => {
      state.selectedNodeId = action.payload;
      state.federationRingState.selectedNodeId = action.payload;
    },
    // Ledger
    setLedgerEntries: (state, action: PayloadAction<BlockchainLedgerEntry[]>) => {
      state.ledgerEntries = action.payload;
      state.ledgerTimeline.entries = action.payload;
      state.ledgerTimeline.totalEntries = action.payload.length;
      state.lastUpdate = new Date().toISOString();
    },
    addLedgerEntry: (state, action: PayloadAction<BlockchainLedgerEntry>) => {
      state.ledgerEntries.unshift(action.payload);
      state.ledgerTimeline.entries.unshift(action.payload);
    },
    toggleLedgerEntryExpanded: (state, action: PayloadAction<string>) => {
      const idx = state.ledgerTimeline.expandedEntryIds.indexOf(action.payload);
      if (idx >= 0) {
        state.ledgerTimeline.expandedEntryIds.splice(idx, 1);
      } else {
        state.ledgerTimeline.expandedEntryIds.push(action.payload);
      }
    },
    selectLedgerEntry: (state, action: PayloadAction<string | null>) => {
      state.selectedEntryId = action.payload;
      state.ledgerTimeline.selectedEntryId = action.payload;
    },
    setLedgerFilterCriteria: (state, action: PayloadAction<Partial<LedgerFilterCriteria>>) => {
      state.ledgerTimeline.filterCriteria = {
        ...state.ledgerTimeline.filterCriteria,
        ...action.payload,
      };
    },
    // Model Provenance
    setModelProvenance: (state, action: PayloadAction<ModelProvenanceCard[]>) => {
      state.modelProvenance.models = action.payload;
      state.lastUpdate = new Date().toISOString();
    },
    toggleModelExpanded: (state, action: PayloadAction<string>) => {
      const idx = state.modelProvenance.expandedModelIds.indexOf(action.payload);
      if (idx >= 0) {
        state.modelProvenance.expandedModelIds.splice(idx, 1);
      } else {
        state.modelProvenance.expandedModelIds.push(action.payload);
      }
    },
    selectModel: (state, action: PayloadAction<string | null>) => {
      state.selectedModelId = action.payload;
      state.modelProvenance.selectedModelId = action.payload;
    },
    // Sync Events
    addSyncEvent: (state, action: PayloadAction<FederationSyncEvent>) => {
      state.syncEvents.unshift(action.payload);
      if (state.syncEvents.length > 100) {
        state.syncEvents.pop();
      }
    },
    // UI
    setActiveTab: (state, action: PayloadAction<'federation' | 'ledger' | 'models' | 'training'>) => {
      state.activeTab = action.payload;
    },
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload;
    },
    // WebSocket
    setWSConnected: (state, action: PayloadAction<boolean>) => {
      state.wsConnected = action.payload;
    },
    setWSLatency: (state, action: PayloadAction<number>) => {
      state.wsLatency = action.payload;
    },
    // State Management
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setWarning: (state, action: PayloadAction<string | null>) => {
      state.warning = action.payload;
    },
    setSuccess: (state, action: PayloadAction<string | null>) => {
      state.successMessage = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    resetXDR: (_state) => {
      return initialState;
    },
  },
});

export const {
  setFederationNodes,
  updateFederationNode,
  selectFederationNode,
  setLedgerEntries,
  addLedgerEntry,
  toggleLedgerEntryExpanded,
  selectLedgerEntry,
  setLedgerFilterCriteria,
  setModelProvenance,
  toggleModelExpanded,
  selectModel,
  addSyncEvent,
  setActiveTab,
  setSearchQuery,
  setWSConnected,
  setWSLatency,
  setError,
  setWarning,
  setSuccess,
  setLoading,
  resetXDR,
} = xdrSlice.actions;

export default xdrSlice.reducer;
