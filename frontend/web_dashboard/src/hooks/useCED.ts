import { useEffect, useState, useCallback } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import type { RootState } from '../store'
import type { CounterfactualIntervention, CounterfactualResponse, CEDExplanation, CounterfactualSimulation } from '../types/ced.types'

// Mock API base URL - will be replaced with actual backend URL
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000'

/**
 * useCED Hook
 * 
 * Handles CED API interactions including:
 * - Fetching causal explanations for predictions
 * - Simulating counterfactual interventions
 * - Managing CED state with Redux
 * - Error handling and data caching
 */
export function useCED(predictionId?: string) {
  const dispatch = useDispatch()
  const cedState = useSelector((state: RootState) => state.ced || { activeExplanation: null, simulations: [], loading: false, error: null })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [explanation, setExplanation] = useState<CEDExplanation | null>(null)

  // Fetch causal explanation for a prediction
  const fetchExplanation = useCallback(
    async (id: string) => {
      if (!id) return

      setLoading(true)
      setError(null)

      try {
        const response = await fetch(`${API_BASE}/ced/explain?prediction_id=${id}`)
        if (!response.ok) {
          throw new Error(`Failed to fetch explanation: ${response.statusText}`)
        }

        const data: CEDExplanation = await response.json()
        setExplanation(data)
        dispatch({ type: 'CED_SET_EXPLANATION', payload: data })
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Unknown error'
        setError(errorMsg)
        dispatch({ type: 'CED_SET_ERROR', payload: errorMsg })
      } finally {
        setLoading(false)
      }
    },
    [dispatch]
  )

  // Simulate counterfactual interventions
  const simulateCounterfactual = useCallback(
    async (interventions: CounterfactualIntervention[]): Promise<CounterfactualSimulation> => {
      if (!predictionId || !explanation) {
        throw new Error('No prediction or explanation selected')
      }

      setLoading(true)
      setError(null)

      try {
        const payload = {
          prediction_id: predictionId,
          interventions: interventions.map((i) => ({
            type: i.type,
            target: i.target,
          })),
        }

        const response = await fetch(`${API_BASE}/ced/simulate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })

        if (!response.ok) {
          throw new Error(`Simulation failed: ${response.statusText}`)
        }

        const data: CounterfactualResponse = await response.json()

        const simulation: CounterfactualSimulation = {
          simulationId: data.simulation_id,
          predictionId,
          interventions,
          baselineProb: data.baseline_probability,
          reducedProb: data.reduced_probability,
          delta: data.delta,
          explanation: data.explanation,
          affectedChain: data.affected_nodes,
          timestamp: new Date().toISOString(),
        }

        dispatch({ type: 'CED_ADD_SIMULATION', payload: simulation })

        return simulation
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Simulation failed'
        setError(errorMsg)
        throw err
      } finally {
        setLoading(false)
      }
    },
    [predictionId, explanation, dispatch]
  )

  // Auto-fetch explanation when predictionId changes
  useEffect(() => {
    if (predictionId) {
      fetchExplanation(predictionId)
    }
  }, [predictionId, fetchExplanation])

  return {
    explanation: explanation || cedState.activeExplanation,
    simulations: cedState.simulations || [],
    loading: loading || cedState.loading,
    error: error || cedState.error,
    fetchExplanation,
    simulateCounterfactual,
  }
}

export default useCED
