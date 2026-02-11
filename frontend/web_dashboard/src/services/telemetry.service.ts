import { TelemetryEvent, TelemetryMetrics } from '../types/index'

// Read environment variables used across the repo. Keep backward-compatible fallbacks
const _env = (import.meta as unknown as { env: Record<string, string> }).env
const API_BASE_URL = _env.VITE_API_BASE_URL || _env.VITE_API_URL || 'http://127.0.0.1:8000'
const WS_URL = _env.VITE_WEBSOCKET_URL || _env.VITE_WS_URL || 'ws://127.0.0.1:8000'

export type TelemetryCallback = (event: TelemetryEvent) => void

/**
 * Telemetry Service
 * Subscribes to /ws/telemetry WebSocket endpoint for real-time
 * Kafka/ROMA streams from Tactical Defense Shield
 */
class TelemetryService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 3000
  private subscribers: Set<TelemetryCallback> = new Set()
  private messageQueue: TelemetryEvent[] = []
  private isConnected = false

  /**
   * Connect to telemetry WebSocket endpoint
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${WS_URL.replace(/^http/, 'ws')}/ws/telemetry`
        console.log('Connecting to telemetry endpoint:', wsUrl)

        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          console.log('Telemetry WebSocket connected')
          this.isConnected = true
          this.reconnectAttempts = 0

          // Flush queued messages
          while (this.messageQueue.length > 0) {
            const event = this.messageQueue.shift()
            if (event) {
              this.notifySubscribers(event)
            }
          }

          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            const telemetryEvent = data as TelemetryEvent

            // Queue message if subscribers aren't ready yet
            if (this.subscribers.size === 0) {
              this.messageQueue.push(telemetryEvent)
            } else {
              this.notifySubscribers(telemetryEvent)
            }
          } catch (error) {
            console.error('Failed to parse telemetry message:', error)
          }
        }

        this.ws.onerror = (error) => {
          console.error('Telemetry WebSocket error:', error)
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('Telemetry WebSocket closed')
          this.isConnected = false
          this.attemptReconnect()
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  /**
   * Disconnect from telemetry WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.isConnected = false
    this.subscribers.clear()
    this.messageQueue = []
  }

  /**
   * Subscribe to telemetry events
   */
  subscribe(callback: TelemetryCallback): () => void {
    this.subscribers.add(callback)

    // Return unsubscribe function
    return () => {
      this.subscribers.delete(callback)
    }
  }

  /**
   * Notify all subscribers of new event
   */
  private notifySubscribers(event: TelemetryEvent): void {
    this.subscribers.forEach((callback) => {
      try {
        callback(event)
      } catch (error) {
        console.error('Subscriber callback error:', error)
      }
    })
  }

  /**
   * Attempt to reconnect to WebSocket
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Failed to reconnect after maximum attempts')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)

    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`)

    setTimeout(() => {
      this.connect().catch((error) => {
        console.error('Reconnection failed:', error)
      })
    }, delay)
  }

  /**
   * Check if WebSocket is connected
   */
  isConnectedCheck(): boolean {
    return this.isConnected
  }

  /**
   * Get current message queue size
   */
  getQueueSize(): number {
    return this.messageQueue.length
  }

  /**
   * Get number of active subscribers
   */
  getSubscriberCount(): number {
    return this.subscribers.size
  }

  /**
   * Fetch historical telemetry metrics
   */
  async getMetrics(timeRange: { start: number; end: number }): Promise<TelemetryMetrics> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/telemetry/metrics`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': this.getAuthHeader(),
        },
        body: JSON.stringify(timeRange),
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch metrics: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Failed to fetch telemetry metrics:', error)
      throw error
    }
  }

  /**
   * Get authorization header from localStorage
   */
  private getAuthHeader(): string {
    const token = localStorage.getItem('jarvis_access_token')
    return token ? `Bearer ${token}` : ''
  }
}

// Export singleton instance
export default new TelemetryService()
