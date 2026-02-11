# PASM & CED Pages Implementation Plan

**Status:** Ready for Implementation  
**Complexity:** Advanced (Graph Visualization + Real-time WebSocket)  
**Total Lines:** ~1,800 lines  

---

## Overview

This document outlines the implementation of two advanced visualization pages for J.A.R.V.I.S.:

1. **PASM Page** (Predictive Attack Surface Modeling)
   - Temporal graph viewer with attack chains
   - Asset detail panel with vulnerabilities
   - Real-time predictions and uncertainty scoring
   - ~1,000 lines (page + 4 new components)

2. **CED Page** (Causal Explainable Defense)
   - Causal chain visualization
   - Counterfactual simulator UI
   - Explanation timeline with interventions
   - ~800 lines (page + 3 new components)

---

## PART 1: PASM Page Architecture

### Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│ PASM (Predictive Attack Surface Modeling)                   │
├─────────────────────────────────────────────────────────────┤
│ Controls:  [← Model Select ▼] [Time ▓████░] [Filters: X]   │
├──────────────────────────────────────────────┬───────────────┤
│                                              │  Asset Detail │
│  Graph Viewer                                │  ┌───────────┐│
│  ┌──────────────────────────────────────┐   │  │ Node: DB01││
│  │                                      │   │  │ Risk: 0.72││
│  │  Web-01───(CVE-X)──→App-02          │   │  │ Vulns: 3  ││
│  │    │         ↓         │             │   │  │           ││
│  │    │       DB-01       │             │   │  │ Details... ││
│  │    └────────────────────┘             │   │  └───────────┘│
│  │                                      │   │               │
│  │  [Paths: 5] [Avg Risk: 0.64]        │   │  [Top-K: ▼]  │
│  └──────────────────────────────────────┘   │               │
├──────────────────────────────────────────────┴───────────────┤
│ Recent Events:  [4-12-2025 10:00] Critical: SQL-Inject (0.89)│
└─────────────────────────────────────────────────────────────┘
```

### Component Structure

```
src/pages/PASM.tsx (450+ lines)
├─ PASMGraphViewer.tsx (280+ lines)
│  ├─ React-Force-Graph or Cytoscape for 3D graph
│  ├─ Node/Edge rendering with risk colors
│  └─ Interactive selection + highlighting
│
├─ TimeSlider.tsx (100+ lines)
│  ├─ Timeline with date range
│  ├─ Playback controls
│  └─ Animation state tracking
│
├─ NodeDetailPanel.tsx (150+ lines)
│  ├─ Asset info (hostname, type, criticality)
│  ├─ Vulnerability list (CVE, CVSS, patch status)
│  ├─ Risk timeline (graph)
│  └─ Related attacks
│
└─ ConfidenceHalo.tsx (80+ lines)
   ├─ Visual indicator for uncertainty
   ├─ Concentric rings by confidence level
   └─ Color mapping (green > yellow > red)
```

### Data Flow

```
Backend Endpoints:
  GET /pasm/models
  GET /pasm/graph?range=...
  GET /pasm/predict?asset={id}
  GET /pasm/confidence?prediction_id={id}
  WS /ws/pasm?asset={id}
    ↓
usePasm Hook (1)
  - Fetches graph data
  - Subscribes to predictions
  - Manages cache
    ↓
PASMGraphViewer
  - Renders nodes/edges
  - Highlights paths
    ↓
NodeDetailPanel
  - Shows selected node details
  - Lists vulnerabilities
```

### Component Specifications

#### PASMGraphViewer.tsx

**Props:**
```typescript
interface PASMGraphViewerProps {
  nodes: GraphNode[]
  edges: GraphEdge[]
  selectedNodeId?: string
  onNodeSelect: (id: string) => void
  highlightPath?: string[]
  threatLevel: 'low' | 'medium' | 'high' | 'critical'
  isLoading?: boolean
  className?: string
}

interface GraphNode {
  id: string
  type: 'web' | 'app' | 'db' | 'firewall' | 'vpn'
  risk: number           // 0-1
  confidence: number     // 0-1
  vulnerabilityCount: number
  isCompromised?: boolean
  metadata?: Record<string, any>
}

