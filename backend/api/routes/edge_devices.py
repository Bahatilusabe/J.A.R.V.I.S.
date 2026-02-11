"""
Edge Devices Management API Routes
REST endpoints for edge device lifecycle management, monitoring, and remote execution.

Endpoints:
- GET /edge-devices - Get all edge devices with metrics
- GET /edge-devices/{id} - Get specific device details and history
- GET /edge-devices/metrics - Get network-wide security metrics
- POST /edge-devices/{id}/command - Execute remote command on device
- POST /edge-devices/{id}/reboot - Reboot a device

Author: J.A.R.V.I.S. Edge Device Management Team
Date: December 2025
"""

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json
from pathlib import Path as PathlibPath
import random

# ============================================================================
# ENUMS
# ============================================================================

class DeviceStatus(str, Enum):
    """Device operational status"""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


class PlatformType(str, Enum):
    """Device platform type"""
    ATLAS = "atlas"
    HISILICON = "hisilicon"
    UNKNOWN = "unknown"


class CommandType(str, Enum):
    """Remote command types"""
    STATUS = "status"
    REBOOT = "reboot"
    RESTART = "restart"


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class EdgeDevice(BaseModel):
    """Edge device information"""
    id: str
    name: str
    platform: PlatformType
    status: DeviceStatus
    cpu_usage: float = Field(ge=0.0, le=100.0)
    memory_usage: float = Field(ge=0.0, le=100.0)
    temperature: float = Field(ge=0.0, le=150.0)
    uptime: int  # hours
    last_seen: datetime
    firmware_version: str
    tee_enabled: bool
    tpm_attestation: bool
    location: str
    model: str
    cores: int = Field(ge=1)
    memory_gb: int = Field(ge=1)


class SecurityMetrics(BaseModel):
    """Network-wide security metrics"""
    total_devices: int
    secure_devices: int
    attestation_success: float = Field(ge=0.0, le=100.0)
    encryption_enabled: str  # e.g., "All devices encrypted"
    seal_status: float = Field(ge=0.0, le=100.0)
    device_binding: float = Field(ge=0.0, le=100.0)


class DeviceHistory(BaseModel):
    """Device metrics history entry"""
    timestamp: datetime
    device_id: str
    cpu_usage: float = Field(ge=0.0, le=100.0)
    memory_usage: float = Field(ge=0.0, le=100.0)
    temperature: float = Field(ge=0.0, le=150.0)
    status: DeviceStatus


class EdgeDevicesListResponse(BaseModel):
    """Response for devices list"""
    devices: List[EdgeDevice]
    metrics: SecurityMetrics
    total: int
    timestamp: datetime


class DeviceDetailsResponse(BaseModel):
    """Response for device details"""
    device: EdgeDevice
    history: List[DeviceHistory]
    timestamp: datetime


class RemoteCommandRequest(BaseModel):
    """Request to execute remote command"""
    device_id: str
    command: CommandType
    params: Optional[Dict[str, Any]] = None


class RemoteCommandResponse(BaseModel):
    """Response from remote command"""
    status: str
    message: str
    device_id: str
    command: CommandType
    executed_at: datetime
    result: Optional[Dict[str, Any]] = None


class RebootDeviceRequest(BaseModel):
    """Request to reboot device"""
    device_id: str
    force: bool = False


class RebootDeviceResponse(BaseModel):
    """Response from reboot"""
    status: str
    message: str
    device_id: str
    rebooted_at: datetime


class MetricsResponse(BaseModel):
    """Response for security metrics"""
    metrics: SecurityMetrics
    timestamp: datetime


# ============================================================================
# ROUTER & STORAGE
# ============================================================================

router = APIRouter()

# In-memory storage (in production, use database)
DEVICES_DB: Dict[str, EdgeDevice] = {}
DEVICE_HISTORY_DB: Dict[str, List[DeviceHistory]] = {}
COMMAND_HISTORY: List[Dict[str, Any]] = []

