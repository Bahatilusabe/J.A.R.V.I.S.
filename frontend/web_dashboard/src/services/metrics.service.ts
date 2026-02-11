import { apiClient } from '../utils/api'
import { SystemMetrics, SecurityMetrics, PerformanceMetrics, GrafanaPanel } from '../types/index'

/**
 * Metrics Service
 * Queries metrics from backend/utils/metrics.py exported to Prometheus
 * Supports both direct API queries and Grafana integration
 */
class MetricsService {
  /**
   * Get current system metrics
   */
  async getSystemMetrics(): Promise<SystemMetrics> {
    try {
      const response = await apiClient.get<SystemMetrics>(
        '/api/metrics/system'
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch system metrics:', error)
      throw error
    }
  }

  /**
   * Get historical system metrics
   */
  async getSystemMetricsHistory(options: {
    startTime: string
    endTime: string
    step?: string
  }): Promise<SystemMetrics[]> {
    try {
      const params = new URLSearchParams()
      params.append('startTime', options.startTime)
      params.append('endTime', options.endTime)
      if (options.step) params.append('step', options.step)

      const response = await apiClient.get<SystemMetrics[]>(
        `/api/metrics/system/history?${params}`
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch system metrics history:', error)
      throw error
    }
  }

  /**
   * Get security metrics
   */
  async getSecurityMetrics(): Promise<SecurityMetrics> {
    try {
      const response = await apiClient.get<SecurityMetrics>(
        '/api/metrics/security'
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch security metrics:', error)
      throw error
    }
  }

  /**
   * Get historical security metrics
   */
  async getSecurityMetricsHistory(options: {
    startTime: string
    endTime: string
    step?: string
  }): Promise<SecurityMetrics[]> {
    try {
      const params = new URLSearchParams()
      params.append('startTime', options.startTime)
      params.append('endTime', options.endTime)
      if (options.step) params.append('step', options.step)

      const response = await apiClient.get<SecurityMetrics[]>(
        `/api/metrics/security/history?${params}`
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch security metrics history:', error)
      throw error
    }
  }

  /**
   * Get performance metrics
   */
  async getPerformanceMetrics(): Promise<PerformanceMetrics> {
    try {
      const response = await apiClient.get<PerformanceMetrics>(
        '/api/metrics/performance'
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch performance metrics:', error)
      throw error
    }
  }

  /**
   * Get historical performance metrics
   */
  async getPerformanceMetricsHistory(options: {
    startTime: string
    endTime: string
    step?: string
  }): Promise<PerformanceMetrics[]> {
    try {
      const params = new URLSearchParams()
      params.append('startTime', options.startTime)
      params.append('endTime', options.endTime)
      if (options.step) params.append('step', options.step)

      const response = await apiClient.get<PerformanceMetrics[]>(
        `/api/metrics/performance/history?${params}`
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch performance metrics history:', error)
      throw error
    }
  }

  /**
   * Query Prometheus metrics directly
   */
  async queryPrometheus(query: string): Promise<unknown> {
    try {
      const params = new URLSearchParams()
      params.append('query', query)

      const response = await apiClient.get<unknown>(
        `/api/metrics/prometheus?${params}`
      )

      return response.data
    } catch (error) {
      console.error('Failed to query Prometheus:', error)
      throw error
    }
  }

  /**
   * Get Grafana dashboard panels
   */
  async getGrafanaPanels(): Promise<GrafanaPanel[]> {
    try {
      const response = await apiClient.get<GrafanaPanel[]>(
        '/api/metrics/grafana/panels'
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch Grafana panels:', error)
      throw error
    }
  }

  /**
   * Get Grafana iframe URLs for embedding
   */
  async getGrafanaEmbedUrl(panelId: number, dashboardId?: number): Promise<string> {
    try {
      const params = new URLSearchParams()
      params.append('panelId', String(panelId))
      if (dashboardId) params.append('dashboardId', String(dashboardId))

      const response = await apiClient.get<{ url: string }>(
        `/api/metrics/grafana/embed?${params}`
      )

      return response.data.url
    } catch (error) {
      console.error('Failed to get Grafana embed URL:', error)
      throw error
    }
  }

  /**
   * Get metric aggregations
   */
  async getMetricAggregations(options: {
    metrics: string[]
    aggregation: 'avg' | 'sum' | 'min' | 'max' | 'rate'
    startTime: string
    endTime: string
  }): Promise<Record<string, number>> {
    try {
      const response = await apiClient.post<Record<string, number>>(
        '/api/metrics/aggregate',
        options
      )

      return response.data
    } catch (error) {
      console.error('Failed to get metric aggregations:', error)
      throw error
    }
  }

  /**
   * Get custom metrics by name
   */
  async getCustomMetric(name: string, options?: {
    startTime?: string
    endTime?: string
    step?: string
  }): Promise<Record<string, unknown>> {
    try {
      const params = new URLSearchParams()
      if (options?.startTime) params.append('startTime', options.startTime)
      if (options?.endTime) params.append('endTime', options.endTime)
      if (options?.step) params.append('step', options.step)

      const response = await apiClient.get<Record<string, unknown>>(
        `/api/metrics/custom/${name}?${params}`
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch custom metric:', error)
      throw error
    }
  }

  /**
   * Export metrics as CSV
   */
  async exportMetricsAsCSV(options: {
    metrics: string[]
    startTime: string
    endTime: string
  }): Promise<Blob> {
    try {
      const response = await apiClient.getInstance().post(
        '/api/metrics/export/csv',
        options,
        { responseType: 'blob' }
      )

      return response.data
    } catch (error) {
      console.error('Failed to export metrics:', error)
      throw error
    }
  }

  /**
   * Get alert thresholds
   */
  async getAlertThresholds(): Promise<Record<string, { warn: number; critical: number }>> {
    try {
      const response = await apiClient.get<
        Record<string, { warn: number; critical: number }>
      >('/api/metrics/thresholds')

      return response.data
    } catch (error) {
      console.error('Failed to fetch alert thresholds:', error)
      throw error
    }
  }

  /**
   * Get metrics health status
   */
  async getHealthStatus(): Promise<{
    prometheus: 'healthy' | 'degraded' | 'unavailable'
    grafana: 'healthy' | 'degraded' | 'unavailable'
    database: 'healthy' | 'degraded' | 'unavailable'
    lastUpdate: string
  }> {
    try {
      const response = await apiClient.get<{
        prometheus: 'healthy' | 'degraded' | 'unavailable'
        grafana: 'healthy' | 'degraded' | 'unavailable'
        database: 'healthy' | 'degraded' | 'unavailable'
        lastUpdate: string
      }>('/api/metrics/health')

      return response.data
    } catch (error) {
      console.error('Failed to fetch health status:', error)
      throw error
    }
  }
}

// Export singleton instance
export default new MetricsService()
