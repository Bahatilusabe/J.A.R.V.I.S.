/**
 * Edge Device Management API Service
 * Handles all API calls related to edge device monitoring and management
 */

import axios, { AxiosInstance, AxiosError } from 'axios'

interface EdgeDevice {
  id: string
  name: string
  platform: 'atlas' | 'hisilicon' | 'unknown'
  status: 'online' | 'offline' | 'degraded'
  cpu_usage: number
  memory_usage: number
  temperature: number
  uptime: number
  last_seen: string
  firmware_version: string
  tee_enabled: boolean
  tpm_attestation: boolean
  location: string
  model: string
  cores: number
  memory_gb: number
}

interface DeviceHistory {
  timestamp: string
  device_id: string
  cpu_usage: number
  memory_usage: number
  temperature: number
  status: string
}

interface SecurityMetrics {
  total_devices: number
  secure_devices: number
  attestation_success: number
  encryption_enabled: number
  seal_status: string
  device_binding: number
}

interface RemoteCommandResponse {
  success: boolean
  device_id: string
  command: string
  result?: string
  error?: string
  timestamp: string
}

interface AttestationResult {
  device_id: string
  tpm_version: string
  pcr_values: Record<string, string>
  attestation_status: 'success' | 'failed' | 'pending'
  timestamp: string
}

class EdgeDeviceService {
  private apiClient: AxiosInstance
  private baseURL: string

  constructor(baseURL: string = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000')) {
    this.baseURL = baseURL
    this.apiClient = axios.create({
      baseURL: `${this.baseURL}/api/edge-devices`,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add token to requests
    this.apiClient.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    // Handle errors
    this.apiClient.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        console.error('API Error:', error.response?.status, error.response?.data)
        return Promise.reject(error)
      }
    )
  }

  /**
   * Fetch all edge devices
   */
  async getDevices(): Promise<EdgeDevice[]> {
    try {
      const response = await this.apiClient.get<EdgeDevice[]>('/devices')
      return response.data
    } catch (error) {
      console.error('Failed to fetch devices:', error)
      throw error
    }
  }

  /**
   * Fetch specific device details
   */
  async getDevice(deviceId: string): Promise<EdgeDevice> {
    try {
      const response = await this.apiClient.get<EdgeDevice>(`/devices/${deviceId}`)
      return response.data
    } catch (error) {
      console.error(`Failed to fetch device ${deviceId}:`, error)
      throw error
    }
  }

  /**
   * Get device history for trend analysis
   */
  async getDeviceHistory(
    deviceId: string,
    options: {
      limit?: number
      offset?: number
      start_time?: string
      end_time?: string
    } = {}
  ): Promise<DeviceHistory[]> {
    try {
      const response = await this.apiClient.get<DeviceHistory[]>(`/devices/${deviceId}/history`, {
        params: options,
      })
      return response.data
    } catch (error) {
      console.error(`Failed to fetch device history for ${deviceId}:`, error)
      throw error
    }
  }

  /**
   * Get aggregated security metrics
   */
  async getSecurityMetrics(): Promise<SecurityMetrics> {
    try {
      const response = await this.apiClient.get<SecurityMetrics>('/metrics')
      return response.data
    } catch (error) {
      console.error('Failed to fetch security metrics:', error)
      throw error
    }
  }

  /**
   * Get system health status
   */
  async getHealthStatus(): Promise<{
    overall_status: 'healthy' | 'degraded' | 'critical'
    devices_online: number
    devices_offline: number
    alerts: string[]
  }> {
    try {
      const response = await this.apiClient.get('/health')
      return response.data
    } catch (error) {
      console.error('Failed to fetch health status:', error)
      throw error
    }
  }

  /**
   * Get active alerts
   */
  async getAlerts(options: {
    severity?: 'critical' | 'warning' | 'info'
    device_id?: string
    limit?: number
  } = {}): Promise<
    Array<{
      id: string
      device_id: string
      severity: string
      message: string
      timestamp: string
    }>
  > {
    try {
      const response = await this.apiClient.get('/alerts', { params: options })
      return response.data
    } catch (error) {
      console.error('Failed to fetch alerts:', error)
      throw error
    }
  }

  /**
   * Execute remote command on device
   */
  async executeRemoteCommand(
    deviceId: string,
    command: string,
    parameters?: Record<string, string | number | boolean>
  ): Promise<RemoteCommandResponse> {
    try {
      const response = await this.apiClient.post<RemoteCommandResponse>(
        `/devices/${deviceId}/command`,
        {
          command,
          parameters,
        }
      )
      return response.data
    } catch (error) {
      console.error(`Failed to execute command on ${deviceId}:`, error)
      throw error
    }
  }

  /**
   * Get TPM attestation status
   */
  async getAttestationStatus(deviceId: string): Promise<AttestationResult> {
    try {
      const response = await this.apiClient.get<AttestationResult>(
        `/devices/${deviceId}/attestation`
      )
      return response.data
    } catch (error) {
      console.error(`Failed to fetch attestation status for ${deviceId}:`, error)
      throw error
    }
  }

