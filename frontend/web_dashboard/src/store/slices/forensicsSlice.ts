import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { ForensicsState, ForensicReportSummary, SignedForensicReport, DilithiumPublicKey, ForensicsUIState } from '../../types/forensics.types';

const initialUIState: ForensicsUIState = {
  selectedReports: [],
  expandedReportId: undefined,
  reportListFilter: {},
  reportListSort: { field: 'date', order: 'desc' },
  viewingReportId: undefined,
  viewerTab: 'summary',
  pdfViewerPage: 1,
  pdfViewerZoom: 100,
  verificationInProgress: false,
  verificationResults: {},
  showSignatureDetails: false,
  timelineExpanded: {},
  timelineFilter: { severities: [], actionTypes: [] },
  isLoading: false,
  error: undefined,
  successMessage: undefined,
};

const initialState: ForensicsState = {
  reports: [],
  currentReport: undefined,
  publicKeys: [],
  totalReports: 0,
  isLoadingReports: false,
  isLoadingCurrentReport: false,
  ui: initialUIState,
  lastUpdated: new Date().toISOString(),
  cacheExpiry: undefined,
};

const forensicsSlice = createSlice({
  name: 'forensics',
  initialState,
  reducers: {
    setReports: (state, action: PayloadAction<ForensicReportSummary[]>) => {
      state.reports = action.payload;
      state.totalReports = action.payload.length;
      state.lastUpdated = new Date().toISOString();
    },

    addReport: (state, action: PayloadAction<ForensicReportSummary>) => {
      state.reports.unshift(action.payload);
      state.totalReports = state.reports.length;
      state.lastUpdated = new Date().toISOString();
    },

    setCurrentReport: (state, action: PayloadAction<SignedForensicReport | undefined>) => {
      state.currentReport = action.payload;
      state.isLoadingCurrentReport = false;
    },

    setPublicKeys: (state, action: PayloadAction<DilithiumPublicKey[]>) => {
      state.publicKeys = action.payload;
    },

    setLoadingReports: (state, action: PayloadAction<boolean>) => {
      state.isLoadingReports = action.payload;
    },

    setLoadingCurrentReport: (state, action: PayloadAction<boolean>) => {
      state.isLoadingCurrentReport = action.payload;
    },

    setUIState: (state, action: PayloadAction<Partial<ForensicsUIState>>) => {
      state.ui = { ...state.ui, ...action.payload } as ForensicsUIState;
    },

    reportsFetched: (state, action: PayloadAction<{ reports: ForensicReportSummary[]; total?: number }>) => {
      state.reports = action.payload.reports;
      state.totalReports = action.payload.total ?? action.payload.reports.length;
      state.isLoadingReports = false;
      state.lastUpdated = new Date().toISOString();
    },

    resetForensicsState: () => initialState,
  },
});

export const {
  setReports,
  addReport,
  setCurrentReport,
  setPublicKeys,
  setLoadingReports,
  setLoadingCurrentReport,
  setUIState,
  reportsFetched,
  resetForensicsState,
} = forensicsSlice.actions;

export default forensicsSlice.reducer;
