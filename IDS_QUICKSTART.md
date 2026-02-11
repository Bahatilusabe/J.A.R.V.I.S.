# IDS/IPS Quick Start Guide

**Get the AI-Powered Intrusion Detection System running in 5 minutes.**

---

## 1. Backend Setup (2 min)

### Copy Files
```bash
cp /backend/ids_engine.py /backend/
cp /backend/mlops_infrastructure.py /backend/
cp /backend/explainability_engine.py /backend/
cp /backend/api/routes/ids.py /backend/api/routes/
```

### Register Routes in `main.py`
```python
from fastapi import FastAPI
from api.routes import ids

app = FastAPI()
app.include_router(ids.router)
```

### Test Endpoint
```bash
curl -X GET http://localhost:8000/ids/health
```

Expected response:
```json
{
  "status": "healthy",
  "engine_id": "ids_engine_uuid",
  "active_models": 4,
  "alerts_queued": 0,
  "timestamp": "2025-12-15T14:30:45Z"
}
```

---

## 2. Frontend Setup (2 min)

### Copy Files
```bash
cp /frontend/web_dashboard/src/pages/IDSThreats.tsx /frontend/web_dashboard/src/pages/
cp /frontend/web_dashboard/src/pages/IDSThreats.module.scss /frontend/web_dashboard/src/pages/
```

### Register Route in `App.tsx`
```tsx
import IDSThreats from "./pages/IDSThreats";

<Routes>
  <Route path="/ids-threats" element={<IDSThreats />} />
</Routes>
```

### Add Navigation Link
```tsx
// In SidePanel.tsx or Navigation component
<Link to="/ids-threats" className="nav-link">
  <Shield size={20} />
  IDS Threats
</Link>
```

### Install Dependencies
```bash
npm install recharts lucide-react
```

---

## 3. Quick Test (1 min)

### Analyze a Sample Flow
```bash
curl -X POST http://localhost:8000/ids/detect \
  -H "Content-Type: application/json" \
  -d '{
    "src_ip": "192.168.1.100",
    "dst_ip": "10.0.0.50",
    "src_port": 54321,
    "dst_port": 443,
    "protocol": "tcp",
    "duration_sec": 120,
    "packet_count": 5000,
    "byte_count": 2500000,
    "dpi_app": "BitTorrent",
    "dpi_category": "P2P"
  }'
```

Response:
```json
{
  "threat_detected": true,
  "threat_score": 0.87,
  "threat_level": "HIGH",
  "alert_id": "alert_123456",
  "detection_methods": ["LSTM", "TRANSFORMER"],
  "latency_ms": 45.2,
  "models_evaluated": 4,
  "explanation_available": true
}
```

### Get Explanation
```bash
curl http://localhost:8000/ids/alerts/alert_123456/explanation
```

---

## 4. Dashboard Access

Navigate to: `http://localhost:3000/ids-threats`

**You'll see:**
- 📊 4 KPI cards (flows, threats, detection rate, open alerts)
- 📈 Threat timeline chart
- 📋 Active alerts list
- 🎯 Alert details with explanations
- ⚙️ Model status monitoring
- 🥧 Threat distribution pie chart

---

## Key Endpoints Cheat Sheet

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/ids/detect` | POST | Analyze flow for threats |
| `/ids/alerts` | GET | List all alerts |
| `/ids/alerts/:id` | GET | Alert details |
| `/ids/alerts/:id/explanation` | GET | SHAP/LIME explanation |
| `/ids/alerts/:id/investigate` | POST | Update alert status |
| `/ids/models/status` | GET | Model health |
| `/ids/metrics` | GET | System metrics |
| `/ids/health` | GET | Engine health |

---

## Common Tasks

### Generate Sample Alert
```python
from ids_engine import AIIntrusionDetectionEngine, create_network_flow

engine = AIIntrusionDetectionEngine()

flow = create_network_flow(
    src_ip="10.0.0.1",
    dst_ip="8.8.8.8",
    src_port=45123,
    dst_port=53,
    protocol="udp",
    duration_sec=0.5,
    packet_count=10,
    byte_count=2000,
    dpi_app="DNS",
    dpi_category="legitimate"
)

threat_detected, alert, info = engine.detect_threats(flow)
if threat_detected:
    print(f"Alert: {alert.alert_id}")
    print(f"Score: {alert.threat_score:.2%}")
```

### Get Alerts from Dashboard
```bash
# List HIGH/CRITICAL threats
curl "http://localhost:8000/ids/alerts?threat_level=high&limit=50"

# Filter by status
curl "http://localhost:8000/ids/alerts?status=open&limit=20"

# Sort and limit
curl "http://localhost:8000/ids/alerts?limit=10&offset=0"
```

### Check Model Performance
```bash
curl http://localhost:8000/ids/models/status
```

Output shows:
- Model accuracy (target: >0.92)
- AUC-ROC score (target: >0.95)
- Drift score (red if >0.5)
- Retraining needed flag

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| 404 on `/ids/health` | Ensure API routes registered in `main.py` |
| Slow responses (>200ms) | Check CPU usage, enable GPU if available |
| Dashboard blank | Check browser console for errors, verify API running |
| No alerts appearing | Test `/ids/detect` endpoint directly |
| Models not loading | Check `/backend/ids_engine.py` imports |

---

## Next Steps

1. ✅ **Now running:** Core IDS with 4 ML models
2. 📊 **Dashboard:** Real-time alert visualization
3. 🔗 **Integration:** Connect to DPI, Firewall, Telemetry (see `IDS_IMPLEMENTATION_COMPLETE.md`)
4. 🚀 **Deploy:** Production monitoring and alerting

---

## Architecture

```
Flow → /ids/detect → Ensemble (4 Models) → Alert → Dashboard
         ↓              ↓
      Database      Explanations
         ↓              ↓
    /ids/alerts ← /ids/alerts/:id/explanation
```

---

## Performance Target

- **Latency:** <100ms per flow
- **Throughput:** >1000 flows/sec
- **Accuracy:** >92% on known threats
- **False Positive Rate:** <5%

---

## Support

For detailed architecture, see: `IDS_IMPLEMENTATION_COMPLETE.md`  
For API docs, see: OpenAPI endpoints at `http://localhost:8000/docs`

---

**Status:** ✅ READY TO USE
