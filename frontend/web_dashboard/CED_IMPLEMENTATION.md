# CED (Causal Explainable Defense) Implementation Guide

## Overview

The CED module provides causal chain visualization, natural-language explanations, and counterfactual simulation capabilities for understanding and mitigating attack patterns in the J.A.R.V.I.S system.

## Architecture

### Components

#### 1. **CausalGraphComponent** (`src/components/CausalGraph.tsx`)
- **Purpose**: Visualize attack causal chains as directed acyclic graphs (DAGs)
- **Features**:
  - Interactive SVG-based visualization
  - Hierarchical layout algorithm (topological sort)
  - Zoom/pan/reset controls
  - Node selection with detail panel
  - Edge highlighting for interaction strength
  - Severity color-coding (critical→red, high→orange, medium→yellow, low→blue)

- **Props**:
  - `graph`: CausalGraph object with nodes and edges
  - `onNodeClick`: Callback when user clicks a node
  - `highlightedNodes`: Array of node IDs to highlight
  - `highlightedEdges`: Array of edges to highlight
  - `className`: Additional CSS classes

#### 2. **CounterfactualEditor** (`src/components/CounterfactualEditor.tsx`)
- **Purpose**: "What-if" simulator for testing defensive interventions
- **Features**:
  - Baseline vs. predicted probability comparison
  - Intervention selection with impact metrics
  - Simulation execution with backend API
  - Results display with affected chain nodes
  - Intervention type badges (patch, detection, isolation, config, monitoring)

- **Props**:
  - `baselineProbability`: Current attack probability (0-1)
  - `minimalInterventions`: Available defensive actions
  - `onSimulate`: Callback to execute simulation
  - `loading`: Loading state during simulation
  - `className`: Additional CSS classes

#### 3. **ExplanationPanel** (`src/components/ExplanationPanel.tsx`)
- **Purpose**: Display natural-language causal explanations
- **Features**:
  - Collapsible sections (summary, why chain exists, impact assessment)
  - Key contributing factors list
  - Recommended minimal interventions
  - Confidence score display
  - Expandable/collapsible sections

- **Props**:
  - `explanation`: CEDExplanation object
  - `loading`: Loading state
  - `className`: Additional CSS classes

#### 4. **ExplanationTimeline** (`src/components/ExplanationTimeline.tsx`)
- **Purpose**: Show attack chain as sequential timeline
- **Features**:
  - Vertical timeline with phase-coded dots
  - Severity badges with icons
  - Expandable event details
  - Probability bars (color-coded by risk)
  - Indicators of Compromise display
  - Recommended mitigations

### Hooks

#### **useCED** (`src/hooks/useCED.ts`)
- **Purpose**: Custom hook for CED API integration
- **Functions**:
  - `fetchExplanation(predictionId)`: Fetch causal explanation from backend
  - `simulateCounterfactual(interventions)`: Run counterfactual simulation
- **Returns**:
  - `explanation`: Current CEDExplanation
  - `simulations`: Array of past simulations
  - `loading`: Loading state
  - `error`: Error message if any

**Example Usage**:
```typescript
const { explanation, simulateCounterfactual, loading } = useCED(predictionId)

const handleSimulate = async (interventions) => {
  const result = await simulateCounterfactual(interventions)
  // Use result
}
```

### Redux State

#### **cedSlice** (`src/store/slices/cedSlice.ts`)
- **State Shape**:
  ```typescript
  {
    ced: {
      activeExplanation: CEDExplanation | null
      simulations: CounterfactualSimulation[]
      loading: boolean
      error: string | null
      selectedPredictionId: string | null
    }
  }
  ```

- **Actions**:
  - `setExplanation(explanation)`: Store fetched explanation
  - `addSimulation(simulation)`: Add simulation result
  - `clearSimulations()`: Clear all simulations
  - `removeSimulation(simulationId)`: Remove specific simulation
  - `setLoading(loading)`: Set loading state
  - `setError(error)`: Set error message
  - `setSelectedPredictionId(id)`: Set active prediction
  - `clearExplanation()`: Clear all CED data

## API Integration

### Endpoints

#### `GET /ced/explain?prediction_id={id}`
**Backend**: `backend/core/ced/causal_engine.py` & `explanation_builder.py`

**Response**:
```json
{
  "predictionId": "pred-123",
  "baselineProbability": 0.72,
  "causalGraph": {
    "nodes": [
      {
        "id": "node-1",
        "label": "Unpatched Server",
        "type": "source",
        "severity": "critical",
        "probability": 0.95,
        "description": "Unpatched vulnerability on web server",
        "indicators": ["CVE-2024-1234", "exploit attempt in logs"]
      }
    ],
    "edges": [
      {
        "source": "node-1",
        "target": "node-2",
        "label": "causal",
        "strength": 0.85,
        "type": "causal"
      }
    ]
  },
  "naturalLanguage": {
    "summary": "Attack likely due to unpatched vulnerability...",
    "whyChainExists": "Server lacks security patches for known CVEs...",
    "impactAssessment": "If exploited, attacker gains code execution...",
    "keyFactors": ["Unpatched software", "Network exposure", "Weak credentials"]
  },
  "minimalInterventions": [
    {
      "type": "patch",
      "target": "Web-Server-01",
      "description": "Apply security patches for CVE-2024-1234",
      "expectedImpact": 0.51,
      "effort": "low"
    }
  ],
  "confidence": 0.92
}
```

#### `POST /ced/simulate`
**Backend**: `backend/core/ced/causal_engine.py` or `backend/api/policy.py`

