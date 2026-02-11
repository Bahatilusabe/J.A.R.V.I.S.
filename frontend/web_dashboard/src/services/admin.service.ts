/**
 * Admin Service - Typed API client for admin operations
 * 
 * Provides methods for:
 * - System health & metrics
 * - User management (CRUD, password reset)
 * - Feature flags toggling
 * - Audit logs retrieval
 * - Settings management
 * - Key rotation
 * - Device binding
 * 
 * All methods include error handling and proper status codes.
 */

const API_BASE = '/api'

// ============================================================================
// Type Definitions
// ============================================================================

export interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'analyst' | 'operator' | 'viewer'
  status: 'active' | 'inactive'
  lastLogin?: string
  createdAt?: string
  passwordChangedAt?: string
}

export interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical'
  timestamp: string
  uptimeSeconds: number
  uptimeFormatted: string
  memory: {
    usageBytes: number
    percent: number
  }
  cpu: {
    percent: number
  }
  components: {
    api_server: string
    database: string
    cache: string
    websocket: string
  }
}

export interface SystemMetrics {
  timestamp: string
  process: {
    pid: number
    memoryRssMb: number
    memoryPercent: number
    cpuPercent: number
    numThreads: number
  }
  system: {
    cpuCount: number
    virtualMemoryTotalGb: number
    virtualMemoryAvailableGb: number
    virtualMemoryPercent: number
  }
  uptimeSeconds: number
}

export interface FeatureFlags {
  [key: string]: boolean
}

export interface FeatureFlagsResponse {
  flags: FeatureFlags
  timestamp: string
  count: number
}

export interface AuditLog {
  id: string
  timestamp: string
  user: string
  action: string
  resource: string
  details: string
  status: 'success' | 'failure'
}

export interface AuditLogsResponse {
  logs: AuditLog[]
  count: number
  total: number
  timestamp: string
}

export interface CreateUserRequest {
  username: string
  email: string
  role: 'admin' | 'analyst' | 'operator'
}

export interface CreateUserResponse {
  user: Omit<User, 'passwordChangedAt' | 'createdAt'>
  temporaryPassword: string
  created: boolean
  message: string
}

export interface ResetPasswordResponse {
  success: boolean
  username: string
  temporaryPassword: string
  message: string
}

export interface ChangePasswordRequest {
  newPassword: string
}

export interface ChangePasswordResponse {
  success: boolean
  username: string
  message: string
}

export interface ToggleFlagRequest {
  enabled: boolean
}

export interface ToggleFlagResponse {
  flag: string
  enabled: boolean
  previous: boolean
  timestamp: string
}

export interface SettingsResponse {
  [key: string]: unknown
}

export interface RotateKeysResponse {
  status: string
  applied: boolean
  sk_b64: string
  pk_b64: string
}

export interface DeviceBindRequest {
  deviceId: string
  biometricToken: string
}

export interface DeviceBindResponse {
  bound: boolean
  bindId: string
  handshakeId: string
}

// ============================================================================
// API Error Handler
// ============================================================================

class AdminServiceError extends Error {
  constructor(
    public statusCode: number,
    public detail: string,
    message?: string
  ) {
    super(message || detail)
    this.name = 'AdminServiceError'
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `HTTP ${response.status}`
    try {
      const errorData = await response.json() as { detail?: string }
      detail = errorData.detail || detail
    } catch {
      // Could not parse error response
    }
    throw new AdminServiceError(response.status, detail)
  }
  return response.json() as Promise<T>
}

// ============================================================================
// Admin Service
// ============================================================================

