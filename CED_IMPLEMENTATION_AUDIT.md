# CED (Causal Explainable Defense) Implementation Audit Report

**Date:** December 14, 2025  
**Assessment:** Correctness & Integration Verification  
**Status:** ⚠️ **PARTIALLY IMPLEMENTED - CRITICAL INTEGRATION GAP**

---

## Executive Summary

The **Causal Explainable Defense (CED)** system is **~50% complete**:

| Component | Status | Notes |
|-----------|--------|-------|
| **Frontend** | ✅ Complete | 1,379 lines, 8 React components, fully implemented |
| **Backend Logic** | ⚠️ Minimal | 2 modules (causal_engine.py, explanation_builder.py) exist but incomplete |
| **API Routes** | ❌ MISSING | No `/ced/explain` or `/ced/simulate` endpoints created |
| **Server Registration** | ❌ MISSING | CED router not included in FastAPI app |
| **Integration** | ❌ BROKEN | Frontend calls `/ced/explain` but backend has no route |
| **PASM Integration** | ❌ Missing | No connection to PASM predictions |
| **SOC UI Integration** | ❌ Missing | No integration with SOC dashboard |

### Bottom Line
**Frontend is complete but useless without backend. Backend is incomplete and not registered.**

---

## Part 1: Frontend Implementation Status ✅

### What's Implemented (1,379 lines)

**Files Created:**
1. ✅ `src/types/ced.types.ts` (80 lines) - Complete type definitions
2. ✅ `src/components/CausalGraph.tsx` (345 lines) - Interactive DAG visualization
3. ✅ `src/components/CounterfactualEditor.tsx` (215 lines) - "What-if" simulator
4. ✅ `src/components/ExplanationPanel.tsx` (175 lines) - Text explanations
5. ✅ `src/components/ExplanationTimeline.tsx` (172 lines) - Attack timeline
6. ✅ `src/hooks/useCED.ts` (125 lines) - API integration hook
7. ✅ `src/store/slices/cedSlice.ts` (83 lines) - Redux state management
8. ✅ `src/pages/CED.tsx` (184 lines) - Main page UI

**Features Implemented:**
- ✅ Causal chain visualization (hierarchical SVG layout)
- ✅ Zoom/pan/reset controls
- ✅ Node selection and detail panels
- ✅ Severity color-coding (critical→red, high→orange, medium→yellow, low→blue)
- ✅ Edge highlighting for interaction strength
- ✅ Natural language explanation panels (summary, why chain, impact)
- ✅ Counterfactual intervention simulator with impact metrics
- ✅ Attack timeline with phase-coded events
- ✅ Simulation history tracking
- ✅ Redux state management with caching
- ✅ Error handling and loading states
- ✅ Full TypeScript type safety

### Frontend API Calls Expected

The frontend expects these backend endpoints:

```typescript
// src/hooks/useCED.ts Line 37-48
GET  /ced/explain?prediction_id={id}
     Response: CEDExplanation {
       predictionId, baselineProbability, causalGraph,
       naturalLanguage, minimalInterventions, confidence, generatedAt
     }

POST /ced/simulate
     Body: { prediction_id, interventions: [{type, target, enabled}...] }
     Response: {
       simulation_id, baseline_probability, reduced_probability, delta,
       explanation, affected_nodes
     }
```

---

## Part 2: Backend Implementation Status ⚠️

### What's Implemented

**File 1: `backend/core/ced/causal_engine.py` (259 lines)**

```python
class CausalEngine:
    """Small structural causal model container."""
    ✅ add_node(name, func, parents) - Register SCM nodes
    ✅ predict(interventions) - Forward prediction under interventions
    ✅ _infer_noise(observed) - Infer exogenous noise from observations
    ✅ counterfactual(observed, intervention) - Run counterfactual analysis

class DoWhyMindSporeCausalEngine(CausalEngine):
    ✅ Hybrid engine supporting DoWhy + MindSpore
    ⚠️ Minimal implementation (scaffold only)
```

