/**
 * VocalSOC (Voice Command Center) Type Definitions
 * Interfaces for audio streaming, intent recognition, voice authentication, and voice command execution
 */

/**
 * Audio stream metadata for WebSocket communication
 */
export interface AudioStream {
  streamId: string
  userId: string
  startTime: string
  sampleRate: number // typically 16000 Hz
  audioFormat: 'pcm' | 'wav' | 'opus'
  duration?: number // milliseconds
}

/**
 * Real-time audio chunk sent over WebSocket
 */
export interface AudioChunk {
  streamId: string
  sequenceNumber: number
  data: ArrayBuffer // base64 encoded audio data
  timestamp: string
  isFinal: boolean // true when user stops speaking
}

/**
 * Live transcription update from ASR engine
 */
export interface TranscriptUpdate {
  streamId: string
  text: string
  isFinal: boolean
  confidence: number // 0-1
  timestamp: string
  alternatives?: Array<{
    text: string
    confidence: number
  }>
}

/**
 * Parsed intent from NLU processor
 */
export interface ParsedIntent {
  intent: string // e.g., "contain_node", "isolate_service", "enable_2fa"
  confidence: number // 0-1
  slots: Record<string, unknown> // extracted parameters (e.g., { target: "DB-01" })
  requires2FA: boolean
  requiresManualApproval: boolean
  riskLevel: 'low' | 'medium' | 'high' | 'critical'
}

/**
 * Intent request payload
 */
export interface IntentRequest {
  userId: string
  audioStreamId: string
  transcript?: string // optional: if already transcribed
}

/**
 * Intent response from backend
 */
export interface IntentResponse {
  intent: string
  target?: string
  confidence: number
  requires2FA: boolean
  slots?: Record<string, unknown>
  riskLevel: 'low' | 'medium' | 'high' | 'critical'
  explanation?: string
}

/**
 * Voice authentication request
 */
export interface VoiceAuthRequest {
  userId: string
  audioStreamId: string
}

/**
 * Voice authentication response with speaker verification
 */
export interface VoiceAuthResponse {
  userId: string
  verified: boolean
  confidence: number // 0-1 speaker identification confidence
  voiceprintMatch: number // 0-1, similarity to enrolled voiceprint
  spoofingDetected: boolean
  details?: {
    enrollmentCount: number
    lastEnrolled: string
    matchScore: number
  }
}

/**
 * Voiceprint identity badge information
 */
export interface VoiceprintBadge {
  userId: string
  displayName: string
  verified: boolean
  confidence: number
  matchScore: number
  spoofingRisk: 'none' | 'low' | 'medium' | 'high'
  lastVerified: string
  enrolledVoiceprints: number
}

/**
 * Command verification for destructive actions
 */
export interface CommandVerification {
  commandId: string
  intent: string
  target: string
  action: string
  scope: 'read-only' | 'modify' | 'destructive' | 'critical'
  requires2FA: boolean
  requiresManualApproval: boolean
  confirmationText: string
  estimatedImpact: string
  riskWarning?: string
}

/**
 * Voice command execution request
 */
export interface VoiceCommandRequest {
  userId: string
  commandId: string
  intent: string
  target: string
  verified: boolean
  voiceAuthConfidence: number
  twoFAToken?: string
  manualApprovalToken?: string
}

/**
 * Voice command execution response
 */
export interface VoiceCommandResponse {
  success: boolean
  commandId: string
  executionId: string
  result?: unknown
  error?: string
  details?: {
    executionTime: number // ms
    nodesAffected: number
    policiesEnforced: string[]
  }
}

/**
 * Offline cache entry for mapped intents
 */
export interface OfflineCacheEntry {
  transcript: string
  intent: string
  target?: string
  confidence: number
  timestamp: string
  expiresAt: string
}

/**
 * VocalSOC state shape for Redux
 */
export interface VocalSOCState {
  // Audio streaming
  isStreaming: boolean
  currentStreamId: string | null
  audioLevel: number // 0-1, microphone input level

  // Transcription
  liveTranscript: string
  finalTranscript: string
  transcriptConfidence: number
  transcriptUpdates: TranscriptUpdate[]

  // Intent recognition
  recognizedIntent: ParsedIntent | null
  intentLoading: boolean

  // Voice authentication
  voiceAuth: VoiceprintBadge | null
  authLoading: boolean
  authError: string | null

  // Command verification
  pendingVerification: CommandVerification | null
  verificationConfirmed: boolean

  // Network state
  isOnline: boolean
  lastOfflineCache: OfflineCacheEntry | null

  // Error handling
  error: string | null
  warning: string | null

  // History
  recentCommands: VoiceCommandResponse[]
}

/**
 * WebSocket message types
 */
export type WSMessageType =
  | 'audio_chunk'
  | 'stream_start'
  | 'stream_end'
  | 'transcript_update'
  | 'intent_recognized'
  | 'auth_complete'
  | 'error'
  | 'keepalive'

export interface WSMessage {
  type: WSMessageType
  payload: unknown
  timestamp: string
}

/**
 * Mic recording state
 */
export interface MicRecordingState {
  isRecording: boolean
  isPaused: boolean
  audioLevel: number
  frequency?: number
  waveformData: number[]
}
