"""
Python bindings for high-performance packet capture engine.

Provides unified interface to C/C++ packet capture backend with support for:
- Zero-copy packet capture (DPDK, XDP, PF_RING backends)
- Flow metering and NetFlow export
- At-rest encryption of capture buffers
- Firmware integrity validation
- Real-time statistics and monitoring

Integrates with J.A.R.V.I.S. backend for DPI, forensics, and analytics.
"""

import ctypes
import os
import threading
from ctypes import c_int, c_uint32, c_uint64, c_uint16, c_uint8, c_char_p, c_void_p, POINTER, Structure
from dataclasses import dataclass
from typing import Optional, List, Callable, Dict, Any
from enum import IntEnum
import logging
import time

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class CaptureBackend(IntEnum):
    """Supported packet capture backends"""
    DPDK = 0
    XDP = 1
    PF_RING = 2
    PCAP = 3


class PacketDirection(IntEnum):
    """Packet flow direction"""
    UNKNOWN = 0
    INGRESS = 1
    EGRESS = 2
    MIRRORED = 3


class TimestampSource(IntEnum):
    """Timestamp synchronization source"""
    NTP = 0
    PTP = 1
    KERNEL = 2
    HARDWARE = 3


# ============================================================================
# CTYPES STRUCTURES
# ============================================================================

class FlowTuple(Structure):
    """5-tuple flow identifier"""
    _fields_ = [
        ("src_ip", c_uint32),
        ("dst_ip", c_uint32),
        ("src_port", c_uint16),
        ("dst_port", c_uint16),
        ("protocol", c_uint8),
        ("vlan_id", c_uint16),
    ]


class PacketMetadata(Structure):
    """Packet metadata with timing"""
    _fields_ = [
        ("packet_id", c_uint64),
        ("timestamp_ns", c_uint64),
        ("ts_source", c_uint32),
        ("direction", c_uint32),
        ("interface_id", c_uint32),
        ("vlan_id", c_uint16),
        ("payload_length", c_uint16),
        ("wire_length", c_uint16),
        ("encapsulation_level", c_uint8),
        ("_reserved1", c_uint8),
    ]


class FlowRecord(Structure):
    """Flow statistics record"""
    _fields_ = [
        ("tuple", FlowTuple),
        ("flow_id", c_uint64),
        ("first_packet_id", c_uint64),
        ("last_packet_id", c_uint64),
        ("first_seen_ns", c_uint64),
        ("last_seen_ns", c_uint64),
        ("packets", c_uint64),
        ("bytes", c_uint64),
        ("bytes_fwd", c_uint64),
        ("bytes_rev", c_uint64),
        ("flags", c_uint32),
        ("interface_id", c_uint16),
        ("state", c_uint8),
        ("_reserved", c_uint8),
    ]


class CaptureStats(Structure):
    """Capture statistics"""
    _fields_ = [
        ("packets_captured", c_uint64),
        ("packets_dropped", c_uint64),
        ("packets_errors", c_uint64),
        ("bytes_captured", c_uint64),
        ("buffer_used_pct", c_uint64),
        ("flows_active", c_uint64),
        ("flows_total", c_uint64),
        ("rx_errors", c_uint32),
        ("tx_errors", c_uint32),
        ("avg_pps", ctypes.c_double),
        ("avg_throughput_mbps", ctypes.c_double),
    ]


# ============================================================================
# PYTHON DATACLASSES
# ============================================================================

@dataclass
class PacketInfo:
    """Python-friendly packet information"""
    packet_id: int
    timestamp_ns: int
    direction: str
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: int
    payload_length: int
    wire_length: int
    vlan_id: int
    
    def __str__(self) -> str:
        return (f"Packet {self.packet_id}: {self.src_ip}:{self.src_port} -> "
                f"{self.dst_ip}:{self.dst_port} ({self.payload_length}B)")


@dataclass
class FlowStats:
    """Python-friendly flow statistics"""
    flow_id: int
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: int
    packets: int
    bytes: int
    first_seen: float  # Seconds since epoch
    last_seen: float   # Seconds since epoch
    state: str
    
    def __str__(self) -> str:
        duration = self.last_seen - self.first_seen
        return (f"Flow {self.flow_id}: {self.src_ip}:{self.src_port} -> "
                f"{self.dst_ip}:{self.dst_port} "
                f"({self.packets} pkts, {self.bytes} bytes, {duration:.1f}s)")


