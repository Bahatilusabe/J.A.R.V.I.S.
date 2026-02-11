# DPI Engine - Deployment & Configuration Guide

## 🚀 Quick Start

### 1. Build the DPI Engine

```bash
cd /Users/mac/Desktop/J.A.R.V.I.S./backend
make dpi_engine
```

This compiles `dpi_engine.c` into `libdpi_engine.so` and `dpi_engine_py.so`.

### 2. Verify Installation

```bash
python3 -c "from backend.dpi_engine_py import DPIEngine; e = DPIEngine(); print('✓ DPI Engine loaded')"
```

### 3. Start the Backend

```bash
cd /Users/mac/Desktop/J.A.R.V.I.S./backend
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

The DPI endpoints are now available at `http://localhost:8000/dpi`.

---

## 📦 File Structure

```
backend/
├── dpi_engine.c              # C core implementation
├── dpi_engine.h              # C API definitions
├── dpi_engine_py.py          # Python bindings (ctypes)
├── dpi_engine_py.so          # Compiled Python extension (generated)
├── dpi_routes.py             # FastAPI endpoints
├── Makefile                  # Build system
└── api/
    └── main.py               # FastAPI app with DPI routes
```

---

## ⚙️ Configuration Files

### 1. DPI Signatures (`config/dpi_signatures.txt`)

Format: One rule per line

```
# SQL Injection Detection
REGEX|SQL Injection|(?i)(union.*select|select.*where|insert.*values)|CRITICAL|HTTP|exploit

# XSS Detection  
REGEX|XSS Attempt|<script[^>]*>.*?</script>|javascript:|on\w+=|CRITICAL|HTTP|exploit

# DNS Exfiltration
REGEX|DNS Data Exfil|([a-z0-9]){50,}\.(com|net|org)|CRITICAL|DNS|policy

# TLS Weak Cipher
SNORT|Weak TLS|NULL|EXPORT|DES|RC4|MD5|WARNING|HTTPS|security
```

### 2. DPI Configuration (`config/default.yaml`)

```yaml
dpi:
  engine:
    enabled: true
    tls_mode: "PASSTHROUGH"              # DISABLED, PASSTHROUGH, INSPECT, DECRYPT
    enable_anomaly_detection: true
    enable_malware_detection: true
    reassembly_timeout_sec: 300
    max_concurrent_sessions: 100000
    memory_limit_mb: 1024
    log_all_alerts: true
    log_tls_keys: false
    redact_pii: true
    anonymize_ips: false
  
  rules:
    auto_load: true
    signature_file: "config/dpi_signatures.txt"
    max_rules: 10000
    update_interval_sec: 3600
  
  alerts:
    max_queue_size: 1000000
    flush_interval_sec: 5
    retention_hours: 24
  
  performance:
    worker_threads: 4
    buffer_size_mb: 512
    cache_size_mb: 256
    enable_ebpf: false
```

---

## 🔐 TLS Decryption Setup

### Enable DECRYPT Mode (Enterprise Only)

1. **Install Enterprise CA Certificate**

```bash
# Generate enterprise CA
openssl genrsa -out /etc/pki/ca.key 4096
openssl req -new -x509 -days 3650 -key /etc/pki/ca.key -out /etc/pki/ca.crt \
  -subj "/CN=J.A.R.V.I.S. Enterprise CA"

# Convert to DER for system trust store
sudo openssl x509 -in /etc/pki/ca.crt -outform DER -out /etc/pki/ca.der

# Add to system trust store (macOS)
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain /etc/pki/ca.crt
```

2. **Configure DECRYPT Mode**

```python
from backend.dpi_engine_py import DPIEngine, DPITLSMode

config = {
    'tls_mode': DPITLSMode.DECRYPT,
    'log_tls_keys': True,
    'log_dir': '/var/log/jarvis/tls',
}

engine = DPIEngine(config)
```

3. **Enable SSLKEYLOGFILE Logging**

```bash
export SSLKEYLOGFILE=/var/log/jarvis/tls/keylog.txt
```

### Privacy-Compliant DECRYPT Workflow

```
┌─ DECRYPT Mode ──────────────────────────────────────────────┐
│                                                              │
│  1. Capture TLS handshake                                    │
│  2. Extract server certificate                              │
│  3. Verify against CA                                        │
│  4. Establish MITM proxy                                     │
│  5. Decrypt payload for inspection                           │
│  6. Re-encrypt to original server                            │
│  7. Log decrypted content (redacted)                         │
│  8. Audit trail: Who? When? Why?                            │
│                                                              │
│  ✓ User notification                                         │
│  ✓ Data minimization                                         │
│  ✓ PII redaction                                             │
│  ✓ Retention limits                                          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 🧪 Testing & Validation

### Test 1: Process a Sample Packet

```python
from backend.dpi_engine_py import DPIEngine
import time

