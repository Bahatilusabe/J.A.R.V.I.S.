import { useState, useEffect, useCallback, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import telemetryService from '../services/telemetry.service'
import { TelemetryEvent, TelemetryMetrics } from '../types/index'
import { RootState } from '../store/index'

interface UseTelemetryReturn {
  events: TelemetryEvent[]
  metrics: TelemetryMetrics | null
  isConnected: boolean
  isLoading: boolean
  error: string | null
  subscribe: () => void
  unsubscribe: () => void
  fetchMetrics: (startTime: string, endTime: string) => Promise<void>
  clearEvents: () => void
}

/**
 * Hook for real-time telemetry streaming
 * Provides WebSocket connection management and event subscription
 * Caches events in Redux store
 */
export function useTelemetry(): UseTelemetryReturn {
  const dispatch = useDispatch()
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const unsubscribeRef = useRef<(() => void) | null>(null)

  // Get telemetry state from Redux
  const telemetryState = useSelector((state: RootState) => state.telemetry)
  const events = telemetryState?.events || []
  const metrics = telemetryState?.metrics || null

  /**
   * Subscribe to telemetry events
   */
  const subscribe = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      // Connect WebSocket
      await telemetryService.connect()
      setIsConnected(true)

      // Subscribe to events
      unsubscribeRef.current = telemetryService.subscribe((event) => {
        // Dispatch new event to Redux store
        dispatch({
          type: 'telemetry/eventReceived',
          payload: event,
        })
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to connect to telemetry'
      setError(message)
      setIsConnected(false)
    } finally {
      setIsLoading(false)
    }
  }, [dispatch])

  /**
   * Unsubscribe from telemetry events
   */
  const unsubscribe = useCallback(() => {
    try {
      if (unsubscribeRef.current) {
        unsubscribeRef.current()
        unsubscribeRef.current = null
      }

      telemetryService.disconnect()
      setIsConnected(false)
      setError(null)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to disconnect'
      setError(message)
    }
  }, [])

  /**
   * Fetch historical metrics
   */
  const fetchMetrics = useCallback(
    async (startTime: string, endTime: string) => {
      try {
        setIsLoading(true)
        setError(null)

        const metricsData = await telemetryService.getMetrics({
          start: new Date(startTime).getTime(),
          end: new Date(endTime).getTime(),
        })

        // Dispatch metrics to Redux store
        dispatch({
          type: 'telemetry/metricsFetched',
          payload: metricsData,
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch metrics'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [dispatch]
  )

  /**
   * Clear events from state
   */
  const clearEvents = useCallback(() => {
    dispatch({
      type: 'telemetry/eventsCleared',
    })
  }, [dispatch])

  /**
   * Connect on mount, disconnect on unmount
   */
  useEffect(() => {
    subscribe()

    return () => {
      unsubscribe()
    }
  }, [subscribe, unsubscribe])

  return {
    events,
    metrics,
    isConnected,
    isLoading,
    error,
    subscribe,
    unsubscribe,
    fetchMetrics,
    clearEvents,
  }
}

export default useTelemetry
