"""
Python bindings for the Deep Packet Inspection (DPI) Engine.

Provides a Pythonic interface to the high-performance C DPI engine with:
- Protocol classification and dissection
- Pattern matching and anomaly detection
- Rule management
- Alert handling
- TLS interception controls
- Privacy-compliant logging

Author: J.A.R.V.I.S. Team
"""

import ctypes
import os
from ctypes import (
    c_int, c_uint32, c_uint64, c_uint16, c_uint8, c_char_p, c_void_p,
    POINTER, Structure, byref, create_string_buffer, CDLL
)
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple, Any
from enum import IntEnum
import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS
# ============================================================================

class DPIProtocol(IntEnum):
    """Supported protocols"""
    UNKNOWN = 0
    HTTP = 1
    HTTPS = 2
    DNS = 3
    SMTP = 4
    SMTPS = 5
    FTP = 6
    FTPS = 7
    SMB = 8
    SSH = 9
    TELNET = 10
    SNMP = 11
    QUIC = 12
    DTLS = 13
    MQTT = 14
    COAP = 15


class DPIAlertSeverity(IntEnum):
    """Alert severity levels"""
    INFO = 0
    WARNING = 1
    CRITICAL = 2
    MALWARE = 3
    ANOMALY = 4


class DPIRuleType(IntEnum):
    """Rule types"""
    REGEX = 0
    SNORT = 1
    YARA = 2
    CONTENT = 3
    BEHAVIORAL = 4


class DPITLSMode(IntEnum):
    """TLS interception modes"""
    DISABLED = 0
    PASSTHROUGH = 1
    DECRYPT = 2
    INSPECT = 3


class DPISessionState(IntEnum):
    """Session states"""
    NEW = 0
    ESTABLISHED = 1
    CLOSING = 2
    CLOSED = 3
    ERROR = 4


class DPISessionCategory(IntEnum):
    """Session risk categorization"""
    BENIGN = 0
    SUSPICIOUS = 1
    MALICIOUS = 2
    COMPROMISED = 3
    QUARANTINED = 4


class DPIFlowAction(IntEnum):
    """Flow action/routing decisions"""
    ALLOW = 0
    BLOCK = 1
    QUARANTINE = 2
    RATE_LIMIT = 3
    REDIRECT_IPS = 4
    DEEP_INSPECT = 5
    ALERT_ONLY = 6


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
    ]


class ProtocolResult(Structure):
    """Protocol classification result"""
    _fields_ = [
        ("protocol", c_uint32),
        ("confidence", c_uint8),
        ("detection_tick", c_uint32),
        ("app_name", c_char_p),
    ]


class HTTPData(Structure):
    """HTTP dissection data"""
    _fields_ = [
        ("method", c_char_p),
        ("uri", c_char_p),
        ("host", c_char_p),
        ("user_agent", c_char_p),
        ("status_code", c_uint16),
        ("content_length", c_uint64),
        ("is_request", c_uint8),
    ]


class DNSData(Structure):
    """DNS dissection data"""
    _fields_ = [
        ("transaction_id", c_uint16),
        ("query_name", c_char_p),
        ("query_type", c_uint16),
        ("is_query", c_uint8),
        ("response_code", c_uint8),
        ("answered_ips", POINTER(c_uint32)),
        ("answer_count", c_uint32),
    ]


class TLSData(Structure):
    """TLS dissection data"""
    _fields_ = [
        ("version_major", c_uint8),
        ("version_minor", c_uint8),
        ("cipher_suite", c_uint16),
        ("sni", c_char_p),
        ("cert_subject", c_char_p),
        ("is_client_hello", c_uint8),
        ("cert_chain_depth", c_uint32),
    ]


class Anomaly(Structure):
    """Anomaly detection result"""
    _fields_ = [
        ("anomaly_type", c_uint16),
        ("description", c_char_p),
        ("severity", c_uint8),
    ]


