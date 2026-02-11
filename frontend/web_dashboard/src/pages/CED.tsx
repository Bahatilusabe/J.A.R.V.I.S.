import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Filter, RefreshCw } from 'lucide-react'
import CausalGraphComponent from '../components/CausalGraph'
import CounterfactualEditor from '../components/CounterfactualEditor'
import ExplanationPanel from '../components/ExplanationPanel'
import { ExplanationTimeline } from '../components/ExplanationTimeline'
import { useCED } from '../hooks/useCED'
import type { CounterfactualIntervention, CounterfactualSimulation, CausalNode } from '../types/ced.types'

// Mock prediction data
const MOCK_PREDICTIONS = [
  { id: 'pred-001', name: 'Lateral Movement Attack', probability: 0.78 },
  { id: 'pred-002', name: 'Privilege Escalation', probability: 0.65 },
  { id: 'pred-003', name: 'Data Exfiltration', probability: 0.45 },
]

export function CED() {
  const [selectedPredictionId, setSelectedPredictionId] = useState<string>('pred-001')
  const [searchQuery, setSearchQuery] = useState('')

  const { explanation, simulations, loading, error, simulateCounterfactual } = useCED(selectedPredictionId)

  // Filter predictions based on search
  const filteredPredictions = useMemo(() => {
    return MOCK_PREDICTIONS.filter((p) => p.name.toLowerCase().includes(searchQuery.toLowerCase()))
  }, [searchQuery])

  const navigate = useNavigate()

  const handleSimulate = async (interventions: CounterfactualIntervention[]): Promise<CounterfactualSimulation> => {
    return simulateCounterfactual(interventions)
  }

  // Convert explanation to timeline events for ExplanationTimeline component
  const timelineEvents = useMemo(() => {
    if (!explanation?.causalGraph) return []

    return explanation.causalGraph.nodes.map((node: CausalNode, idx: number) => ({
      id: node.id,
      timestamp: new Date(Date.now() - (explanation.causalGraph.nodes.length - idx) * 60000).toISOString(),
      step: idx + 1,
      phase: 'reconnaissance' as const,
      severity: node.severity,
      description: node.description,
      probability: node.probability,
      indicators: node.indicators || [],
      mitigations: node.indicators ? node.indicators.slice(0, 2) : [],
    }))
  }, [explanation])

  return (
    <div className="flex flex-col h-full gap-6 p-6 bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Causal Explainable Defense (CED)</h1>
          <p className="text-slate-600 mt-1">Visualize attack chains and simulate defensive interventions</p>
        </div>
        <button
          onClick={() => {
            // SPA-safe refresh: navigate to the current path to trigger router navigation without a full reload.
            try {
              navigate(window.location.pathname + window.location.search + window.location.hash)
            } catch (err) {
              // If SPA navigation fails, log and do not perform a full page reload.
              // The SPA should handle refreshes; forcing a reload would lose app state.
              // eslint-disable-next-line no-console
              console.warn('SPA navigate failed — refresh aborted to avoid full reload', err)
            }
          }}
          className="p-3 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 transition-colors text-slate-600"
          title="Refresh"
        >
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>

      {/* Prediction selector */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Search and filter */}
        <div className="lg:col-span-4 flex items-center gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-3 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search predictions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button className="p-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 transition-colors text-slate-600" title="Filter">
            <Filter className="w-5 h-5" />
          </button>
        </div>

        {/* Prediction cards */}
        {filteredPredictions.map((pred) => (
          <button
            key={pred.id}
            onClick={() => setSelectedPredictionId(pred.id)}
            className={`p-4 rounded-lg border-2 transition-all text-left ${selectedPredictionId === pred.id
              ? 'border-blue-500 bg-blue-50'
              : 'border-slate-200 bg-white hover:border-slate-300'
              }`}
          >
            <div className="text-sm font-medium text-slate-900 mb-2">{pred.name}</div>
            <div className="text-2xl font-bold text-slate-900">{Math.round(pred.probability * 100)}%</div>
            <div className="text-xs text-slate-500 mt-1">Risk Probability</div>
          </button>
        ))}
      </div>

      {/* Error display */}
      {error && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1">
        {/* Left: Causal Graph */}
        <div className="lg:col-span-2 flex flex-col">
          {explanation?.causalGraph ? (
            <CausalGraphComponent
              graph={explanation.causalGraph}
              className="flex-1 min-h-[500px]"
              highlightedNodes={[]}
              highlightedEdges={[]}
            />
          ) : (
            <div className="flex items-center justify-center h-96 rounded-lg border border-slate-200 bg-slate-50 text-slate-500">
              {loading ? 'Loading causal graph...' : 'Select a prediction to view causal chain'}
            </div>
          )}
        </div>

        {/* Right: Explanation Panel */}
        <div className="flex flex-col">
          <ExplanationPanel explanation={explanation || null} loading={loading} className="flex-1" />
        </div>
      </div>

      {/* Bottom: Counterfactual Editor and Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Counterfactual Simulator */}
        <CounterfactualEditor
          baselineProbability={explanation?.baselineProbability || 0}
          minimalInterventions={explanation?.minimalInterventions || []}
          onSimulate={handleSimulate}
          loading={loading}
          className="flex-1"
        />

        {/* Timeline of attack chain */}
        <div className="rounded-lg border border-slate-200 p-4 bg-white">
          <h3 className="font-semibold text-slate-900 mb-4">Attack Timeline</h3>
          {timelineEvents.length > 0 ? (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              <ExplanationTimeline events={timelineEvents} />
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500 text-sm">
              No timeline data available
            </div>
          )}
        </div>
      </div>

      {/* Simulations history */}
      {simulations.length > 0 && (
        <div className="rounded-lg border border-slate-200 p-4 bg-white">
          <h3 className="font-semibold text-slate-900 mb-4">Simulation History</h3>
          <div className="flex flex-wrap gap-1">
            {simulations.map((sim: CounterfactualSimulation) => (
              <div key={sim.simulationId} className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                <div className="flex items-center justify-between mb-1">
                  <div className="font-medium text-slate-900">
                    {sim.interventions.length} intervention{sim.interventions.length !== 1 ? 's' : ''}
                  </div>
                  <div className="text-sm font-bold">
                    <span style={{ color: sim.delta < 0 ? '#16a34a' : '#dc2626' }}>
                      {sim.delta < 0 ? '-' : '+'}{Math.round(Math.abs(sim.delta) * 100)}%
                    </span>
                  </div>
                </div>
                <p className="text-sm text-slate-600">{sim.explanation}</p>
                <div className="text-xs text-slate-500 mt-2">
                  {new Date(sim.timestamp).toLocaleTimeString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default CED
