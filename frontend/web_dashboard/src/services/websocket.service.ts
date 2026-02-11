import { WebSocketMessage, ConnectionStatus } from '@/types'

// Provide a typed view over import.meta.env without using `any`
const env = (import.meta as unknown as { env?: Record<string, string | undefined> }).env || {}

interface SocketListener<T = unknown> {
  (data: T): void
}

class WebSocketService {
  private socket: WebSocket | null = null
  private url: string
  private listeners: Map<string, Set<SocketListener>> = new Map()
  private connectionStatus: ConnectionStatus = {
    isConnected: false,
    reconnectAttempts: 0,
  }
  private reconnectTimer: NodeJS.Timeout | null = null
  private maxReconnectAttempts = parseInt(env?.VITE_WEBSOCKET_MAX_RETRIES || '5')
  private reconnectInterval = parseInt(env?.VITE_WEBSOCKET_RECONNECT_INTERVAL || '3000')

  constructor() {
  this.url = env?.VITE_WEBSOCKET_URL || 'ws://127.0.0.1:5000'
  }

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.socket = new WebSocket(this.url)

        this.socket.onopen = () => {
          console.log('WebSocket connected')
          this.connectionStatus.isConnected = true
          this.connectionStatus.lastConnected = new Date().toISOString()
          this.connectionStatus.reconnectAttempts = 0
          this.emit('connected', {})
          resolve()
        }

        this.socket.onmessage = (event: MessageEvent) => {
          try {
            const message = JSON.parse(event.data as string) as WebSocketMessage
            this.handleMessage(message)
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }

        this.socket.onerror = (ev: Event | ErrorEvent) => {
          console.error('WebSocket error:', ev)
          const errMsg = (ev as ErrorEvent).message || String(ev)
          this.connectionStatus.lastError = errMsg
          this.emit('error', { error: errMsg })
          reject(ev)
        }

        this.socket.onclose = () => {
          console.log('WebSocket closed')
          this.connectionStatus.isConnected = false
          this.emit('disconnected', {})
          this.reconnect()
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.socket) {
      this.socket.close()
      this.socket = null
    }

    this.connectionStatus.isConnected = false
  }

  /**
   * Reconnect with exponential backoff
   */
  private reconnect(): void {
    if (this.connectionStatus.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      return
    }

    const backoffDelay = this.reconnectInterval * Math.pow(2, this.connectionStatus.reconnectAttempts)
    this.reconnectTimer = setTimeout(() => {
      this.connectionStatus.reconnectAttempts++
      console.log(`Reconnecting... (attempt ${this.connectionStatus.reconnectAttempts})`)
      this.connect().catch((error) => {
        console.error('Reconnection failed:', error)
      })
    }, backoffDelay)
  }

  /**
   * Send message through WebSocket
   */
  send<T = unknown>(type: string, payload: T): void {
    if (!this.connectionStatus.isConnected || !this.socket) {
      console.warn('WebSocket not connected, buffering message')
      return
    }

    const message: WebSocketMessage<T> = {
      type,
      payload,
      timestamp: new Date().toISOString(),
    }

    this.socket.send(JSON.stringify(message))
  }

  /**
   * Subscribe to specific message type
   */
  on<T = unknown>(type: string, listener: SocketListener<T>): () => void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set())
    }

    this.listeners.get(type)!.add(listener as SocketListener)

    // Return unsubscribe function
    return () => {
      this.listeners.get(type)?.delete(listener as SocketListener)
    }
  }

  /**
   * Subscribe to message type once
   */
  once<T = unknown>(type: string, listener: SocketListener<T>): void {
    const unsubscribe = this.on(type, (data: T) => {
      listener(data)
      unsubscribe()
    })
  }

  /**
   * Emit message to local listeners
   */
  private emit<T = unknown>(type: string, data: T): void {
    const listeners = this.listeners.get(type)
    if (listeners) {
      listeners.forEach((listener) => {
        try {
          listener(data)
        } catch (error) {
          console.error(`Error in listener for ${type}:`, error)
        }
      })
    }
  }

  /**
   * Handle incoming message
   */
  private handleMessage(message: WebSocketMessage): void {
    this.emit(message.type, message.payload)
  }

  /**
   * Get connection status
   */
  getStatus(): ConnectionStatus {
    return { ...this.connectionStatus }
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.connectionStatus.isConnected
  }
}

export default new WebSocketService()
