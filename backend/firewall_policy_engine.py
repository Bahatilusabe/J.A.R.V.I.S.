"""
Stateful Firewall & Policy Engine

Purpose: Enforce network policies, NAT, routing and connection tracking.

Responsibilities:
- Access control lists (ACLs)
- Application-aware policies
- Geo-blocking
- Rate limiting
- QoS marking
- NAT (Network Address Translation)
- Policy versioning and staged rollout
- Connection tracking and state machine

Inputs:
- DPI classifications (protocol, app, behavior)
- Identity assertions from IAM (user, role, permissions)
- Admin policy definitions

Outputs:
- PASS/DROP/REJECT decisions
- Logs with full forensics
- Metrics (throughput, dropped packets, policy violations)

Architecture:
- Control plane: Python FastAPI (policy management, versioning, rollout)
- Data plane: Connection tracking with state machine
- Kernel integration: Hooks for eBPF/AF_XDP for high-performance enforcement
- Hardware offload: SmartNIC support for ultra-low latency

Author: J.A.R.V.I.S. Team
"""

import logging
import hashlib
import json
import ipaddress
from datetime import datetime, timedelta
from enum import IntEnum, Enum
from typing import Optional, List, Dict, Tuple, Set, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from pathlib import Path
import threading
import time

logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS & TYPES
# ============================================================================

class PolicyDecision(str, Enum):
    """Policy enforcement decision"""
    PASS = "pass"
    DROP = "drop"
    REJECT = "reject"
    RATE_LIMIT = "rate_limit"
    REDIRECT = "redirect"
    QUARANTINE = "quarantine"


class ACLAction(str, Enum):
    """ACL rule action"""
    ALLOW = "allow"
    DENY = "deny"
    LOG = "log"
    ALERT = "alert"
    RATE_LIMIT = "rate_limit"