class DPIAlert(Structure):
    """DPI Alert"""
    _fields_ = [
        ("alert_id", c_uint64),
        ("timestamp_ns", c_uint64),
        ("flow", FlowTuple),
        ("severity", c_uint32),
        ("protocol", c_uint32),
        ("rule_id", c_uint32),
        ("rule_name", c_char_p),
        ("message", c_char_p),
        ("payload_sample", POINTER(c_uint8)),
        ("payload_sample_len", c_uint32),
        ("offset_in_stream", c_uint32),
    ]


class DPIStats(Structure):
    """DPI Statistics"""
    _fields_ = [
        ("packets_processed", c_uint64),
        ("bytes_processed", c_uint64),
        ("flows_created", c_uint64),
        ("flows_terminated", c_uint64),
        ("active_sessions", c_uint32),
        ("alerts_generated", c_uint64),
        ("anomalies_detected", c_uint64),
        ("http_packets", c_uint64),
        ("dns_packets", c_uint64),
        ("tls_packets", c_uint64),
        ("smtp_packets", c_uint64),
        ("smb_packets", c_uint64),
        ("avg_processing_time_us", ctypes.c_double),
        ("max_packet_processing_us", ctypes.c_double),
        ("buffer_utilization_percent", c_uint32),
    ]


class DPIConfig(Structure):
    """DPI Configuration"""
    _fields_ = [
        ("tls_mode", c_uint32),
        ("enable_anomaly_detection", c_uint8),
        ("enable_malware_detection", c_uint8),
        ("reassembly_timeout_sec", c_uint32),
        ("max_concurrent_sessions", c_uint32),
        ("memory_limit_mb", c_uint64),
        ("log_all_alerts", c_uint8),
        ("log_tls_keys", c_uint8),
        ("log_dir", c_char_p),
        ("redact_pii", c_uint8),
        ("anonymize_ips", c_uint8),
    ]


class DPIRule(Structure):
    """DPI Rule"""
    _fields_ = [
        ("rule_id", c_uint32),
        ("type", c_uint32),
        ("name", c_char_p),
        ("description", c_char_p),
        ("severity", c_uint32),
        ("pattern", c_char_p),
        ("pattern_len", c_uint32),
        ("protocol", c_uint32),
        ("port_range_start", c_uint16),
        ("port_range_end", c_uint16),
        ("applies_to_request", c_uint8),
        ("applies_to_response", c_uint8),
        ("category", c_char_p),
        ("created_at", c_uint64),
        ("last_modified", c_uint64),
        ("enabled", c_uint8),
    ]


# ============================================================================
# PYTHON WRAPPER CLASSES
# ============================================================================

@dataclass
class ClassifiedProtocol:
    """Protocol classification result"""
    protocol: DPIProtocol
    confidence: int
    detection_tick: int
    app_name: str


@dataclass
class HTTPInfo:
    """HTTP protocol information"""
    method: Optional[str]
    uri: Optional[str]
    host: Optional[str]
    user_agent: Optional[str]
    status_code: int
    content_length: int
    is_request: bool


@dataclass
class DNSInfo:
    """DNS protocol information"""
    transaction_id: int
    query_name: Optional[str]
    query_type: int
    is_query: bool
    response_code: int
    answered_ips: List[str]


@dataclass
class TLSInfo:
    """TLS protocol information"""
    version_major: int
    version_minor: int
    cipher_suite: int
    sni: Optional[str]
    cert_subject: Optional[str]
    is_client_hello: bool
    cert_chain_depth: int


@dataclass
class DPIAlertData:
    """DPI Alert data"""
    alert_id: int
    timestamp_ns: int
    flow: Tuple[str, int, str, int, int]
    severity: DPIAlertSeverity
    protocol: DPIProtocol
    rule_id: int
    rule_name: str
    message: str
    payload_sample: Optional[bytes]
    offset_in_stream: int


@dataclass
class DPIStatsData:
    """DPI statistics"""
    packets_processed: int
    bytes_processed: int
    flows_created: int
    flows_terminated: int
    active_sessions: int
    alerts_generated: int
    anomalies_detected: int
    http_packets: int
    dns_packets: int
    tls_packets: int
    smtp_packets: int
    smb_packets: int
    avg_processing_time_us: float
    max_packet_processing_us: float
    buffer_utilization_percent: int


