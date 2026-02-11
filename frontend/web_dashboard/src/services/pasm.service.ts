import { apiClient } from '../utils/api'
import { PasmDetailedPrediction, AttackPathDetails } from '../types/index'

const WS_URL = (import.meta as unknown as { env: Record<string, string> }).env.VITE_WS_URL || 'ws://127.0.0.1:5000'

export type PasmCallback = (prediction: PasmDetailedPrediction) => void

/**
 * PASM (Provably Attributable Security Model) Service
 * Handles MindSpore model inference via REST + WebSocket
 * Provides attack path analysis and vulnerability predictions
 */
class PasmService {
  private ws: WebSocket | null = null
  private subscribers: Map<string, Set<PasmCallback>> = new Map()
  private predictionCache: Map<string, PasmDetailedPrediction> = new Map()
  private isConnected = false

  /**
   * Connect to PASM WebSocket for continuous predictions
   */
  connectWebSocket(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${WS_URL.replace(/^http/, 'ws')}/ws/pasm`
        console.log('Connecting to PASM WebSocket:', wsUrl)

        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          console.log('PASM WebSocket connected')
          this.isConnected = true
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            const prediction = data as PasmDetailedPrediction

            // Cache prediction
            this.predictionCache.set(prediction.nodeId, prediction)

            // Notify subscribers for this asset
            const callbacks = this.subscribers.get(prediction.nodeId)
            if (callbacks) {
              callbacks.forEach((callback) => {
                try {
                  callback(prediction)
                } catch (error) {
                  console.error('Subscriber callback error:', error)
                }
              })
            }
          } catch (error) {
            console.error('Failed to parse PASM message:', error)
          }
        }

        this.ws.onerror = (error) => {
          console.error('PASM WebSocket error:', error)
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('PASM WebSocket closed')
          this.isConnected = false
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  /**
   * Disconnect from PASM WebSocket
   */
  disconnectWebSocket(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.isConnected = false
  }

  /**
   * Subscribe to predictions for a specific asset
   */
  subscribe(assetId: string, callback: PasmCallback): () => void {
    if (!this.subscribers.has(assetId)) {
      this.subscribers.set(assetId, new Set())
    }

    this.subscribers.get(assetId)!.add(callback)

    // Return unsubscribe function
    return () => {
      const callbacks = this.subscribers.get(assetId)
      if (callbacks) {
        callbacks.delete(callback)
        if (callbacks.size === 0) {
          this.subscribers.delete(assetId)
        }
      }
    }
  }

  /**
   * Query PASM predictions for a specific asset via REST
   */
  async queryPrediction(assetId: string): Promise<PasmDetailedPrediction> {
    try {
      const response = await apiClient.get<PasmDetailedPrediction>(
        `/api/pasm/predict/${assetId}`
      )

      const prediction = response.data

      // Cache the prediction
      this.predictionCache.set(assetId, prediction)

      return prediction
    } catch (error) {
      console.error('Failed to fetch PASM prediction:', error)
      throw error
    }
  }

  /**
   * Get attack path details between two assets
   */
  async getAttackPath(sourceId: string, targetId: string): Promise<AttackPathDetails> {
    try {
      const response = await apiClient.get<AttackPathDetails>(
        `/api/pasm/attack-path/${sourceId}/${targetId}`
      )

      return response.data
    } catch (error) {
      console.error('Failed to fetch attack path:', error)
      throw error
    }
  }

  /**
   * Get all asset predictions (attack graph)
   */
  async getAllPredictions(): Promise<PasmDetailedPrediction[]> {
    try {
      const response = await apiClient.get<PasmDetailedPrediction[]>(
        '/api/pasm/predictions'
      )

      // Cache all predictions
      response.data.forEach((pred) => {
        this.predictionCache.set(pred.nodeId, pred)
      })

      return response.data
    } catch (error) {
      console.error('Failed to fetch all predictions:', error)
      throw error
    }
  }

  /**
   * Get cached prediction
   */
  getCachedPrediction(assetId: string): PasmDetailedPrediction | undefined {
    return this.predictionCache.get(assetId)
  }

  /**
   * Clear prediction cache
   */
  clearCache(): void {
    this.predictionCache.clear()
  }

  /**
   * Get vulnerability recommendations for an asset
   */
  async getRecommendations(assetId: string): Promise<string[]> {
    try {
      const response = await apiClient.get<{ recommendations: string[] }>(
        `/api/pasm/recommendations/${assetId}`
      )

      return response.data.recommendations
    } catch (error) {
      console.error('Failed to fetch recommendations:', error)
      throw error
    }
  }

  /**
   * Submit feedback on prediction accuracy
   */
  async submitFeedback(
    predictionId: string,
    accurate: boolean,
    notes?: string
  ): Promise<void> {
    try {
      await apiClient.post(`/api/pasm/feedback`, {
        predictionId,
        accurate,
        notes,
        timestamp: new Date().toISOString(),
      })
    } catch (error) {
      console.error('Failed to submit feedback:', error)
      throw error
    }
  }

  /**
   * Check WebSocket connection status
   */
  isConnectedCheck(): boolean {
    return this.isConnected && this.ws?.readyState === WebSocket.OPEN
  }

  /**
   * Get number of active subscriptions
   */
  getSubscriptionCount(): number {
    return Array.from(this.subscribers.values()).reduce(
      (total, set) => total + set.size,
      0
    )
  }

  /**
   * Get cache size
   */
  getCacheSize(): number {
    return this.predictionCache.size
  }
}

// Export singleton instance
export default new PasmService()