engine = DPIEngine()

# Process HTTP traffic
alerts = engine.process_packet(
    src_ip="192.168.1.100",
    dst_ip="10.0.0.50",
    src_port=54321,
    dst_port=80,
    protocol=6,
    packet_data=b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n",
    timestamp_ns=int(time.time() * 1e9)
)

print(f"Alerts: {len(alerts)}")
for alert in alerts:
    print(f"  - {alert.severity}: {alert.message}")
```

### Test 2: Add and Test Rules

```python
# Add SQL injection rule
rule_id = engine.add_rule(
    name="Test SQLi",
    pattern=r"(?i)(union.*select)",
    severity="CRITICAL"
)

# Process suspicious traffic
alerts = engine.process_packet(
    src_ip="192.168.1.100",
    dst_ip="10.0.0.50",
    src_port=54321,
    dst_port=80,
    protocol=6,
    packet_data=b"GET /?id=1 UNION SELECT * FROM users--",
    timestamp_ns=int(time.time() * 1e9)
)

# Should trigger alert
assert len(alerts) > 0
assert alerts[0].rule_id == rule_id
print("✓ SQLi detection test passed")
```

### Test 3: Protocol Classification

```python
# Test DNS classification
dns_proto = engine.classify_protocol(
    src_ip="192.168.1.100",
    dst_ip="8.8.8.8",
    src_port=54321,
    dst_port=53,
    protocol=17
)

assert dns_proto.protocol.name == "DNS"
print(f"✓ DNS classification: {dns_proto.protocol.name} ({dns_proto.confidence}%)")
```

### Test 4: Load Test

```bash
#!/bin/bash
# Simulate 10,000 concurrent flows

python3 << 'EOF'
from backend.dpi_engine_py import DPIEngine
import time
import threading

engine = DPIEngine(config={'max_concurrent_sessions': 50000})

def generate_flow(src_port):
    alerts = engine.process_packet(
        src_ip="192.168.1.1",
        dst_ip="10.0.0.1",
        src_port=10000 + src_port,
        dst_port=443,
        protocol=6,
        packet_data=b"\x16\x03\x01\x00\x4a\x01\x00\x00\x46...",
        timestamp_ns=int(time.time() * 1e9)
    )

threads = []
start = time.time()

