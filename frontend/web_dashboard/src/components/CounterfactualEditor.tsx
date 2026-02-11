import { useState, useCallback } from 'react'
import { Plus, X, Zap } from 'lucide-react'
import type { CounterfactualIntervention, CounterfactualSimulation, MinimalIntervention } from '../types/ced.types'

export interface CounterfactualEditorProps {
  baselineProbability: number
  minimalInterventions: MinimalIntervention[]
  onSimulate: (interventions: CounterfactualIntervention[]) => Promise<CounterfactualSimulation>
  loading?: boolean
  className?: string
}

export function CounterfactualEditor({
  baselineProbability,
  minimalInterventions,
  onSimulate,
  loading = false,
  className = '',
}: CounterfactualEditorProps) {
  const [selectedInterventions, setSelectedInterventions] = useState<CounterfactualIntervention[]>([])
  const [lastSimulation, setLastSimulation] = useState<CounterfactualSimulation | null>(null)
  const [simulating, setSimulating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const toggleIntervention = useCallback((intervention: MinimalIntervention) => {
    setSelectedInterventions((prev) => {
      const existing = prev.findIndex((i) => i.target === intervention.target && i.type === intervention.type)
      if (existing >= 0) {
        return prev.filter((_, i) => i !== existing)
      }
      return [...prev, { type: intervention.type, target: intervention.target, enabled: true }]
    })
  }, [])

  const handleSimulate = async () => {
    setError(null)
    setSimulating(true)

    try {
      const simulation = await onSimulate(selectedInterventions)
      setLastSimulation(simulation)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Simulation failed')
    } finally {
      setSimulating(false)
    }
  }

  const probabilityDelta = lastSimulation ? lastSimulation.delta : 0
  const reducedProbability = lastSimulation ? lastSimulation.reducedProb : baselineProbability

  return (
    <div className={`flex flex-col gap-4 rounded-lg border border-slate-200 p-4 bg-white ${className}`}>
      {/* Header */}
      <div>
        <h3 className="font-semibold text-slate-900 mb-1">Counterfactual Simulator</h3>
        <p className="text-sm text-slate-600">Apply 'what-if' interventions to see predicted probability impact</p>
      </div>

      {/* Baseline metrics */}
      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-lg bg-slate-50 p-3 border border-slate-200">
          <div className="text-xs font-medium text-slate-600 mb-1">Baseline Probability</div>
          <div className="text-xl font-bold text-slate-900">{Math.round(baselineProbability * 100)}%</div>
        </div>

        <div className="rounded-lg bg-slate-50 p-3 border border-slate-200">
          <div className="text-xs font-medium text-slate-600 mb-1">Predicted Reduced</div>
          <div className="text-xl font-bold" style={{ color: reducedProbability <= 0.3 ? '#16a34a' : reducedProbability <= 0.5 ? '#f59e0b' : '#dc2626' }}>
            {Math.round(reducedProbability * 100)}%
          </div>
        </div>

        <div className="rounded-lg bg-slate-50 p-3 border border-slate-200">
          <div className="text-xs font-medium text-slate-600 mb-1">Probability Delta</div>
          <div className="text-xl font-bold" style={{ color: probabilityDelta < 0 ? '#16a34a' : '#6b7280' }}>
            {probabilityDelta < 0 ? '-' : '+'}{Math.round(Math.abs(probabilityDelta) * 100)}%
          </div>
        </div>
      </div>

      {/* Interventions selection */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="text-sm font-medium text-slate-700">Available Interventions</label>
          <span className="text-xs text-slate-500">{selectedInterventions.length} selected</span>
        </div>

        <div className="space-y-2 max-h-64 overflow-y-auto">
          {minimalInterventions.length === 0 ? (
            <div className="text-center py-6 text-slate-500 text-sm">
              No interventions available
            </div>
          ) : (
            minimalInterventions.map((intervention) => {
              const isSelected = selectedInterventions.some(
                (i) => i.target === intervention.target && i.type === intervention.type
              )

              return (
                <button
                  key={`${intervention.type}-${intervention.target}`}
                  onClick={() => toggleIntervention(intervention)}
                  className={`w-full flex items-center gap-3 p-3 rounded-lg border-2 transition-all text-left ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
                  }`}
                >
                  {/* Checkbox */}
                  <div
                    className={`w-5 h-5 rounded border-2 flex-shrink-0 flex items-center justify-center ${
                      isSelected
                        ? 'border-blue-500 bg-blue-500'
                        : 'border-slate-300'
                    }`}
                  >
                    {isSelected && <span className="text-white text-xs font-bold">✓</span>}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-slate-900 truncate">{intervention.target}</span>
                      <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 flex-shrink-0">
                        {intervention.type}
                      </span>
                    </div>
                    <p className="text-sm text-slate-600 line-clamp-2">{intervention.description}</p>
                    <div className="flex items-center gap-3 mt-2 text-xs">
                      <span className="text-slate-500">
                        Impact: <span className="font-semibold text-green-600">{Math.round(intervention.expectedImpact * 100)}%</span>
                      </span>
                      <span className="text-slate-500 capitalize">
                        Effort: <span className="font-semibold text-slate-700">{intervention.effort}</span>
                      </span>
                    </div>
                  </div>

                  {/* Icon */}
                  <div className="text-slate-400 flex-shrink-0">
                    {isSelected ? <X className="w-5 h-5" /> : <Plus className="w-5 h-5" />}
                  </div>
                </button>
              )
            })
          )}
        </div>
      </div>

      {/* Simulate button */}
      <button
        onClick={handleSimulate}
        disabled={selectedInterventions.length === 0 || simulating || loading}
        className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed bg-blue-600 hover:bg-blue-700 text-white"
      >
        <Zap className="w-4 h-4" />
        Simulate Impact
      </button>

      {/* Error message */}
      {error && (
        <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Simulation results */}
      {lastSimulation && (
        <div className="rounded-lg bg-green-50 border border-green-200 p-4">
          <h4 className="font-semibold text-green-900 mb-3">Simulation Results</h4>

          <div className="space-y-3">
            {/* Impact summary */}
            <div>
              <p className="text-sm text-green-800 mb-2">{lastSimulation.explanation}</p>
            </div>

            {/* Affected nodes */}
            {lastSimulation.affectedChain.length > 0 && (
              <div>
                <div className="text-xs font-medium text-green-700 mb-1">Affected Chain Nodes</div>
                <div className="flex flex-wrap gap-1">
                  {lastSimulation.affectedChain.map((nodeId) => (
                    <span
                      key={nodeId}
                      className="px-2 py-1 rounded text-xs bg-white border border-green-200 text-green-700 font-medium"
                    >
                      {nodeId}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Intervention list */}
            <div>
              <div className="text-xs font-medium text-green-700 mb-1">Applied Interventions</div>
              <ul className="space-y-1 text-xs text-green-800">
                {selectedInterventions.map((intervention) => (
                  <li key={`${intervention.type}-${intervention.target}`} className="flex items-center gap-2">
                    <span className="text-green-600">✓</span>
                    <span>
                      <span className="font-medium">{intervention.target}</span> ({intervention.type})
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Clear results button */}
          <button
            onClick={() => setLastSimulation(null)}
            className="w-full mt-3 py-2 px-3 text-xs font-medium rounded-lg border border-green-200 text-green-700 hover:bg-green-100 transition-colors"
          >
            Clear Results
          </button>
        </div>
      )}
    </div>
  )
}

export default CounterfactualEditor
