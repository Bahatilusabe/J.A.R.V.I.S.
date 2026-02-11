# Next Steps & Advanced Operations

## 🎯 Immediate Actions (What You Can Do Now)

### 1. Explore the Dashboard
- Open http://127.0.0.1:5173 in your browser
- Login with the mobile authentication flow
- Navigate through all dashboard tabs
- Trigger DPI classification from the UI
- View policy decisions in real-time

### 2. Test API Endpoints Directly
Open http://127.0.0.1:8000/docs to access Swagger UI where you can:
- Test all 104 endpoints directly
- Provide request payloads
- See response schemas
- Explore data models

### 3. Monitor in Real-time
```bash
# Watch backend logs
tail -f backend.log

# Monitor frontend requests
# Open browser DevTools → Network tab
# See all API calls as they happen
```

### 4. Run Advanced Tests
```bash
# Load test the DPI endpoint
for i in {1..100}; do
  curl -s -X POST http://127.0.0.1:8000/api/dpi/classify/protocol \
    -H "Content-Type: application/json" \
    -d '{"src_ip":"192.168.1.'$i'","dst_port":443}' &
done
wait
echo "Load test complete"

# Benchmark all endpoints
python3 -m pytest test_e2e_with_auth.py -v --tb=line

# Audit entire system
python3 audit_path_mismatches.py
```

---

## 🔧 Configuration & Customization

### Change Backend Port
```bash
python3 -m uvicorn backend.api.server:app --host 127.0.0.1 --port 9000
```

### Change Frontend Port
```bash
cd frontend/web_dashboard
VITE_PORT=3000 npm run dev
```

### Update API Base URL in Frontend
Edit `/frontend/web_dashboard/src/services/*.service.ts`:
```typescript
// Change from:
const baseURL = "http://127.0.0.1:8000";
// To:
const baseURL = "https://api.example.com";
```

### Enable Real Ledger (Hyperledger Fabric)
Edit `backend/ledger_manager.py`:
```python
# Set up Fabric credentials
os.environ["FABRIC_CONFIG_PATH"] = "/path/to/fabric/config"
os.environ["FABRIC_USERNAME"] = "admin"
os.environ["FABRIC_PASSWORD"] = "password"
```

### Switch to Web3 (Ethereum)
Edit `backend/ledger_manager.py`:
```python
# Configure Web3 provider
os.environ["WEB3_PROVIDER"] = "https://mainnet.infura.io/v3/YOUR_KEY"
os.environ["SMART_CONTRACT_ADDRESS"] = "0x..."
```

---

## 📊 Performance Tuning

### Backend Optimization
```bash
# Run with multiple workers (production)
gunicorn backend.api.server:app \
  --workers 4 \
  --threads 2 \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Frontend Optimization
```bash
# Build for production
cd frontend/web_dashboard
npm run build

# Output is in dist/ folder
# Serve with: npx serve dist
```

### Database Optimization
```python
# In backend/ledger_manager.py
# Implement caching layer
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_forensics_record(txid):
    return _ledger_manager.retrieve_threat(txid)
```

---

## 🔐 Security Enhancements

### Enable HTTPS
```bash
# Generate self-signed cert
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Run with HTTPS
python3 -m uvicorn backend.api.server:app \
  --host 127.0.0.1 \
  --port 8443 \
  --ssl-keyfile=key.pem \
  --ssl-certfile=cert.pem
```

### Add Rate Limiting
```python
# In backend/api/server.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/dpi/classify/protocol")
@limiter.limit("100/minute")
async def classify_protocol(request: Request):
    # ... endpoint code
```

### Add Request Validation
```python
# Already implemented with Pydantic models
# All endpoints validate:
# - Request body schemas
# - Query parameter types
# - Header validation
# - Response schemas
```

---

## 🚀 Deployment Options

### Option 1: Docker Deployment
Create `Dockerfile` in project root:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ backend/
CMD ["python3", "-m", "uvicorn", "backend.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t jarvis-backend .
docker run -p 8000:8000 jarvis-backend
```

### Option 2: Kubernetes Deployment
Create `deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jarvis-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: jarvis-backend
  template:
    metadata:
      labels:
        app: jarvis-backend
    spec:
      containers:
      - name: jarvis-backend
        image: jarvis-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: LEDGER_MODE
          value: "fabric"
```

Deploy:
```bash
kubectl apply -f deployment.yaml
```

### Option 3: Cloud Deployment (AWS Lambda)
```bash
# Install serverless framework
npm install -g serverless

# Deploy FastAPI to Lambda
serverless deploy
```

---

## 📈 Monitoring & Logging

### Enable Detailed Logging
```python
# In backend/api/server.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

### Add Prometheus Metrics
```python
from prometheus_client import Counter, Histogram

