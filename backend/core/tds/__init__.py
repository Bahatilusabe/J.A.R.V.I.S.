"""
Tactical Defense Shield (TDS) Module
======================================

Zero-trust security engine combining device attestation, deep packet inspection,
encrypted session management, and real-time threat detection.

Components:
-----------
- zero_trust: Device attestation and micro-segmentation
- dpi_engine: Deep packet inspection with signature matching
- vpn_gateway: Encrypted session management with anomaly detection
- packet_inspector: Raw packet parsing and extraction

Usage:
------
from backend.core.tds import (
    ZeroTrustEngine,
    DpiEngine,
    VPNGateway,
    PacketInspector
)

or per-module:

from backend.core.tds.zero_trust import ZeroTrustEngine, attest_device
from backend.core.tds.dpi_engine import DpiEngine, load_signatures
from backend.core.tds.vpn_gateway import VPNGateway, WireGuardManager
from backend.core.tds.packet_inspector import PacketInspector
"""

from .zero_trust import (
    attest_device,
    enforce_microsegmentation,
    generate_handshake,
    verify_biometric_token,
    AttestationError
)

from .dpi_engine import (
    DpiEngine,
    load_signatures,
)

from .vpn_gateway import (
    VPNGateway,
    WireGuardManager,
    KeyStore,
    AnomalyDetector
)

from .packet_inspector import (
    parse_packet
)

# DPI verdict constants
DPI_VERDICT_DROP = "drop"
DPI_VERDICT_ACCEPT = "accept"
DPI_VERDICT_ALERT = "alert"

__all__ = [
    # Zero-trust module
    'attest_device',
    'enforce_microsegmentation',
    'generate_handshake',
    'verify_biometric_token',
    'AttestationError',
    
    # DPI module
    'DpiEngine',
    'load_signatures',
    'DPI_VERDICT_DROP',
    'DPI_VERDICT_ACCEPT',
    'DPI_VERDICT_ALERT',
    
    # VPN gateway module
    'VPNGateway',
    'WireGuardManager',
    'KeyStore',
    'AnomalyDetector',
    
    # Packet inspection
    'parse_packet',
]

__version__ = "1.0.0"
__module_name__ = "Tactical Defense Shield (TDS)"