**Features:**
- ✅ Structural causal model (SCM) abstraction
- ✅ Deterministic structural functions
- ✅ Abduction-action-prediction counterfactual workflow
- ✅ NumPy fallback (no heavy dependencies)
- ✅ Optional MindSpore and DoWhy support

**File 2: `backend/core/ced/explanation_builder.py` (190 lines)**

```python
class ExplanationBuilder:
    ✅ build_explanation(original, counterfactual) - Create text explanations
    ✅ _summarize_diffs(orig, cf) - Compare original vs counterfactual

class DashExplanationBuilder(ExplanationBuilder):
    ⚠️ Optional Dash/Plotly visualization support
```

**Features:**
- ✅ Plain-text explanation generation
- ✅ Counterfactual difference summarization
- ⚠️ Optional Dash app builder (incomplete)
- ✅ MindSpore integration (gated)

### What's Missing (Critical)

**❌ NO API ROUTES FILE**
- No `backend/api/routes/ced.py` created
- No FastAPI route handlers for `/ced/explain` or `/ced/simulate`
- No HTTP endpoints to handle frontend requests

**❌ NOT REGISTERED IN SERVER**
- `backend/api/server.py` doesn't import CED routes
- `app.include_router()` call missing for CED
- Even if routes existed, they wouldn't be accessible

**Code Evidence:**
```python
# backend/api/server.py Lines 32-48
# Imports include: telemetry, pasm, policy, vocal, forensics, vpn, 
# auth, admin, self_healing, packet_capture_routes, dpi_routes, 
# compatibility, ids, federation, deception, metrics, threat_intelligence, tds

# ❌ NO 'ced' imported
# ❌ NO ced.router registered with app.include_router()
```

---

## Part 3: Missing Components

### 1. ❌ API Route Handler (`backend/api/routes/ced.py` - MISSING)

Should contain:

```python
# MISSING IMPLEMENTATION
from fastapi import APIRouter, HTTPException
from backend.core.ced.causal_engine import CausalEngine
from backend.core.ced.explanation_builder import ExplanationBuilder

router = APIRouter()

@router.get("/explain")
async def explain(prediction_id: str):
    """GET /api/ced/explain?prediction_id={id}"""
    # 1. Load PASM prediction
    # 2. Build causal DAG from prediction
    # 3. Run causal engine to generate interventions
    # 4. Build NL explanations
    # 5. Return CEDExplanation
    pass

@router.post("/simulate")
async def simulate(request: CounterfactualRequest):
    """POST /api/ced/simulate"""
    # 1. Load original prediction
    # 2. Apply counterfactual interventions
    # 3. Recompute attack probability
    # 4. Return CounterfactualResponse
    pass
```

### 2. ❌ PASM Integration Layer (MISSING)

Currently no code connects CED → PASM predictions:
- ❌ Can't load PASM predictions
- ❌ Can't extract causal graph from PASM
- ❌ Can't correlate attack chains with PASM output

**Needs:** Import PASM predictor, load prediction for given ID, convert to causal DAG.

### 3. ❌ Counterfactual Inference Engine (INCOMPLETE)

Current `causal_engine.py` is a **scaffold only**:
- ✅ Basic counterfactual math exists
- ❌ No integration with PASM predictions
- ❌ No attack chain extraction
- ❌ No intervention impact modeling
- ❌ No MindSpore structural functions

**Needs:** Real structural functions for attack chains, integration with threat models.

### 4. ❌ Natural Language Generation (BASIC)

Current `explanation_builder.py`:
- ✅ Simple text diff generation exists
- ❌ No domain-specific explanations (attack chains, tactics)
- ❌ No MITRE ATT&CK context
- ❌ No impact assessment
- ❌ No minimal intervention reasoning

**Needs:** Security-focused explanation templates, MITRE mapping, impact scoring.

### 5. ❌ Server Registration (MISSING)

`backend/api/server.py` needs:

```python
# Missing import
from backend.api.routes import ced  # ❌ NOT THERE

# Missing router registration (Line ~140)
app.include_router(ced.router, prefix="/api/ced", tags=["ced"])  # ❌ NOT THERE
```