endpoint_calls = Counter('endpoint_calls_total', 'Total endpoint calls')
endpoint_duration = Histogram('endpoint_duration_seconds', 'Endpoint duration')

@app.get("/api/dpi/classify/protocol")
def classify_protocol():
    endpoint_calls.inc()
    start = time.time()
    # ... your code
    endpoint_duration.observe(time.time() - start)
```

### Monitor with ELK Stack (Elasticsearch, Logstash, Kibana)
```bash
# Docker compose for monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

---

## 🧪 Advanced Testing

### Load Testing with Locust
Create `locustfile.py`:
```python
from locust import HttpUser, task, between

class JarvisUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def classify_protocol(self):
        self.client.post("/api/dpi/classify/protocol", json={
            "src_ip": "192.168.1.1",
            "dst_port": 443
        })
    
    @task
    def evaluate_policy(self):
        self.client.post("/api/policy/evaluate", json={
            "protocol": "HTTPS"
        })
```

Run load test:
```bash
locust -f locustfile.py --host=http://127.0.0.1:8000
```

### Security Testing with OWASP ZAP
```bash
docker run -t owasp/zap2docker-stable \
  zap-baseline.py -t http://127.0.0.1:8000
```

---

## 🔄 CI/CD Pipeline Setup

### GitHub Actions Workflow
Create `.github/workflows/test.yml`:
```yaml
name: Tests & Deploy

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          cd frontend/web_dashboard && npm install
      
      - name: Run tests
        run: |
          python3 test_frontend_backend_integration.py
          python3 test_e2e_with_auth.py
      
      - name: Build frontend
        run: |
          cd frontend/web_dashboard && npm run build
      
      - name: Deploy
        run: |
          # Your deployment script here
```

---

## 📚 Useful Commands Reference

### Backend Commands
```bash
# Start backend with auto-reload
python3 -m uvicorn backend.api.server:app --reload

# Check backend logs
tail -f backend.log

# Test backend connectivity
curl -s http://127.0.0.1:8000/health | jq .

# Get all endpoints
curl -s http://127.0.0.1:8000/openapi.json | jq '.paths | keys'
```

### Frontend Commands
```bash
# Start frontend
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Format code
npm run format

# Type check
npm run type-check
```

### Testing Commands
```bash
# Run all tests
python3 test_frontend_backend_integration.py
python3 test_e2e_with_auth.py

# Run with verbose output
python3 -m pytest test_*.py -v

# Run specific test
python3 -m pytest test_frontend_backend_integration.py::test_dpi_classification -v

# Generate coverage report
python3 -m pytest --cov=backend test_*.py
```

---

## 🎓 Learning Resources

### API Documentation
- **Interactive Docs**: http://127.0.0.1:8000/docs (Swagger UI)
- **ReDoc**: http://127.0.0.1:8000/redoc
- **OpenAPI Spec**: http://127.0.0.1:8000/openapi.json

### Code Documentation
- **Backend Structure**: `backend/` folder
- **Frontend Structure**: `frontend/web_dashboard/src/`
- **Test Examples**: `test_*.py` files

### External Resources
- FastAPI Docs: https://fastapi.tiangolo.com
- React Docs: https://react.dev
- Vite Docs: https://vitejs.dev
- Tailwind CSS: https://tailwindcss.com

---

## ✅ Verification Commands

Run these to verify system health:
```bash
# All should return green checkmarks
echo "Checking backend..."
curl -s http://127.0.0.1:8000/health && echo " ✅ Backend OK"

echo "Checking frontend port..."
lsof -i :5173 > /dev/null && echo "✅ Frontend OK" || echo "❌ Frontend not running"

echo "Running integration tests..."
python3 test_frontend_backend_integration.py | grep "Pass Rate"

echo "Running E2E tests..."
python3 test_e2e_with_auth.py | grep "Pass Rate"

echo "Auditing paths..."
python3 audit_path_mismatches.py | grep "match rate"
```

---

## 🆘 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend port in use | `lsof -i :8000` then `kill -9 <PID>` |
| Frontend not loading | Check `npm install` completed, port 5173 free |
| API returns 422 | Check request schema matches model in `backend/api/routes/` |
| CORS errors | Backend has CORS enabled for `http://localhost:5173` |
| Tests failing | Run `python3 audit_path_mismatches.py` to find path mismatches |
| Performance slow | Check backend logs, run load test with `locust` |

---

## 🎬 What's Next?

1. **Immediate**: Explore dashboard at http://127.0.0.1:5173
2. **Short-term**: Run load tests and performance benchmarks
3. **Medium-term**: Set up CI/CD pipeline with GitHub Actions
4. **Long-term**: Deploy to production (Docker/Kubernetes/AWS)

**System is fully operational and ready for advanced configurations!** 🚀

---

Updated: 2025-12-10 | Status: ✅ OPERATIONAL
