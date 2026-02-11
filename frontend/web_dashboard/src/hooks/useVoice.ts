import { useState, useCallback, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import voiceService from '../services/voice.service'
import { VoiceCommand, VoiceIntent, ASRResult } from '../types/index'
import { RootState } from '../store/index'

interface UseVoiceReturn {
  commands: VoiceCommand[]
  currentCommand: VoiceCommand | null
  availableIntents: VoiceIntent[]
  asrResults: ASRResult[]
  isRecording: boolean
  isASRConnected: boolean
  isLoading: boolean
  error: string | null
  getAvailableIntents: () => Promise<void>
  executeCommand: (text: string) => Promise<void>
  connectASRStream: () => Promise<void>
  disconnectASRStream: () => void
  startRecording: () => Promise<void>
  stopRecording: () => void
  clearCommandHistory: () => void
  clearError: () => void
}

/**
 * Hook for voice commands and ASR
 * Manages voice command execution, recording, and transcription
 * Provides real-time ASR streaming with WebSocket
 */
export function useVoice(): UseVoiceReturn {
  const dispatch = useDispatch()
  const [isRecording, setIsRecording] = useState(false)
  const [isASRConnected, setIsASRConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const unsubscribeRef = useRef<(() => void) | null>(null)

  // Get voice state from Redux
  const voiceState = useSelector((state: RootState) => state.voice)
  const commands = voiceState?.commands || []
  const currentCommand = voiceState?.currentCommand || null
  const availableIntents = voiceState?.availableIntents || []
  const asrResults = voiceState?.asrResults || []

  /**
   * Get available voice intents
   */
  const getAvailableIntents = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const intents = await voiceService.getAvailableIntents()

      // Dispatch to Redux store
      dispatch({
        type: 'voice/intentsFetched',
        payload: intents,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch voice intents'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [dispatch])

  /**
   * Execute voice command
   */
  const executeCommand = useCallback(
    async (text: string) => {
      try {
        setIsLoading(true)
        setError(null)

        const command = await voiceService.executeCommand(text)

        // Dispatch to Redux store
        dispatch({
          type: 'voice/commandExecuted',
          payload: command,
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to execute command'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [dispatch]
  )

  /**
   * Connect to ASR stream
   */
  const connectASRStream = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      await voiceService.connectASRStream()
      setIsASRConnected(true)

      // Subscribe to ASR results
      unsubscribeRef.current = voiceService.subscribeToASR((result) => {
        // Dispatch new ASR result to Redux store
        dispatch({
          type: 'voice/asrResultReceived',
          payload: result,
        })
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to connect to ASR'
      setError(message)
      setIsASRConnected(false)
    } finally {
      setIsLoading(false)
    }
  }, [dispatch])

  /**
   * Disconnect from ASR stream
   */
  const disconnectASRStream = useCallback(() => {
    try {
      if (unsubscribeRef.current) {
        unsubscribeRef.current()
        unsubscribeRef.current = null
      }

      voiceService.disconnectASRStream()
      setIsASRConnected(false)
      setError(null)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to disconnect from ASR'
      setError(message)
    }
  }, [])

  /**
   * Start audio recording
   */
  const startRecording = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      await voiceService.startRecording()
      setIsRecording(true)

      // Dispatch to Redux store
      dispatch({
        type: 'voice/recordingStarted',
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to start recording'
      setError(message)
      setIsRecording(false)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [dispatch])

  /**
   * Stop audio recording
   */
  const stopRecording = useCallback(() => {
    try {
      voiceService.stopRecording()
      setIsRecording(false)

      // Dispatch to Redux store
      dispatch({
        type: 'voice/recordingStopped',
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to stop recording'
      setError(message)
    }
  }, [dispatch])

  /**
   * Clear command history
   */
  const clearCommandHistory = useCallback(() => {
    try {
      voiceService.clearCommandHistory()

      // Dispatch to Redux store
      dispatch({
        type: 'voice/historyCleared',
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to clear history'
      setError(message)
    }
  }, [dispatch])

  /**
   * Clear error message
   */
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    commands,
    currentCommand,
    availableIntents,
    asrResults,
    isRecording,
    isASRConnected,
    isLoading,
    error,
    getAvailableIntents,
    executeCommand,
    connectASRStream,
    disconnectASRStream,
    startRecording,
    stopRecording,
    clearCommandHistory,
    clearError,
  }
}

export default useVoice
