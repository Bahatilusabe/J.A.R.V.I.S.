# DPI Engine - Quick Reference

## 🎯 Essential Commands

### Start DPI Engine
```bash
cd /Users/mac/Desktop/J.A.R.V.I.S./backend
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Check Health
```bash
curl http://localhost:8000/dpi/health
```

### Get Statistics
```bash
curl http://localhost:8000/dpi/statistics | jq
```

### Get Recent Alerts
```bash
curl http://localhost:8000/dpi/alerts?max_alerts=100
```

---

## 🐍 Python API Cheat Sheet

### Initialize Engine
```python
from backend.dpi_engine_py import DPIEngine

engine = DPIEngine()
```

### Add Rule
```python
rule_id = engine.add_rule(
    name="SQL Injection",
    pattern=r"(?i)(union.*select|insert|delete)",
    severity="CRITICAL",
    protocol="HTTP"
)
```

### Process Packet
```python
alerts = engine.process_packet(
    src_ip="192.168.1.100",
    dst_ip="8.8.8.8",
    src_port=54321,
    dst_port=443,
    protocol=6,
    packet_data=b"<packet_bytes>",
    timestamp_ns=int(time.time() * 1e9)
)
```

### Get Statistics
```python
stats = engine.get_stats()
print(f"Packets: {stats.packets_processed:,}")
print(f"Alerts: {stats.alerts_generated:,}")
```

### Classify Protocol
```python
proto = engine.classify_protocol(
    src_ip="192.168.1.100",
    dst_ip="8.8.8.8",
    src_port=54321,
    dst_port=443,
    protocol=6
)
print(f"Protocol: {proto.protocol.name} ({proto.confidence}%)")
```

---

## 🌐 REST API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/dpi/process/packet` | POST | Process a packet |
| `/dpi/rules/add` | POST | Add detection rule |
| `/dpi/rules/{rule_id}` | DELETE | Remove rule |
| `/dpi/alerts` | GET | Get alert queue |
| `/dpi/classify/protocol` | POST | Classify protocol |
| `/dpi/tls/mode` | POST | Set TLS mode |
| `/dpi/statistics` | GET | Engine statistics |
| `/dpi/session/terminate` | POST | Terminate flow |
| `/dpi/health` | GET | Health check |

---

## 🎨 Protocol Detection

### Detected Protocols
- HTTP (port 80, 8080, 8888)
- HTTPS (port 443, 8443)
- DNS (port 53)
- SMTP (port 25, 587)
- SMB (port 445)
- FTP (port 21)
- SSH (port 22)
- TELNET (port 23)
- SNMP (port 161)
- QUIC (port 443, 80)
- DTLS (port 443)
- MQTT (port 1883, 8883)
- COAP (port 5683)

---

## 🚨 Alert Severity Levels

| Level | Color | Meaning |
|-------|-------|---------|
| INFO | Blue | Informational |
| WARNING | Yellow | Potential issue |
| CRITICAL | Red | Security threat |
| MALWARE | Dark Red | Malware detected |
| ANOMALY | Orange | Unusual behavior |

---

## 📊 Rule Types

| Type | Example | Use Case |
|------|---------|----------|
| REGEX | `(?i)union.*select` | Pattern matching |
| SNORT | Snort rule format | Complex patterns |
| YARA | YARA rule | Malware detection |
| CONTENT | Hex signatures | Binary matching |
| BEHAVIORAL | Custom logic | Complex detection |

---

## ⚙️ Configuration Quick Reference

### Enable/Disable Features
```python
config = {
    'enable_anomaly_detection': True,
    'enable_malware_detection': True,
}
```

### Set TLS Mode
```python
config = {
    'tls_mode': 'PASSTHROUGH',  # DISABLED, PASSTHROUGH, INSPECT, DECRYPT
}
```

### Adjust Memory
```python
config = {
    'max_concurrent_sessions': 100000,
    'memory_limit_mb': 1024,
}
```

---

## 🔍 Common Use Cases

### 1. Detect SQL Injection
```python
engine.add_rule(
    name="SQL Injection",
    pattern=r"(?i)(union.*select|insert.*values|delete.*where)",
    severity="CRITICAL",
    protocol="HTTP"
)
```

### 2. Monitor DNS Exfiltration
```python
engine.add_rule(
    name="DNS Data Exfil",
    pattern=r"([a-z0-9]){50,}\.(com|net|org)",
    severity="CRITICAL",
    protocol="DNS"
)
```

### 3. Detect Weak TLS
```python
engine.add_rule(
    name="Weak TLS Cipher",
    pattern=r"(NULL|EXPORT|DES|RC4|MD5)",
    severity="WARNING",
    protocol="HTTPS"
)
```

### 4. Monitor SMB Lateral Movement
```python
engine.add_rule(
    name="SMB Lateral Move",
    pattern=r"(IPC\$|ADMIN\$|C\$)",
    severity="CRITICAL",
    protocol="SMB"
)
```

### 5. Detect Command Injection
```python
engine.add_rule(
    name="Command Injection",
    pattern=r"[&|;`$()]|exec\(|system\(",
    severity="CRITICAL",
    protocol="HTTP"
)
```

---

## 🐛 Quick Debugging

### Check if Engine is Running
```bash
curl -s http://localhost:8000/dpi/health | jq .status
```

### View Active Sessions
```bash
curl -s http://localhost:8000/dpi/statistics | jq .active_sessions
```

### Get Last 10 Alerts
```bash
curl -s http://localhost:8000/dpi/alerts?max_alerts=10 | jq '.alerts[-10:]'
```

### Test Rule Pattern
```bash
python3 << 'EOF'
import re

pattern = r"(?i)(union.*select)"
test_string = "SELECT * FROM users UNION SELECT * FROM admins"

if re.search(pattern, test_string):
    print("✓ Pattern matched")
else:
    print("✗ Pattern did not match")
EOF
```

---

## 📈 Performance Tips

- **High throughput**: Increase `worker_threads` and `buffer_size_mb`
- **Low memory**: Reduce `max_concurrent_sessions` and `reassembly_timeout_sec`
- **Many rules**: Use rule categories and port filtering
- **CPU intensive**: Enable eBPF/XDP offloading

---

## 🔗 Documentation Links

- Full Documentation: [DPI_ENGINE.md](DPI_ENGINE.md)
- Deployment Guide: [DPI_DEPLOYMENT_GUIDE.md](DPI_DEPLOYMENT_GUIDE.md)
- API Reference: [API_reference.md](API_reference.md)
- Network Security: [PACKET_CAPTURE.md](PACKET_CAPTURE.md)

---

**Last Updated**: December 9, 2024