**Request**:
```json
{
  "prediction_id": "pred-123",
  "interventions": [
    {
      "type": "patch",
      "target": "Firewall-1"
    },
    {
      "type": "detection",
      "target": "IDS-Network"
    }
  ]
}
```

**Response**:
```json
{
  "simulation_id": "sim-456",
  "reduced_probability": 0.21,
  "delta": -0.51,
  "explanation": "Applying Firewall-1 patch blocks exploit chain at step 2. Adding IDS detection enables early response.",
  "affected_nodes": ["node-2", "node-3"],
  "baseline_probability": 0.72
}
```

## Type Definitions

### Core Types (`src/types/ced.types.ts`)

```typescript
interface CausalNode {
  id: string
  label: string
  type: 'source' | 'intermediate' | 'target' | 'defense' | 'asset'
  phase?: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  probability: number
  description: string
  indicators?: string[]
}

interface CausalEdge {
  source: string
  target: string
  label: string
  strength: number
  type: 'causal' | 'enabling' | 'mitigating'
  explanation?: string
}

interface CEDExplanation {
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

interface CounterfactualSimulation {
  simulationId: string
  predictionId: string
  interventions: CounterfactualIntervention[]
  baselineProb: number
  reducedProb: number
  delta: number
  explanation: string
  affectedChain: string[]
  timestamp: string
}
```

## Page Layout (`src/pages/CED.tsx`)

### Structure
```
┌─────────────────────────────────────────────────┐
│  CED Header + Refresh Button                    │
├─────────────────────────────────────────────────┤
│  Prediction Selection Cards (Search + Filter)   │
├─────────────────────────────────────────────────┤
│  ┌────────────────────────────┬─────────────────┤
│  │  Causal Graph (SVG)        │ Explanation     │
│  │  - Interactive Nodes       │ Panel           │
│  │  - Zoom/Pan Controls       │ - Summary       │
│  │  - Node Details            │ - Why Chain     │
│  │                            │ - Impact        │
│  │                            │ - Interventions │
│  └────────────────────────────┴─────────────────┘
├─────────────────────────────────────────────────┤
│  ┌────────────────┬──────────────────────────────┤
│  │ Counterfactual │  Attack Timeline             │
│  │ Editor         │  - Phase-coded Timeline      │
│  │ - Intervention │  - Expandable Events         │
│  │   Selection    │  - IoCs & Mitigations        │
│  │ - Simulate Btn │                              │
│  │ - Results      │                              │
│  └────────────────┴──────────────────────────────┘
├─────────────────────────────────────────────────┤
│  Simulation History (if any)                    │
└─────────────────────────────────────────────────┘
```

## Usage Flow

### 1. Select Prediction
```typescript
// User selects from prediction cards or search
setSelectedPredictionId('pred-123')
```

### 2. Fetch Explanation
```typescript
// useCED hook auto-fetches on predictionId change
const { explanation, simulateCounterfactual } = useCED(selectedPredictionId)
```

### 3. View Causal Chain
```typescript
// CausalGraphComponent renders the DAG
<CausalGraphComponent graph={explanation.causalGraph} />
```

### 4. Simulate Interventions
```typescript
// User selects interventions in CounterfactualEditor
// onClick "Simulate Impact" button
const simulation = await simulateCounterfactual([
  { type: 'patch', target: 'Firewall-1', enabled: true }
])
// Results update automatically
```

## Backend Integration Checklist

- [ ] Implement `GET /ced/explain?prediction_id={id}` endpoint
  - Call `backend/core/ced/causal_engine.py` for graph generation
  - Call `backend/core/ced/explanation_builder.py` for NL generation
  - Return complete CEDExplanation object

- [ ] Implement `POST /ced/simulate` endpoint
  - Accept CounterfactualRequest payload
  - Run counterfactual analysis in `causal_engine.py`
  - Calculate delta and affected nodes
  - Return CounterfactualResponse

- [ ] Ensure proper authentication
  - Add Authorization header requirement
  - Validate user permissions for prediction access

- [ ] Add error handling
  - 400: Invalid prediction_id
  - 401: Unauthorized
  - 500: Backend computation error

## Testing

### Unit Tests
```typescript
// Test CausalGraphComponent rendering
test('renders nodes with severity colors', () => {
  const graph = { nodes: [...], edges: [...] }
  render(<CausalGraphComponent graph={graph} />)
  // assertions
})

// Test CounterfactualEditor
test('calculates delta correctly', () => {
  // simulation with baseline 0.72, reduced 0.21, delta -0.51
})
```

### Integration Tests
```typescript
// Test full CED flow
test('CED page fetches and displays explanation', async () => {
  // Select prediction → fetch explanation → render components
})
```

## Performance Optimizations

1. **Memoization**: Use `useMemo` for expensive calculations (graph layout, timeline conversion)
2. **Lazy Loading**: Load causal graph only when prediction is selected
3. **Caching**: Store explanations in Redux to avoid re-fetching
4. **Pagination**: Limit simulation history display to last 10 items
5. **Debouncing**: Debounce search queries (300ms)

## Future Enhancements

1. **Real-time WebSocket Updates**: Stream causal graph changes
2. **Advanced Filtering**: Filter by severity, intervention type, confidence
3. **Export Functionality**: Export causal graphs as PNG/PDF, explanations as reports
4. **Comparison Mode**: Compare multiple predictions side-by-side
5. **Recommendation Engine**: Auto-suggest optimal intervention combinations
6. **Learning Loop**: Feedback on simulation accuracy over time