interface GraphEdge {
  source: string
  target: string
  vuln?: string          // CVE-XXXX
  weight: number         // 0-1 (attack likelihood)
  exploitType?: string   // 'lateral_movement' | 'privilege_escalation'
}
```

**Features:**
- Force-directed graph layout (React-Force-Graph)
- Node coloring by risk (green < yellow < orange < red)
- Edge thickness by weight
- Click to select + highlight connected nodes
- Hover tooltips showing CVE/risk details
- Zoom/pan controls
- Full-screen toggle
- Export graph as SVG/PNG

#### TimeSlider.tsx

**Props:**
```typescript
interface TimeSliderProps {
  startTime: Date
  endTime: Date
  currentTime: Date
  onTimeChange: (time: Date) => void
  isAnimating?: boolean
  onAnimationToggle?: () => void
  step?: number  // milliseconds
  className?: string
}
```

**Features:**
- Draggable timeline slider
- Date/time display
- Play/pause animation controls
- Speed adjustment (0.5x, 1x, 2x)
- Mark important events on timeline
- Keyboard shortcuts (space to play, arrows to seek)

#### NodeDetailPanel.tsx

**Props:**
```typescript
interface NodeDetailPanelProps {
  node: GraphNode & {
    hostname: string
    criticality: 'critical' | 'high' | 'medium' | 'low'
    owner: string
    lastScanned: string
    vulnerabilities: Vulnerability[]
    relatedIncidents: Incident[]
  }
  predictions?: Prediction[]
  onClose: () => void
  className?: string
}

interface Vulnerability {
  cveId: string
  cvss: number
  patchAvailable: boolean
  exploitProbability: number
}

interface Incident {
  timestamp: string
  type: 'lateral_movement' | 'reconnaissance' | 'exploitation'
  severity: 'critical' | 'high' | 'medium' | 'low'
}
```

**Features:**
- Tabbed interface: Overview | Vulnerabilities | Incidents | Timeline
- Risk gauge (0-100 scale, color-coded)
- Vulnerability list with CVSS scores
- Patch availability indicators
- Related incident timeline
- Copy hostname to clipboard
- Close button

#### ConfidenceHalo.tsx

**Props:**
```typescript
interface ConfidenceHaloProps {
  confidence: number     // 0-1
  risk: number          // 0-1
  size?: 'sm' | 'md' | 'lg'
  animated?: boolean
  className?: string
}
```

**Features:**
- Concentric rings: inner (high confidence) → outer (low confidence)
- Color intensity: saturated (high risk) → faded (low risk)
- Pulse animation for selected nodes
- Tooltip: "89% confidence, 0.72 risk"
- Smooth transitions

### PASM.tsx Page Implementation

**Key State:**
```typescript
const [selectedAsset, setSelectedAsset] = useState<string>('')
const [graphData, setGraphData] = useState<{ nodes: GraphNode[], edges: GraphEdge[] }>()
const [timeRange, setTimeRange] = useState<[Date, Date]>()
const [predictions, setPredictions] = useState<Prediction[]>()
const [selectedNodeDetails, setSelectedNodeDetails] = useState<GraphNode | null>()
const [highlightedPath, setHighlightedPath] = useState<string[]>()
const [modelMetadata, setModelMetadata] = useState<ModelMetadata>()
const [isAnimating, setIsAnimating] = useState(false)
```

**Hooks Integration:**
- `usePasm()` → predictions, graph data
- `useSystemStatus()` → threat level, system mode
- Custom WebSocket subscription to `/ws/pasm?asset={selectedAsset}`

**API Calls:**
1. **GET /pasm/models** (on mount)
   - Display model version, training date, accuracy

2. **GET /pasm/graph?range={startTime}-{endTime}** (time range change)
   - Fetch attack graph for time period
   - Parse nodes/edges

3. **GET /pasm/predict?asset={assetId}** (on asset select)
   - Get top-K predictions for asset
   - Sort by probability descending

4. **GET /pasm/confidence?prediction_id={id}** (when prediction selected)
   - Fetch uncertainty scores
   - Update ConfidenceHalo display

5. **WS /ws/pasm?asset={assetId}** (subscribe on asset select)
   - Receive live prediction deltas
   - Update graph edges/nodes
   - Track confidence updates

---

## PART 2: CED Page Architecture

### Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│ CED (Causal Explainable Defense)                            │
├─────────────────────────────────────────────────────────────┤
│ [Event: CVE-2025-XXXX] [Prediction ID: pred-123] [Time: ...]│
├──────────────────────────┬──────────────────────────────────┤
│ Causal Chain:            │ Explanation & Interventions      │
│ ┌────────────────────┐   │ ┌──────────────────────────────┐ │
│ │ Reconnaissance     │   │ Why:                           │ │
│ │ (Step 1)           │   │ ┌─ Firewall rule permissive   │ │
│ │      ↓             │   │ └─ ASR not enabled            │ │
│ │ Network Scan       │   │                                │ │
│ │ (Step 2)           │   │ Counterfactual (What-if?):     │ │
│ │      ↓             │   │ ☐ Patch Firewall-1            │ │
│ │ Exploitation       │   │ ☐ Enable ASR Monitoring       │ │
│ │ (Step 3, Critical) │   │ ☐ Isolate DB-01               │ │
│ │                    │   │                                │ │
│ │ [Prob: 0.72 ●████]│   │ [Simulate] [Reset]             │ │
│ └────────────────────┘   │ └──────────────────────────────┘ │
│                          │ → Delta: Prob -0.51 (0.21)     │
├──────────────────────────┴──────────────────────────────────┤
│ Timeline: [Initial] → [+Firewall] → [+ASR] → [Final]       │
│           0.72        0.65           0.43        0.21       │
└─────────────────────────────────────────────────────────────┘
```

