import { apiClient } from '../utils/api'
import {
  PolicyAction,
  ContainmentAction,
  HealingPolicy,
  PaginatedResponse,
} from '../types/index'

/**
 * Policy & Containment Service
 * Handles policy enforcement and containment actions
 * Routes through backend/api/policy.py to backend/core/self_healing/policy_engine.py
 */
class PolicyService {
  /**
   * Enforce a policy action
   */
  async enforcePolicy(options: {
    policyId: string
    target: string
    actionType: string
    severity: 'critical' | 'high' | 'medium' | 'low'
    reason: string
  }): Promise<PolicyAction> {
    try {
      const response = await apiClient.post<PolicyAction>(
        '/api/policy/enforce',
        {
          ...options,
          timestamp: new Date().toISOString(),
        }
      )

      return response.data
    } catch (error) {
      console.error('Failed to enforce policy:', error)
      throw error
    }
  }

  /**
   * Execute a containment action
   */
  async executeContainment(options: {
    type: 'isolate' | 'quarantine' | 'kill-process' | 'block-connection' | 'disable-service'
    target: string
    reason: string
    duration?: number
  }): Promise<ContainmentAction> {
    try {
      const response = await apiClient.post<ContainmentAction>(
        '/api/policy/containment/execute',
        {
          ...options,
          timestamp: new Date().toISOString(),
        }
      )

      return response.data
    } catch (error) {
      console.error('Failed to execute containment action:', error)
      throw error
    }
  }

  /**
   * Get action history with pagination
   */
  async getActionHistory(options: {
    page?: number
    pageSize?: number
    status?: 'pending' | 'executing' | 'completed' | 'failed'
    type?: string
    target?: string
    startDate?: string
    endDate?: string
  } = {}): Promise<PaginatedResponse<PolicyAction>> {
    try {
      const params = new URLSearchParams()

      if (options.page) params.append('page', String(options.page))
      if (options.pageSize) params.append('pageSize', String(options.pageSize))
      if (options.status) params.append('status', options.status)
      if (options.type) params.append('type', options.type)
      if (options.target) params.append('target', options.target)
      if (options.startDate) params.append('startDate', options.startDate)
      if (options.endDate) params.append('endDate', options.endDate)

      const response = await apiClient.get<PaginatedResponse<PolicyAction>>(
        `/api/policy/actions?${params}`
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch action history:', error)
      throw error
    }
  }

  /**
   * Get specific policy action
   */
  async getAction(actionId: string): Promise<PolicyAction> {
    try {
      const response = await apiClient.get<PolicyAction>(
        `/api/policy/actions/${actionId}`
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch policy action:', error)
      throw error
    }
  }

  /**
   * Get all available healing policies
   */
  async getAvailablePolicies(): Promise<HealingPolicy[]> {
    try {
      const response = await apiClient.get<HealingPolicy[]>(
        '/api/policy/policies'
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch healing policies:', error)
      throw error
    }
  }

  /**
   * Get specific healing policy
   */
  async getPolicy(policyId: string): Promise<HealingPolicy> {
    try {
      const response = await apiClient.get<HealingPolicy>(
        `/api/policy/policies/${policyId}`
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch healing policy:', error)
      throw error
    }
  }

  /**
   * Get policy execution statistics
   */
  async getExecutionStats(
    policyId?: string
  ): Promise<{
    totalExecutions: number
    successful: number
    failed: number
    pending: number
    successRate: number
    averageExecutionTime: number
  }> {
    try {
      const path = policyId
        ? `/api/policy/stats/${policyId}`
        : '/api/policy/stats'

      const response = await apiClient.get<{
        totalExecutions: number
        successful: number
        failed: number
        pending: number
        successRate: number
        averageExecutionTime: number
      }>(path)

      return response.data
    } catch (error) {
      console.error('Failed to fetch execution stats:', error)
      throw error
    }
  }

  /**
   * Revert a containment action
   */
  async revertAction(actionId: string, reason: string): Promise<PolicyAction> {
    try {
      const response = await apiClient.post<PolicyAction>(
        `/api/policy/actions/${actionId}/revert`,
        { reason, timestamp: new Date().toISOString() }
      )

      return response.data
    } catch (error) {
      console.error('Failed to revert action:', error)
      throw error
    }
  }

  /**
   * Check ethical compliance of an action before execution
   */
  async checkEthicalCompliance(options: {
    actionType: string
    target: string
    reason: string
    severity: 'critical' | 'high' | 'medium' | 'low'
  }): Promise<{ compliant: boolean; reasons: string[]; recommendation: string }> {
    try {
      const response = await apiClient.post<{
        compliant: boolean
        reasons: string[]
        recommendation: string
      }>('/api/policy/ethical-check', options)

      return response.data
    } catch (error) {
      console.error('Failed to check ethical compliance:', error)
      throw error
    }
  }

  /**
   * Get containment action status
   */
  async getContainmentStatus(actionId: string): Promise<ContainmentAction> {
    try {
      const response = await apiClient.get<ContainmentAction>(
        `/api/policy/containment/${actionId}`
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch containment status:', error)
      throw error
    }
  }

  /**
   * Get active containment actions
   */
  async getActiveContainments(): Promise<ContainmentAction[]> {
    try {
      const response = await apiClient.get<ContainmentAction[]>(
        '/api/policy/containment/active'
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch active containments:', error)
      throw error
    }
  }

  /**
   * Update policy settings
   */
  async updatePolicy(
    policyId: string,
    updates: Partial<HealingPolicy>
  ): Promise<HealingPolicy> {
    try {
      const response = await apiClient.patch<HealingPolicy>(
        `/api/policy/policies/${policyId}`,
        updates
      )

      return response.data
    } catch (error) {
      console.error('Failed to update policy:', error)
      throw error
    }
  }

  /**
   * Enable or disable a policy
   */
  async togglePolicy(policyId: string, enabled: boolean): Promise<HealingPolicy> {
    try {
      const response = await apiClient.patch<HealingPolicy>(
        `/api/policy/policies/${policyId}`,
        { enabled }
      )

      return response.data
    } catch (error) {
      console.error('Failed to toggle policy:', error)
      throw error
    }
  }
}

// Export singleton instance
export default new PolicyService()