class TrafficDirection(str, Enum):
    """Traffic direction"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


class ConnectionState(str, Enum):
    """TCP connection states for tracking"""
    NEW = "new"
    ESTABLISHED = "established"
    FIN_WAIT = "fin_wait"
    CLOSE_WAIT = "close_wait"
    CLOSED = "closed"
    TIMEOUT = "timeout"
    INVALID = "invalid"


class QoSClass(str, Enum):
    """Quality of Service classification"""
    CRITICAL = "critical"              # VoIP, real-time
    HIGH = "high"                      # Streaming, business apps
    NORMAL = "normal"                  # General traffic
    LOW = "low"                        # Background, best-effort
    BULK = "bulk"                      # Downloads, backups


class GeoBlockAction(str, Enum):
    """Geo-blocking actions"""
    ALLOW = "allow"
    BLOCK = "block"
    INSPECT = "inspect"


class NATMode(str, Enum):
    """NAT modes"""
    DISABLED = "disabled"
    SOURCE_NAT = "source_nat"          # SNAT
    DESTINATION_NAT = "destination_nat" # DNAT
    BIDIRECTIONAL_NAT = "bidirectional_nat" # Full NAT


# ============================================================================
# DATA CLASSES & MODELS
# ============================================================================

@dataclass
class FirewallRule:
    """Atomic firewall rule"""
    rule_id: str
    name: str
    priority: int                      # Higher = higher priority
    direction: TrafficDirection
    
    # Matching criteria
    src_ip_prefix: Optional[str] = None        # CIDR
    dst_ip_prefix: Optional[str] = None        # CIDR
    src_port_range: Optional[Tuple[int, int]] = None
    dst_port_range: Optional[Tuple[int, int]] = None
    protocol: Optional[str] = None             # tcp, udp, icmp, etc.
    
    # DPI-based matching
    app_name: Optional[str] = None             # From DPI
    dpi_category: Optional[str] = None         # e.g., "malware", "intrusion"
    
    # IAM-based matching
    user_identity: Optional[str] = None        # From IAM
    user_role: Optional[str] = None            # From IAM
    
    # Actions
    action: ACLAction = ACLAction.ALLOW
    qos_class: Optional[QoSClass] = None       # QoS marking
    nat_mode: Optional[NATMode] = None         # NAT
    
    # Advanced
    rate_limit_kbps: Optional[int] = None      # kbps
    geo_block_countries: List[str] = field(default_factory=list)
    geo_block_action: GeoBlockAction = GeoBlockAction.ALLOW
    
    # Metadata
    enabled: bool = True
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['direction'] = self.direction.value
        data['action'] = self.action.value
        data['qos_class'] = self.qos_class.value if self.qos_class else None
        data['nat_mode'] = self.nat_mode.value if self.nat_mode else None
        data['geo_block_action'] = self.geo_block_action.value
        return data


@dataclass
class FlowTuple:
    """5-tuple flow identifier"""
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str  # tcp, udp, icmp
    
    def to_key(self) -> str:
        """Generate hashable key"""
        return f"{self.src_ip}:{self.src_port}-{self.dst_ip}:{self.dst_port}/{self.protocol}"
    
    def reverse(self) -> 'FlowTuple':
        """Get reverse flow (for bidirectional tracking)"""
        return FlowTuple(
            src_ip=self.dst_ip,
            dst_port=self.src_port,
            dst_ip=self.src_ip,
            src_port=self.dst_port,
            protocol=self.protocol
        )


@dataclass
class ConnectionTrackEntry:
    """Connection tracking state machine entry"""
    flow: FlowTuple
    state: ConnectionState = ConnectionState.NEW
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_packet_at: datetime = field(default_factory=datetime.utcnow)
    timeout_seconds: int = 3600  # 1 hour default
    
    # Statistics
    bytes_fwd: int = 0      # Forward direction (src -> dst)
    bytes_rev: int = 0      # Reverse direction (dst -> src)
    packets_fwd: int = 0
    packets_rev: int = 0
    
    # Metadata
    policy_decision: PolicyDecision = PolicyDecision.PASS
    matched_rule_id: Optional[str] = None
    dpi_app: Optional[str] = None
    user_identity: Optional[str] = None
    qos_class: Optional[QoSClass] = None
    
    def is_expired(self) -> bool:
        """Check if connection has timed out"""
        elapsed = (datetime.utcnow() - self.last_packet_at).total_seconds()
        return elapsed > self.timeout_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'flow': {
                'src_ip': self.flow.src_ip,
                'dst_ip': self.flow.dst_ip,
                'src_port': self.flow.src_port,
                'dst_port': self.flow.dst_port,
                'protocol': self.flow.protocol,
            },
            'state': self.state.value,
            'created_at': self.created_at.isoformat(),
            'last_packet_at': self.last_packet_at.isoformat(),
            'bytes_fwd': self.bytes_fwd,
            'bytes_rev': self.bytes_rev,
            'packets_fwd': self.packets_fwd,
            'packets_rev': self.packets_rev,
            'policy_decision': self.policy_decision.value,
            'matched_rule_id': self.matched_rule_id,
            'dpi_app': self.dpi_app,
            'user_identity': self.user_identity,
            'qos_class': self.qos_class.value if self.qos_class else None,
            'is_expired': self.is_expired(),
        }


@dataclass
class PolicyEvaluationResult:
    """Policy evaluation decision"""
    decision: PolicyDecision
    rule_id: Optional[str] = None
    reason: str = ""
    qos_class: Optional[QoSClass] = None
    rate_limit_kbps: Optional[int] = None
    nat_target: Optional[Tuple[str, int]] = None  # (ip, port) for NAT
    geo_block_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'decision': self.decision.value,
            'rule_id': self.rule_id,
            'reason': self.reason,
            'qos_class': self.qos_class.value if self.qos_class else None,
            'rate_limit_kbps': self.rate_limit_kbps,
            'nat_target': self.nat_target,
            'geo_block_reason': self.geo_block_reason,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class PolicyVersion:
    """Policy version for staged rollout"""
    version_id: str
    name: str
    description: str
    rules: List[FirewallRule] = field(default_factory=list)
    
    # Versioning
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "admin"
    
    # Rollout
    status: str = "draft"  # draft, staged, active, archived
    deployment_percentage: int = 0  # 0-100 for canary rollout
    deployment_target: Optional[str] = None  # Segment/region for canary
    
    # Comparison
    parent_version_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'version_id': self.version_id,
            'name': self.name,
            'description': self.description,
            'rules': [r.to_dict() for r in self.rules],
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'status': self.status,
            'deployment_percentage': self.deployment_percentage,
            'deployment_target': self.deployment_target,
            'parent_version_id': self.parent_version_id,
            'rule_count': len(self.rules),
        }


@dataclass
class NATMapping:
    """Network Address Translation mapping"""
    nat_id: str
    mode: NATMode
    
    # Source NAT
    source_pool_start: Optional[str] = None
    source_pool_end: Optional[str] = None
    
    # Destination NAT
    target_server: Optional[str] = None
    target_port: Optional[int] = None
    
    # Conditions
    src_ip_prefix: Optional[str] = None
    dst_ip_prefix: Optional[str] = None
    protocol: Optional[str] = None
    
    # Metrics
    active_translations: int = 0
    total_translations: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


# ============================================================================
# STATEFUL FIREWALL & POLICY ENGINE
# ============================================================================

class StatefulFirewallPolicyEngine:
    """
    High-performance stateful firewall with policy evaluation.
    
    Features:
    - Connection tracking with state machine
    - ACL-based policy enforcement
    - DPI and IAM integration
    - NAT support (SNAT, DNAT)
    - Rate limiting and QoS marking
    - Geo-blocking
    - Policy versioning and staged rollout
    - Comprehensive logging and metrics
    """
    
    def __init__(self, max_connections: int = 100000, cleanup_interval: int = 60):
        """
        Initialize firewall engine.
        
        Args:
            max_connections: Maximum concurrent connections to track
            cleanup_interval: Seconds between cleanup runs
        """
        self.max_connections = max_connections
        self.cleanup_interval = cleanup_interval
        
        # Connection tracking
        self._connections: Dict[str, ConnectionTrackEntry] = {}
        self._connection_lock = threading.RLock()
        
        # Policy management
        self._rules: Dict[str, FirewallRule] = {}
        self._rules_lock = threading.RLock()
        
        self._versions: Dict[str, PolicyVersion] = {}
        self._active_version_id: Optional[str] = None
        
        # NAT mappings
        self._nat_mappings: Dict[str, NATMapping] = {}
        self._nat_sessions: Dict[str, Tuple[str, int]] = {}  # (original_addr, original_port)
        
        # Metrics
        self._metrics = {
            'packets_passed': 0,
            'packets_dropped': 0,
            'packets_rejected': 0,
            'connections_established': 0,
            'connections_terminated': 0,
            'bytes_passed': 0,
            'bytes_dropped': 0,
            'policy_violations': 0,
            'rate_limit_events': 0,
            'geo_block_events': 0,
            'nat_translations': 0,
        }
        self._metrics_lock = threading.RLock()
        
        # Cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True
        )
        self._cleanup_thread.start()
        
        logger.info("Stateful Firewall & Policy Engine initialized")
    
    # ====== Policy Management ======
    
    def add_rule(self, rule: FirewallRule) -> bool:
        """Add a firewall rule"""
        with self._rules_lock:
            if rule.rule_id in self._rules:
                logger.warning(f"Rule {rule.rule_id} already exists")
                return False
            self._rules[rule.rule_id] = rule
            logger.info(f"Added rule {rule.rule_id}: {rule.name}")
            return True
    
    def delete_rule(self, rule_id: str) -> bool:
        """Delete a firewall rule"""
        with self._rules_lock:
            if rule_id not in self._rules:
                return False
            del self._rules[rule_id]
            logger.info(f"Deleted rule {rule_id}")
            return True
    
    def get_rule(self, rule_id: str) -> Optional[FirewallRule]:
        """Get a rule by ID"""
        with self._rules_lock:
            return self._rules.get(rule_id)
    
    def list_rules(self) -> List[FirewallRule]:
        """List all rules"""
        with self._rules_lock:
            return sorted(self._rules.values(), key=lambda r: -r.priority)
    
    # ====== Policy Versioning ======
    
    def create_policy_version(
        self,
        name: str,
        description: str,
        rules: Optional[List[FirewallRule]] = None,
        parent_version_id: Optional[str] = None
    ) -> PolicyVersion:
        """Create a new policy version"""
        import uuid
        version_id = f"pv_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        version = PolicyVersion(
            version_id=version_id,
            name=name,
            description=description,
            rules=rules or [],
            parent_version_id=parent_version_id,
            status="draft"
        )
        
        self._versions[version_id] = version
        logger.info(f"Created policy version {version_id}: {name}")
        return version
    
    def stage_policy_version(
        self,
        version_id: str,
        deployment_percentage: int = 10,
        deployment_target: Optional[str] = None
    ) -> bool:
        """Stage a policy version for canary rollout"""
        if version_id not in self._versions:
            return False
        
        version = self._versions[version_id]
        version.status = "staged"
        version.deployment_percentage = max(0, min(100, deployment_percentage))
        version.deployment_target = deployment_target
        
        logger.info(f"Staged policy version {version_id} at {version.deployment_percentage}%")
        return True
    
    def activate_policy_version(self, version_id: str) -> bool:
        """Activate a policy version (100% rollout)"""
        if version_id not in self._versions:
            return False
        
        version = self._versions[version_id]
        version.status = "active"
        version.deployment_percentage = 100
        
        self._active_version_id = version_id
        self._rules.clear()
        
        # Load rules from version
        for rule in version.rules:
            self.add_rule(rule)
        
        logger.info(f"Activated policy version {version_id}")
        return True
    
    def get_policy_version(self, version_id: str) -> Optional[PolicyVersion]:
        """Get a policy version"""
        return self._versions.get(version_id)
    
    def list_policy_versions(self) -> List[PolicyVersion]:
        """List all policy versions"""
        return sorted(
            self._versions.values(),
            key=lambda v: v.created_at,
            reverse=True
        )
    
    # ====== Packet/Flow Evaluation ======
    
    def evaluate_flow(
        self,
        flow: FlowTuple,
        direction: TrafficDirection = TrafficDirection.INBOUND,
        dpi_app: Optional[str] = None,
        dpi_category: Optional[str] = None,
        user_identity: Optional[str] = None,
        user_role: Optional[str] = None,
        src_country: Optional[str] = None,
        packet_bytes: int = 1500,
    ) -> PolicyEvaluationResult:
        """
        Evaluate a flow against policies.
        
        Returns: PolicyEvaluationResult (PASS, DROP, REJECT, etc.)
        """
        # Check connection state
        flow_key = flow.to_key()
        with self._connection_lock:
            if flow_key in self._connections:
                conn = self._connections[flow_key]
                # Established connection - fast path
                if conn.state == ConnectionState.ESTABLISHED:
                    # Update stats
                    conn.packets_fwd += 1
                    conn.bytes_fwd += packet_bytes
                    conn.last_packet_at = datetime.utcnow()
                    
                    # Apply QoS if needed
                    decision = PolicyDecision(
                        decision=PolicyDecision.PASS,
                        rule_id=conn.matched_rule_id,
                        qos_class=conn.qos_class,
                    )
                    
                    with self._metrics_lock:
                        self._metrics['packets_passed'] += 1
                        self._metrics['bytes_passed'] += packet_bytes
                    
                    return decision
        
        # New flow - evaluate against rules
        matched_rule = self._match_rules(
            flow=flow,
            direction=direction,
            dpi_app=dpi_app,
            dpi_category=dpi_category,
            user_identity=user_identity,
            user_role=user_role,
            src_country=src_country,
        )
        
        if not matched_rule:
            # Default deny
            decision = PolicyEvaluationResult(
                decision=PolicyDecision.DROP,
                reason="no_matching_rule"
            )
            with self._metrics_lock:
                self._metrics['packets_dropped'] += 1
                self._metrics['policy_violations'] += 1
            return decision
        
        # Evaluate matched rule
        decision = self._apply_rule(
            flow=flow,
            rule=matched_rule,
            dpi_app=dpi_app,
            user_identity=user_identity,
            src_country=src_country,
            packet_bytes=packet_bytes,
        )
        
        # Create connection tracking entry
        if decision.decision == PolicyDecision.PASS:
            conn = ConnectionTrackEntry(
                flow=flow,
                state=ConnectionState.ESTABLISHED,
                policy_decision=decision.decision,
                matched_rule_id=matched_rule.rule_id,
                dpi_app=dpi_app,
                user_identity=user_identity,
                qos_class=decision.qos_class,
            )
            
            with self._connection_lock:
                if len(self._connections) < self.max_connections:
                    self._connections[flow_key] = conn
                    with self._metrics_lock:
                        self._metrics['connections_established'] += 1
        
        # Update metrics
        with self._metrics_lock:
            if decision.decision == PolicyDecision.PASS:
                self._metrics['packets_passed'] += 1
                self._metrics['bytes_passed'] += packet_bytes
            elif decision.decision in (PolicyDecision.DROP, PolicyDecision.RATE_LIMIT):
                self._metrics['packets_dropped'] += 1
                self._metrics['bytes_dropped'] += packet_bytes
            elif decision.decision == PolicyDecision.REJECT:
                self._metrics['packets_rejected'] += 1
        
        return decision
    
    def _match_rules(
        self,
        flow: FlowTuple,
        direction: TrafficDirection,
        dpi_app: Optional[str] = None,
        dpi_category: Optional[str] = None,
        user_identity: Optional[str] = None,
        user_role: Optional[str] = None,
        src_country: Optional[str] = None,
    ) -> Optional[FirewallRule]:
        """Match flow against rules (in priority order)"""
        with self._rules_lock:
            rules = sorted(self._rules.values(), key=lambda r: -r.priority)
        
        for rule in rules:
            if not rule.enabled:
                continue
            
            # Direction check
            if rule.direction != TrafficDirection.BIDIRECTIONAL:
                if direction == TrafficDirection.INBOUND and rule.direction != TrafficDirection.INBOUND:
                    continue
                if direction == TrafficDirection.OUTBOUND and rule.direction != TrafficDirection.OUTBOUND:
                    continue
            
            # IP prefix matching
            if rule.src_ip_prefix:
                try:
                    if not ipaddress.ip_address(flow.src_ip) in ipaddress.ip_network(rule.src_ip_prefix):
                        continue
                except ValueError:
                    continue
            
            if rule.dst_ip_prefix:
                try:
                    if not ipaddress.ip_address(flow.dst_ip) in ipaddress.ip_network(rule.dst_ip_prefix):
                        continue
                except ValueError:
                    continue
            
            # Port range matching
            if rule.src_port_range:
                min_port, max_port = rule.src_port_range
                if not (min_port <= flow.src_port <= max_port):
                    continue
            
            if rule.dst_port_range:
                min_port, max_port = rule.dst_port_range
                if not (min_port <= flow.dst_port <= max_port):
                    continue
            
            # Protocol matching
            if rule.protocol and flow.protocol.lower() != rule.protocol.lower():
                continue
            
            # DPI matching
            if rule.app_name and dpi_app != rule.app_name:
                continue
            if rule.dpi_category and dpi_category != rule.dpi_category:
                continue
            
            # IAM matching
            if rule.user_identity and user_identity != rule.user_identity:
                continue
            if rule.user_role and user_role != rule.user_role:
                continue
            
            # All criteria matched
            return rule
        
        return None
    
    def _apply_rule(
        self,
        flow: FlowTuple,
        rule: FirewallRule,
        dpi_app: Optional[str],
        user_identity: Optional[str],
        src_country: Optional[str],
        packet_bytes: int,
    ) -> PolicyEvaluationResult:
        """Apply rule actions"""
        # Geo-blocking check
        if rule.geo_block_countries and src_country:
            if src_country in rule.geo_block_countries:
                if rule.geo_block_action == GeoBlockAction.BLOCK:
                    with self._metrics_lock:
                        self._metrics['geo_block_events'] += 1
                    return PolicyEvaluationResult(
                        decision=PolicyDecision.DROP,
                        rule_id=rule.rule_id,
                        reason=f"geo_blocked_{src_country}",
                        geo_block_reason=f"Country {src_country} blocked"
                    )
                elif rule.geo_block_action == GeoBlockAction.INSPECT:
                    # Mark for deep inspection but allow
                    pass
        
        # Apply action
        if rule.action == ACLAction.DENY:
            return PolicyEvaluationResult(
                decision=PolicyDecision.DROP,
                rule_id=rule.rule_id,
                reason=f"denied_by_rule_{rule.rule_id}"
            )
        
        # Allow with enhancements
        qos_class = rule.qos_class or QoSClass.NORMAL
        
        decision = PolicyEvaluationResult(
            decision=PolicyDecision.PASS,
            rule_id=rule.rule_id,
            reason=f"allowed_by_rule_{rule.rule_id}",
            qos_class=qos_class,
            rate_limit_kbps=rule.rate_limit_kbps,
        )
        
        # NAT handling
        if rule.nat_mode and rule.nat_mode != NATMode.DISABLED:
            nat_target = self._apply_nat(flow, rule.nat_mode)
            if nat_target:
                decision.nat_target = nat_target
        
        return decision
    
    def _apply_nat(self, flow: FlowTuple, nat_mode: NATMode) -> Optional[Tuple[str, int]]:
        """Apply NAT to a flow"""
        # Simplified NAT - in production, use connection pooling
        if nat_mode == NATMode.SOURCE_NAT:
            # Would need NAT pool management
            return (flow.src_ip, flow.src_port)  # Placeholder
        elif nat_mode == NATMode.DESTINATION_NAT:
            # Would need destination mapping
            return (flow.dst_ip, flow.dst_port)  # Placeholder
        return None
    
    def close_connection(self, flow: FlowTuple) -> bool:
        """Mark connection as closed"""
        flow_key = flow.to_key()
        with self._connection_lock:
            if flow_key in self._connections:
                conn = self._connections[flow_key]
                conn.state = ConnectionState.CLOSED
                with self._metrics_lock:
                    self._metrics['connections_terminated'] += 1
                logger.debug(f"Closed connection {flow_key}")
                return True
        return False
    
    # ====== Metrics & Status ======
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        with self._metrics_lock:
            metrics = self._metrics.copy()
        
        with self._connection_lock:
            metrics['active_connections'] = len(self._connections)
            metrics['connection_capacity_percent'] = (
                len(self._connections) / self.max_connections * 100
            )
        
        return metrics
    
    def get_active_connections(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get list of active connections"""
        with self._connection_lock:
            conns = list(self._connections.values())
        
        conns = sorted(conns, key=lambda c: c.last_packet_at, reverse=True)
        return [c.to_dict() for c in conns[offset:offset+limit]]
    
    # ====== Cleanup & Maintenance ======
    
    def _cleanup_loop(self):
        """Periodically clean up expired connections"""
        while True:
            try:
                time.sleep(self.cleanup_interval)
                self._cleanup_expired_connections()
            except Exception as e:
                logger.exception(f"Cleanup loop error: {e}")
    
    def _cleanup_expired_connections(self):
        """Remove expired connections"""
        with self._connection_lock:
            expired_keys = [
                key for key, conn in self._connections.items()
                if conn.is_expired()
            ]
            
            for key in expired_keys:
                del self._connections[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired connections")