@dataclass
class CaptureMetrics:
    """Capture engine metrics"""
    packets_captured: int
    packets_dropped: int
    bytes_captured: int
    drop_rate: float
    active_flows: int
    total_flows: int
    throughput_mbps: float
    buffer_usage_pct: float
    timestamp: float


# ============================================================================
# PACKET CAPTURE ENGINE
# ============================================================================

class PacketCaptureEngine:
    """High-performance packet capture engine with flow metering"""
    
    def __init__(self, interface: str = "any", buffer_size_mb: int = 256,
                 backend: CaptureBackend = CaptureBackend.XDP,
                 timestamp_source: TimestampSource = TimestampSource.PTP):
        """
        Initialize packet capture engine.
        
        Args:
            interface: Network interface to capture on (e.g., "eth0")
            buffer_size_mb: Ring buffer size in MB
            backend: Preferred capture backend
            timestamp_source: Timestamp synchronization source
        """
        self.interface = interface
        self.buffer_size_mb = buffer_size_mb
        self.backend = backend
        self.timestamp_source = timestamp_source
        
        # Try to load C library
        self._lib = self._load_library()
        if not self._lib:
            logger.warning("Could not load compiled packet capture library, "
                          "using emulation mode")
            self._lib = None
            self._emulated = True
        else:
            self._emulated = False
        
        self._session = None
        self._lock = threading.Lock()
        self._running = False
        self._stats = {
            'packets_captured': 0,
            'packets_dropped': 0,
            'bytes_captured': 0,
        }
    
    def _load_library(self) -> Optional[ctypes.CDLL]:
        """Try to load compiled packet capture library"""
        lib_paths = [
            os.path.join(os.path.dirname(__file__), 'libpacket_capture.so'),
            '/usr/local/lib/libpacket_capture.so',
            '/usr/lib/libpacket_capture.so',
        ]
        
        for path in lib_paths:
            try:
                if os.path.exists(path):
                    lib = ctypes.CDLL(path)
                    logger.info(f"Loaded packet capture library: {path}")
                    return lib
            except OSError as e:
                logger.debug(f"Could not load {path}: {e}")
        
        return None
    
    def start(self, filter_expr: Optional[str] = None, snaplen: int = 0) -> bool:
        """
        Start packet capture.
        
        Args:
            filter_expr: Optional BPF filter expression
            snaplen: Snap length (0 = full packets)
            
        Returns:
            True if successful
        """
        with self._lock:
            if self._running:
                logger.warning("Capture already running")
                return False
            
            if self._lib and not self._emulated:
                # Use compiled backend
                init_func = self._lib.capture_init
                init_func.argtypes = [c_int, c_char_p, c_uint32, c_int]
                init_func.restype = c_void_p
                
                self._session = init_func(
                    c_int(self.backend),
                    self.interface.encode('utf-8'),
                    c_uint32(self.buffer_size_mb),
                    c_int(self.timestamp_source)
                )
                
                if not self._session:
                    logger.error("Failed to initialize capture session")
                    return False
                
                start_func = self._lib.capture_start
                start_func.argtypes = [c_void_p, c_uint16, c_char_p]
                start_func.restype = c_int
                
                filter_bytes = filter_expr.encode('utf-8') if filter_expr else None
                result = start_func(self._session, c_uint16(snaplen), filter_bytes)
                
                if result != 0:
                    logger.error("Failed to start capture")
                    return False
            
            self._running = True
            logger.info(f"Started packet capture on {self.interface} "
                       f"(backend={self.backend.name})")
            return True
    
    def stop(self) -> bool:
        """Stop packet capture"""
        with self._lock:
            if not self._running:
                return False
            
            if self._lib and self._session and not self._emulated:
                stop_func = self._lib.capture_stop
                stop_func.argtypes = [c_void_p]
                stop_func.restype = c_int
                stop_func(self._session)
                
                cleanup_func = self._lib.capture_cleanup
                cleanup_func.argtypes = [c_void_p]
                cleanup_func(self._session)
                self._session = None
            
            self._running = False
            logger.info("Stopped packet capture")
            return True
    
    def enable_flow_metering(self, table_size: int = 100000,
                            idle_timeout_sec: int = 300) -> bool:
        """
        Enable flow metering and aggregation.
        
        Args:
            table_size: Maximum number of concurrent flows
            idle_timeout_sec: Timeout to age out inactive flows
            
        Returns:
            True if successful
        """
        if not self._session or self._emulated:
            logger.warning("Flow metering requires running compiled backend")
            return False
        
        flow_enable = self._lib.capture_flow_enable
        flow_enable.argtypes = [c_void_p, c_uint32, c_uint32]
        flow_enable.restype = c_int
        
        result = flow_enable(self._session, c_uint32(table_size),
                            c_uint32(idle_timeout_sec))
        
        if result == 0:
            logger.info(f"Enabled flow metering (table_size={table_size})")
            return True
        
        logger.error("Failed to enable flow metering")
        return False
    
    def enable_netflow_export(self, collector_ip: str, collector_port: int = 2055,
                             export_interval_sec: int = 60) -> bool:
        """
        Enable NetFlow/IPFIX export.
        
        Args:
            collector_ip: NetFlow collector IP address
            collector_port: NetFlow collector port
            export_interval_sec: Export interval in seconds
            
        Returns:
            True if successful
        """
        if not self._session or self._emulated:
            logger.warning("NetFlow export requires running compiled backend")
            return False
        
        netflow_enable = self._lib.capture_netflow_enable
        netflow_enable.argtypes = [c_void_p, c_char_p, c_uint16, c_uint32, c_void_p]
        netflow_enable.restype = c_int
        
        result = netflow_enable(self._session, collector_ip.encode('utf-8'),
                               c_uint16(collector_port),
                               c_uint32(export_interval_sec), None)
        
        if result == 0:
            logger.info(f"Enabled NetFlow export to {collector_ip}:{collector_port}")
            return True
        
        logger.error("Failed to enable NetFlow export")
        return False
    
    def enable_encryption(self, cipher_suite: str = "AES-256-GCM",
                         key_file: str = "/etc/jarvis/capture.key") -> bool:
        """
        Enable at-rest encryption for capture buffers.
        
        Args:
            cipher_suite: Encryption cipher suite
            key_file: Path to encryption key file
            
        Returns:
            True if successful
        """
        if not self._session or self._emulated:
            logger.warning("Encryption requires running compiled backend")
            return False
        
        encrypt_func = self._lib.capture_set_encryption
        encrypt_func.argtypes = [c_void_p, c_char_p, c_char_p]
        encrypt_func.restype = c_int
        
        result = encrypt_func(self._session, cipher_suite.encode('utf-8'),
                             key_file.encode('utf-8'))
        
        if result == 0:
            logger.info(f"Enabled encryption: {cipher_suite}")
            return True
        
        logger.error("Failed to enable encryption")
        return False
    
    def get_metrics(self) -> CaptureMetrics:
        """Get current capture metrics"""
        with self._lock:
            if self._emulated:
                # Return emulated metrics
                return CaptureMetrics(
                    packets_captured=self._stats['packets_captured'],
                    packets_dropped=self._stats['packets_dropped'],
                    bytes_captured=self._stats['bytes_captured'],
                    drop_rate=0.0,
                    active_flows=0,
                    total_flows=0,
                    throughput_mbps=0.0,
                    buffer_usage_pct=0.0,
                    timestamp=time.time()
                )
            
            if not self._session:
                return CaptureMetrics(
                    packets_captured=0, packets_dropped=0, bytes_captured=0,
                    drop_rate=0.0, active_flows=0, total_flows=0,
                    throughput_mbps=0.0, buffer_usage_pct=0.0,
                    timestamp=time.time()
                )
            
            stats = CaptureStats()
            get_stats = self._lib.capture_get_stats
            get_stats.argtypes = [c_void_p, POINTER(CaptureStats)]
            get_stats.restype = c_int
            
            result = get_stats(self._session, ctypes.byref(stats))
            
            if result == 0:
                drop_rate = (stats.packets_dropped / 
                            (stats.packets_captured + stats.packets_dropped)
                            if (stats.packets_captured + stats.packets_dropped) > 0 else 0.0)
                
                return CaptureMetrics(
                    packets_captured=stats.packets_captured,
                    packets_dropped=stats.packets_dropped,
                    bytes_captured=stats.bytes_captured,
                    drop_rate=drop_rate,
                    active_flows=stats.flows_active,
                    total_flows=stats.flows_total,
                    throughput_mbps=stats.avg_throughput_mbps,
                    buffer_usage_pct=stats.buffer_used_pct,
                    timestamp=time.time()
                )
            
            return CaptureMetrics(
                packets_captured=0, packets_dropped=0, bytes_captured=0,
                drop_rate=0.0, active_flows=0, total_flows=0,
                throughput_mbps=0.0, buffer_usage_pct=0.0,
                timestamp=time.time()
            )
    
    def get_flows(self) -> List[FlowStats]:
        """Get all active flows"""
        flows = []
        
        if self._emulated or not self._session:
            return flows
        
        get_flows = self._lib.capture_flow_get_all
        get_flows.argtypes = [c_void_p, POINTER(POINTER(FlowRecord)), POINTER(c_uint32)]
        get_flows.restype = c_int
        
        flows_ptr = POINTER(FlowRecord)()
        count = c_uint32()
        
        result = get_flows(self._session, ctypes.byref(flows_ptr), ctypes.byref(count))
        
        if result == 0 and flows_ptr:
            for i in range(count.value):
                flow = flows_ptr[i]
                flows.append(FlowStats(
                    flow_id=flow.flow_id,
                    src_ip=self._format_ipv4(flow.tuple.src_ip),
                    dst_ip=self._format_ipv4(flow.tuple.dst_ip),
                    src_port=flow.tuple.src_port,
                    dst_port=flow.tuple.dst_port,
                    protocol=flow.tuple.protocol,
                    packets=flow.packets,
                    bytes=flow.bytes,
                    first_seen=flow.first_seen_ns / 1e9,
                    last_seen=flow.last_seen_ns / 1e9,
                    state='ACTIVE' if flow.state == 0 else 'CLOSING' if flow.state == 1 else 'CLOSED'
                ))
            
            # Free returned array
            free_func = self._lib.free
            if hasattr(free_func, 'argtypes'):
                free_func.argtypes = [c_void_p]
            free_func(flows_ptr)
        
        return flows
    
    @staticmethod
    def _format_ipv4(ip_int: int) -> str:
        """Format IPv4 address from 32-bit integer"""
        return f"{(ip_int >> 24) & 0xFF}.{(ip_int >> 16) & 0xFF}." \
               f"{(ip_int >> 8) & 0xFF}.{ip_int & 0xFF}"
    
    def is_running(self) -> bool:
        """Check if capture is running"""
        with self._lock:
            return self._running
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()


