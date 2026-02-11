import { apiClient } from '../utils/api'
import { VoiceCommand, VoiceIntent, ASRResult } from '../types/index'

const WS_URL = (import.meta as unknown as { env: Record<string, string> }).env.VITE_WS_URL || 'ws://127.0.0.1:5000'

export type ASRCallback = (result: ASRResult) => void

/**
 * Voice & VocalSOC Service
 * Handles voice commands via /vocal/intent and streaming ASR
 */
class VoiceService {
  private asrWs: WebSocket | null = null
  private mediaRecorder: MediaRecorder | null = null
  private audioStream: MediaStream | null = null
  private asrSubscribers: Set<ASRCallback> = new Set()
  private commandHistory: VoiceCommand[] = []
  private isRecording = false

  /**
   * Get available voice intents
   */
  async getAvailableIntents(): Promise<VoiceIntent[]> {
    try {
      const response = await apiClient.get<VoiceIntent[]>(
        '/api/vocal/intents'
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch voice intents:', error)
      throw error
    }
  }

  /**
   * Execute voice command
   */
  async executeCommand(text: string): Promise<VoiceCommand> {
    try {
      const response = await apiClient.post<VoiceCommand>(
        '/api/vocal/intent',
        {
          text,
          timestamp: new Date().toISOString(),
        }
      )

      const command = response.data

      // Add to history
      this.commandHistory.push(command)

      // Keep only last 100 commands
      if (this.commandHistory.length > 100) {
        this.commandHistory.shift()
      }

      return command
    } catch (error) {
      console.error('Failed to execute voice command:', error)
      throw error
    }
  }

  /**
   * Connect to ASR (Automatic Speech Recognition) streaming WebSocket
   */
  async connectASRStream(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${WS_URL.replace(/^http/, 'ws')}/ws/asr`
        console.log('Connecting to ASR stream:', wsUrl)

        this.asrWs = new WebSocket(wsUrl)

        this.asrWs.onopen = () => {
          console.log('ASR WebSocket connected')
          resolve()
        }

        this.asrWs.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            const result = data as ASRResult

            // Notify subscribers
            this.asrSubscribers.forEach((callback) => {
              try {
                callback(result)
              } catch (error) {
                console.error('ASR subscriber callback error:', error)
              }
            })
          } catch (error) {
            console.error('Failed to parse ASR message:', error)
          }
        }

        this.asrWs.onerror = (error) => {
          console.error('ASR WebSocket error:', error)
          reject(error)
        }

        this.asrWs.onclose = () => {
          console.log('ASR WebSocket closed')
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  /**
   * Disconnect from ASR stream
   */
  disconnectASRStream(): void {
    this.stopRecording()

    if (this.asrWs) {
      this.asrWs.close()
      this.asrWs = null
    }

    this.asrSubscribers.clear()
  }

  /**
   * Subscribe to ASR results
   */
  subscribeToASR(callback: ASRCallback): () => void {
    this.asrSubscribers.add(callback)

    // Return unsubscribe function
    return () => {
      this.asrSubscribers.delete(callback)
    }
  }

  /**
   * Start recording audio and send to ASR
   */
  async startRecording(): Promise<void> {
    try {
      this.audioStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      })

      const mimeType = this.getSupportedMimeType()
      const options = { mimeType }

      this.mediaRecorder = new MediaRecorder(this.audioStream, options)

      this.mediaRecorder.ondataavailable = (event) => {
        if (this.asrWs && this.asrWs.readyState === WebSocket.OPEN) {
          this.asrWs.send(event.data)
        }
      }

      this.mediaRecorder.start(100) // Send chunks every 100ms
      this.isRecording = true

      console.log('Audio recording started')
    } catch (error) {
      console.error('Failed to start recording:', error)
      throw error
    }
  }

  /**
   * Stop recording audio
   */
  stopRecording(): void {
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop()
    }

    if (this.audioStream) {
      this.audioStream.getTracks().forEach((track) => track.stop())
      this.audioStream = null
    }

    this.isRecording = false
    console.log('Audio recording stopped')
  }

  /**
   * Get supported MIME type for audio recording
   */
  private getSupportedMimeType(): string {
    const types = [
      'audio/webm;codecs=opus',
      'audio/mp4',
      'audio/mpeg',
      'audio/wav',
    ]

    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        return type
      }
    }

    return 'audio/webm' // Fallback
  }

  /**
   * Get command history
   */
  getCommandHistory(): VoiceCommand[] {
    return [...this.commandHistory]
  }

  /**
   * Clear command history
   */
  clearCommandHistory(): void {
    this.commandHistory = []
  }

  /**
   * Check if currently recording
   */
  isRecordingCheck(): boolean {
    return this.isRecording
  }

  /**
   * Check if ASR stream is connected
   */
  isASRConnected(): boolean {
    return this.asrWs?.readyState === WebSocket.OPEN
  }

  /**
   * Get ASR subscriber count
   */
  getASRSubscriberCount(): number {
    return this.asrSubscribers.size
  }
}

// Export singleton instance
export default new VoiceService()
