import { useState, useCallback, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import policyService from '../services/policy.service'
import { PolicyAction, ContainmentAction } from '../types/index'
import { RootState } from '../store/index'

interface ActionHistory extends PolicyAction {
  id: string
}

interface ExecutionStats {
  totalExecutions: number
  successful: number
  failed: number
  pending: number
  successRate: number
  averageExecutionTime: number
}

interface UsePolicyReturn {
  activeActions: PolicyAction[]
  actionHistory: ActionHistory[]
  executionStats: ExecutionStats | null
  currentPage: number
  totalPages: number
  activeContainments: ContainmentAction[]
  isLoading: boolean
  error: string | null
  enforcePolicy: (policyId: string, target: string, actionType?: string) => Promise<void>
  executeContainment: (actionType: string, targetId: string, duration?: number) => Promise<void>
  getActionHistory: (page?: number, pageSize?: number) => Promise<void>
  getExecutionStats: () => Promise<void>
  revertAction: (actionId: string, reason: string) => Promise<void>
  togglePolicy: (policyId: string, enabled: boolean) => Promise<void>
  checkEthicalCompliance: (options: {
    actionType: string
    target: string
    reason: string
    severity: 'critical' | 'high' | 'medium' | 'low'
  }) => Promise<boolean>
  getActiveContainments: () => Promise<void>
  clearActionHistory: () => void
  clearError: () => void
}

/**
 * Hook for policy enforcement and self-healing containment
 * Manages policy enforcement, action history, and execution statistics
 * Provides real-time action monitoring with rollback capability
 */
export function usePolicy(): UsePolicyReturn {
  const dispatch = useDispatch()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const totalPagesRef = useRef(1)

  // Get policy state from Redux
  const policyState = useSelector((state: RootState) => state.policy)
  const activeActions = policyState?.activeActions || []
  const actionHistory = policyState?.actionHistory || []
  const executionStats = policyState?.executionStats || null
  const activeContainments = policyState?.activeContainments || []

  /**
   * Enforce policy with ethical checks
   */
  const enforcePolicy = useCallback(
    async (policyId: string, target: string, actionType = 'enforce') => {
      try {
        setIsLoading(true)
        setError(null)

        const action = await policyService.enforcePolicy({
          policyId,
          target,
          actionType,
          severity: 'high',
          reason: 'Policy enforcement action',
        })

        // Dispatch to Redux store
        dispatch({
          type: 'policy/actionEnforced',
          payload: action,
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to enforce policy'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [dispatch]
  )

  /**
   * Execute containment action
   */
  const executeContainment = useCallback(
    async (actionType: string, targetId: string, duration?: number) => {
      try {
        setIsLoading(true)
        setError(null)

        const action = await policyService.executeContainment({
          type: actionType as 'isolate' | 'quarantine' | 'kill-process' | 'block-connection' | 'disable-service',
          target: targetId,
          reason: 'Self-healing containment action',
          duration,
        })

        // Dispatch to Redux store
        dispatch({
          type: 'policy/containmentExecuted',
          payload: action,
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to execute containment'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [dispatch]
  )

  /**
   * Get action history with pagination
   */
  const getActionHistory = useCallback(
    async (page = 1, pageSize = 20) => {
      try {
        setIsLoading(true)
        setError(null)

        const response = await policyService.getActionHistory({
          page,
          pageSize,
        })

        setCurrentPage(page)
        totalPagesRef.current = Math.ceil(response.total / pageSize)

        // Dispatch to Redux store
        dispatch({
          type: 'policy/actionHistoryFetched',
          payload: {
            actions: response.items,
            totalPages: Math.ceil(response.total / pageSize),
            page,
          },
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch action history'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [dispatch]
  )

  /**
   * Get execution statistics
   */
  const getExecutionStats = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const stats = await policyService.getExecutionStats()

      // Dispatch to Redux store
      dispatch({
        type: 'policy/statsFetched',
        payload: stats,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch execution stats'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [dispatch])

  /**
   * Revert/rollback action
   */
  const revertAction = useCallback(
    async (actionId: string, reason: string) => {
      try {
        setIsLoading(true)
        setError(null)

        const action = await policyService.revertAction(actionId, reason)

        // Dispatch to Redux store
        dispatch({
          type: 'policy/actionReverted',
          payload: action,
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to revert action'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [dispatch]
  )

  /**
   * Toggle policy enabled/disabled
   */
  const togglePolicy = useCallback(
    async (policyId: string, enabled: boolean) => {
      try {
        setIsLoading(true)
        setError(null)

        const policy = await policyService.togglePolicy(policyId, enabled)

        // Dispatch to Redux store
        dispatch({
          type: 'policy/policyToggled',
          payload: policy,
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to toggle policy'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [dispatch]
  )

  /**
   * Check ethical compliance before executing action
   */
  const checkEthicalCompliance = useCallback(
    async (options: {
      actionType: string
      target: string
      reason: string
      severity: 'critical' | 'high' | 'medium' | 'low'
    }): Promise<boolean> => {
      try {
        setError(null)

        const result = await policyService.checkEthicalCompliance(options)

        if (!result.compliant) {
          setError(`Action violates policy: ${result.reasons.join(', ')}`)
        }

        return result.compliant
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to check ethical compliance'
        setError(message)
        return false
      }
    },
    []
  )

  /**
   * Get active containments
   */
  const getActiveContainments = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const containments = await policyService.getActiveContainments()

      // Dispatch to Redux store
      dispatch({
        type: 'policy/activeContainmentsFetched',
        payload: containments,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch active containments'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [dispatch])

  /**
   * Clear action history from Redux
   */
  const clearActionHistory = useCallback(() => {
    try {
      // Dispatch to Redux store
      dispatch({
        type: 'policy/historyCleared',
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
    activeActions,
    actionHistory,
    executionStats,
    currentPage,
    totalPages: totalPagesRef.current,
    activeContainments,
    isLoading,
    error,
    enforcePolicy,
    executeContainment,
    getActionHistory,
    getExecutionStats,
    revertAction,
    togglePolicy,
    checkEthicalCompliance,
    getActiveContainments,
    clearActionHistory,
    clearError,
  }
}

export default usePolicy