# ============================================================================
# BACKEND INTEGRATION
# ============================================================================

def get_available_backends() -> List[str]:
    """Get list of available capture backends"""
    backends = []
    
    try:
        import subprocess
        
        # Check DPDK
        if subprocess.run(['which', 'dpdk-testpmd'], 
                         capture_output=True).returncode == 0:
            backends.append('DPDK (Intel Data Plane)')
        
        # Check XDP
        if subprocess.run(['ip', 'link', 'show'], 
                         capture_output=True).returncode == 0:
            backends.append('XDP (Linux eBPF)')
        
        # Check PF_RING
        if subprocess.run(['modinfo', 'pf_ring'], 
                         capture_output=True).returncode == 0:
            backends.append('PF_RING (Kernel Bypass)')
    except Exception:
        pass
    
    # libpcap always available
    backends.append('libpcap (Fallback)')
    
    return backends


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Start capture
    engine = PacketCaptureEngine(interface='any', backend=CaptureBackend.XDP)
    engine.start(filter_expr="tcp port 80 or tcp port 443")
    engine.enable_flow_metering()
    
    # Run for 10 seconds
    try:
        for i in range(10):
            metrics = engine.get_metrics()
            print(f"\n[{i}s] {metrics}")
            time.sleep(1)
    finally:
        engine.stop()