### Component Structure

```
src/pages/CED.tsx (400+ lines)
├─ CausalGraph.tsx (200+ lines)
│  ├─ Chain visualization (linear or DAG layout)
│  ├─ Node interactivity (hover for details)
│  └─ Step-by-step progression
│
├─ CounterfactualEditor.tsx (220+ lines)
│  ├─ Checkbox list of interventions
│  ├─ Simulate button
│  ├─ Delta probability display
│  └─ Result explanation
│
└─ ExplanationTimeline.tsx (100+ lines)
   ├─ Timeline of probability updates
   ├─ Step markers with explanations
   └─ Interactive step selection
```

### Data Flow

```
Backend Endpoints:
  GET /ced/explain?prediction_id={id}
    → { narrative, causal_chain, interventions }
  POST /ced/simulate
    → { prediction_id, interventions }
    ← { reduced_probability, delta, explanation }
    ↓
CED Page State
  - causalChain (steps)
  - currentProbability (0.72)
  - interventions (selected)
    ↓
CounterfactualEditor
  - Show intervention options
  - Send POST /ced/simulate
    ↓
ExplanationTimeline
  - Animate probability changes
```

### Component Specifications

#### CausalGraph.tsx

**Props:**
```typescript
interface CausalGraphProps {
  chain: CausalStep[]
  currentStep?: number
  onStepSelect?: (index: number) => void
  highlightedFactors?: string[]
  className?: string
}

interface CausalStep {
  id: string
  order: number
  name: string
  description: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  contributingFactors: string[]
  probability: number
}
```

**Features:**
- Linear chain layout (left-to-right or top-to-bottom)
- Step nodes with severity color coding
- Arrow connections showing progression
- Click step to highlight contributing factors
- Hover details: "Why did this happen?"
- Animation showing chain progression
- Critical step highlighting (red border)

#### CounterfactualEditor.tsx

**Props:**
```typescript
interface CounterfactualEditorProps {
  predictionId: string
  currentProbability: number
  availableInterventions: Intervention[]
  onSimulate: (selectedIds: string[]) => Promise<SimulationResult>
  className?: string
}

interface Intervention {
  id: string
  type: 'patch' | 'isolate' | 'monitor' | 'configure'
  target: string
  description: string
  estimatedImpact?: number  // Expected probability reduction
  riskOfRollback?: number
}

interface SimulationResult {
  predictionId: string
  reducedProbability: number
  delta: number
  explanation: string
  timeToImplement?: number
}
```

**Features:**
- Checkbox list of interventions
- Estimated impact display (if available)
- Toggle "show advanced options"
- Multi-select support
- Simulate button (disabled until selection)
- Loading spinner during simulation
- Results display:
  - New probability
  - Delta (change)
  - Explanation text
  - Implementation time estimate
