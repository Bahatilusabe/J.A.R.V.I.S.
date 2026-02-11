import { useState, useCallback, useEffect, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import systemStatusService, {
  SystemStatus,
  HealthCheckResponse,
  FederationStatus,
} from '../services/system-status.service'
import { RootState } from '../store/index'

interface UseSystemStatusReturn {
  systemStatus: SystemStatus | null
  healthCheck: HealthCheckResponse | null
  federationStatus: FederationStatus | null
  isConnected: boolean
  isLoading: boolean
  error: string | null
  refreshSystemStatus: () => Promise<void>
  refreshHealthCheck: () => Promise<void>
  refreshFederationStatus: () => Promise<void>
  reconnect: () => Promise<void>
  clearError: () => void
}

/**
 * Hook for real-time system status monitoring
 * Manages system mode, health checks, and federation status
 */
export function useSystemStatus(): UseSystemStatusReturn {
  const dispatch = useDispatch()
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const unsubscribeRef = useRef<(() => void) | null>(null)

  // Get system state from Redux
  const systemState = useSelector((state: RootState) => state.system)
  const systemStatus = systemState?.status || null
  const healthCheck = systemState?.health || null
  const federationStatus = systemState?.federation || null

  /**
   * Refresh system status
   */
  const refreshSystemStatus = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const status = await systemStatusService.getSystemStatus()

      dispatch({
        type: 'system/statusUpdated',
        payload: status,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to refresh system status'
      setError(message)
      // Do not rethrow to prevent top-level unhandled promise rejections
      return
    } finally {
      setIsLoading(false)
    }
  }, [dispatch])

  /**
   * Refresh health check
   */
  const refreshHealthCheck = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const health = await systemStatusService.getHealthCheck()

      dispatch({
        type: 'system/healthUpdated',
        payload: health,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to refresh health check'
      setError(message)
      // Do not rethrow
      return
    } finally {
      setIsLoading(false)
    }
  }, [dispatch])

  /**
   * Refresh federation status
   */
  const refreshFederationStatus = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const federation = await systemStatusService.getFederationStatus()

      dispatch({
        type: 'system/federationUpdated',
        payload: federation,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to refresh federation status'
      setError(message)
      // Do not rethrow
      return
    } finally {
      setIsLoading(false)
    }
  }, [dispatch])

  /**
   * Reconnect to WebSocket
   */
  const reconnect = useCallback(async () => {
    try {
      setError(null)
      await systemStatusService.forceReconnect()
      setIsConnected(true)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to reconnect'
      setError(message)
    }
  }, [])

  /**
   * Clear error
   */
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  /**
   * Setup WebSocket subscription on mount
   */
  useEffect(() => {
    // Subscribe to real-time status updates
    unsubscribeRef.current = systemStatusService.connectSystemStatus((status) => {
      setIsConnected(true)

      dispatch({
        type: 'system/statusUpdated',
        payload: status,
      })
    })

    // Initial fetch
    refreshSystemStatus()
    refreshHealthCheck()
    refreshFederationStatus()

    // Polling interval (30 seconds)
    const pollInterval = setInterval(() => {
      refreshHealthCheck()
    }, 30000)

    return () => {
      clearInterval(pollInterval)
      if (unsubscribeRef.current) {
        unsubscribeRef.current()
      }
    }
  }, [dispatch, refreshSystemStatus, refreshHealthCheck, refreshFederationStatus])

  return {
    systemStatus,
    healthCheck,
    federationStatus,
    isConnected,
    isLoading,
    error,
    refreshSystemStatus,
    refreshHealthCheck,
    refreshFederationStatus,
    reconnect,
    clearError,
  }
}

export default useSystemStatus
