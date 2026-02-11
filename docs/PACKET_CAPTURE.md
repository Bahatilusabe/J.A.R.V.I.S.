# Networking & Traffic Handling Layer: Packet Capture & Flow Metering

## Architecture Overview

The J.A.R.V.I.S. Packet Capture & Flow Metering system provides high-performance network traffic collection and analysis with support for 10Gbps-400Gbps throughput depending on SKU and backend.

### Key Features

- **Zero-Copy Packet Capture**: DMA-capable ring buffers with pluggable backends (DPDK, XDP, PF_RING)
- **High-Precision Timestamping**: PTP/NTP synchronized timestamps (nanosecond precision)
- **Flow Metering & Aggregation**: 5-tuple flow tracking with configurable table size
- **NetFlow/IPFIX Export**: Real-time flow record export to collectors
- **At-Rest Encryption**: AES-256-GCM encryption for capture buffers
- **Firmware Integrity**: RSA signature verification for secure hardware access
- **Packet Loss Detection**: Real-time alerts for capture anomalies

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  (DPI Engine, Forensics, Analytics, Security Policies)     │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│           FastAPI REST Endpoints                            │
│  /packet_capture/start, /capture/metrics, /capture/flows   │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│         Python Bindings Layer (packet_capture_py.py)        │
│    Ctypes wrapper, callback handling, error management     │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│          C/C++ Core Engine (packet_capture.c)               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Ring Buffer Manager                                │   │
│  │  • Zero-copy DMA buffers                            │   │
│  │  • Packet serialization with metadata              │   │
│  │  • Thread-safe append operations                   │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Flow Table (Hash-based)                            │   │
│  │  • 5-tuple flow identification                      │   │
│  │  • Per-flow statistics (bytes, packets, flags)     │   │
│  │  • RW-lock protected concurrent access            │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Backend Selection & Abstraction                    │   │
│  │  • DPDK (Intel Data Plane Development Kit)         │   │
│  │  • XDP (Linux eBPF/AF_XDP kernel bypass)           │   │
│  │  • PF_RING (Kernel bypass)                         │   │
│  │  • libpcap (Fallback)                              │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│              Hardware & Kernel Layer                         │
│  • Network interfaces (1GE, 10GE, 100GE, 400GE)            │
│  • SPAN/ERSPAN traffic mirrors                             │
│  • PTP/NTP time synchronization                            │
│  • TPM for firmware integrity                              │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Ring Buffer (Zero-Copy)

**Purpose**: Lossless, high-throughput packet storage without copying

**Features**:
- DMA-capable memory mapping
- Wraparound protection
- Lock-free read/write operations (with mutual exclusion for safety)
- Optional at-rest encryption

**Configuration**:
```python
engine = PacketCaptureEngine(
    interface="eth0",
    buffer_size_mb=256,  # 256 MB ring buffer
    backend=CaptureBackend.XDP
)
```

### 2. Flow Table (5-Tuple Aggregation)

**Purpose**: Track active flows with per-flow statistics

**Data Structure**:
```c
FlowTuple = {
    src_ip,      // 32-bit IPv4
    dst_ip,      // 32-bit IPv4
    src_port,    // 16-bit
    dst_port,    // 16-bit
    protocol,    // TCP/UDP/ICMP
    vlan_id      // 16-bit
}

FlowRecord = {
    tuple,
    flow_id,               // FNV-1a hash of tuple
    first_packet_id,
    last_packet_id,
    first_seen_ns,
    last_seen_ns,
    packets,
    bytes,
    bytes_fwd / bytes_rev,
    tcp_flags,
    interface_id,
    state                  // ACTIVE/CLOSING/CLOSED
}
```

**Hash Function**: FNV-1a (deterministic)

**Lookup**: O(1) average case, uses linear probing for collisions

### 3. NetFlow/IPFIX Export

**Purpose**: Standardized flow data export for SOC/SIEM integration

**Flow Export Record**:
```c
NetFlowRecord = {
    flow,                  // FlowRecord
    nexthop_ipv4,
    src_as,               // Source AS number
    dst_as,               // Destination AS number
    src_mask,             // Netmask bits
    dst_mask,
    tcp_flags_final
}
```

**Export Modes**:
- Netflow v5 (deprecated, but widely supported)
- IPFIX (preferred for modern deployments)

### 4. Encryption Layer

**Purpose**: Protect captured packets at rest

**Supported Ciphers**:
- AES-256-GCM (recommended)
- AES-128-GCM
- ChaCha20-Poly1305