- Reset button to clear selections
- Export simulation as report

#### ExplanationTimeline.tsx

**Props:**
```typescript
interface ExplanationTimelineProps {
  steps: TimelineStep[]
  currentIndex?: number
  onStepClick?: (index: number) => void
  className?: string
}

interface TimelineStep {
  label: string
  probability: number
  explanation: string
  interventionApplied?: string
}
```

**Features:**
- Horizontal timeline with step markers
- Probability values at each step
- Click to jump to step
- Smooth transitions between steps
- Color coding (red for high prob, green for low)
- Annotations: "✓ Firewall patched"
- Tooltip with full explanation

### CED.tsx Page Implementation

**Key State:**
```typescript
const [predictionId, setPredictionId] = useState<string>('')
const [causalChain, setCausalChain] = useState<CausalStep[]>()
const [currentProbability, setCurrentProbability] = useState<number>(0)
const [selectedInterventions, setSelectedInterventions] = useState<Set<string>>(new Set())
const [simulationResult, setSimulationResult] = useState<SimulationResult | null>()
const [isSimulating, setIsSimulating] = useState(false)
const [timeline, setTimeline] = useState<TimelineStep[]>()
const [explanation, setExplanation] = useState<CEDExplanation>()
const [selectedStep, setSelectedStep] = useState<number>(0)
```

**Hooks Integration:**
- `usePasm()` → predictions (to select from)
- Query parameter: `?prediction_id=pred-123`

**API Calls:**
1. **GET /ced/explain?prediction_id={id}** (on page load)
   - Fetch causal explanation
   - Parse chain steps
   - Extract interventions
   - Build timeline

2. **POST /ced/simulate** (on simulate click)
   - Payload: `{ prediction_id, interventions: [{ type, target }] }`
   - Receive: `{ reduced_probability, delta, explanation }`
   - Update timeline with new step
   - Animate probability change

---

## Implementation Sequence

### Phase A: Backend API Enhancements (OPTIONAL - Frontend Ready for Mock)

1. **Extend /pasm.py:**
   - Add `GET /pasm/models` endpoint
   - Add `GET /pasm/graph?range=...&filters=...` endpoint
   - Add `GET /pasm/confidence?prediction_id={id}` endpoint
   - Add `GET /pasm/predict?asset={id}&top_k=5` endpoint
   - Add WebSocket `/ws/pasm?asset={id}` handler

2. **Create /ced.py route:**
   - Add `GET /ced/explain?prediction_id={id}` endpoint
   - Add `POST /ced/simulate` endpoint
   - Connect to `backend/core/ced/causal_engine.py`

### Phase B: Frontend Components (Primary Task)

1. **Create PASM Components** (500+ lines)
   ```bash
   src/components/
   ├─ PASMGraphViewer.tsx
   ├─ TimeSlider.tsx
   ├─ NodeDetailPanel.tsx
   └─ ConfidenceHalo.tsx
   ```

2. **Update PASM Page** (450+ lines)
   ```bash
   src/pages/PASM.tsx
   ```

3. **Create CED Components** (400+ lines)
   ```bash
   src/components/
   ├─ CausalGraph.tsx
   ├─ CounterfactualEditor.tsx
   └─ ExplanationTimeline.tsx
   ```

4. **Create CED Page** (400+ lines)
   ```bash
   src/pages/CED.tsx
   ```

### Phase C: Integration & Testing

1. Update types/index.ts with new interfaces
2. Verify WebSocket subscriptions
3. Test error scenarios
4. Documentation

---

## Implementation Details

### Type Definitions to Add

