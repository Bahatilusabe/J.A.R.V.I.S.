import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import type { CEDState, CEDExplanation, CounterfactualSimulation } from '../../types/ced.types'

const initialState: CEDState = {
  activeExplanation: null,
  simulations: [],
  loading: false,
  error: null,
  selectedPredictionId: null,
}

const cedSlice = createSlice({
  name: 'ced',
  initialState,
  reducers: {
    // Set the active explanation
    setExplanation: (state, action: PayloadAction<CEDExplanation>) => {
      state.activeExplanation = action.payload
      state.error = null
    },

    // Add a simulation result
    addSimulation: (state, action: PayloadAction<CounterfactualSimulation>) => {
      state.simulations.push(action.payload)
    },

    // Clear all simulations
    clearSimulations: (state) => {
      state.simulations = []
    },

    // Remove a specific simulation
    removeSimulation: (state, action: PayloadAction<string>) => {
      state.simulations = state.simulations.filter((s: CounterfactualSimulation) => s.simulationId !== action.payload)
    },

    // Set loading state
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },

    // Set error state
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
      state.loading = false
    },

    // Set selected prediction ID
    setSelectedPredictionId: (state, action: PayloadAction<string | null>) => {
      state.selectedPredictionId = action.payload
    },

    // Clear active explanation
    clearExplanation: (state) => {
      state.activeExplanation = null
      state.simulations = []
      state.error = null
    },
  },
})

export const {
  setExplanation,
  addSimulation,
  clearSimulations,
  removeSimulation,
  setLoading,
  setError,
  setSelectedPredictionId,
  clearExplanation,
} = cedSlice.actions

export default cedSlice.reducer