# Storage file paths
STORAGE_PATH = PathlibPath(__file__).parent.parent.parent / "data"
STORAGE_PATH.mkdir(exist_ok=True)
DEVICES_FILE = STORAGE_PATH / "edge_devices.json"
HISTORY_FILE = STORAGE_PATH / "device_history.json"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _load_devices_from_storage():
    """Load devices from persistent storage"""
    global DEVICES_DB
    if DEVICES_FILE.exists():
        try:
            with open(DEVICES_FILE, 'r') as f:
                data = json.load(f)
                for device_id, device_data in data.items():
                    # Parse datetime strings
                    if 'last_seen' in device_data and isinstance(device_data['last_seen'], str):
                        device_data['last_seen'] = datetime.fromisoformat(device_data['last_seen'])
                    DEVICES_DB[device_id] = EdgeDevice(**device_data)
        except Exception as e:
            print(f"Warning: Could not load devices from storage: {e}")


def _load_history_from_storage():
    """Load device history from persistent storage"""
    global DEVICE_HISTORY_DB
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r') as f:
                data = json.load(f)
                for device_id, history_data in data.items():
                    device_history = []
                    for entry in history_data:
                        if 'timestamp' in entry and isinstance(entry['timestamp'], str):
                            entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                        device_history.append(DeviceHistory(**entry))
                    DEVICE_HISTORY_DB[device_id] = device_history
        except Exception as e:
            print(f"Warning: Could not load history from storage: {e}")