```typescript
// PASM Types
export interface GraphNode {
  id: string
  type: 'web' | 'app' | 'db' | 'firewall' | 'vpn'
  risk: number
  confidence: number
  vulnerabilityCount: number
  isCompromised?: boolean
  metadata?: Record<string, any>
}

export interface GraphEdge {
  source: string
  target: string
  vuln?: string
  weight: number
  exploitType?: string
}

export interface PASMPrediction {
  id: string
  assetId: string
  attackChains: AttackChain[]
  topKPaths: string[][]
  averageRisk: number
  timestamp: string
  modelVersion: string
}

export interface AttackChain {
  steps: string[]
  probability: number
  impactScore: number
  countermeasures: string[]
}

export interface ModelMetadata {
  version: string
  trainedOn: string
  accuracy: number
  lastUpdated: string
}

// CED Types
export interface CausalStep {
  id: string
  order: number
  name: string
  description: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  contributingFactors: string[]
  probability: number
}

export interface CausalChain {
  predictionId: string
  steps: CausalStep[]
  narrative: string
  totalProbability: number
}

export interface Intervention {
  id: string
  type: 'patch' | 'isolate' | 'monitor' | 'configure'
  target: string
  description: string
  estimatedImpact?: number
  riskOfRollback?: number
}

export interface SimulationResult {
  predictionId: string
  reducedProbability: number
  delta: number
  explanation: string
  timeToImplement?: number
  appliedInterventions: Intervention[]
}
```

### Technology Stack

- **Graph Visualization:**
  - `react-force-graph` OR `cytoscape` for interactive graph
  - Alternative: `vis.js` for timeline-aware visualization

- **Time-Series:**
  - `recharts` for timeline/probability chart
  - Native Slider for timeline input

- **State Management:**
  - Redux (existing)
  - React hooks for local component state

- **Real-time:**
  - WebSocket (existing infrastructure)
  - Auto-reconnect with exponential backoff

### Performance Considerations

1. **Graph Rendering:**
   - Lazy load nodes when graph > 100 nodes
   - Use webworker for physics simulation
   - Debounce zoom/pan events

2. **Data Fetching:**
   - Cache graph data by time range
   - Use `/ws/pasm` for incremental updates
   - Pagination for vulnerability lists (20 per page)

3. **Memory:**
   - Clean up graph resources on unmount
   - Dispose WebSocket connections
   - Cancel pending API calls on route change

---

## Success Criteria

### PASM Page
- ✅ Attack graph renders with 50+ nodes smoothly (60fps)
- ✅ Time slider updates graph data in <500ms
- ✅ Node selection highlights connected paths
- ✅ Detail panel shows all vulnerability information
- ✅ WebSocket receives live predictions
- ✅ Zero TypeScript errors
- ✅ Mobile responsive (basic layout on tablet)

### CED Page
- ✅ Causal chain displays all steps
- ✅ Intervention checkboxes functional
- ✅ Simulate button calls backend correctly
- ✅ Timeline updates with simulation results
- ✅ Probability delta displays correctly
- ✅ Zero TypeScript errors
- ✅ Export simulation as PDF/JSON

---

## File Structure Summary

```
frontend/web_dashboard/src/
├── components/
│   ├── PASMGraphViewer.tsx          (280+ lines)
│   ├── TimeSlider.tsx               (100+ lines)
│   ├── NodeDetailPanel.tsx          (150+ lines)
│   ├── ConfidenceHalo.tsx           (80+ lines)
│   ├── CausalGraph.tsx              (200+ lines)
│   ├── CounterfactualEditor.tsx     (220+ lines)
│   └── ExplanationTimeline.tsx      (100+ lines)
├── pages/
│   ├── PASM.tsx                     (450+ lines)
│   └── CED.tsx                      (400+ lines)
├── services/
│   ├── pasm.service.ts              (existing)
│   └── ced.service.ts               (new, if needed)
├── types/
│   └── index.ts                     (updated with new interfaces)
└── hooks/
    └── usePasm.ts                   (existing, may extend)
```

---

## Next Steps

1. **Create PASMGraphViewer.tsx** with react-force-graph
2. **Create TimeSlider.tsx** with date range picker
3. **Create NodeDetailPanel.tsx** with tabbed interface
4. **Update PASM.tsx** page to integrate components
5. **Create CausalGraph.tsx** with chain visualization
6. **Create CounterfactualEditor.tsx** with simulation UI
7. **Create CED.tsx** page with full flow
8. **Update backend routes** if needed (optional)
9. **Comprehensive testing** and error handling
10. **Documentation** with deployment guide

---

## Notes

- All components follow existing patterns from Dashboard.tsx
- Use Tailwind CSS for styling (dark theme)
- Maintain TypeScript strict mode
- No `any` types allowed
- Proper error handling with user feedback
- Accessibility compliance (ARIA labels, keyboard nav)
- Performance optimized for large graphs
