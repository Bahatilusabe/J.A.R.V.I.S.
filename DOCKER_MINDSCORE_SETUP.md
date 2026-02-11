# Docker + MindSpore Setup Guide
**Date**: December 15, 2025

## Prerequisites

### Step 1: Install Docker Desktop for macOS

**Option A: Using Homebrew (Recommended)**
```bash
brew install --cask docker
```

**Option B: Download Directly**
Visit: https://www.docker.com/products/docker-desktop

**After Installation:**
```bash
# Verify Docker installation
docker --version
# Output: Docker version XX.XX.XX, build XXXXX
```

---

## Setup MindSpore with Docker

### Step 1: Pull MindSpore Image

```bash
# Pull the official MindSpore CPU image
docker pull mindspore/mindspore:latest-cpu

# Verify image is downloaded
docker images | grep mindspore
```

### Step 2: Option A - Interactive Shell

```bash
# Run MindSpore in interactive mode
docker run -it mindspore/mindspore:latest-cpu python3

# Inside container:
>>> import mindspore
>>> print(f"MindSpore Version: {mindspore.__version__}")
>>> exit()
```

### Step 3: Option B - Mount Your App

```bash
# Run MindSpore with your app directory mounted
docker run -v $(pwd):/app mindspore/mindspore:latest-cpu \
  python3 -c "import mindspore; print('MindSpore Ready')"
```

---

## Production Deployment Configuration

### Dockerfile for Your PQC System

Create `deployment/docker/Dockerfile.mindscore`:

```dockerfile
FROM mindspore/mindspore:latest-cpu

# Install additional dependencies
RUN pip install --no-cache-dir \
    fastapi==0.95.2 \
    uvicorn==0.22.0 \
    liboqs-python>=0.7.2 \
    cryptography>=41.0.0

# Copy your app
WORKDIR /app
COPY . /app

# Install PQC requirements
RUN pip install --no-cache-dir -r backend/requirements.txt

# Expose port
EXPOSE 8000

# Run your app
CMD ["uvicorn", "backend.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose Configuration

Create `docker-compose.mindscore.yml`:

```yaml
version: '3.8'

services:
  mindscore-app:
    build:
      context: .
      dockerfile: deployment/docker/Dockerfile.mindscore
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - PYTHONUNBUFFERED=1
      - PQC_SK_B64=${PQC_SK_B64}
      - PQC_PK_B64=${PQC_PK_B64}
      - API_HMAC_KEY=${API_HMAC_KEY}
    command: uvicorn backend.api.server:app --host 0.0.0.0 --port 8000 --reload

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: jarvis
      POSTGRES_PASSWORD: jarvis_secure
      POSTGRES_DB: jarvis_pqc
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  redis-data:
  postgres-data:
```

---

## Quick Start Commands

### Build and Run

```bash
# Build the MindSpore image
docker build -f deployment/docker/Dockerfile.mindscore -t jarvis:mindscore .

# Run the container
docker run -p 8000:8000 \
  -e PQC_SK_B64=${PQC_SK_B64} \
  -e PQC_PK_B64=${PQC_PK_B64} \
  -e API_HMAC_KEY=${API_HMAC_KEY} \
  jarvis:mindscore

# Or use Docker Compose
docker-compose -f docker-compose.mindscore.yml up --build
```

### Verify MindSpore in Container

```bash
# Enter container shell
docker run -it mindspore/mindspore:latest-cpu /bin/bash

# Inside container, verify installation
python3 << 'PYEOF'
import mindspore
import mindspore.nn as nn
from mindspore import ops

print(f"✅ MindSpore Version: {mindspore.__version__}")
print(f"✅ Backend: {mindspore.get_context('device_target')}")

# Test basic operations
x = mindspore.Tensor([1, 2, 3])
print(f"✅ Tensor ops working: {x}")

PYEOF
```

---

## Integration with Your PQC System

### Update requirements.txt

Add to `backend/requirements.txt`:

```python
# ML & AI Framework (Docker-based)
# Note: On Docker, MindSpore is included in mindspore/mindspore:latest-cpu image
# mindspore>=2.0.0  # Provided by Docker image, uncomment for local Linux

# For local Linux installations only:
# pip install mindspore>=2.0.0
```

### Update Makefile

Add Docker targets to `Makefile`:

```makefile
# Docker targets for MindSpore
.PHONY: build-mindscore run-mindscore docker-mindscore

build-mindscore:
	docker build -f deployment/docker/Dockerfile.mindscore -t jarvis:mindscore .

run-mindscore:
	docker-compose -f docker-compose.mindscore.yml up --build

docker-mindscore:
	docker run -it mindspore/mindspore:latest-cpu python3

# Test MindSpore in container
test-mindscore:
	docker run mindspore/mindspore:latest-cpu python3 -c \
		"import mindspore; print('✅ MindSpore Ready')"
```

---

## Troubleshooting

### Issue: Docker daemon not running

**Solution:**
```bash
# Start Docker Desktop (macOS)
open -a Docker

# Or use command line
docker version  # This will start Docker if not running
```

### Issue: MindSpore import fails in container

**Solution:**
```bash
# Pull latest image
docker pull mindspore/mindspore:latest-cpu

# Verify image
docker run mindspore/mindspore:latest-cpu python3 -c \
  "import mindspore; print(mindspore.__version__)"
```

### Issue: Permission denied while building

**Solution:**
```bash
# Ensure Docker has permissions
sudo chown -R $(id -u):$(id -g) ~/.docker

# Or run with proper permissions
docker build --rm -f Dockerfile.mindscore -t jarvis:mindscore .
```

---

## Performance Comparison

| Method | Startup | Performance | Portability |
|--------|---------|-------------|------------|
| **Docker (CPU)** | ~5s | Baseline | 100% ✅ |
| **Docker (GPU)** | ~8s | 5-10x faster | 95% ⚠️ |
| **Conda local** | ~2s | Baseline | 80% (macOS) |
| **PyTorch alt** | ~1s | Similar | 100% ✅ |

---

## Next Steps

1. **Install Docker Desktop**: https://www.docker.com/products/docker-desktop
2. **Pull MindSpore image**: `docker pull mindspore/mindspore:latest-cpu`
3. **Test MindSpore**: `docker run -it mindspore/mindspore:latest-cpu python3`
4. **Build your image**: `docker build -f deployment/docker/Dockerfile.mindscore -t jarvis:mindscore .`
5. **Deploy**: `docker-compose -f docker-compose.mindscore.yml up`

---

## References

- **Docker Desktop**: https://www.docker.com/products/docker-desktop
- **MindSpore Docker**: https://hub.docker.com/r/mindspore/mindspore
- **Docker Compose**: https://docs.docker.com/compose/
- **MindSpore Installation**: https://www.mindspore.cn/install

---

**Status**: ✅ Ready to implement
**Recommendation**: Use Docker for production deployment
**Time to setup**: ~15 minutes (including Docker installation)

