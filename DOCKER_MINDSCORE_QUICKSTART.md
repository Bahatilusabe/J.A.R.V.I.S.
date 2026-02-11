# Docker + MindSpore Quick Start Guide

**December 15, 2025**

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Docker Desktop

**macOS (Recommended via Homebrew):**

```bash
brew install --cask docker
```

**Or download directly:**
Visit https://www.docker.com/products/docker-desktop

### Step 2: Verify Docker Installation

```bash
docker --version
# Output: Docker version 24.x.x, build xxxxx

docker run hello-world
# Output: Hello from Docker!
```

### Step 3: Test MindSpore Image

```bash
# Pull MindSpore CPU image
docker pull mindspore/mindspore:latest-cpu

# Test it
docker run -it mindspore/mindspore:latest-cpu python3 -c "import mindspore; print(f'✅ MindSpore {mindspore.__version__}')"
```

### Step 4: Build and Run Your App

```bash
# Navigate to your project directory
cd /Users/mac/Desktop/J.A.R.V.I.S.

# Method A: Using Make (Recommended)
make docker-up

# Method B: Direct Docker Compose
docker-compose -f docker-compose.mindscore.yml up --build
```

### Step 5: Verify Everything is Running

```bash
# Check if containers are running
docker-compose -f docker-compose.mindscore.yml ps

# View logs
docker-compose -f docker-compose.mindscore.yml logs -f mindscore-app

# Test API endpoint
curl http://localhost:8000/api/pqc/health
# Expected response: {"status": "healthy"}
```

______________________________________________________________________

## 📋 Available Make Commands

```bash
# Build Docker image
make docker-mindscore

# Start all services
make docker-up

# Stop all services
make docker-down

# View logs
make docker-logs

# Test MindSpore
make docker-test-mindscore

# Open container shell
make docker-shell

# Clean up everything
make docker-clean
```

______________________________________________________________________

## 🔧 Configuration

### 1. Create Environment File

```bash
cp .env.docker.template .env.docker
```

### 2. Edit `.env.docker` with Your Settings

```bash
# Required: Set your PQC keys
PQC_SK_B64=your_secret_key_base64
PQC_PK_B64=your_public_key_base64
API_HMAC_KEY=your_hmac_key

# Optional: Database credentials
POSTGRES_PASSWORD=your_secure_password
REDIS_PASSWORD=your_redis_password
```

### 3. Load Environment in Docker

```bash
# Use the env file
docker-compose -f docker-compose.mindscore.yml --env-file .env.docker up
```

______________________________________________________________________

## 🌐 Accessing Services

Once running, access these URLs:

| Service | URL | Purpose |
|---------|-----|---------|
| **API** | http://localhost:8000 | PQC API server |
| **Health** | http://localhost:8000/api/health | Server health check |
| **PQC Keys** | http://localhost:8000/api/pqc/keys | Get PQC public keys |
| **pgAdmin** | http://localhost:5050 | Database management (if enabled) |
| **Redis** | localhost:6379 | Session storage |
| **PostgreSQL** | localhost:5432 | Main database |

______________________________________________________________________

## 🐛 Troubleshooting

### Docker not found?

```bash
# Install Docker Desktop
brew install --cask docker

# Start Docker daemon
open -a Docker
```

### Port already in use?

```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port in docker-compose.mindscore.yml
```

### MindSpore import fails?

```bash
# Re-pull the image
docker pull mindspore/mindspore:latest-cpu

# Rebuild your image
docker build -f deployment/docker/Dockerfile.mindscore -t jarvis:mindscore .
```

### Containers won't start?

```bash
# View detailed error logs
docker-compose -f docker-compose.mindscore.yml logs mindscore-app

# Check if ports are available
netstat -tuln | grep -E '6379|5432|8000|5050'

# Remove and recreate containers
docker-compose -f docker-compose.mindscore.yml down -v
docker-compose -f docker-compose.mindscore.yml up --build
```

______________________________________________________________________

## 📊 Health Checks

### Verify All Services are Healthy

```bash
# Check container status
docker-compose -f docker-compose.mindscore.yml ps

# Test API health
curl -s http://localhost:8000/api/health | jq .

# Test PQC system
curl -s http://localhost:8000/api/pqc/keys | jq .

# Test Redis
docker exec jarvis-redis redis-cli ping
# Output: PONG

# Test PostgreSQL
docker exec jarvis-postgres psql -U jarvis -d jarvis_pqc -c "SELECT 1;"
```