def _save_devices_to_storage():
    """Save devices to persistent storage"""
    try:
        data = {
            device_id: json.loads(device.model_dump_json())
            for device_id, device in DEVICES_DB.items()
        }
        with open(DEVICES_FILE, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        print(f"Warning: Could not save devices to storage: {e}")


def _save_history_to_storage():
    """Save device history to persistent storage"""
    try:
        data = {}
        for device_id, history_list in DEVICE_HISTORY_DB.items():
            data[device_id] = [json.loads(h.model_dump_json()) for h in history_list]
        with open(HISTORY_FILE, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        print(f"Warning: Could not save history to storage: {e}")


def _initialize_demo_devices():
    """Initialize with demo devices if database is empty"""
    global DEVICES_DB, DEVICE_HISTORY_DB
    
    if DEVICES_DB:
        return
    
    demo_devices = [
        {
            "id": "edge-001",
            "name": "Atlas-500-East",
            "platform": PlatformType.ATLAS,
            "status": DeviceStatus.ONLINE,
            "cpu_usage": 45.2,
            "memory_usage": 62.1,
            "temperature": 52.3,
            "uptime": 720,  # 30 days
            "last_seen": datetime.now(),
            "firmware_version": "5.2.1",
            "tee_enabled": True,
            "tpm_attestation": True,
            "location": "Eastern Region Data Center",
            "model": "Atlas 500",
            "cores": 32,
            "memory_gb": 256
        },
        {
            "id": "edge-002",
            "name": "Kunpeng-920-Central",
            "platform": PlatformType.HISILICON,
            "status": DeviceStatus.ONLINE,
            "cpu_usage": 38.7,
            "memory_usage": 54.3,
            "temperature": 48.1,
            "uptime": 1080,  # 45 days
            "last_seen": datetime.now(),
            "firmware_version": "4.8.3",
            "tee_enabled": True,
            "tpm_attestation": True,
            "location": "Central Region Hub",
            "model": "Kunpeng 920",
            "cores": 64,
            "memory_gb": 512
        },
        {
            "id": "edge-003",
            "name": "Atlas-300i-West",
            "platform": PlatformType.ATLAS,
            "status": DeviceStatus.ONLINE,
            "cpu_usage": 72.4,
            "memory_usage": 78.2,
            "temperature": 68.5,
            "uptime": 360,  # 15 days
            "last_seen": datetime.now(),
            "firmware_version": "5.1.8",
            "tee_enabled": True,
            "tpm_attestation": False,
            "location": "Western Region Edge Node",
            "model": "Atlas 300i",
            "cores": 16,
            "memory_gb": 128
        },
        {
            "id": "edge-004",
            "name": "HiSilicon-Echo-South",
            "platform": PlatformType.HISILICON,
            "status": DeviceStatus.DEGRADED,
            "cpu_usage": 89.6,
            "memory_usage": 92.3,
            "temperature": 76.2,
            "uptime": 240,  # 10 days
            "last_seen": datetime.now() - timedelta(minutes=5),
            "firmware_version": "4.7.2",
            "tee_enabled": True,
            "tpm_attestation": True,
            "location": "Southern Region Border Node",
            "model": "HiSilicon Echo",
            "cores": 48,
            "memory_gb": 256
        }
    ]
    
    for device_data in demo_devices:
        device = EdgeDevice(**device_data)
        DEVICES_DB[device.id] = device
        
        # Generate 20 history entries for each device
        history = []
        for i in range(20):
            timestamp = datetime.now() - timedelta(minutes=(19 - i) * 5)
            entry = DeviceHistory(
                timestamp=timestamp,
                device_id=device.id,
                cpu_usage=max(0, min(100, device.cpu_usage + (random.random() - 0.5) * 20)),
                memory_usage=max(0, min(100, device.memory_usage + (random.random() - 0.5) * 15)),
                temperature=max(0, device.temperature + (random.random() - 0.5) * 10),
                status=device.status
            )
            history.append(entry)
        DEVICE_HISTORY_DB[device.id] = history
    
    _save_devices_to_storage()
    _save_history_to_storage()


def _calculate_security_metrics() -> SecurityMetrics:
    """Calculate network-wide security metrics"""
    devices = list(DEVICES_DB.values())
    
    if not devices:
        return SecurityMetrics(
            total_devices=0,
            secure_devices=0,
            attestation_success=0.0,
            encryption_enabled="N/A",
            seal_status=0.0,
            device_binding=0.0
        )
    
    secure_devices = sum(1 for d in devices if d.tee_enabled and d.tpm_attestation)
    attestation_success = (sum(1 for d in devices if d.tpm_attestation) / len(devices)) * 100
    device_binding = (sum(1 for d in devices if d.tee_enabled) / len(devices)) * 100
    
    return SecurityMetrics(
        total_devices=len(devices),
        secure_devices=secure_devices,
        attestation_success=attestation_success,
        encryption_enabled="All devices encrypted",
        seal_status=92.5,
        device_binding=device_binding
    )


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/edge-devices", tags=["edge-devices"], summary="List all edge devices")
def get_edge_devices() -> EdgeDevicesListResponse:
    """
    Get all edge devices with current metrics and security posture.
    
    Returns:
        EdgeDevicesListResponse: List of devices and overall metrics
    """
    devices = list(DEVICES_DB.values())
    metrics = _calculate_security_metrics()
    
    return EdgeDevicesListResponse(
        devices=devices,
        metrics=metrics,
        total=len(devices),
        timestamp=datetime.now()
    )


@router.get("/edge-devices/{device_id}", tags=["edge-devices"], summary="Get device details")
def get_device_details(device_id: str = Path(..., description="Device ID")) -> DeviceDetailsResponse:
    """
    Get details for a specific edge device including historical metrics.
    
    Args:
        device_id: The device ID
        
    Returns:
        DeviceDetailsResponse: Device details and history
        
    Raises:
        HTTPException: 404 if device not found
    """
    if device_id not in DEVICES_DB:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    device = DEVICES_DB[device_id]
    history = DEVICE_HISTORY_DB.get(device_id, [])
    
    return DeviceDetailsResponse(
        device=device,
        history=history,
        timestamp=datetime.now()
    )


@router.get("/edge-devices/metrics", tags=["edge-devices"], summary="Get security metrics")
def get_security_metrics() -> MetricsResponse:
    """
    Get network-wide security and compliance metrics.
    
    Returns:
        MetricsResponse: Security metrics for all devices
    """
    metrics = _calculate_security_metrics()
    return MetricsResponse(metrics=metrics, timestamp=datetime.now())


@router.post("/edge-devices/{device_id}/command", tags=["edge-devices"], summary="Execute remote command")
def execute_remote_command(
    device_id: str = Path(..., description="Device ID"),
    request: RemoteCommandRequest = None
) -> RemoteCommandResponse:
    """
    Execute a remote command on an edge device.
    
    Supported commands:
    - status: Get device status
    - reboot: Reboot the device
    - restart: Restart services
    
    Args:
        device_id: The device ID
        request: Command request details
        
    Returns:
        RemoteCommandResponse: Command execution result
        
    Raises:
        HTTPException: 404 if device not found
    """
    if device_id not in DEVICES_DB:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    device = DEVICES_DB[device_id]
    
    # Simulate command execution
    result = {
        "command": request.command.value,
        "execution_time_ms": random.randint(100, 500),
        "output": f"Command '{request.command.value}' executed successfully on {device.name}"
    }
    
    if request.command == CommandType.STATUS:
        result["device_status"] = device.status.value
        result["cpu_usage"] = device.cpu_usage
        result["memory_usage"] = device.memory_usage
        result["temperature"] = device.temperature
    
    # Record command in history
    command_record = {
        "device_id": device_id,
        "command": request.command.value,
        "executed_at": datetime.now().isoformat(),
        "result": result
    }
    COMMAND_HISTORY.append(command_record)
    
    return RemoteCommandResponse(
        status="success",
        message=f"Command '{request.command.value}' executed on device {device.name}",
        device_id=device_id,
        command=request.command,
        executed_at=datetime.now(),
        result=result
    )


@router.post("/edge-devices/{device_id}/reboot", tags=["edge-devices"], summary="Reboot device")
def reboot_device(
    device_id: str = Path(..., description="Device ID"),
    request: RebootDeviceRequest = None
) -> RebootDeviceResponse:
    """
    Reboot an edge device.
    
    Args:
        device_id: The device ID
        request: Reboot request with optional force flag
        
    Returns:
        RebootDeviceResponse: Reboot confirmation
        
    Raises:
        HTTPException: 404 if device not found
    """
    if device_id not in DEVICES_DB:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    device = DEVICES_DB[device_id]
    
    # Simulate reboot (in reality, this would be async)
    now = datetime.now()
    device.last_seen = now
    _save_devices_to_storage()
    
    # Record reboot in history
    command_record = {
        "device_id": device_id,
        "command": "reboot",
        "force": request.force if request else False,
        "executed_at": now.isoformat()
    }
    COMMAND_HISTORY.append(command_record)
    
    return RebootDeviceResponse(
        status="success",
        message=f"Device {device.name} reboot initiated",
        device_id=device_id,
        rebooted_at=now
    )


class ProvisionDeviceRequest(BaseModel):
    """Request model for device provisioning"""
    name: str = Field(..., description="Device name")
    platform: PlatformType = Field(default=PlatformType.ATLAS, description="Device platform")
    model: str = Field(default="TEE-HPM-001", description="Device model")
    location: str = Field(default="data-center-1", description="Device location")
    cores: int = Field(default=4, ge=1, le=64)
    memory_gb: int = Field(default=16, ge=1, le=256)


class ProvisionDeviceResponse(BaseModel):
    """Response model for device provisioning"""
    status: str
    message: str
    device_id: str
    device: Optional[EdgeDevice] = None
    provisioned_at: datetime


@router.post("/edge-devices", tags=["edge-devices"], summary="Provision new edge device")
def provision_device(request: ProvisionDeviceRequest) -> ProvisionDeviceResponse:
    """
    Provision a new edge device with TEE and TPM capabilities.
    
    Args:
        request: Device provisioning parameters
        
    Returns:
        ProvisionDeviceResponse: Newly provisioned device details
    """
    now = datetime.now()
    device_id = f"edge-{str(uuid.uuid4())[:8]}"
    
    # Create new device
    new_device = EdgeDevice(
        id=device_id,
        name=request.name,
        platform=request.platform,
        status=DeviceStatus.ONLINE,
        cpu_usage=random.uniform(5, 25),
        memory_usage=random.uniform(10, 30),
        temperature=random.uniform(45, 55),
        uptime=86400,  # 1 day
        last_seen=now.isoformat(),
        firmware_version="v2.4.1",
        tee_enabled=True,
        tpm_attestation=True,
        location=request.location,
        model=request.model,
        cores=request.cores,
        memory_gb=request.memory_gb,
    )
    
    # Store device
    DEVICES_DB[device_id] = new_device
    _save_devices_to_storage()
    
    # Initialize history for new device
    initial_history = DeviceHistory(
        timestamp=now.isoformat(),
        device_id=device_id,
        cpu_usage=new_device.cpu_usage,
        memory_usage=new_device.memory_usage,
        temperature=new_device.temperature,
        status=new_device.status,
    )
    if device_id not in DEVICE_HISTORY_DB:
        DEVICE_HISTORY_DB[device_id] = []
    DEVICE_HISTORY_DB[device_id].append(initial_history)
    _save_history_to_storage()
    
    print(f"Device provisioned: {device_id} ({request.name})")
    
    return ProvisionDeviceResponse(
        status="success",
        message=f"Device {request.name} provisioned successfully",
        device_id=device_id,
        device=new_device,
        provisioned_at=now
    )


# ============================================================================
# LIFECYCLE
# ============================================================================

# Initialize demo data on module load
_load_devices_from_storage()
_load_history_from_storage()
_initialize_demo_devices()