@dataclass
class ClassifiedSession:
    """Session with classification and routing"""
    session_id: str
    flow_tuple: Tuple[str, int, str, int, int]
    state: DPISessionState
    category: DPISessionCategory
    risk_score: float
    packet_count: int
    byte_count: int
    protocol: DPIProtocol
    alerts_count: int
    created_at: float
    last_seen: float
    metadata: Dict[str, Any]


@dataclass
class FlowRoutingDecision:
    """Routing decision for a flow"""
    flow_id: str
    decision: DPIFlowAction
    confidence: float
    reason: str
    target_ips_engine: Optional[str] = None
    sandbox_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    timestamp_ns: int = 0


# ============================================================================
# DPI ENGINE CLASS
# ============================================================================

class DPIEngine:
    """High-performance Deep Packet Inspection Engine"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize DPI engine.
        
        Args:
            config: Optional configuration dict with keys:
                - tls_mode: DPITLSMode enum value
                - enable_anomaly_detection: bool
                - enable_malware_detection: bool
                - reassembly_timeout_sec: int
                - max_concurrent_sessions: int
                - memory_limit_mb: int
                - log_all_alerts: bool
                - log_tls_keys: bool
                - log_dir: str
                - redact_pii: bool
                - anonymize_ips: bool
        """
        # Load C library
        self._load_library()
        self._mock_mode = self._lib is None
        
        # Create default config
        c_config = DPIConfig()
        c_config.tls_mode = config.get('tls_mode', DPITLSMode.PASSTHROUGH) if config else DPITLSMode.PASSTHROUGH
        c_config.enable_anomaly_detection = config.get('enable_anomaly_detection', True) if config else True
        c_config.enable_malware_detection = config.get('enable_malware_detection', True) if config else True
        c_config.reassembly_timeout_sec = config.get('reassembly_timeout_sec', 300) if config else 300
        c_config.max_concurrent_sessions = config.get('max_concurrent_sessions', 100000) if config else 100000
        c_config.memory_limit_mb = config.get('memory_limit_mb', 1024) if config else 1024
        c_config.log_all_alerts = config.get('log_all_alerts', True) if config else True
        c_config.log_tls_keys = config.get('log_tls_keys', False) if config else False
        c_config.redact_pii = config.get('redact_pii', True) if config else True
        c_config.anonymize_ips = config.get('anonymize_ips', False) if config else False
        
        # Initialize engine
        if not self._mock_mode:
            self._engine = self._lib.dpi_init(byref(c_config))
            if not self._engine:
                raise RuntimeError("Failed to initialize DPI engine")
        else:
            self._engine = "mock"  # Use string as mock engine instance
        
        self._lock = threading.RLock()
        mode = "MOCK" if self._mock_mode else "REAL"
        logger.info(f"DPI Engine initialized successfully ({mode} mode)")
    
    def _load_library(self):
        """Load the C DPI library"""
        lib_path = Path(__file__).parent.parent / "hardware_integration" / "dpi" / "libdpi_engine.so"
        
        if not lib_path.exists():
            logger.warning(f"DPI engine library not found: {lib_path}. Using mock mode for testing.")
            self._lib = None
            return
        
        self._lib = CDLL(str(lib_path))
        
        # Define function signatures
        self._lib.dpi_init.argtypes = [POINTER(DPIConfig)]
        self._lib.dpi_init.restype = c_void_p
        
        self._lib.dpi_process_packet.argtypes = [
            c_void_p, POINTER(FlowTuple), POINTER(c_uint8),
            c_uint32, c_uint64, c_uint8, POINTER(POINTER(DPIAlert))
        ]
        self._lib.dpi_process_packet.restype = c_uint32
        
        self._lib.dpi_add_rule.argtypes = [c_void_p, POINTER(DPIRule)]
        self._lib.dpi_add_rule.restype = c_uint32
        
        self._lib.dpi_remove_rule.argtypes = [c_void_p, c_uint32]
        self._lib.dpi_remove_rule.restype = c_int
        
        self._lib.dpi_get_alerts.argtypes = [
            c_void_p, POINTER(DPIAlert), c_uint32, c_uint8
        ]
        self._lib.dpi_get_alerts.restype = c_uint32
        
        self._lib.dpi_get_stats.argtypes = [c_void_p]
        self._lib.dpi_get_stats.restype = DPIStats
        
        self._lib.dpi_get_session.argtypes = [c_void_p, POINTER(FlowTuple)]
        self._lib.dpi_get_session.restype = c_void_p
        
        self._lib.dpi_classify_protocol.argtypes = [c_void_p, POINTER(FlowTuple)]
        self._lib.dpi_classify_protocol.restype = ProtocolResult
        
        self._lib.dpi_set_tls_mode.argtypes = [c_void_p, POINTER(FlowTuple), c_uint32]
        self._lib.dpi_set_tls_mode.restype = c_int
        
        self._lib.dpi_get_protocol_data.argtypes = [c_void_p, POINTER(FlowTuple), c_uint32]
        self._lib.dpi_get_protocol_data.restype = c_void_p
        
        self._lib.dpi_terminate_session.argtypes = [c_void_p, POINTER(FlowTuple)]
        self._lib.dpi_terminate_session.restype = c_int
        
        self._lib.dpi_get_engine_stats.argtypes = [c_void_p]
        self._lib.dpi_get_engine_stats.restype = DPIStats
        
        self._lib.dpi_shutdown.argtypes = [c_void_p]
        self._lib.dpi_shutdown.restype = None
    
    def process_packet(
        self,
        src_ip: str,
        dst_ip: str,
        src_port: int,
        dst_port: int,
        protocol: int,
        packet_data: bytes,
        timestamp_ns: int,
        is_response: bool = False
    ) -> List[DPIAlertData]:
        """
        Process a packet through the DPI engine.
        
        Args:
            src_ip: Source IP address
            dst_ip: Destination IP address
            src_port: Source port
            dst_port: Destination port
            protocol: IPPROTO_TCP (6) or IPPROTO_UDP (17)
            packet_data: Packet payload bytes
            timestamp_ns: Timestamp in nanoseconds
            is_response: Whether this is a response packet
        
        Returns:
            List of DPI alerts generated
        """
        with self._lock:
            # Convert IP strings to uint32
            src_ip_int = self._ip_to_uint32(src_ip)
            dst_ip_int = self._ip_to_uint32(dst_ip)
            
            # Create flow tuple
            flow = FlowTuple()
            flow.src_ip = src_ip_int
            flow.dst_ip = dst_ip_int
            flow.src_port = src_port
            flow.dst_port = dst_port
            flow.protocol = protocol
            
            # Convert packet data
            packet_buffer = (c_uint8 * len(packet_data)).from_buffer_copy(packet_data)
            
            # Process packet
            alerts_ptr = POINTER(DPIAlert)()
            alert_count = self._lib.dpi_process_packet(
                self._engine,
                byref(flow),
                packet_buffer,
                len(packet_data),
                timestamp_ns,
                1 if is_response else 0,
                byref(alerts_ptr)
            )
            
            # Convert alerts to Python
            alerts = []
            if alert_count > 0 and alerts_ptr:
                for i in range(alert_count):
                    alert = alerts_ptr[i]
                    alerts.append(self._convert_alert(alert))
            
            return alerts
    
    def add_rule(
        self,
        name: str,
        pattern: str,
        rule_type: DPIRuleType = DPIRuleType.REGEX,
        severity: DPIAlertSeverity = DPIAlertSeverity.WARNING,
        protocol: Optional[DPIProtocol] = None,
        category: str = "general",
        description: str = ""
    ) -> int:
        """
        Add a DPI rule.
        
        Args:
            name: Rule name
            pattern: Regex pattern or signature
            rule_type: Type of rule
            severity: Alert severity level
            protocol: Applicable protocol (None = all)
            category: Rule category
            description: Rule description
        
        Returns:
            Rule ID or 0 on error
        """
        with self._lock:
            rule = DPIRule()
            rule.name = name.encode('utf-8')
            rule.pattern = pattern.encode('utf-8')
            rule.pattern_len = len(pattern)
            rule.type = rule_type
            rule.severity = severity
            rule.protocol = protocol or DPIProtocol.UNKNOWN
            rule.category = category.encode('utf-8')
            rule.description = description.encode('utf-8')
            rule.enabled = 1
            
            rule_id = self._lib.dpi_add_rule(self._engine, byref(rule))
            
            if rule_id > 0:
                logger.info(f"Added DPI rule: {name} (ID: {rule_id})")
            else:
                logger.error(f"Failed to add DPI rule: {name}")
            
            return rule_id
    
    def remove_rule(self, rule_id: int) -> bool:
        """Remove a DPI rule"""
        with self._lock:
            result = self._lib.dpi_remove_rule(self._engine, rule_id)
            if result == 0:
                logger.info(f"Removed DPI rule: {rule_id}")
                return True
            else:
                logger.error(f"Failed to remove DPI rule: {rule_id}")
                return False
    
    def get_alerts(self, max_alerts: int = 100, clear: bool = False) -> List[DPIAlertData]:
        """Get pending DPI alerts"""
        with self._lock:
            alerts_array = (DPIAlert * max_alerts)()
            alert_count = self._lib.dpi_get_alerts(
                self._engine,
                alerts_array,
                max_alerts,
                1 if clear else 0
            )
            
            alerts = []
            for i in range(alert_count):
                alerts.append(self._convert_alert(alerts_array[i]))
            
            return alerts
    
    def classify_protocol(
        self,
        src_ip: str,
        dst_ip: str,
        src_port: int,
        dst_port: int,
        protocol: int
    ) -> ClassifiedProtocol:
        """Classify protocol for a flow"""
        with self._lock:
            # Mock mode: return simulated classification
            if self._mock_mode:
                # Determine protocol based on port
                if dst_port == 443 or dst_port == 8443:
                    proto = DPIProtocol.HTTPS
                    app = "HTTPS"
                elif dst_port == 80 or dst_port == 8080:
                    proto = DPIProtocol.HTTP
                    app = "HTTP"
                elif dst_port == 53:
                    proto = DPIProtocol.DNS
                    app = "DNS"
                elif dst_port == 22:
                    proto = DPIProtocol.SSH
                    app = "SSH"
                else:
                    proto = DPIProtocol.UNKNOWN
                    app = "UNKNOWN"
                
                return ClassifiedProtocol(
                    protocol=proto,
                    confidence=95,
                    detection_tick=1,
                    app_name=app
                )
            
            src_ip_int = self._ip_to_uint32(src_ip)
            dst_ip_int = self._ip_to_uint32(dst_ip)
            
            flow = FlowTuple()
            flow.src_ip = src_ip_int
            flow.dst_ip = dst_ip_int
            flow.src_port = src_port
            flow.dst_port = dst_port
            flow.protocol = protocol
            
            result = self._lib.dpi_classify_protocol(self._engine, byref(flow))
            
            return ClassifiedProtocol(
                protocol=DPIProtocol(result.protocol),
                confidence=result.confidence,
                detection_tick=result.detection_tick,
                app_name=result.app_name.decode('utf-8') if result.app_name else ""
            )
    
    def set_tls_mode(
        self,
        src_ip: str,
        dst_ip: str,
        src_port: int,
        dst_port: int,
        protocol: int,
        mode: DPITLSMode
    ) -> bool:
        """Set TLS interception mode for a flow"""
        with self._lock:
            src_ip_int = self._ip_to_uint32(src_ip)
            dst_ip_int = self._ip_to_uint32(dst_ip)
            
            flow = FlowTuple()
            flow.src_ip = src_ip_int
            flow.dst_ip = dst_ip_int
            flow.src_port = src_port
            flow.dst_port = dst_port
            flow.protocol = protocol
            
            result = self._lib.dpi_set_tls_mode(self._engine, byref(flow), mode)
            return result == 0
    
    def get_stats(self) -> DPIStatsData:
        """Get DPI engine statistics"""
        with self._lock:
            c_stats = self._lib.dpi_get_engine_stats(self._engine)
            
            return DPIStatsData(
                packets_processed=c_stats.packets_processed,
                bytes_processed=c_stats.bytes_processed,
                flows_created=c_stats.flows_created,
                flows_terminated=c_stats.flows_terminated,
                active_sessions=c_stats.active_sessions,
                alerts_generated=c_stats.alerts_generated,
                anomalies_detected=c_stats.anomalies_detected,
                http_packets=c_stats.http_packets,
                dns_packets=c_stats.dns_packets,
                tls_packets=c_stats.tls_packets,
                smtp_packets=c_stats.smtp_packets,
                smb_packets=c_stats.smb_packets,
                avg_processing_time_us=c_stats.avg_processing_time_us,
                max_packet_processing_us=c_stats.max_packet_processing_us,
                buffer_utilization_percent=c_stats.buffer_utilization_percent,
            )
    
    def terminate_session(
        self,
        src_ip: str,
        dst_ip: str,
        src_port: int,
        dst_port: int,
        protocol: int
    ) -> bool:
        """Terminate a DPI session"""
        with self._lock:
            src_ip_int = self._ip_to_uint32(src_ip)
            dst_ip_int = self._ip_to_uint32(dst_ip)
            
            flow = FlowTuple()
            flow.src_ip = src_ip_int
            flow.dst_ip = dst_ip_int
            flow.src_port = src_port
            flow.dst_port = dst_port
            flow.protocol = protocol
            
            result = self._lib.dpi_terminate_session(self._engine, byref(flow))
            return result == 0
    
    def shutdown(self):
        """Shutdown the DPI engine"""
        with self._lock:
            if self._engine:
                self._lib.dpi_shutdown(self._engine)
                self._engine = None
                logger.info("DPI Engine shutdown")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.shutdown()
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    @staticmethod
    def _ip_to_uint32(ip_str: str) -> int:
        """Convert IP string to uint32"""
        parts = ip_str.split('.')
        return (int(parts[0]) << 24) | (int(parts[1]) << 16) | \
               (int(parts[2]) << 8) | int(parts[3])
    
    @staticmethod
    def _uint32_to_ip(ip_int: int) -> str:
        """Convert uint32 to IP string"""
        return f"{(ip_int >> 24) & 0xFF}.{(ip_int >> 16) & 0xFF}." \
               f"{(ip_int >> 8) & 0xFF}.{ip_int & 0xFF}"
    
    @staticmethod
    def _convert_alert(alert: DPIAlert) -> DPIAlertData:
        """Convert C alert to Python data class"""
        return DPIAlertData(
            alert_id=alert.alert_id,
            timestamp_ns=alert.timestamp_ns,
            flow=(
                DPIEngine._uint32_to_ip(alert.flow.src_ip),
                alert.flow.src_port,
                DPIEngine._uint32_to_ip(alert.flow.dst_ip),
                alert.flow.dst_port,
                alert.flow.protocol
            ),
            severity=DPIAlertSeverity(alert.severity),
            protocol=DPIProtocol(alert.protocol),
            rule_id=alert.rule_id,
            rule_name=alert.rule_name.decode('utf-8') if alert.rule_name else "",
            message=alert.message.decode('utf-8') if alert.message else "",
            payload_sample=bytes(alert.payload_sample[:alert.payload_sample_len]) 
                          if alert.payload_sample else None,
            offset_in_stream=alert.offset_in_stream,
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_available_protocols() -> List[str]:
    """Get list of available protocol names"""
    return [p.name for p in DPIProtocol]


def get_available_rule_types() -> List[str]:
    """Get list of available rule types"""
    return [t.name for t in DPIRuleType]