______________________________________________________________________

## 🧪 Testing MindSpore Integration

### Run MindSpore Tests in Container

```bash
# Open container shell
make docker-shell

# Inside the container:
python3 << 'EOF'
import mindspore
import mindspore.nn as nn
from mindspore import Tensor, ops

print(f"✅ MindSpore {mindspore.__version__}")

# Test tensor operations
x = Tensor([1, 2, 3])
print(f"✅ Tensor: {x}")

# Test neural network
class Network(nn.Cell):
    def __init__(self):
        super().__init__()
        self.dense = nn.Dense(10, 5)
    
    def construct(self, x):
        return self.dense(x)

net = Network()
print(f"✅ Neural Network: {net}")
EOF
```

______________________________________________________________________

## 📦 Deployment

### For Production

```bash
# Build optimized image
docker build -f deployment/docker/Dockerfile.mindscore \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  -t jarvis:mindscore:v1.0 .

# Push to registry (optional)
docker tag jarvis:mindscore:v1.0 your-registry/jarvis:v1.0
docker push your-registry/jarvis:v1.0

# Use in production
docker run -p 8000:8000 \
  --env-file .env.docker \
  your-registry/jarvis:v1.0
```

### Using Kubernetes

```bash
# Deploy to Kubernetes
kubectl apply -f deployment/kubernetes/jarvis-mindscore-deployment.yaml

# Check status
kubectl get pods -l app=jarvis-mindscore
```

______________________________________________________________________

## 🔐 Security Best Practices

### 1. Don't Commit `.env.docker`

```bash
echo ".env.docker" >> .gitignore
```

### 2. Use Secret Management in Production

```yaml
# Use Kubernetes Secrets or AWS Secrets Manager
apiVersion: v1
kind: Secret
metadata:
  name: jarvis-pqc-secrets
type: Opaque
stringData:
  PQC_SK_B64: <your-secret>
  API_HMAC_KEY: <your-key>
```

### 3. Set Strong Passwords

```bash
# In .env.docker
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
```

### 4. Enable mTLS (Optional)

```bash
# In .env.docker
JARVIS_MTLS_REQUIRED=true
JARVIS_MTLS_ALLOWED_FINGERPRINTS=cert-fingerprint-1,cert-fingerprint-2
```

______________________________________________________________________

## 📈 Monitoring & Logs

### View Real-time Logs

```bash
# All services
docker-compose -f docker-compose.mindscore.yml logs -f

# Specific service
docker-compose -f docker-compose.mindscore.yml logs -f mindscore-app

# Last 100 lines
docker-compose -f docker-compose.mindscore.yml logs --tail=100
```

### Monitor Container Stats

```bash
# CPU/Memory usage
docker stats

# Specific container
docker stats jarvis-mindscore
```

______________________________________________________________________

## 🧹 Cleanup

### Remove All Containers and Data

```bash
# Stop and remove containers
make docker-down

# Remove volumes (data will be deleted)
docker-compose -f docker-compose.mindscore.yml down -v

# Remove image
docker image rm jarvis:mindscore

# Clean up system
docker system prune -a --volumes
```

______________________________________________________________________

## 📚 Additional Resources

- **Docker Docs**: https://docs.docker.com/
- **Docker Compose**: https://docs.docker.com/compose/
- **MindSpore Docker Hub**: https://hub.docker.com/r/mindspore/mindspore
- **MindSpore Docs**: https://www.mindspore.cn/en
- **FastAPI Docs**: https://fastapi.tiangolo.com/

______________________________________________________________________

## ✅ Verification Checklist

- [ ] Docker Desktop installed and running
- [ ] MindSpore image pulled: `docker pull mindspore/mindspore:latest-cpu`
- [ ] `.env.docker` created and configured
- [ ] Services started: `make docker-up`
- [ ] API responding: `curl http://localhost:8000/api/health`
- [ ] PQC system working: `curl http://localhost:8000/api/pqc/keys`
- [ ] Redis connected: `docker exec jarvis-redis redis-cli ping`
- [ ] PostgreSQL working: `docker exec jarvis-postgres psql -U jarvis -d jarvis_pqc -c "SELECT 1;"`

______________________________________________________________________

**Status**: ✅ Ready for deployment
**Last Updated**: December 15, 2025
**Version**: 1.0