### 6. ❌ SOC UI Integration (MISSING)

No connection to SOC dashboard:
- ❌ No embedded CED widget in SOC
- ❌ No incident → CED explanation link
- ❌ No one-click intervention simulation
- ❌ No recommendation dashboard

---

## Part 4: Implementation Gaps vs Specification

| Requirement | Spec | Frontend | Backend | Status |
|-------------|------|----------|---------|--------|
| **Dataset Selection** | PASM predictions | ❌ Missing | ❌ Missing | ❌ NO |
| | Incident response logs | ❌ Missing | ❌ Missing | ❌ NO |
| | Attack chain sequences | ❌ Missing | ❌ Missing | ❌ NO |
| | Counterfactual datasets | ❌ Missing | ❌ Missing | ❌ NO |
| **Data Processing** | Build causal DAG (SCM) | ✅ Display only | ⚠️ Scaffold | ⚠️ Partial |
| | Extract cause-effect relations | ❌ Missing | ❌ Missing | ❌ NO |
| | Generate counterfactual samples | ❌ Missing | ⚠️ Partial | ⚠️ Partial |
| **Model Implementation** | MindSpore SCM | ❌ Frontend only | ⚠️ Optional import | ⚠️ Not used |
| | Counterfactual inference engine | ✅ UI only | ⚠️ Basic | ⚠️ Incomplete |
| | Decision-ranking algorithm | ❌ Missing | ❌ Missing | ❌ NO |
| **Training** | Causal supervised learning | ❌ Not applicable | ❌ Missing | ❌ NO |
| | Metrics: causal accuracy | ❌ Missing | ❌ Missing | ❌ NO |
| | Intervention success | ❌ Missing | ❌ Missing | ❌ NO |
| **Inference** | /ced/explain endpoint | ✅ Expected | ❌ NOT CREATED | ❌ NO |
| | Root cause + causal graph | ✅ Display component | ⚠️ Partial | ⚠️ Partial |
| | Minimal interventions | ✅ UI component | ❌ Missing | ❌ NO |
| | /ced/simulate endpoint | ✅ Expected | ❌ NOT CREATED | ❌ NO |
| | What-if scenarios | ✅ UI component | ❌ NOT CALLABLE | ❌ NO |
| **Deployment** | REST microservice | ❌ Missing | ❌ Missing | ❌ NO |
| | SOC UI integration | ❌ Missing | ❌ Missing | ❌ NO |
| | Cloud ready | ❌ Missing | ❌ Missing | ❌ NO |

---

## Part 5: What Happens If You Try to Use It

### Scenario: User selects prediction in CED page

**Frontend:**
```typescript
// src/pages/CED.tsx
const { explanation } = useCED('pred-001')  // Tries to fetch explanation
```

**Hook Execution:**
```typescript
// src/hooks/useCED.ts Line 40-50
const response = await fetch(`${API_BASE}/ced/explain?prediction_id=pred-001`)
// Calls: GET http://localhost:8000/ced/explain?prediction_id=pred-001
```

**Backend:**
```
❌ NO ROUTE HANDLER EXISTS

GET /ced/explain?prediction_id=pred-001
→ 404 Not Found
→ Frontend catches error
→ Error message: "Failed to fetch explanation"
→ CED page shows error, causal graph empty
```

**Result:** Completely broken. User sees error, nothing renders.

---

## Critical Issues Summary

| Priority | Issue | Impact | Effort |
|----------|-------|--------|--------|
| 🔴 **CRITICAL** | No API routes created | Frontend completely non-functional | 2-3 days |
| 🔴 **CRITICAL** | Routes not registered in server | Even if created, won't be accessible | 1 hour |
| 🔴 **CRITICAL** | No PASM integration | Can't load predictions, causal graphs empty | 2-3 days |
| 🟠 **MAJOR** | Incomplete causal engine | Counterfactuals unreliable | 3-5 days |
| 🟠 **MAJOR** | Basic explanation generator | Explanations are generic, not domain-specific | 2-3 days |
| 🟠 **MAJOR** | No SOC integration | Can't use from security dashboard | 2-3 days |
| 🟡 **MEDIUM** | No intervention modeling | Can't rank/recommend interventions properly | 2-3 days |
| 🟡 **MEDIUM** | No training/metrics | No way to improve model over time | 1-2 weeks |