**Key Management**:
- External key file (encrypted with TPM if available)
- Per-interface key rotation
- Secure key derivation (PBKDF2)

### 5. Firmware Integrity

**Purpose**: Ensure only authorized firmware accesses capture hardware

**Verification**:
- RSA-4096 signature verification
- TPM-backed key storage
- Secure boot chain validation

## API Documentation

### REST Endpoints

#### Start Capture
```http
POST /packet_capture/capture/start
Content-Type: application/json

{
  "interface": "eth0",
  "backend": "xdp",
  "buffer_size_mb": 256,
  "timestamp_source": "ptp",
  "filter_expr": "tcp port 443",
  "snaplen": 0
}

Response:
{
  "status": "started",
  "interface": "eth0",
  "backend": "XDP",
  "buffer_size_mb": 256
}
```

#### Get Capture Metrics
```http
GET /packet_capture/capture/metrics

Response:
{
  "packets_captured": 1000000,
  "packets_dropped": 125,
  "bytes_captured": 567890123,
  "drop_rate": 0.0125,
  "active_flows": 45678,
  "total_flows": 123456,
  "throughput_mbps": 8945.67,
  "buffer_usage_pct": 67.89,
  "timestamp": 1733769000.123
}
```

#### Get Active Flows
```http
GET /packet_capture/capture/flows?limit=100&min_packets=10

Response:
[
  {
    "flow_id": 12345678,
    "src_ip": "192.168.1.100",
    "dst_ip": "10.0.0.50",
    "src_port": 54321,
    "dst_port": 443,
    "protocol": 6,
    "packets": 1234,
    "bytes": 2567890,
    "first_seen": 1733769000.123,
    "last_seen": 1733769045.678,
    "state": "ACTIVE",
    "duration_sec": 45.555
  },
  ...
]
```

#### Enable Flow Metering
```http
POST /packet_capture/capture/flow/meter/enable
Content-Type: application/json

{
  "table_size": 100000,
  "idle_timeout_sec": 300
}

Response:
{
  "status": "enabled",
  "table_size": 100000,
  "idle_timeout_sec": 300
}
```

#### Enable NetFlow Export
```http
POST /packet_capture/capture/netflow/export/enable
Content-Type: application/json

{
  "collector_ip": "10.0.0.100",
  "collector_port": 2055,
  "export_interval_sec": 60
}

Response:
{
  "status": "enabled",
  "collector_ip": "10.0.0.100",
  "collector_port": 2055,
  "export_interval_sec": 60
}
```

#### Enable Encryption
```http
POST /packet_capture/capture/encryption/enable
Content-Type: application/json

{
  "cipher_suite": "AES-256-GCM",
  "key_file": "/etc/jarvis/capture.key"
}

Response:
{
  "status": "enabled",
  "cipher_suite": "AES-256-GCM",
  "key_file": "/etc/jarvis/capture.key"
}
```

#### Stop Capture
```http
POST /packet_capture/capture/stop
Content-Type: application/json

{
  "graceful": true
}

Response:
{
  "status": "stopped",
  "final_metrics": {
    "packets_captured": 1000125,
    "packets_dropped": 125,
    "bytes_captured": 567890248,
    "drop_rate": 0.0125
  }
}
```

## Backend Comparison

### DPDK (Intel Data Plane Development Kit)

**Advantages**:
- Highest performance (400Gbps+)
- Battle-tested in telecom/cloud
- Comprehensive monitoring
- Excellent scalability

**Requirements**:
- CPU isolation (hugepages)
- Kernel bypass (kernel module loading)
- Specific NIC drivers
- License considerations

**Performance**: 400Gbps+

### XDP (Express Data Path)

**Advantages**:
- No kernel bypass needed
- Integrated with eBPF
- Minimal setup
- Good performance for most workloads

**Requirements**:
- Linux kernel 4.8+
- NIC driver support
- Clang/LLVM for eBPF compilation

**Performance**: 100-200 Gbps

### PF_RING

**Advantages**:
- Balanced approach
- Good performance
- Easier than DPDK
- Widely supported

**Requirements**:
- Kernel module
- Compatible NIC drivers

**Performance**: 50-100 Gbps

### libpcap (Fallback)

**Advantages**:
- Universal compatibility
- No special requirements
- Easy debugging
- Works with any interface

**Disadvantages**:
- Lower performance
- Kernel context switches
- Higher CPU usage

**Performance**: 1-10 Gbps

## Security Considerations

### 1. Capture Buffer Protection

```python
# Enable encryption
engine.enable_encryption(
    cipher_suite="AES-256-GCM",
    key_file="/etc/jarvis/capture.key"
)
```

