import { useState, useCallback } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import metricsService from '../services/metrics.service'
import { RootState } from '../store/index'

interface SystemMetrics {
  cpu: number
  memory: number
  disk: number
  network: {
    bytesIn: number
    bytesOut: number
  }
  timestamp: string
}

interface SecurityMetrics {
  threatLevel: 'critical' | 'high' | 'medium' | 'low'
  alertCount: number
  vulnerabilityCount: number
  breachAttempts: number
  timestamp: string
}

interface PerformanceMetrics {
  latency: number
  throughput: number
  errorRate: number
  availability: number
  timestamp: string
}

interface GrafanaPanel {
  id: string
  title: string
  url: string
}

interface UseMetricsReturn {
  systemMetrics: SystemMetrics | null
  securityMetrics: SecurityMetrics | null
  performanceMetrics: PerformanceMetrics | null
  grafanaPanels: GrafanaPanel[]
  healthStatus: Record<string, unknown> | null
  isLoading: boolean
  error: string | null
  getSystemMetrics: () => Promise<void>
  getSystemMetricsHistory: (startTime: string, endTime: string, step?: string) => Promise<void>
  getSecurityMetrics: () => Promise<void>
  getSecurityMetricsHistory: (startTime: string, endTime: string, step?: string) => Promise<void>
  getPerformanceMetrics: () => Promise<void>
  getPerformanceMetricsHistory: (startTime: string, endTime: string, step?: string) => Promise<void>
  getGrafanaPanels: () => Promise<void>
  getGrafanaEmbedUrl: (panelId: number, dashboardId?: number) => Promise<string>
  getMetricAggregations: (options: {
    metrics: string[]
    aggregation: 'avg' | 'sum' | 'min' | 'max' | 'rate'
    startTime: string
    endTime: string
  }) => Promise<Record<string, number>>
  getHealthStatus: () => Promise<void>
  clearError: () => void
}

/**
 * Hook for system metrics and monitoring
 * Manages system, security, and performance metrics
 * Integrates with Prometheus and Grafana
 */
export function useMetrics(): UseMetricsReturn {
  const dispatch = useDispatch()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Get metrics state from Redux
  const metricsState = useSelector((state: RootState) => state.metrics)
  const systemMetrics = metricsState?.systemMetrics || null
  const securityMetrics = metricsState?.securityMetrics || null
  const performanceMetrics = metricsState?.performanceMetrics || null
  const grafanaPanels = metricsState?.grafanaPanels || []
  const healthStatus = metricsState?.healthStatus || null

  /**
   * Get system metrics (CPU, memory, disk, network)
   */
  const getSystemMetrics = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const metrics = await metricsService.getSystemMetrics()

      // Dispatch to Redux store
      dispatch({
        type: 'metrics/systemMetricsFetched',
        payload: metrics,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch system metrics'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [dispatch])

  /**
   * Get historical system metrics
   */
  const getSystemMetricsHistory = useCallback(
    async (startTime: string, endTime: string, step?: string) => {
      try {
        setIsLoading(true)
        setError(null)

        const metrics = await metricsService.getSystemMetricsHistory({
          startTime,
          endTime,
          step,
        })

        // Dispatch to Redux store
        dispatch({
          type: 'metrics/systemMetricsHistoryFetched',
          payload: metrics,
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch system metrics history'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [dispatch]
  )

  /**
   * Get security metrics
   */
  const getSecurityMetrics = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const metrics = await metricsService.getSecurityMetrics()

      // Dispatch to Redux store
      dispatch({
        type: 'metrics/securityMetricsFetched',
        payload: metrics,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch security metrics'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [dispatch])

  /**
   * Get historical security metrics
   */
  const getSecurityMetricsHistory = useCallback(
    async (startTime: string, endTime: string, step?: string) => {
      try {
        setIsLoading(true)
        setError(null)

        const metrics = await metricsService.getSecurityMetricsHistory({
          startTime,
          endTime,
          step,
        })

        // Dispatch to Redux store
        dispatch({
          type: 'metrics/securityMetricsHistoryFetched',
          payload: metrics,
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch security metrics history'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [dispatch]
  )

  /**
   * Get performance metrics
   */
  const getPerformanceMetrics = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const metrics = await metricsService.getPerformanceMetrics()

      // Dispatch to Redux store
      dispatch({
        type: 'metrics/performanceMetricsFetched',
        payload: metrics,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch performance metrics'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [dispatch])

  /**
   * Get historical performance metrics
   */
  const getPerformanceMetricsHistory = useCallback(
    async (startTime: string, endTime: string, step?: string) => {
      try {
        setIsLoading(true)
        setError(null)

        const metrics = await metricsService.getPerformanceMetricsHistory({
          startTime,
          endTime,
          step,
        })

        // Dispatch to Redux store
        dispatch({
          type: 'metrics/performanceMetricsHistoryFetched',
          payload: metrics,
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch performance metrics history'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [dispatch]
  )

  /**
   * Get available Grafana panels
   */
  const getGrafanaPanels = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const panels = await metricsService.getGrafanaPanels()

      // Dispatch to Redux store
      dispatch({
        type: 'metrics/grafanaPanelsFetched',
        payload: panels,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch Grafana panels'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [dispatch])

  /**
   * Get Grafana panel embed URL
   */
  const getGrafanaEmbedUrl = useCallback(
    async (panelId: number, dashboardId?: number): Promise<string> => {
      try {
        return await metricsService.getGrafanaEmbedUrl(panelId, dashboardId)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to generate Grafana URL'
        setError(message)
        return ''
      }
    },
    []
  )

  /**
   * Get metric aggregations
   */
  const getMetricAggregations = useCallback(
    async (options: {
      metrics: string[]
      aggregation: 'avg' | 'sum' | 'min' | 'max' | 'rate'
      startTime: string
      endTime: string
    }): Promise<Record<string, number>> => {
      try {
        setIsLoading(true)
        setError(null)

        const aggregations = await metricsService.getMetricAggregations(options)

        return aggregations
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch metric aggregations'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    []
  )

  /**
   * Get system health status
   */
  const getHealthStatus = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const status = await metricsService.getHealthStatus()

      // Dispatch to Redux store
      dispatch({
        type: 'metrics/healthStatusFetched',
        payload: status,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch health status'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [dispatch])

  /**
   * Clear error message
   */
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    systemMetrics,
    securityMetrics,
    performanceMetrics,
    grafanaPanels,
    healthStatus,
    isLoading,
    error,
    getSystemMetrics,
    getSystemMetricsHistory,
    getSecurityMetrics,
    getSecurityMetricsHistory,
    getPerformanceMetrics,
    getPerformanceMetricsHistory,
    getGrafanaPanels,
    getGrafanaEmbedUrl,
    getMetricAggregations,
    getHealthStatus,
    clearError,
  }
}

export default useMetrics