  /**
   * Trigger TPM attestation
   */
  async triggerAttestation(deviceId: string): Promise<AttestationResult> {
    try {
      const response = await this.apiClient.post<AttestationResult>(
        `/devices/${deviceId}/attestation/verify`
      )
      return response.data
    } catch (error) {
      console.error(`Failed to trigger attestation for ${deviceId}:`, error)
      throw error
    }
  }

  /**
   * Get compliance status
   */
  async getComplianceStatus(deviceId?: string): Promise<{
    device_id?: string
    tee_status: string
    tpm_status: string
    encryption_status: string
    compliance_score: number
    last_check: string
  }> {
    try {
      const response = await this.apiClient.get('/security/compliance', {
        params: deviceId ? { device_id: deviceId } : undefined,
      })
      return response.data
    } catch (error) {
      console.error('Failed to fetch compliance status:', error)
      throw error
    }
  }

  /**
   * Seal keys on device
   */
  async sealKeys(
    deviceId: string,
    options: {
      key_id: string
      policy?: string
      pcr_values?: string[]
    }
  ): Promise<{
    success: boolean
    device_id: string
    key_id: string
    sealed_data?: string
    error?: string
  }> {
    try {
      const response = await this.apiClient.post(`/security/seal`, {
        device_id: deviceId,
        ...options,
      })
      return response.data
    } catch (error) {
      console.error(`Failed to seal keys on ${deviceId}:`, error)
      throw error
    }
  }

  /**
   * Get device metrics for performance monitoring
   */
  async getDeviceMetrics(
    deviceId: string,
    options: {
      metric_type?: 'cpu' | 'memory' | 'temperature' | 'all'
      time_range?: 'last_hour' | 'last_day' | 'last_week'
    } = {}
  ): Promise<
    Array<{
      timestamp: string
      cpu_usage?: number
      memory_usage?: number
      temperature?: number
    }>
  > {
    try {
      const response = await this.apiClient.get(`/devices/${deviceId}/metrics`, {
        params: options,
      })
      return response.data
    } catch (error) {
      console.error(`Failed to fetch metrics for ${deviceId}:`, error)
      throw error
    }
  }

  /**
   * Search devices by criteria
   */
  async searchDevices(query: {
    name?: string
    platform?: string
    status?: string
    location?: string
    limit?: number
    offset?: number
  }): Promise<EdgeDevice[]> {
    try {
      const response = await this.apiClient.get<EdgeDevice[]>('/devices/search', {
        params: query,
      })
      return response.data
    } catch (error) {
      console.error('Failed to search devices:', error)
      throw error
    }
  }

  /**
   * Bulk operations on multiple devices
   */
  async bulkOperation(
    deviceIds: string[],
    operation: string,
    parameters?: Record<string, string | number | boolean>
  ): Promise<
    Array<{
      device_id: string
      success: boolean
      result?: string
      error?: string
    }>
  > {
    try {
      const response = await this.apiClient.post('/devices/bulk', {
        device_ids: deviceIds,
        operation,
        parameters,
      })
      return response.data
    } catch (error) {
      console.error('Failed to execute bulk operation:', error)
      throw error
    }
  }

  /**
   * Get platform-specific information
   */
  async getPlatformInfo(platform: 'atlas' | 'hisilicon'): Promise<{
    platform: string
    supported_features: string[]
    driver_version: string
    hardware_capabilities: Record<string, string | number | boolean>
    status: 'available' | 'unavailable'
  }> {
    try {
      const response = await this.apiClient.get(`/platforms/${platform}`)
      return response.data
    } catch (error) {
      console.error(`Failed to fetch platform info for ${platform}:`, error)
      throw error
    }
  }

  /**
   * Set device configuration
   */
  async setDeviceConfig(
    deviceId: string,
    config: Record<string, string | number | boolean | object>
  ): Promise<{
    success: boolean
    device_id: string
    applied_config: Record<string, string | number | boolean | object>
  }> {
    try {
      const response = await this.apiClient.put(`/devices/${deviceId}/config`, config)
      return response.data
    } catch (error) {
      console.error(`Failed to set device config for ${deviceId}:`, error)
      throw error
    }
  }

  /**
   * Get device logs
   */
  async getDeviceLogs(
    deviceId: string,
    options: {
      level?: 'debug' | 'info' | 'warning' | 'error'
      limit?: number
      offset?: number
      start_time?: string
      end_time?: string
    } = {}
  ): Promise<
    Array<{
      timestamp: string
      level: string
      message: string
      context?: Record<string, unknown>
    }>
  > {
    try {
      const response = await this.apiClient.get(`/devices/${deviceId}/logs`, {
        params: options,
      })
      return response.data
    } catch (error) {
      console.error(`Failed to fetch device logs for ${deviceId}:`, error)
      throw error
    }
  }

  /**
   * Verify device firmware integrity
   */
  async verifyFirmwareIntegrity(deviceId: string): Promise<{
    device_id: string
    firmware_hash: string
    is_valid: boolean
    signature_status: 'valid' | 'invalid' | 'unknown'
    verification_timestamp: string
  }> {
    try {
      const response = await this.apiClient.post(`/devices/${deviceId}/firmware/verify`)
      return response.data
    } catch (error) {
      console.error(`Failed to verify firmware for ${deviceId}:`, error)
      throw error
    }
  }
}

// Export singleton instance
export const edgeDeviceService = new EdgeDeviceService()

export default EdgeDeviceService
