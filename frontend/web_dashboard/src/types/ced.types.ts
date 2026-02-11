/**
 * CED (Causal Explainable Defense) Type Definitions
 * Interfaces for causal graph visualization, explanations, and counterfactual simulations
 */

export interface CausalNode {
  id: string
  label: string
  type: 'source' | 'intermediate' | 'target' | 'defense' | 'asset'
  phase?: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  probability: number
  description: string
  indicators?: string[]
}

export interface CausalEdge {
  source: string
  target: string
  label: string
  strength: number // 0-1, correlation/causality strength
  type: 'causal' | 'enabling' | 'mitigating'
  explanation?: string
}

export interface CausalGraph {
  nodes: CausalNode[]
  edges: CausalEdge[]
  rootCause: string
  targetEvent: string
  chainLength: number
  overallRisk: number
}

export interface MinimalIntervention {
  type: 'patch' | 'detection' | 'isolation' | 'config' | 'monitoring'
  target: string
  description: string
  expectedImpact: number // 0-1, probability reduction
  effort: 'low' | 'medium' | 'high'
}

export interface CEDExplanation {
  predictionId: string
  baselineProbability: number
  causalGraph: CausalGraph
  naturalLanguage: {
    summary: string
    whyChainExists: string
    impactAssessment: string
    keyFactors: string[]
  }
  minimalInterventions: MinimalIntervention[]
  confidence: number
  generatedAt: string
}

export interface CounterfactualIntervention {
  type: 'patch' | 'detection' | 'isolation' | 'config' | 'monitoring'
  target: string
  enabled: boolean
}

export interface CounterfactualSimulation {
  simulationId: string
  predictionId: string
  interventions: CounterfactualIntervention[]
  baselineProb: number
  reducedProb: number
  delta: number // probability change (negative = reduced risk)
  explanation: string
  affectedChain: string[] // nodes affected by interventions
  timestamp: string
}

export interface CounterfactualRequest {
  prediction_id: string
  interventions: Array<{
    type: string
    target: string
  }>
}

export interface CounterfactualResponse {
  simulation_id: string
  reduced_probability: number
  delta: number
  explanation: string
  affected_nodes: string[]
  baseline_probability: number
}

export interface CEDState {
  activeExplanation: CEDExplanation | null
  simulations: CounterfactualSimulation[]
  loading: boolean
  error: string | null
  selectedPredictionId: string | null
}