---

## Recommended Fix Sequence

### Phase 1: Make It Work (3-4 days)

1. **Create CED API routes** (`backend/api/routes/ced.py`)
   - Implement `/ced/explain` endpoint
   - Implement `/ced/simulate` endpoint
   - Add error handling

2. **Register with FastAPI**
   - Import in `backend/api/server.py`
   - Call `app.include_router(ced.router, prefix="/api/ced")`

3. **Add PASM integration**
   - Load predictions from PASM module
   - Extract causal graph from attack chain
   - Convert to CED format

4. **Basic counterfactual support**
   - Connect causal engine to PASM data
   - Implement simple intervention impact calculation

### Phase 2: Make It Correct (1-2 weeks)

1. **Complete causal engine**
   - Real attack chain structural functions
   - Proper counterfactual inference
   - Intervention impact modeling

2. **Improve explanations**
   - MITRE ATT&CK context
   - Domain-specific templates
   - Impact assessment language

3. **Decision ranking**
   - Minimal intervention identification
   - Effort-impact tradeoff analysis

### Phase 3: Make It Integrate (3-5 days)

1. **SOC Dashboard Integration**
   - Add CED widget to incident details
   - Link incident → CED explanation
   - One-click simulation from SOC

2. **API Metrics**
   - Track explanation accuracy
   - Measure intervention effectiveness
   - Monitor response times

---

## Files That Need Creation/Modification

### Must Create
```
✅ backend/api/routes/ced.py ........................... (150-200 lines)
   - GET /explain, POST /simulate handlers
   - PASM integration
   - Error handling
```

### Must Modify
```
✅ backend/api/server.py ............................. (2 additions)
   - Import: from backend.api.routes import ced
   - Register: app.include_router(ced.router, prefix="/api/ced")
```

### Should Enhance
```
⚠️ backend/core/ced/causal_engine.py ................ (enhance from 259)
   - Real attack chain functions
   - PASM prediction integration

⚠️ backend/core/ced/explanation_builder.py ......... (enhance from 190)
   - Security-specific templates
   - MITRE ATT&CK integration
   - Impact assessment
```

### Optional
```
💡 frontend/ (no changes needed - already complete)
💡 SOC dashboard integration (future phase)
```

---

## Summary: Is CED Correctly Implemented?

| Layer | Status | Details |
|-------|--------|---------|
| **Frontend UI** | ✅ **COMPLETE** | 1,379 lines, all components working |
| **Type Safety** | ✅ **COMPLETE** | Full TypeScript types defined |
| **API Integration** | ❌ **BROKEN** | Endpoints called but not implemented |
| **Backend Logic** | ⚠️ **INCOMPLETE** | Core logic scaffolded, not functional |
| **PASM Integration** | ❌ **MISSING** | No connection to PASM predictions |
| **Server Registration** | ❌ **MISSING** | Routes not registered in FastAPI app |
| **SOC Integration** | ❌ **MISSING** | No integration with security dashboard |
| **Overall** | ❌ **NOT READY** | ~50% complete, requires backend work |

---

## Conclusion

**CED is a beautiful frontend looking for a backend.**

The React components are production-ready, but they call non-existent API endpoints. The backend has some logic (causal engine, explanation builder) but:

1. No API routes have been created
2. Routes aren't registered in the server
3. Backend isn't integrated with PASM
4. Core functionality is incomplete (just scaffolds)

**Estimated effort to production: 2-3 weeks** (backend + integration).

**Current status:** Not suitable for production use. Frontend loads but errors on first interaction.

---

## Detailed Audit Files

See companion documents for full details:
- `CED_BACKEND_IMPLEMENTATION_ANALYSIS.md` - Deep backend analysis
- `CED_INTEGRATION_CHECKLIST.md` - Step-by-step fix guide
