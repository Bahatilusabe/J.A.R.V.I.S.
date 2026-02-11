import { useCallback, useRef, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import {
  setTranscript,
  setLiveTranscript,
  setIntent,
  setVoiceAuth,
  setLoading,
  setError,
} from '../store/slices/vocalsocSlice'
import {
  TranscriptUpdate,
  IntentRequest,
  IntentResponse,
  VoiceAuthRequest,
  VoiceAuthResponse,
  VoiceprintBadge,
  VocalSOCState,
} from '../types/vocalsoc.types'

const API_BASE = 'http://localhost:5000'

export const useVocalSOC = () => {
  const dispatch = useDispatch()
  const vocalsocState = useSelector((state: { vocalsoc: VocalSOCState }) => state.vocalsoc)

  // One-time warning in dev if state is missing to help debugging
  if (process.env.NODE_ENV !== 'production' && !vocalsocState) {
    // eslint-disable-next-line no-console
    console.warn('[useVocalSOC] vocalsoc slice missing from store; using safe defaults')
  }

  const wsRef = useRef<WebSocket | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyzerRef = useRef<AnalyserNode | null>(null)
  const dataArrayRef = useRef<Uint8Array | null>(null)

  const [isRecording, setIsRecording] = useState(false)
  const [audioLevel, setAudioLevel] = useState(0)
  const [waveformData, setWaveformData] = useState<number[]>([])
  const [streamId, setStreamId] = useState<string>('')

  const initializeWebSocket = useCallback((newStreamId: string) => {
    try {
      const wsUrl = `${API_BASE.replace('http', 'ws')}/ws/vocal/stream`
      wsRef.current = new WebSocket(wsUrl)

      wsRef.current.onopen = () => {
        wsRef.current?.send(
          JSON.stringify({
            type: 'stream_start',
            streamId: newStreamId,
            sampleRate: 16000,
            audioFormat: 'pcm',
            timestamp: new Date().toISOString(),
          })
        )
      }

      wsRef.current.onmessage = (event) => {
        const message = JSON.parse(event.data)
        if (message.type === 'transcript_update') {
          const update = message.payload as TranscriptUpdate
          dispatch(setLiveTranscript(update.text))
          if (update.isFinal) {
            dispatch(setTranscript(update.text))
          }
        } else if (message.type === 'intent_recognized') {
          const intent = message.payload as IntentResponse
          dispatch(
            setIntent({
              intent: intent.intent,
              confidence: intent.confidence,
              slots: intent.slots || {},
              requires2FA: intent.requires2FA,
              requiresManualApproval: false,
              riskLevel: intent.riskLevel,
            })
          )
        }
      }

      wsRef.current.onerror = () => {
        dispatch(setError('WebSocket connection failed'))
      }
    } catch (error) {
      console.error('WebSocket init failed:', error)
      dispatch(setError('Failed to initialize audio streaming'))
    }
  }, [dispatch])

  // Send recorded audio to backend for processing


  // Send recorded audio to backend for processing


  const startRecording = useCallback(async () => {
    try {
      setIsRecording(true)
      const newStreamId = `stream-${Date.now()}`
      setStreamId(newStreamId)

      if (!audioContextRef.current) {
        // Support legacy webkitAudioContext without using `any`
        const maybeWebkit = (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
        const AudioCtx = maybeWebkit || window.AudioContext
        audioContextRef.current = new AudioCtx()
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: false },
      })

      const source = audioContextRef.current.createMediaStreamSource(stream)
      analyzerRef.current = audioContextRef.current.createAnalyser()
      analyzerRef.current.fftSize = 2048
      source.connect(analyzerRef.current)

      const buffer = new Uint8Array(analyzerRef.current.frequencyBinCount)
      dataArrayRef.current = buffer

      const updateWaveform = () => {
        if (!analyzerRef.current || !buffer) return
        analyzerRef.current.getByteFrequencyData(buffer)
        setWaveformData(Array.from(buffer.slice(0, 128)))
        const average = buffer.reduce((a, b) => a + b, 0) / buffer.length
        setAudioLevel(average / 255)
        if (isRecording) {
          requestAnimationFrame(updateWaveform)
        }
      }
      updateWaveform()

      mediaRecorderRef.current = new MediaRecorder(stream)
      const chunks: Blob[] = []

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data)
      }

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' })
        sendAudioForProcessing(audioBlob, newStreamId)
        stream.getTracks().forEach((track) => track.stop())
      }

      initializeWebSocket(newStreamId)
      mediaRecorderRef.current.start()
    } catch (error) {
      console.error('Recording failed:', error)
      dispatch(setError('Microphone access denied'))
      setIsRecording(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dispatch, initializeWebSocket, isRecording])

  const stopRecording = useCallback(() => {
    setIsRecording(false)
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.close()
    }
  }, [])

  const sendAudioForProcessing = useCallback(
    async (audioBlob: Blob, _newStreamId: string) => {
      try {
        dispatch(setLoading(true))
        const formData = new FormData()
        formData.append('audio', audioBlob)
        const response = await fetch(`${API_BASE}/vocal/process`, {
          method: 'POST',
          body: formData,
        })
        if (!response.ok) throw new Error('Processing failed')
        const data = await response.json()
        dispatch(setTranscript(data.transcript || ''))
      } catch (error) {
        dispatch(setError('Failed to process audio'))
      } finally {
        dispatch(setLoading(false))
      }
    },
    [dispatch]
  )

  const recognizeIntent = useCallback(
    async (transcript: string) => {
      try {
        dispatch(setLoading(true))
        const payload: IntentRequest = {
          userId: 'user-default',
          audioStreamId: streamId,
          transcript,
        }
        const response = await fetch(`${API_BASE}/vocal/intent`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
        if (!response.ok) throw new Error('Intent recognition failed')
        const data: IntentResponse = await response.json()
        dispatch(
          setIntent({
            intent: data.intent,
            confidence: data.confidence,
            slots: data.slots || {},
            requires2FA: data.requires2FA,
            requiresManualApproval: false,
            riskLevel: data.riskLevel,
          })
        )
      } catch (error) {
        dispatch(setError('Failed to recognize intent'))
      } finally {
        dispatch(setLoading(false))
      }
    },
    [dispatch, streamId]
  )

  const authenticateVoice = useCallback(
    async (audioStreamId: string) => {
      try {
        dispatch(setLoading(true))
        const payload: VoiceAuthRequest = {
          userId: 'user-default',
          audioStreamId,
        }
        const response = await fetch(`${API_BASE}/vocal/auth`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
        if (!response.ok) throw new Error('Auth failed')
        const data: VoiceAuthResponse = await response.json()
        const badge: VoiceprintBadge = {
          userId: data.userId,
          displayName: 'Authorized User',
          verified: data.verified,
          confidence: data.confidence,
          matchScore: data.voiceprintMatch,
          spoofingRisk: data.spoofingDetected ? 'high' : 'none',
          lastVerified: new Date().toISOString(),
          enrolledVoiceprints: data.details?.enrollmentCount || 1,
        }
        dispatch(setVoiceAuth(badge))
        return data.verified
      } catch (error) {
        dispatch(setError('Voice authentication failed'))
        return false
      } finally {
        dispatch(setLoading(false))
      }
    },
    [dispatch]
  )

  return {
    isRecording,
    audioLevel,
    waveformData,
    streamId,
    finalTranscript: vocalsocState?.finalTranscript || '',
    liveTranscript: vocalsocState?.liveTranscript || '',
    recognizedIntent: vocalsocState?.recognizedIntent || null,
    voiceAuth: vocalsocState?.voiceAuth || null,
    isLoading: vocalsocState?.intentLoading || false,
    error: vocalsocState?.error || null,
    startRecording,
    stopRecording,
    recognizeIntent,
    authenticateVoice,
  }
}