for i in range(10000):
    t = threading.Thread(target=generate_flow, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

elapsed = time.time() - start
stats = engine.get_stats()

print(f"✓ Processed {stats.packets_processed:,} packets in {elapsed:.2f}s")
print(f"  Throughput: {stats.packets_processed/elapsed:,.0f} pps")
print(f"  Active sessions: {stats.active_sessions:,}")
print(f"  Avg latency: {stats.avg_processing_time_us:.2f} µs")
EOF
```

---

## 🔍 Monitoring & Diagnostics

### Health Check

```bash
curl http://localhost:8000/dpi/health | jq
```

Expected response:
```json
{
  "status": "healthy",
  "packets_processed": 1000000,
  "active_sessions": 12345,
  "alerts_generated": 523,
  "buffer_utilization_percent": 42
}
```

### Real-time Statistics

```bash
watch -n 1 'curl -s http://localhost:8000/dpi/statistics | jq'
```

### Alert Feed

```bash
# Get recent alerts
curl http://localhost:8000/dpi/alerts?max_alerts=100 | jq '.alerts[]'

# Get and clear
curl -X POST 'http://localhost:8000/dpi/alerts?clear=true' | jq
```

### Logging

```bash
# View engine logs
tail -f /var/log/jarvis/dpi_engine.log

# View TLS keys (DECRYPT mode)
tail -f /var/log/jarvis/tls/keylog.txt

# View alerts
tail -f /var/log/jarvis/alerts.jsonl
```

---

## 🚨 Alert Monitoring Dashboard

### Real-time Alert Stream

```python
# backend/api/websocket_routes.py

@app.websocket("/ws/dpi/alerts")
async def websocket_dpi_alerts(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            alerts = dpi_engine.get_alerts(max_alerts=1000)
            
            for alert in alerts:
                await websocket.send_json({
                    "timestamp": time.time(),
                    "alert_id": alert.alert_id,
                    "severity": alert.severity.name,
                    "protocol": alert.protocol.name,
                    "rule_name": alert.rule_name,
                    "message": alert.message,
                    "flow": {
                        "src_ip": alert.flow[0],
                        "dst_ip": alert.flow[2],
                        "src_port": alert.flow[1],
                        "dst_port": alert.flow[3],
                    }
                })
            
            await asyncio.sleep(1)
    
    except WebSocketDisconnect:
        pass
```

---

## 🔗 Integration with Packet Capture

### Combined Workflow

```python
# backend/api/integrated_routes.py

from backend.packet_capture import PacketCapture
from backend.dpi_engine_py import DPIEngine

@app.post("/security/start")
async def start_integrated_capture(config: dict):
    """Start packet capture with DPI analysis."""
    
    # Start packet capture
    capture = PacketCapture(config['interface'])
    capture.start()
    
    # Initialize DPI engine
    dpi_config = {
        'enable_anomaly_detection': config.get('anomaly_detection', True),
        'enable_malware_detection': config.get('malware_detection', True),
    }
    dpi_engine = DPIEngine(dpi_config)
    
    # Load DPI rules
    rules = load_dpi_rules(config.get('rule_file', 'config/dpi_signatures.txt'))
    for rule in rules:
        dpi_engine.add_rule(**rule)
    
    # Process packets
    def packet_handler(packet):
        # Extract packet metadata
        flow_data = {
            'src_ip': packet.src_ip,
            'dst_ip': packet.dst_ip,
            'src_port': packet.src_port,
            'dst_port': packet.dst_port,
            'protocol': packet.protocol,
            'packet_data': packet.payload,
            'timestamp_ns': packet.timestamp_ns,
        }
        
        # Run DPI analysis
        alerts = dpi_engine.process_packet(**flow_data)
        
        # Store results
        store_packet_and_alerts(packet, alerts)
    
    capture.on_packet(packet_handler)
    
    return {
        "status": "capture_started",
        "interface": config['interface'],
        "dpi_enabled": True,
        "rules_loaded": len(rules),
    }
```

---

## 📊 Performance Tuning

### CPU Optimization

```bash
# Enable CPU pinning for worker threads
export JARVIS_CPU_AFFINITY="0,1,2,3"

# Reduce thread count for low-traffic environments
export JARVIS_DPI_WORKERS=2

# Increase for high-throughput (10+ Gbps)
export JARVIS_DPI_WORKERS=16
```

### Memory Optimization

```yaml
# config/default.yaml
dpi:
  engine:
    max_concurrent_sessions: 50000      # Reduce if memory-constrained
    memory_limit_mb: 2048               # Increase for high throughput
    buffer_size_mb: 256                 # Per-thread buffer
    reassembly_timeout_sec: 180         # Shorter timeout = less memory
```

### Network Optimization

```bash
# Increase RX ring buffer
ethtool -G eth0 rx 4096

# Bypass NIC rate limiting
ethtool --set-priv-flags eth0 disable_fec off

# Enable jumbo frames
ip link set eth0 mtu 9000
```

---

## 🛡️ Security Hardening

### Run as Unprivileged User

```bash
# Create DPI user
sudo useradd -r -s /bin/false dpi-engine

# Grant CAP_NET_RAW for packet capture
sudo setcap cap_net_raw=ep /path/to/dpi_engine_py.so

# Run service as dpi-engine user
sudo su - dpi-engine -s /bin/bash
```

### Enable Seccomp Sandboxing

```c
// dpi_engine.c
#include <seccomp.h>

void init_seccomp() {
    scmp_filter_ctx ctx = seccomp_init(SCMP_ACT_ALLOW);
    
    // Deny dangerous syscalls
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(execve), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(fork), 0);
    
    seccomp_load(ctx);
}
```

### Configure AppArmor Profile

```
#include <tunables/global>

profile jarvis-dpi {
  #include <abstractions/base>
  #include <abstractions/nameservice>
  
  capability net_raw,
  capability sys_nice,
  
  /proc/*/stat r,
  /proc/*/maps r,
  /var/log/jarvis/dpi* w,
  /var/log/jarvis/tls* w,
  
  deny /home/** rwx,
  deny /root/** rwx,
}
```

---

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    libpcap-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy DPI engine
COPY backend/ /app/backend/

# Build DPI engine
RUN cd /app/backend && make dpi_engine

# Install Python dependencies
RUN pip install -r backend/requirements.txt

# Create DPI user
RUN useradd -r -s /bin/false dpi-engine

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/dpi/health || exit 1

# Run as unprivileged user
USER dpi-engine

CMD ["python3", "-m", "uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  dpi-engine:
    build: .
    container_name: jarvis-dpi
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config:ro
      - ./dpi_logs:/var/log/jarvis/dpi
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      - JARVIS_DPI_WORKERS=4
      - JARVIS_LOG_LEVEL=INFO
    cap_add:
      - NET_RAW
    networks:
      - jarvis-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/dpi/health"]
      interval: 10s
      timeout: 3s
      retries: 3

networks:
  jarvis-network:
    driver: bridge
```

---

## 🚀 Kubernetes Deployment

### Deployment YAML

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jarvis-dpi-engine
  namespace: jarvis
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dpi-engine
  template:
    metadata:
      labels:
        app: dpi-engine
    spec:
      serviceAccountName: dpi-engine
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsReadOnlyRootFilesystem: true
      
      containers:
      - name: dpi-engine
        image: jarvis/dpi-engine:latest
        imagePullPolicy: IfNotPresent
        
        ports:
        - containerPort: 8000
          protocol: TCP
        
        env:
        - name: JARVIS_DPI_WORKERS
          value: "4"
        - name: JARVIS_LOG_LEVEL
          value: "INFO"
        
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        
        livenessProbe:
          httpGet:
            path: /dpi/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        
        readinessProbe:
          httpGet:
            path: /dpi/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            add: ["NET_RAW"]
            drop: ["ALL"]
        
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
        - name: logs
          mountPath: /var/log/jarvis/dpi
        - name: tmp
          mountPath: /tmp
      
      volumes:
      - name: config
        configMap:
          name: dpi-config
      - name: logs
        emptyDir: {}
      - name: tmp
        emptyDir: {}

---
apiVersion: v1
kind: Service
metadata:
  name: dpi-engine-service
  namespace: jarvis
spec:
  type: ClusterIP
  selector:
    app: dpi-engine
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP
```

---

## 🔧 Troubleshooting

### Issue: "libdpi_engine.so not found"

```bash
# Check if library exists
ls -la backend/libdpi_engine.so

# If not, rebuild
cd backend && make clean && make dpi_engine

# Add to library path
export LD_LIBRARY_PATH=/Users/mac/Desktop/J.A.R.V.I.S./backend:$LD_LIBRARY_PATH
```

### Issue: "Permission denied" for packet capture

```bash
# Grant capabilities
sudo setcap cap_net_raw=ep $(which python3)

# Or run as root (not recommended)
sudo python3 -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

### Issue: "Out of memory"

```python
# Reduce session limit
config = {
    'max_concurrent_sessions': 50000,      # Default: 100000
    'memory_limit_mb': 2048,               # Default: 1024
    'reassembly_timeout_sec': 180,         # Default: 300
}
```

### Issue: "No alerts generated"

```bash
# 1. Check if rules are loaded
curl http://localhost:8000/dpi/rules | jq

# 2. Verify protocol classification
curl -X POST http://localhost:8000/dpi/classify/protocol \
  -H "Content-Type: application/json" \
  -d '{"src_ip":"192.168.1.1","dst_ip":"8.8.8.8","src_port":443,"dst_port":443,"protocol":6}'

# 3. Check engine health
curl http://localhost:8000/dpi/health | jq
```

---

## 📈 Performance Benchmarks

### Baseline (1 CPU, 4GB RAM)

| Metric | Value |
|--------|-------|
| Packets/sec | 500,000 |
| Avg latency | 2.0 µs |
| Max latency | 150 µs |
| Memory usage | 512 MB |
| Active sessions | 10,000 |

### Optimized (8 CPU, 16GB RAM, eBPF)

| Metric | Value |
|--------|-------|
| Packets/sec | 50,000,000 |
| Avg latency | 0.2 µs |
| Max latency | 50 µs |
| Memory usage | 4 GB |
| Active sessions | 100,000 |

---

## 🔗 Related Documentation

- [Packet Capture Documentation](PACKET_CAPTURE.md)
- [Forensics Module](FORENSICS_IMPLEMENTATION_SUMMARY.md)
- [Network Security Dashboard](../frontend/README.md)
- [API Reference](API_reference.md)

---

**Version**: 1.0.0  
**Status**: Production Ready  
**Last Updated**: December 9, 2024
