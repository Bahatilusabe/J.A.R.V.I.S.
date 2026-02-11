import { useState, useEffect, useCallback, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import pasmService from '../services/pasm.service'
import { PasmDetailedPrediction, AttackPathDetails } from '../types/index'
import { RootState } from '../store/index'

interface UsePasmReturn {
  predictions: PasmDetailedPrediction[]
  selectedAssetId: string | null
  selectedPrediction: PasmDetailedPrediction | null
  attackPath: AttackPathDetails | null
  recommendations: string[]
  isConnected: boolean
  isLoading: boolean
  error: string | null
  connectWebSocket: () => Promise<void>
  disconnectWebSocket: () => void
  queryPrediction: (assetId: string) => Promise<void>
  selectAsset: (assetId: string) => void
  getAttackPath: (sourceId: string, targetId: string) => Promise<void>
  getRecommendations: (assetId: string) => Promise<void>
  submitFeedback: (predictionId: string, accurate: boolean, notes?: string) => Promise<void>
  clearError: () => void
}

/**
 * Hook for PASM model inference
 * Manages attack predictions, caching, and visualization data
 * Provides WebSocket subscription for continuous predictions
 */
export function usePasm(): UsePasmReturn {
  const dispatch = useDispatch()
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const unsubscribeRef = useRef<((id: string) => void) | null>(null)

  // Get PASM state from Redux
  const pasmState = useSelector((state: RootState) => state.pasm)
  const predictionsFromStore = pasmState?.predictions || []
  // Local fallback cache for predictions when the pasm Redux slice isn't mounted
  const [localPredictions, setLocalPredictions] = useState<PasmDetailedPrediction[]>([])
  const predictions = predictionsFromStore.length > 0 ? predictionsFromStore : localPredictions
  const selectedAssetId = pasmState?.selectedAssetId || null
  const selectedPrediction = pasmState?.selectedPrediction || null
  const attackPath = pasmState?.attackPath || null
  const recommendations = pasmState?.recommendations || []

  /**
   * Connect to PASM WebSocket for continuous predictions
   */
  const connectWebSocket = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      await pasmService.connectWebSocket()
      // Populate initial predictions after establishing WS (fallback when Redux slice is absent)
      try {
        const all = await pasmService.getAllPredictions()
        setLocalPredictions(all)
      } catch (err) {
        // ignore - server may not expose REST in demo/local setups
      }
      setIsConnected(true)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to connect to PASM'
      setError(message)
      setIsConnected(false)
    } finally {
      setIsLoading(false)
    }
  }, [])

  /**
   * Disconnect from PASM WebSocket
   */
  const disconnectWebSocket = useCallback(() => {
    try {
      if (unsubscribeRef.current && selectedAssetId) {
        unsubscribeRef.current(selectedAssetId)
        unsubscribeRef.current = null
      }

      pasmService.disconnectWebSocket()
      setIsConnected(false)
      setError(null)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to disconnect'
      setError(message)
    }
  }, [selectedAssetId])

  /**
   * Query PASM prediction for specific asset
   */
  const queryPrediction = useCallback(
    async (assetId: string) => {
      try {
        setIsLoading(true)
        setError(null)

        const prediction = await pasmService.queryPrediction(assetId)

        // Dispatch to Redux store
        dispatch({
          type: 'pasm/predictionFetched',
          payload: { prediction, assetId },
        })
        // Update local cache as fallback
        setLocalPredictions((prev) => {
          const exists = prev.find((p) => p.nodeId === prediction.nodeId || p.id === prediction.id)
          if (exists) {
            return prev.map((p) => (p.nodeId === prediction.nodeId || p.id === prediction.id ? prediction : p))
          }
          return [prediction, ...prev]
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch prediction'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [dispatch]
  )

  /**
   * Select asset for detailed view
   */
  const selectAsset = useCallback(
    (assetId: string) => {
      try {
        // Get cached prediction if available
        const cached = pasmService.getCachedPrediction(assetId)

        dispatch({
          type: 'pasm/assetSelected',
          payload: { assetId, prediction: cached },
        })

        // If not cached, fetch it
        if (!cached) {
          queryPrediction(assetId).catch((err) => {
            console.error('Failed to fetch prediction for selected asset:', err)
          })
        }

        // Subscribe to continuous updates for this asset
        if (unsubscribeRef.current && selectedAssetId && selectedAssetId !== assetId) {
          unsubscribeRef.current(selectedAssetId)
        }

        unsubscribeRef.current = pasmService.subscribe(assetId, (prediction) => {
          dispatch({
            type: 'pasm/predictionUpdated',
            payload: { prediction, assetId },
          })
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to select asset'
        setError(message)
      }
    },
    [dispatch, selectedAssetId, queryPrediction]
  )

  /**
   * Get attack path between two assets
   */
  const getAttackPath = useCallback(
    async (sourceId: string, targetId: string) => {
      try {
        setIsLoading(true)
        setError(null)

        const path = await pasmService.getAttackPath(sourceId, targetId)

        // Dispatch to Redux store
        dispatch({
          type: 'pasm/attackPathFetched',
          payload: path,
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch attack path'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [dispatch]
  )

  /**
   * Get vulnerability recommendations for asset
   */
  const getRecommendations = useCallback(
    async (assetId: string) => {
      try {
        setIsLoading(true)
        setError(null)

        const recs = await pasmService.getRecommendations(assetId)

        // Dispatch to Redux store
        dispatch({
          type: 'pasm/recommendationsFetched',
          payload: recs,
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch recommendations'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [dispatch]
  )

  /**
   * Submit prediction accuracy feedback
   */
  const submitFeedback = useCallback(
    async (predictionId: string, accurate: boolean, notes?: string) => {
      try {
        setIsLoading(true)
        setError(null)

        await pasmService.submitFeedback(predictionId, accurate, notes)

        // Dispatch feedback submitted to Redux
        dispatch({
          type: 'pasm/feedbackSubmitted',
          payload: { predictionId, accurate },
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to submit feedback'
        setError(message)
        throw err
      } finally {
        setIsLoading(false)
      }
    },
    [dispatch]
  )

  /**
   * Clear error message
   */
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      disconnectWebSocket()
    }
  }, [disconnectWebSocket])

  return {
    predictions,
    selectedAssetId,
    selectedPrediction,
    attackPath,
    recommendations,
    isConnected,
    isLoading,
    error,
    connectWebSocket,
    disconnectWebSocket,
    queryPrediction,
    selectAsset,
    getAttackPath,
    getRecommendations,
    submitFeedback,
    clearError,
  }
}

export default usePasm
