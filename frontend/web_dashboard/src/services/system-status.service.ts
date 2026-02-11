import { apiClient } from '../utils/api'

export type SystemMode = 'conscious' | 'predictive' | 'self_healing' | 'under_attack'
export type NodeHealth = 'healthy' | 'degraded' | 'critical'

export interface SystemStatus {
  mode: SystemMode
  nodeId: string
  nodeHealth: NodeHealth
  lastUpdate: string
  threatLevel: 'critical' | 'high' | 'medium' | 'low' | 'none'
  activePolicies: number
  alertCount: number
  timestamp: string
}

export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'critical'
  uptime: number
  components: {
    backend: 'up' | 'down'
    blockchain: 'up' | 'down'
    prometheus: 'up' | 'down'
    grafana: 'up' | 'down'
    database: 'up' | 'down'
  }
  version: string
  timestamp: string
}

export interface FederationStatus {
  nodeId: string
  nodeName: string
  status: 'connected' | 'connecting' | 'disconnected'
  peers: Array<{
    id: string
    name: string
    status: 'connected' | 'unreachable'
    lastSync: string
  }>
  syncStatus: 'synced' | 'syncing' | 'behind'
  lastSyncTime: string
  ledgerHeight: number
  timestamp: string
}

/**
 * System Status Service
 * Real-time system state management, health checks, and federation status
 */
class SystemStatusService {
  private wsConnection: WebSocket | null = null
  private subscribers: Set<(status: SystemStatus) => void> = new Set()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  /**
   * Get current system status
   */
  async getSystemStatus(): Promise<SystemStatus> {
    try {
      const response = await apiClient.get<SystemStatus>('/api/system/status')
      return response.data
    } catch (error) {
      console.error('Failed to fetch system status:', error)
      throw error
    }
  }

  /**
   * Get system health check
   */
  async getHealthCheck(): Promise<HealthCheckResponse> {
    try {
      const response = await apiClient.get<HealthCheckResponse>('/health')
      return response.data
    } catch (error) {
      console.error('Failed to fetch health check:', error)
      throw error
    }
  }

  /**
   * Get federation status
   */
  async getFederationStatus(): Promise<FederationStatus> {
    try {
      const response = await apiClient.get<FederationStatus>('/api/federation/status')
      return response.data
    } catch (error) {
      console.error('Failed to fetch federation status:', error)
      throw error
    }
  }

  /**
   * Subscribe to real-time system status updates via WebSocket
   */
  connectSystemStatus(onUpdate: (status: SystemStatus) => void): () => void {
    this.subscribers.add(onUpdate)

    // Return unsubscribe function
    return () => {
      this.subscribers.delete(onUpdate)
      if (this.subscribers.size === 0) {
        this.disconnect()
      }
    }
  }

  /**
   * Connect to WebSocket for real-time status
   */
  private async connect(): Promise<void> {
    if (this.wsConnection) return

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/ws/system/status`

      this.wsConnection = new WebSocket(wsUrl)

      this.wsConnection.onopen = () => {
        console.log('Connected to system status WebSocket')
        this.reconnectAttempts = 0
      }

      this.wsConnection.onmessage = (event) => {
        try {
          const status = JSON.parse(event.data) as SystemStatus
          this.subscribers.forEach((subscriber) => subscriber(status))
        } catch (error) {
          console.error('Failed to parse system status:', error)
        }
      }

      this.wsConnection.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      this.wsConnection.onclose = () => {
        console.log('System status WebSocket closed')
        this.wsConnection = null
        this.reconnect()
      }
    } catch (error) {
      console.error('Failed to connect to system status WebSocket:', error)
      this.reconnect()
    }
  }

  /**
   * Reconnect with exponential backoff
   */
  private reconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)

    setTimeout(() => {
      if (this.subscribers.size > 0) {
        this.connect()
      }
    }, delay)
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    if (this.wsConnection) {
      this.wsConnection.close()
      this.wsConnection = null
    }
    this.subscribers.clear()
    this.reconnectAttempts = 0
  }

  /**
   * Force reconnect
   */
  async forceReconnect(): Promise<void> {
    this.disconnect()
    this.reconnectAttempts = 0
    if (this.subscribers.size > 0) {
      await this.connect()
    }
  }
}

// Export singleton
export default new SystemStatusService()
