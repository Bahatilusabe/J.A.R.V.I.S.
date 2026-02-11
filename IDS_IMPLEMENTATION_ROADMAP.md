# AI-Powered IDS/IPS - Implementation Roadmap

**Date:** December 13, 2025  
**Status:** Phase 1 Complete ✅ | Phases 2-5 In Progress 🚧  
**Total Effort:** ~35-40 hours  
**Team:** 1-2 engineers

---

## 📋 Quick Reference

```
┌────────────────────────────────────────────────────────────────┐
│               HUAWEI MINDSPORE AI STACK                        │
│                 (Centerpiece Module)                           │
└────────────────────────────────────────────────────────────────┘
│                                                                │
│  PHASE 1 (DONE) ✅      PHASE 2-5 (IN PROGRESS) 🚧            │
│  ─────────────────      ──────────────────────────            │
│  ✅ Core IDS Engine      🚧 Explainability                     │
│  ✅ REST API             🚧 MLOps                              │
│  ✅ Frontend UI          🚧 Edge Inference                     │
│  ✅ Data Models          🚧 MindSpore Training                 │
│                         🚧 Dashboard Enhancements             │
│                         🚧 Integration Tests                  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Implementation Overview

### Phase 1: Foundation ✅ COMPLETE

**Status:** All core components built and tested

**Deliverables:**
- ✅ `backend/ids_engine.py` (957 lines)
  - Multi-model ensemble (LSTM/Transformer/Autoencoder/GNN)
  - Flow ingestion and analysis
  - Threat detection and scoring
  - Alert correlation
  - Model management framework

- ✅ `backend/api/routes/ids.py` (555 lines)
  - 10+ REST endpoints for flow analysis, alerts, models
  - Request/response validation (Pydantic)
  - OpenAPI documentation

- ✅ `frontend/web_dashboard/src/pages/IDSThreats.tsx` (450+ lines)
  - Threat timeline visualization
  - Alert list and filtering
  - Model status display
  - Alert investigation workflow

**Time Spent:** ~20 hours

---

### Phase 2: Explainability 🚧 IN PROGRESS

**Effort:** 3-4 hours | 400+ lines of code

**Tasks:**

1. **Create `backend/explainability_engine.py`**
   ```python
   class ExplainabilityEngine:
       - generate_shap_values(features, model)        # Feature importance
       - generate_attention_heatmap(features, model)  # Attention visualization
       - generate_narrative(threat, features)         # Human-friendly explanation
       - extract_top_features(shap_dict)              # Top 5 contributing features
   ```

2. **Implement Narrative Generator**
   ```
   "Detected DDoS with 98% confidence:
    - Packet rate 10,000 pps (highest impact)
    - Source entropy high at 0.92 (randomized IPs)
    - Duration 300 sec (sustained pattern)
    Recommendation: BLOCK source immediately"
   ```

3. **Add Explainability Endpoint**
   ```
   GET /ids/alerts/{alert_id}/explanation
   Response:
   {
     "shap_values": { "packet_rate": 0.45, ... },
     "attention_heatmap": [ 0.1, 0.15, ... ],
     "top_features": [("packet_rate", 0.45), ...],
     "narrative": "Detected DDoS..."
   }
   ```

**Success Criteria:**
- All detections have explainability data
- SHAP values computed in <50ms
- Narratives pass analyst readability check

---

### Phase 3: MLOps Infrastructure 🚧 IN PROGRESS

**Effort:** 4-5 hours | 600+ lines of code

**Tasks:**

1. **Create `backend/mlops_infrastructure.py`**
   ```python
   class MLOpsOrchestrator:
       - register_model(model_type, metrics)      # Add to model registry
       - activate_model(version_id, percentage)   # Deploy (canary or full)
       - check_model_drift(version_id, dist)      # KL-divergence check
       - run_ab_test(model_a, model_b, percent)   # A/B test management
       - trigger_retraining(condition)            # Auto-retraining
   
   class DriftDetector:
       - compute_kl_divergence(ref, current)      # Distribution shift
       - detect_performance_decay(metrics)        # Performance regression
       - recommend_action()                       # Trigger retraining
   
   class ModelRegistryManager:
       - list_models(filter_by_type)              # Browse registry
       - get_model_metrics(version_id)            # Performance data
       - rollback_model(version_id)               # Revert to old version
   ```

2. **Implement Drift Detection**
   - Monitor feature distributions continuously
   - Calculate KL-divergence (threshold: 0.15)
   - Trigger retraining if drift detected
   - Log all drift events

3. **Add Model Operations Endpoints**
   ```
   GET /ids/models/status             # Active models + metrics
   POST /ids/models/retrain           # Trigger retraining
   GET /ids/drift                     # Drift metrics
   POST /ids/models/{id}/activate     # Deploy model
   ```

**Success Criteria:**
- Model versions tracked in registry
- Drift detected within 1 hour
- A/B tests measurable and automated
- Auto-retraining triggered on conditions

---

### Phase 4: Edge Inference 🚧 IN PROGRESS

**Effort:** 3-4 hours | 300+ lines of code

**Tasks:**

1. **Create `backend/edge_inference/ids_lite_agent.py`**
   ```python
   class EdgeIDSAgent:
       - load_mindspore_lite_model()              # Load optimized model
       - predict_flow_local(flow_features)       # Sub-10ms inference
       - sync_models_from_cloud()                 # Fetch updates
       - fallback_to_cloud(uncertain_flows)      # Cloud for complex cases
       - cache_recent_detections()                # Avoid duplicate alerts
   ```

2. **Model Optimization**
   - Export LSTM/Transformer to MindSpore Lite format
   - Quantization for edge devices (int8)
   - Test on AIoT gateway hardware
   - Achieve <10ms latency

3. **Edge-to-Cloud Sync**
   - Local detections sent to central IDS
   - Model updates from cloud to edge
   - Telemetry batching to reduce bandwidth
   - Offline operation capability

**Success Criteria:**
- <10ms detection latency on edge
- Works with <500MB memory footprint
- Handles model updates without restart
- Reduces central IDS load by 50%

---

### Phase 5: MindSpore Training Pipeline 🚧 IN PROGRESS

**Effort:** 4-5 hours | 400+ lines of code

**Tasks:**

1. **Create `backend/ml_models/train_ids_models.py`**
   ```python
   # MindSpore training for 4 architectures
   class IDSModelTrainer:
       - prepare_dataset(security_logs)           # Data loading
       - train_lstm_model(train_set)              # Temporal sequences
       - train_transformer_model(train_set)       # Attention patterns
       - train_autoencoder_model(train_set)       # Anomaly detection
       - train_gnn_model(train_set)               # Graph topology
   
   # Ascend GPU acceleration
   context.set_context(device_target='Ascend')
   
   # Export for CANN optimization
   export_model(model, 'ids_lstm.onnx', format='ONNX')
   # → aclTransform -i ids_lstm.onnx -o ids_lstm.om
   ```

2. **Model Validation**
   - Cross-validation on historical data
   - ROC-AUC >0.95 target
   - False positive rate <1%
   - Latency <100ms

3. **Hyperparameter Tuning**
   - Learning rate scheduling
   - Batch normalization
   - Dropout rates
   - Model architecture search

**Success Criteria:**
- LSTM F1 score >0.94
- Transformer precision >0.96
- Autoencoder recall >0.92
- GNN topology detection >0.90

---

### Phase 6: Dashboard Enhancements 🚧 IN PROGRESS

**Effort:** 4-5 hours | 500+ lines of code

**Tasks:**

1. **Enhanced `frontend/web_dashboard/src/pages/IDSThreats.tsx`**
   - Real-time threat timeline with drill-down
   - SHAP feature importance charts
   - Attention heatmap visualization
   - Model performance dashboard
   - Alert response workflow UI
   - Threat correlation visualization

2. **New Components**
   ```
   <ThreatTimeline />           # Real-time threat events
   <SHAPVisualization />        # Feature importance chart
   <AttentionHeatmap />         # Attention weights heatmap
   <ModelPerformance />         # F1, precision, recall metrics
   <AlertInvestigation />       # Analyst workflow UI
   <ThreatCorrelation />        # Attack chain visualization
   ```

**Success Criteria:**
- Load time <2 seconds
- Real-time updates <500ms latency
- All threats have explanations displayed
- Analyst can take action within UI

---

### Phase 7: Integration & Testing 🚧 IN PROGRESS

**Effort:** 3-4 hours | 600+ lines of code

**Integration Points:**

1. **DPI Engine Integration**
   ```python
   # Flow enriched with DPI data
   flow.dpi_app = "BitTorrent"
   flow.dpi_category = "P2P"
   # IDS uses for behavioral analysis
   ```

2. **Firewall Policy Engine Integration**
   ```python
   if threat.threat_level == ThreatLevel.CRITICAL:
       firewall_engine.add_temporary_rule(
           src_ip=threat.src_ip,
           action=ACLAction.BLOCK,
           duration=3600
       )
   ```

3. **Telemetry Service Integration**
   ```python
   src_risk = telemetry.get_host_risk(flow.src_ip)
   dst_risk = telemetry.get_host_risk(flow.dst_ip)
   # Adjust threat scoring based on context
   ```

4. **Metrics Collection Integration**
   ```python
   metrics.track({
       'threats_detected': 42,
       'avg_detection_latency': 87.5,
       'model_precision': 0.96,
   })
   ```

**Testing:**
- Unit tests for each component (200+ tests)
- Integration tests for API endpoints (50+ tests)
- E2E tests for threat-to-response flow (20+ tests)
- Load testing with 10K flows/sec

**Success Criteria:**
- All integration points tested
- No performance regression
- <1% data loss in high-load scenarios
- Backward compatible with existing systems

---

### Phase 8: Production Deployment 🚧 IN PROGRESS

**Effort:** 2-3 hours | 300+ lines of documentation

**Documentation:**
1. `MINDSPORE_TRAINING_GUIDE.md`
   - Data preparation
   - Model training on Ascend
   - Validation procedures
   - Performance benchmarks

2. `MLOPS_PROCEDURES.md`
   - Model registration workflow
   - Drift detection alerts
   - A/B testing procedures
   - Auto-retraining triggers

3. `EDGE_DEPLOYMENT_GUIDE.md`
   - AIoT gateway setup
   - Model optimization steps
   - Edge-to-cloud sync
   - Fallback procedures

4. `ANALYST_HANDBOOK.md`
   - Alert triage procedures
   - Explainability interpretation
   - Feedback loop process
   - Escalation procedures

**Deployment Checklist:**
- ✅ All tests passing
- ✅ Performance targets met
- ✅ Documentation complete
- ✅ Monitoring configured
- ✅ Rollback procedures tested
- ✅ On-call support ready

---

## 📊 Current Status Summary

| Component | Status | Lines | Phase | Est. Time |
|-----------|--------|-------|-------|-----------|
| Core Engine | ✅ DONE | 957 | 1 | 8h |
| API Routes | ✅ DONE | 555 | 1 | 6h |
| Frontend UI | ✅ DONE | 450+ | 1 | 6h |
| Explainability | 🚧 TODO | 400+ | 2 | 3-4h |
| MLOps | 🚧 TODO | 600+ | 3 | 4-5h |
| Edge Inference | 🚧 TODO | 300+ | 4 | 3-4h |
| Training | 🚧 TODO | 400+ | 5 | 4-5h |
| Dashboard | 🚧 TODO | 500+ | 6 | 4-5h |
| Testing | 🚧 TODO | 600+ | 7 | 3-4h |
| Deployment | 🚧 TODO | 300+ | 8 | 2-3h |
| **TOTAL** | **50% DONE** | **5,000+** | **1-8** | **38-42h** |

---

## 🎯 Next Immediate Actions

**This week:**

1. **Hour 1-3:** Build `explainability_engine.py`
   - SHAP integration
   - Attention heatmap generation
   - Narrative explanation generation

2. **Hour 4-6:** Create explainability endpoints
   - Add to `ids.py` routes
   - Test with sample detections

3. **Hour 7-10:** Build `mlops_infrastructure.py`
   - Model registry
   - Drift detection
   - A/B testing framework

**Next week:**

4. Edge inference agent for AIoT gateways
5. MindSpore training pipeline
6. Dashboard enhancements
7. Integration and E2E testing
8. Production deployment

---

## 🚀 Critical Success Factors

1. **Detection Accuracy** - >95% true positive rate, <1% false positive
2. **Latency** - <100ms end-to-end threat detection
3. **Explainability** - Every alert has SHAP + attention + narrative
4. **Reliability** - 99.9% uptime with drift detection & auto-recovery
5. **Scalability** - Handle 100K+ flows/sec with distributed inference
6. **Integration** - Seamless with DPI, Firewall, Telemetry systems

---

## 💡 Key Differentiators

✅ **Multi-Model Ensemble**
   - Combines LSTM (temporal), Transformer (attention), Autoencoder (anomalies), GNN (topology)
   - Voting mechanism reduces false positives

✅ **Explainable AI**
   - SHAP values show feature importance
   - Attention heatmaps visualize model reasoning
   - Natural language explanations for analysts

✅ **Production MLOps**
   - Drift detection triggers auto-retraining
   - A/B testing for model updates
   - Model versioning for rollback capability

✅ **Huawei Aligned**
   - MindSpore for training & inference
   - CANN optimization for Ascend GPUs
   - ModelArts for MLOps workflow
   - MindSpore Lite for edge deployment

---

## 📈 Expected Outcomes

After completing all 8 phases:

- **Threat Detection:** 42+ threats/hour (varies by environment)
- **Detection Latency:** <100ms (avg 85ms)
- **Precision:** >96% (minimize false positives)
- **Recall:** >95% (catch real threats)
- **Analyst Efficiency:** 5-minute investigation time per alert
- **Auto-Response:** 1-minute response execution for critical threats
- **Edge Coverage:** 50% of detections happen locally on gateways
- **Model Updates:** Weekly retraining with latest attack patterns

---

## ✨ Success = Huawei AI Showcase

This AI-Powered IDS/IPS system demonstrates:

✅ **End-to-end Huawei ecosystem integration**
   - MindSpore models → CANN optimization → Ascend GPUs
   - ModelArts MLOps → Edge deployment with Lite

✅ **Enterprise security powered by AI**
   - Real-time threat detection with <100ms latency
   - Explainable decisions for human analysts
   - Automated response to security incidents

✅ **Production-grade ML system**
   - Model versioning, drift detection, A/B testing
   - Continuous learning from analyst feedback
   - Auto-retraining pipeline

**This is the centerpiece module for Huawei alignment.**

---

**Status: READY FOR DEVELOPMENT** 🚀  
**Start Date:** December 13, 2025  
**Target Completion:** December 20, 2025  
**Est. Total Effort:** 38-42 hours

---
