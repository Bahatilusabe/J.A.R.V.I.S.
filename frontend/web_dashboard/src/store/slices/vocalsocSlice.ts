import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import {
  VocalSOCState,
  ParsedIntent,
  VoiceprintBadge,
  CommandVerification,
  VoiceCommandResponse,
  TranscriptUpdate,
  OfflineCacheEntry,
} from '../../types/vocalsoc.types'

const initialState: VocalSOCState = {
  isStreaming: false,
  currentStreamId: null,
  audioLevel: 0,
  liveTranscript: '',
  finalTranscript: '',
  transcriptConfidence: 0,
  transcriptUpdates: [],
  recognizedIntent: null,
  intentLoading: false,
  voiceAuth: null,
  authLoading: false,
  authError: null,
  pendingVerification: null,
  verificationConfirmed: false,
  isOnline: true,
  lastOfflineCache: null,
  error: null,
  warning: null,
  recentCommands: [],
}

export const vocalsocSlice = createSlice({
  name: 'vocalsoc',
  initialState,
  reducers: {
    // Streaming state
    setStreamingState: (state, action: PayloadAction<boolean>) => {
      state.isStreaming = action.payload
    },
    setCurrentStreamId: (state, action: PayloadAction<string | null>) => {
      state.currentStreamId = action.payload
    },
    setAudioLevel: (state, action: PayloadAction<number>) => {
      state.audioLevel = action.payload
    },

    // Transcription
    setTranscript: (state, action: PayloadAction<string>) => {
      state.finalTranscript = action.payload
      state.liveTranscript = ''
    },
    setLiveTranscript: (state, action: PayloadAction<string>) => {
      state.liveTranscript = action.payload
    },
    setTranscriptConfidence: (state, action: PayloadAction<number>) => {
      state.transcriptConfidence = action.payload
    },
    addTranscriptUpdate: (state, action: PayloadAction<TranscriptUpdate>) => {
      state.transcriptUpdates.push(action.payload)
    },
    clearTranscripts: (state) => {
      state.finalTranscript = ''
      state.liveTranscript = ''
      state.transcriptUpdates = []
    },

    // Intent recognition
    setIntent: (state, action: PayloadAction<ParsedIntent | null>) => {
      state.recognizedIntent = action.payload
      state.intentLoading = false
    },
    setIntentLoading: (state, action: PayloadAction<boolean>) => {
      state.intentLoading = action.payload
    },

    // Voice authentication
    setVoiceAuth: (state, action: PayloadAction<VoiceprintBadge | null>) => {
      state.voiceAuth = action.payload
      state.authLoading = false
      state.authError = null
    },
    setAuthLoading: (state, action: PayloadAction<boolean>) => {
      state.authLoading = action.payload
    },
    setAuthError: (state, action: PayloadAction<string | null>) => {
      state.authError = action.payload
      state.authLoading = false
    },

    // Command verification
    setPendingVerification: (state, action: PayloadAction<CommandVerification | null>) => {
      state.pendingVerification = action.payload
      state.verificationConfirmed = false
    },
    confirmVerification: (state) => {
      state.verificationConfirmed = true
    },
    clearVerification: (state) => {
      state.pendingVerification = null
      state.verificationConfirmed = false
    },

    // Network state
    setOnlineStatus: (state, action: PayloadAction<boolean>) => {
      state.isOnline = action.payload
    },
    setLastOfflineCache: (state, action: PayloadAction<OfflineCacheEntry | null>) => {
      state.lastOfflineCache = action.payload
    },

    // Error handling
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    setWarning: (state, action: PayloadAction<string | null>) => {
      state.warning = action.payload
    },

    // History
    addRecentCommand: (state, action: PayloadAction<VoiceCommandResponse>) => {
      state.recentCommands.unshift(action.payload)
      // Keep only last 10 commands
      state.recentCommands = state.recentCommands.slice(0, 10)
    },
    clearRecentCommands: (state) => {
      state.recentCommands = []
    },

    // Bulk state reset
    resetVocalSOC: () => {
      return initialState
    },

    // Loading state (generic)
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.intentLoading = action.payload
      state.authLoading = action.payload
    },
  },
})

export const {
  setStreamingState,
  setCurrentStreamId,
  setAudioLevel,
  setTranscript,
  setLiveTranscript,
  setTranscriptConfidence,
  addTranscriptUpdate,
  clearTranscripts,
  setIntent,
  setIntentLoading,
  setVoiceAuth,
  setAuthLoading,
  setAuthError,
  setPendingVerification,
  confirmVerification,
  clearVerification,
  setOnlineStatus,
  setLastOfflineCache,
  setError,
  setWarning,
  addRecentCommand,
  clearRecentCommands,
  resetVocalSOC,
  setLoading,
} = vocalsocSlice.actions

export default vocalsocSlice.reducer