const adminService = {
  /**
   * Get comprehensive system health status
   */
  async getSystemHealth(): Promise<SystemHealth> {
    const response = await fetch(`${API_BASE}/health`)
    const data = await handleResponse<{
      status: string
      timestamp: string
      uptime_seconds: number
      uptime_formatted: string
      memory: { usage_bytes: number; percent: number }
      cpu: { percent: number }
      components: Record<string, string>
    }>(response)

    return {
      status: data.status as 'healthy' | 'warning' | 'critical',
      timestamp: data.timestamp,
      uptimeSeconds: data.uptime_seconds,
      uptimeFormatted: data.uptime_formatted,
      memory: {
        usageBytes: data.memory.usage_bytes,
        percent: data.memory.percent,
      },
      cpu: {
        percent: data.cpu.percent,
      },
      components: data.components as {
        api_server: string
        database: string
        cache: string
        websocket: string
      },
    }
  },

  /**
   * Get detailed system metrics
   */
  async getSystemMetrics(): Promise<SystemMetrics> {
    const response = await fetch(`${API_BASE}/metrics`)
    const data = await handleResponse<{
      timestamp: string
      process: {
        pid: number
        memory_rss_mb: number
        memory_percent: number
        cpu_percent: number
        num_threads: number
      }
      system: {
        cpu_count: number
        virtual_memory_total_gb: number
        virtual_memory_available_gb: number
        virtual_memory_percent: number
      }
      uptime_seconds: number
    }>(response)

    return {
      timestamp: data.timestamp,
      process: {
        pid: data.process.pid,
        memoryRssMb: data.process.memory_rss_mb,
        memoryPercent: data.process.memory_percent,
        cpuPercent: data.process.cpu_percent,
        numThreads: data.process.num_threads,
      },
      system: {
        cpuCount: data.system.cpu_count,
        virtualMemoryTotalGb: data.system.virtual_memory_total_gb,
        virtualMemoryAvailableGb: data.system.virtual_memory_available_gb,
        virtualMemoryPercent: data.system.virtual_memory_percent,
      },
      uptimeSeconds: data.uptime_seconds,
    }
  },

  /**
   * Get all feature flags
   */
  async getFeatureFlags(): Promise<FeatureFlagsResponse> {
    const response = await fetch(`${API_BASE}/flags`)
    const data = await handleResponse<FeatureFlagsResponse>(response)
    return data
  },

  /**
   * Toggle a feature flag
   */
  async toggleFeatureFlag(flagName: string, enabled: boolean): Promise<ToggleFlagResponse> {
    const response = await fetch(`${API_BASE}/flags/${flagName}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled }),
    })
    const data = await handleResponse<ToggleFlagResponse>(response)
    return data
  },

  /**
   * List all users
   */
  async listUsers(): Promise<User[]> {
    const response = await fetch(`${API_BASE}/users`)
    const data = await handleResponse<{ users: User[]; count: number; timestamp: string }>(response)
    return data.users
  },

  /**
   * Create a new user
   */
  async createUser(user: CreateUserRequest): Promise<CreateUserResponse> {
    const response = await fetch(`${API_BASE}/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(user),
    })
    const data = await handleResponse<CreateUserResponse>(response)
    return data
  },

  /**
   * Delete a user
   */
  async deleteUser(username: string): Promise<{ deleted: boolean; username: string }> {
    const response = await fetch(`${API_BASE}/users/${username}`, {
      method: 'DELETE',
    })
    const data = await handleResponse<{ deleted: boolean; username: string }>(response)
    return data
  },

  /**
   * Change a user's password (user-initiated)
   */
  async changePassword(username: string, newPassword: string): Promise<ChangePasswordResponse> {
    const response = await fetch(`${API_BASE}/users/${username}/password/change`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_password: newPassword }),
    })
    const data = await handleResponse<ChangePasswordResponse>(response)
    return data
  },

  /**
   * Reset a user's password (admin-initiated)
   */
  async resetPassword(username: string): Promise<ResetPasswordResponse> {
    const response = await fetch(`${API_BASE}/users/${username}/password/reset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
    const data = await handleResponse<ResetPasswordResponse>(response)
    return data
  },

  /**
   * Get audit logs
   */
  async getAuditLogs(limit: number = 100): Promise<AuditLogsResponse> {
    const response = await fetch(`${API_BASE}/logs?limit=${limit}`)
    const data = await handleResponse<AuditLogsResponse>(response)
    return data
  },

  /**
   * Clear all audit logs
   */
  async clearAuditLogs(): Promise<{ cleared: number; timestamp: string }> {
    const response = await fetch(`${API_BASE}/logs/clear`, {
      method: 'POST',
    })
    const data = await handleResponse<{ cleared: number; timestamp: string }>(response)
    return data
  },

  /**
   * Get incidents
   */
  async getIncidents(): Promise<Array<{ id: string; type: string; severity: string; status: string; title: string; timestamp: string; affectedSystems: string[] }>> {
    const response = await fetch(`${API_BASE}/incidents`)
    const data = await handleResponse<Array<{ id: string; type: string; severity: string; status: string; title: string; timestamp: string; affectedSystems: string[] }>>(response)
    return data
  },

  /**
   * Get secret keys
   */
  async getSecretKeys(): Promise<Array<{ id: string; name: string; type: string; status: string; lastRotated: string; expiresAt?: string }>> {
    const response = await fetch(`${API_BASE}/security/keys`)
    const data = await handleResponse<Array<{ id: string; name: string; type: string; status: string; lastRotated: string; expiresAt?: string }>>(response)
    return data
  },

  /**
   * Rotate a security key
   */
  async rotateKey(keyId: string): Promise<{ success: boolean; newExpiresAt?: string }> {
    const response = await fetch(`${API_BASE}/security/keys/${keyId}/rotate`, {
      method: 'POST',
    })
    const data = await handleResponse<{ success: boolean; newExpiresAt?: string }>(response)
    return data
  },

  /**
   * Update incident status
   */
  async updateIncidentStatus(incidentId: string, status: string): Promise<{ success: boolean }> {
    const response = await fetch(`${API_BASE}/incidents/${incidentId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    })
    const data = await handleResponse<{ success: boolean }>(response)
    return data
  },

  /**
   * Get system settings
   */
  async getSettings(): Promise<SettingsResponse> {
    const response = await fetch(`${API_BASE}/admin/settings`)
    const data = await handleResponse<SettingsResponse>(response)
    return data
  },

  /**
   * Update system settings
   */
  async updateSettings(settings: Record<string, unknown>): Promise<{ ok: boolean }> {
    const response = await fetch(`${API_BASE}/admin/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    })
    const data = await handleResponse<{ ok: boolean }>(response)
    return data
  },

  /**
   * Rotate PQC keys
   */
  async rotateKeys(): Promise<RotateKeysResponse> {
    const response = await fetch(`${API_BASE}/keys/rotate`, {
      method: 'POST',
    })
    const data = await handleResponse<RotateKeysResponse>(response)
    return data
  },

  /**
   * Delete (revoke) an API key
   */
  async deleteApiKey(keyId: string): Promise<{ deleted: boolean; id?: string }> {
    const response = await fetch(`${API_BASE}/api-keys/${keyId}`, {
      method: 'DELETE',
    })
    const data = await handleResponse<{ deleted: boolean; username?: string }>(response)
    return { deleted: data.deleted, id: keyId }
  },

  /**
   * Bind a device with biometric token
   */
  async deviceBind(request: DeviceBindRequest): Promise<DeviceBindResponse> {
    const response = await fetch(`${API_BASE}/device/bind`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        device_id: request.deviceId,
        biometric_token: request.biometricToken,
      }),
    })
    const data = await handleResponse<DeviceBindResponse>(response)
    return data
  },

  /**
   * Check if a specific resource exists or is accessible
   * (Used for validation and capability detection)
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE}/health`)
      return response.ok
    } catch {
      return false
    }
  },
}

export default adminService
export { AdminServiceError }
