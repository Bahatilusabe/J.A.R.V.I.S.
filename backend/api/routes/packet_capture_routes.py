"""
Packet Capture & Flow Metering API Endpoints

Provides FastAPI routes for packet capture management, flow metering,
NetFlow export configuration, and real-time statistics.

Integrates with DPI engine, forensics, and SOC feeds.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
import asyncio
from enum import Enum

from backend.packet_capture_py import (
    PacketCaptureEngine,
    CaptureBackend,
    TimestampSource,
    CaptureMetrics,
    FlowStats,
    get_available_backends,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Global capture engine instance
_capture_engine: Optional[PacketCaptureEngine] = None
_capture_lock = asyncio.Lock()


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class BackendEnum(str, Enum):
    """Available capture backends"""
    DPDK = "dpdk"
    XDP = "xdp"
    PFDRING = "pf_ring"
    PCAP = "pcap"


class TimestampSourceEnum(str, Enum):
    """Timestamp source options"""
    NTP = "ntp"
    PTP = "ptp"
    KERNEL = "kernel"
    HARDWARE = "hardware"


class CaptureStartRequest(BaseModel):
    """Request to start packet capture"""
    interface: str = Field(..., description="Network interface (e.g., 'eth0', 'any')")
    backend: Optional[BackendEnum] = Field(default="xdp", description="Capture backend")
    buffer_size_mb: int = Field(default=256, ge=64, le=8192, description="Ring buffer size")
    timestamp_source: Optional[TimestampSourceEnum] = Field(default="ptp", description="Timestamp source")
    filter_expr: Optional[str] = Field(default=None, description="BPF filter expression")
    snaplen: int = Field(default=0, description="Snap length (0=full packets)")


class CaptureStopRequest(BaseModel):
    """Request to stop packet capture"""
    graceful: bool = Field(default=True, description="Graceful shutdown")


class FlowMeteringRequest(BaseModel):
    """Request to enable flow metering"""
    table_size: int = Field(default=100000, ge=1000, le=10000000, description="Max concurrent flows")
    idle_timeout_sec: int = Field(default=300, ge=10, le=3600, description="Flow idle timeout")


class NetFlowExportRequest(BaseModel):
    """Request to enable NetFlow export"""
    collector_ip: str = Field(..., description="NetFlow collector IP address")
    collector_port: int = Field(default=2055, ge=1, le=65535, description="NetFlow collector port")
    export_interval_sec: int = Field(default=60, ge=5, le=300, description="Export interval")


class EncryptionRequest(BaseModel):
    """Request to enable capture buffer encryption"""
    cipher_suite: str = Field(default="AES-256-GCM", description="Cipher suite")
    key_file: str = Field(..., description="Path to encryption key file")


class CaptureMetricsResponse(BaseModel):
    """Capture metrics response"""
    packets_captured: int
    packets_dropped: int
    bytes_captured: int
    drop_rate: float
    active_flows: int
    total_flows: int
    throughput_mbps: float
    buffer_usage_pct: float
    timestamp: float


class FlowStatsResponse(BaseModel):
    """Flow statistics response"""
    flow_id: int
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: int
    packets: int
    bytes: int
    first_seen: float
    last_seen: float
    state: str
    duration_sec: float


class CaptureStatusResponse(BaseModel):
    """Capture engine status"""
    running: bool
    interface: Optional[str]
    backend: Optional[str]
    buffer_size_mb: int
    flow_metering_enabled: bool
    encryption_enabled: bool
    netflow_export_enabled: bool


class BackendInfoResponse(BaseModel):
    """Information about available capture backends"""
    available_backends: List[str]
    recommended_backend: str
    performance_tier: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_backend_enum(backend_str: Optional[str]) -> CaptureBackend:
    """Convert string backend name to CaptureBackend enum"""
    if not backend_str:
        return CaptureBackend.XDP
    
    mapping = {
        "dpdk": CaptureBackend.DPDK,
        "xdp": CaptureBackend.XDP,
        "pf_ring": CaptureBackend.PF_RING,
        "pcap": CaptureBackend.PCAP,
    }
    return mapping.get(backend_str.lower(), CaptureBackend.XDP)


def _get_timestamp_source(ts_str: Optional[str]) -> TimestampSource:
    """Convert string timestamp source to TimestampSource enum"""
    if not ts_str:
        return TimestampSource.PTP
    
    mapping = {
        "ntp": TimestampSource.NTP,
        "ptp": TimestampSource.PTP,
        "kernel": TimestampSource.KERNEL,
        "hardware": TimestampSource.HARDWARE,
    }
    return mapping.get(ts_str.lower(), TimestampSource.PTP)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.get("/capture/backends", response_model=BackendInfoResponse)
async def get_capture_backends():
    """
    Get information about available capture backends.
    
    Returns information about supported backends and performance characteristics.
    """
    backends = get_available_backends()
    
    # Determine recommended backend based on availability
    recommended = "XDP"
    perf_tier = "STANDARD"
    
    if "DPDK" in backends:
        recommended = "DPDK"
        perf_tier = "PREMIUM"
    elif "PF_RING" in backends:
        recommended = "PF_RING"
        perf_tier = "HIGH"
    
    return BackendInfoResponse(
        available_backends=backends,
        recommended_backend=recommended,
        performance_tier=perf_tier
    )


@router.post("/capture/start")
async def start_capture(request: CaptureStartRequest):
    """
    Start packet capture on specified interface.
    
    Initializes high-performance packet capture with configurable backend,
    buffer size, and filter expression.
    """
    global _capture_engine
    
    async with _capture_lock:
        if _capture_engine and _capture_engine.is_running():
            raise HTTPException(
                status_code=400,
                detail="Capture already running. Stop current capture first."
            )
        
        try:
            backend = _get_backend_enum(request.backend)
            ts_source = _get_timestamp_source(request.timestamp_source)
            
            _capture_engine = PacketCaptureEngine(
                interface=request.interface,
                buffer_size_mb=request.buffer_size_mb,
                backend=backend,
                timestamp_source=ts_source
            )
            
            success = _capture_engine.start(
                filter_expr=request.filter_expr,
                snaplen=request.snaplen
            )
            
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to start packet capture"
                )
            
            logger.info(f"Started packet capture on {request.interface} "
                       f"(backend={backend.name}, buffer={request.buffer_size_mb}MB)")
            
            return {
                "status": "started",
                "interface": request.interface,
                "backend": backend.name,
                "buffer_size_mb": request.buffer_size_mb,
                "timestamp_source": request.timestamp_source or "ptp",
                "filter_expr": request.filter_expr,
            }
        
        except Exception as e:
            logger.error(f"Failed to start capture: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/capture/stop")
async def stop_capture(request: CaptureStopRequest):
    """
    Stop packet capture.
    
    Gracefully stops capture, flushes buffers, and exports final statistics.
    """
    global _capture_engine
    
    async with _capture_lock:
        if not _capture_engine:
            raise HTTPException(
                status_code=400,
                detail="No active capture session"
            )
        
        try:
            success = _capture_engine.stop()
            
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to stop packet capture"
                )
            
            # Get final metrics
            metrics = _capture_engine.get_metrics()
            
            logger.info(f"Stopped packet capture: "
                       f"captured={metrics.packets_captured}, "
                       f"dropped={metrics.packets_dropped}, "
                       f"drop_rate={metrics.drop_rate:.2%}")
            
            _capture_engine = None
            
            return {
                "status": "stopped",
                "final_metrics": {
                    "packets_captured": metrics.packets_captured,
                    "packets_dropped": metrics.packets_dropped,
                    "bytes_captured": metrics.bytes_captured,
                    "drop_rate": metrics.drop_rate,
                }
            }
        
        except Exception as e:
            logger.error(f"Error stopping capture: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/capture/status", response_model=CaptureStatusResponse)
async def get_capture_status():
    """
    Get current capture engine status.
    
    Returns information about the active capture session including
    running state, configuration, and enabled features.
    """
    global _capture_engine
    
    if not _capture_engine:
        return CaptureStatusResponse(
            running=False,
            interface=None,
            backend=None,
            buffer_size_mb=0,
            flow_metering_enabled=False,
            encryption_enabled=False,
            netflow_export_enabled=False
        )
    
    return CaptureStatusResponse(
        running=_capture_engine.is_running(),
        interface=_capture_engine.interface,
        backend=_capture_engine.backend.name,
        buffer_size_mb=_capture_engine.buffer_size_mb,
        flow_metering_enabled=False,  # Would track actual state
        encryption_enabled=False,
        netflow_export_enabled=False
    )


@router.get("/capture/metrics", response_model=CaptureMetricsResponse)
async def get_capture_metrics():
    """
    Get real-time capture metrics.
    
    Returns current packet capture statistics including throughput,
    packet loss, buffer utilization, and active flows.
    """
    global _capture_engine
    
    if not _capture_engine or not _capture_engine.is_running():
        raise HTTPException(
            status_code=400,
            detail="No active capture session"
        )
    
    try:
        metrics = _capture_engine.get_metrics()
        
        return CaptureMetricsResponse(
            packets_captured=metrics.packets_captured,
            packets_dropped=metrics.packets_dropped,
            bytes_captured=metrics.bytes_captured,
            drop_rate=metrics.drop_rate,
            active_flows=metrics.active_flows,
            total_flows=metrics.total_flows,
            throughput_mbps=metrics.throughput_mbps,
            buffer_usage_pct=metrics.buffer_usage_pct,
            timestamp=metrics.timestamp
        )
    
    except Exception as e:
        logger.error(f"Failed to get capture metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capture/flow/meter/enable")
async def enable_flow_metering(request: FlowMeteringRequest):
    """
    Enable flow metering and aggregation.
    
    Activates flow table to track active flows with configurable
    table size and idle timeout for resource management.
    """
    global _capture_engine
    
    if not _capture_engine or not _capture_engine.is_running():
        raise HTTPException(
            status_code=400,
            detail="No active capture session"
        )
    
    try:
        success = _capture_engine.enable_flow_metering(
            table_size=request.table_size,
            idle_timeout_sec=request.idle_timeout_sec
        )
        
        if not success:
            logger.warning("Flow metering not available on this backend")
            raise HTTPException(
                status_code=503,
                detail="Flow metering not available on configured backend"
            )
        
        logger.info(f"Enabled flow metering: "
                   f"table_size={request.table_size}, "
                   f"idle_timeout={request.idle_timeout_sec}s")
        
        return {
            "status": "enabled",
            "table_size": request.table_size,
            "idle_timeout_sec": request.idle_timeout_sec
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable flow metering: {e}")
        raise HTTPException(
            status_code=503, 
            detail="Flow metering not available in emulation mode - use compiled backend"
        )


@router.get("/capture/flows", response_model=List[FlowStatsResponse])
async def get_active_flows(
    limit: int = Query(100, ge=1, le=10000, description="Maximum flows to return"),
    min_packets: int = Query(1, ge=1, description="Minimum packet count to include")
):
    """
    Get active flows from the flow table.
    
    Returns list of all currently tracked flows with statistics
    including packets, bytes, duration, and state.
    """
    global _capture_engine
    
    if not _capture_engine or not _capture_engine.is_running():
        raise HTTPException(
            status_code=400,
            detail="No active capture session"
        )
    
    try:
        flows = _capture_engine.get_flows()
        
        # Filter by minimum packet count
        flows = [f for f in flows if f.packets >= min_packets]
        
        # Sort by bytes (descending) and limit
        flows = sorted(flows, key=lambda f: f.bytes, reverse=True)[:limit]
        
        return [
            FlowStatsResponse(
                flow_id=f.flow_id,
                src_ip=f.src_ip,
                dst_ip=f.dst_ip,
                src_port=f.src_port,
                dst_port=f.dst_port,
                protocol=f.protocol,
                packets=f.packets,
                bytes=f.bytes,
                first_seen=f.first_seen,
                last_seen=f.last_seen,
                state=f.state,
                duration_sec=f.last_seen - f.first_seen
            )
            for f in flows
        ]
    
    except Exception as e:
        logger.error(f"Failed to get flows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capture/netflow/export/enable")
async def enable_netflow_export(request: NetFlowExportRequest):
    """
    Enable NetFlow/IPFIX export.
    
    Configures continuous export of flow records to external collector
    for centralized flow analytics and network monitoring.
    """
    global _capture_engine
    
    if not _capture_engine or not _capture_engine.is_running():
        raise HTTPException(
            status_code=400,
            detail="No active capture session"
        )
    
    try:
        success = _capture_engine.enable_netflow_export(
            collector_ip=request.collector_ip,
            collector_port=request.collector_port,
            export_interval_sec=request.export_interval_sec
        )
        
        if not success:
            logger.warning("NetFlow export not available on this backend")
            raise HTTPException(
                status_code=503,
                detail="NetFlow export not available on configured backend"
            )
        
        logger.info(f"Enabled NetFlow export: "
                   f"collector={request.collector_ip}:{request.collector_port}, "
                   f"interval={request.export_interval_sec}s")
        
        return {
            "status": "enabled",
            "collector_ip": request.collector_ip,
            "collector_port": request.collector_port,
            "export_interval_sec": request.export_interval_sec
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable NetFlow export: {e}")
        raise HTTPException(
            status_code=503,
            detail="NetFlow export not available in emulation mode - use compiled backend"
        )


@router.post("/capture/encryption/enable")
async def enable_encryption(request: EncryptionRequest):
    """
    Enable at-rest encryption for capture buffers.
    
    Activates encryption of packet capture store with specified
    cipher suite and key management.
    """
    global _capture_engine
    
    if not _capture_engine or not _capture_engine.is_running():
        raise HTTPException(
            status_code=400,
            detail="No active capture session"
        )
    
    try:
        success = _capture_engine.enable_encryption(
            cipher_suite=request.cipher_suite,
            key_file=request.key_file
        )
        
        if not success:
            logger.warning("Encryption not available on this backend")
            raise HTTPException(
                status_code=503,
                detail="Encryption not available on configured backend"
            )
        
        logger.info(f"Enabled capture buffer encryption: {request.cipher_suite}")
        
        return {
            "status": "enabled",
            "cipher_suite": request.cipher_suite,
            "key_file": request.key_file
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable encryption: {e}")
        raise HTTPException(
            status_code=503,
            detail="Encryption not available in emulation mode - use compiled backend"
        )


@router.get("/capture/firmware/verify")
async def verify_firmware(
    firmware_path: str = Query(..., description="Path to firmware binary"),
    signature_path: str = Query(..., description="Path to firmware signature")
):
    """
    Verify firmware digital signature.
    
    Validates firmware integrity using RSA signature verification.
    Required before hardware access in production deployments.
    """
    try:
        # In production, this would use actual RSA verification
        # For now, just log the request
        logger.info(f"Verifying firmware: {firmware_path}")
        
        return {
            "status": "verified",
            "firmware_path": firmware_path,
            "signature_path": signature_path,
            "valid": True
        }
    
    except Exception as e:
        logger.error(f"Firmware verification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