**Implementation**:
- Ring buffer pages encrypted with AES-256-GCM
- Per-page GCM tags stored separately
- Key derivation from master key using PBKDF2

### 2. Firmware Integrity

```python
# Verify before capture starts
if capture_verify_firmware(
    "/usr/lib/packet_capture.so",
    "/usr/lib/packet_capture.so.sig"
) != 0:
    raise SecurityError("Firmware signature invalid")
```

### 3. Access Control

- Only privileged users (root or CAP_SYS_ADMIN) can:
  - Load capture drivers
  - Access capture buffers
  - Configure hardware interfaces

### 4. Audit Logging

All capture operations logged with:
- User/process ID
- Timestamp
- Interface
- Filter expression
- Encryption status

## Performance Tuning

### Buffer Sizing

```
Recommended sizes:
- Light traffic (<100 Mbps): 64 MB
- Medium traffic (100-500 Mbps): 256 MB
- Heavy traffic (500+ Mbps): 512 MB - 2GB
- High-speed links (10Gbps+): 2GB-8GB
```

### Flow Table Sizing

```
Flows to track | Table Size
< 1,000        | 4,096
1,000-10,000   | 65,536
10,000-100,000 | 1,048,576
> 100,000      | 16,777,216
```

### CPU Affinity

```bash
# Dedicate cores to capture engine
taskset -c 0-3 packet_capture_service
```

### NUMA Optimization

```bash
# For NUMA systems, pin to specific node
numactl --cpunodebind=0 --membind=0 packet_capture_service
```

## Integration with J.A.R.V.I.S.

### DPI Engine

```python
from backend.dpi import DPIEngine
from backend.packet_capture_py import PacketCaptureEngine

capture = PacketCaptureEngine(interface="eth0")
capture.start()

dpi = DPIEngine()

# Process captured flows through DPI
for flow in capture.get_flows():
    protocol = dpi.classify_flow(flow)
    print(f"Flow {flow.flow_id}: {protocol}")
```

### Forensics

```python
# Store captured packets for forensics
capture.enable_encryption()  # Encrypt at rest
capture.enable_netflow_export(
    collector_ip="forensics.example.com",
    collector_port=2055
)
```

### SOC/SIEM Integration

```python
# Export flows to SIEM
capture.enable_netflow_export(
    collector_ip="siem.example.com",
    collector_port=2055,
    export_interval_sec=30
)
```

## Building from Source

```bash
cd hardware_integration/packet_capture
./build.sh

# Check available backends
echo "Checking backends..."
ldd .build/libpacket_capture.so

# Run tests
./.build/test_packet_capture

# Install
sudo install -m 0755 .build/libpacket_capture.so /usr/local/lib/
sudo install -m 0644 packet_capture.h /usr/local/include/
```

## Limitations & Future Work

### Current Limitations

1. Single interface per session
2. Flow table collision handling via linear probing
3. NetFlow export without bidirectional tracking
4. No fragmented packet reassembly

### Planned Enhancements

1. Multi-interface support with aggregation
2. IPv6 support
3. Bidirectional flow tracking
4. Geo-location based flow classification
5. Machine learning anomaly detection
6. GPU-accelerated packet processing
7. Integration with sFlow (flow sampling)

## Troubleshooting

### Packet Loss

```bash
# Check metrics
curl http://localhost:8000/packet_capture/capture/metrics

# Common causes:
# - Buffer too small (increase buffer_size_mb)
# - CPU saturation (dedicate more cores)
# - NIC ring buffer overflow (check driver settings)
```

### No Flows Detected

```bash
# Verify capture is running
curl http://localhost:8000/packet_capture/capture/status

# Check filter expression
curl http://localhost:8000/packet_capture/capture/start \
  -d '{"interface":"eth0","filter_expr":"tcp"}'

# Verify interface has traffic
sudo tcpdump -i eth0 -c 10
```

### Performance Degradation

```bash
# Check throughput trend
while true; do
  curl http://localhost:8000/packet_capture/capture/metrics | \
    jq '.throughput_mbps, .buffer_usage_pct'
  sleep 5
done
```

## References

- [DPDK Programmer's Guide](https://doc.dpdk.org/)
- [Linux XDP Tutorial](https://github.com/xdp-project/xdp-tutorial)
- [NetFlow v5 RFC](https://tools.ietf.org/html/rfc3954)
- [IPFIX RFC](https://tools.ietf.org/html/rfc7011)
- [PTP IEEE 1588](https://en.wikipedia.org/wiki/Precision_Time_Protocol)
