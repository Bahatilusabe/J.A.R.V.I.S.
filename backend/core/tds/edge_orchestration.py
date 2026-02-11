"""
Edge Orchestration System for TDS Module

Provides distributed gateway coordination and load balancing for TDS across multiple edge locations:
- Multi-gateway deployment management
- Intelligent load balancing and traffic distribution
- Failover and redundancy mechanisms
- Gateway health monitoring and auto-recovery
- Distributed session management and synchronization
- Policy and configuration synchronization
- Geographic distribution awareness

Architecture:
    Central Control Plane
            ↓
    ┌───────────────────────┐
    │  Edge Orchestrator    │
    │  (Session Coordinator) │
    │  (Load Balancer)      │
    │  (Health Monitor)     │
    └───────────────────────┘
            ↓
    ┌─────────┬─────────┬──────────┐
    ↓         ↓         ↓          ↓
  Gateway  Gateway  Gateway    Gateway
  US-East  US-West  EU-North   APAC
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import hashlib

logger = logging.getLogger(__name__)


class GatewayStatus(Enum):
    """Gateway operational status."""
    HEALTHY = "healthy"              # Normal operation
    DEGRADED = "degraded"            # Reduced capacity
    UNHEALTHY = "unhealthy"          # Not operational
    MAINTENANCE = "maintenance"      # Planned downtime
    UNKNOWN = "unknown"              # Status unknown


class LoadBalancingStrategy(Enum):
    """Traffic distribution strategy."""
    ROUND_ROBIN = "round_robin"              # Simple round-robin
    LEAST_CONNECTIONS = "least_connections"  # Route to least busy
    WEIGHTED = "weighted"                    # Based on capacity
    GEOGRAPHIC = "geographic"                # Route by location
    LATENCY_BASED = "latency_based"         # Route by latency


@dataclass
class GatewayMetrics:
    """Real-time metrics for a gateway."""
    gateway_id: str
    timestamp: datetime
    
    # Connection metrics
    active_sessions: int = 0
    total_sessions: int = 0
    session_throughput_mbps: float = 0.0
    
    # Health metrics
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    disk_usage_percent: float = 0.0
    network_latency_ms: float = 0.0
    
    # Packet processing
    packets_processed: int = 0
    packets_dropped: int = 0
    detection_rate: float = 0.95
    false_positive_rate: float = 0.01
    
    # Uptime
    uptime_seconds: int = 0
    last_health_check: datetime = field(default_factory=datetime.now)


@dataclass
class GatewayConfig:
    """Configuration for a gateway node."""
    gateway_id: str
    location: str                     # e.g., "us-east-1", "eu-north-1"
    endpoint_url: str                # REST API endpoint
    grpc_endpoint: Optional[str] = None  # gRPC endpoint for streaming
    
    # Capacity
    max_sessions: int = 10000
    max_throughput_gbps: float = 100.0
    capacity_weight: float = 1.0     # For weighted load balancing
    
    # Priority
    priority: int = 0                 # Higher = preferred
    is_backup: bool = False          # Is this a backup gateway?
    
    # Failover
    failover_timeout_seconds: int = 30
    health_check_interval_seconds: int = 10


@dataclass
class DistributedSession:
    """Session distributed across gateways."""
    session_id: str
    device_id: str
    primary_gateway: str             # Primary gateway handling session
    backup_gateway: Optional[str] = None  # Backup gateway if failover
    state: Dict[str, Any] = field(default_factory=dict)  # Session state
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    risk_score: float = 0.0


@dataclass
class SyncPoint:
    """State synchronization point across gateways."""
    sync_id: str
    timestamp: datetime
    gateway_ids: List[str]           # Gateways involved
    data_type: str                   # "session", "policy", "rules", etc.
    payload: Dict[str, Any]
    confirmed_gateways: List[str] = field(default_factory=list)


class EdgeOrchestrator:
    """
    Orchestrates TDS across multiple edge gateways.
    
    Responsibilities:
    - Discover and manage gateway nodes
    - Monitor gateway health and performance
    - Distribute sessions across gateways
    - Handle failover and failback
    - Synchronize state across gateways
    - Optimize traffic distribution
    """
    
    def __init__(self):
        """Initialize edge orchestrator."""
        # Gateway management
        self.gateways: Dict[str, GatewayConfig] = {}
        self.gateway_metrics: Dict[str, GatewayMetrics] = {}
        self.gateway_status: Dict[str, GatewayStatus] = defaultdict(
            lambda: GatewayStatus.UNKNOWN
        )
        
        # Session management
        self.sessions: Dict[str, DistributedSession] = {}
        self.session_gateway_map: Dict[str, str] = {}  # session_id -> primary_gateway
        
        # Synchronization
        self.sync_points: Dict[str, SyncPoint] = {}
        self.sync_log: List[SyncPoint] = []
        
        # Load balancing
        self.load_balancing_strategy = LoadBalancingStrategy.LEAST_CONNECTIONS
        self.gateway_load: Dict[str, int] = defaultdict(int)
        
        # Failover tracking
        self.failover_history: List[Dict[str, Any]] = []
        self.failover_in_progress: Dict[str, str] = {}  # session_id -> new_gateway
        
        # Lock for thread-safety
        self._lock = threading.RLock()
        
        # Metrics
        self.metrics = {
            "total_gateways": 0,
            "healthy_gateways": 0,
            "sessions_distributed": 0,
            "failovers_triggered": 0,
            "sync_operations": 0,
        }
        
        logger.info("Edge Orchestrator initialized")
    
    def register_gateway(self, config: GatewayConfig) -> None:
        """
        Register a gateway node.
        
        Args:
            config: Gateway configuration
        """
        with self._lock:
            self.gateways[config.gateway_id] = config
            self.gateway_status[config.gateway_id] = GatewayStatus.UNKNOWN
            self.metrics["total_gateways"] = len(self.gateways)
        
        logger.info(f"Gateway registered: {config.gateway_id} ({config.location})")
    
    def unregister_gateway(self, gateway_id: str) -> None:
        """
        Unregister a gateway node.
        
        Args:
            gateway_id: ID of gateway to remove
        """
        with self._lock:
            if gateway_id in self.gateways:
                del self.gateways[gateway_id]
            
            # Migrate sessions from this gateway
            sessions_to_migrate = [
                sid for sid, gw in self.session_gateway_map.items()
                if gw == gateway_id
            ]
            
            for session_id in sessions_to_migrate:
                new_gateway = self._find_best_gateway(exclude=gateway_id)
                if new_gateway:
                    self._migrate_session(session_id, gateway_id, new_gateway)
            
            self.metrics["total_gateways"] = len(self.gateways)
        
        logger.info(f"Gateway unregistered: {gateway_id}")
    
    def update_gateway_metrics(self, gateway_id: str, metrics: GatewayMetrics) -> None:
        """
        Update metrics for a gateway.
        
        Args:
            gateway_id: Gateway identifier
            metrics: Current metrics
        """
        with self._lock:
            self.gateway_metrics[gateway_id] = metrics
            
            # Determine health status based on metrics
            new_status = self._evaluate_gateway_health(gateway_id, metrics)
            old_status = self.gateway_status.get(gateway_id)
            
            if new_status != old_status:
                self.gateway_status[gateway_id] = new_status
                
                if new_status == GatewayStatus.UNHEALTHY:
                    logger.error(f"Gateway became unhealthy: {gateway_id}")
                    self._handle_gateway_failure(gateway_id)
                elif old_status == GatewayStatus.UNHEALTHY:
                    logger.info(f"Gateway recovered: {gateway_id}")
            
            # Update load tracking
            self.gateway_load[gateway_id] = metrics.active_sessions
    
    def _evaluate_gateway_health(
        self,
        gateway_id: str,
        metrics: GatewayMetrics,
    ) -> GatewayStatus:
        """Evaluate gateway health based on metrics."""
        # Critical thresholds
        if metrics.cpu_usage_percent > 95 or metrics.memory_usage_percent > 90:
            return GatewayStatus.UNHEALTHY
        
        if metrics.packets_dropped > metrics.packets_processed * 0.01:  # > 1% drop
            return GatewayStatus.UNHEALTHY
        
        if metrics.network_latency_ms > 500:
            return GatewayStatus.UNHEALTHY
        
        # Degraded thresholds
        if metrics.cpu_usage_percent > 85 or metrics.memory_usage_percent > 80:
            return GatewayStatus.DEGRADED
        
        if metrics.network_latency_ms > 250:
            return GatewayStatus.DEGRADED
        
        # Check capacity
        config = self.gateways.get(gateway_id)
        if config and metrics.active_sessions > config.max_sessions * 0.9:
            return GatewayStatus.DEGRADED
        
        return GatewayStatus.HEALTHY
    
    def distribute_session(
        self,
        session_id: str,
        device_id: str,
        risk_score: float,
    ) -> str:
        """
        Distribute a new session to an appropriate gateway.
        
        Args:
            session_id: VPN session identifier
            device_id: Device identifier
            risk_score: Risk score (0.0-1.0)
            
        Returns:
            Assigned gateway ID
        """
        with self._lock:
            # Select best gateway
            gateway_id = self._find_best_gateway()
            
            if not gateway_id:
                raise RuntimeError("No healthy gateways available")
            
            # Create distributed session
            session = DistributedSession(
                session_id=session_id,
                device_id=device_id,
                primary_gateway=gateway_id,
                risk_score=risk_score,
            )
            
            self.sessions[session_id] = session
            self.session_gateway_map[session_id] = gateway_id
            self.metrics["sessions_distributed"] += 1
            
            logger.info(
                f"Session distributed: {session_id} → {gateway_id} "
                f"(device={device_id}, risk={risk_score:.2f})"
            )
            
            return gateway_id
    
    def _find_best_gateway(self, exclude: Optional[str] = None) -> Optional[str]:
        """
        Find best gateway for new session.
        
        Uses load balancing strategy to select optimal gateway.
        """
        candidate_gateways = [
            gw_id for gw_id in self.gateways.keys()
            if (exclude is None or gw_id != exclude) and
            self.gateway_status.get(gw_id) in [GatewayStatus.HEALTHY, GatewayStatus.DEGRADED]
        ]
        
        if not candidate_gateways:
            return None
        
        if self.load_balancing_strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            # Route to gateway with fewest active sessions
            return min(
                candidate_gateways,
                key=lambda gw: self.gateway_load.get(gw, 0)
            )
        
        elif self.load_balancing_strategy == LoadBalancingStrategy.WEIGHTED:
            # Route based on capacity weight
            total_weight = sum(
                self.gateways[gw].capacity_weight
                for gw in candidate_gateways
            )
            
            if total_weight == 0:
                return candidate_gateways[0]
            
            # Choose gateway with lowest load relative to capacity
            best_gateway = min(
                candidate_gateways,
                key=lambda gw: self.gateway_load.get(gw, 0) /
                               self.gateways[gw].capacity_weight
            )
            return best_gateway
        
        elif self.load_balancing_strategy == LoadBalancingStrategy.GEOGRAPHIC:
            # Route to geographically closest gateway
            # (Would use actual location data in production)
            return candidate_gateways[0]
        
        else:  # Round-robin
            return candidate_gateways[0]
    
    def handle_gateway_failure(self, failed_gateway_id: str) -> List[str]:
        """
        Handle failure of a gateway.
        
        Migrates all sessions from failed gateway to healthy ones.
        
        Args:
            failed_gateway_id: ID of failed gateway
            
        Returns:
            List of migrated session IDs
        """
        return self._handle_gateway_failure(failed_gateway_id)
    
    def _handle_gateway_failure(self, failed_gateway_id: str) -> List[str]:
        """Internal handler for gateway failure."""
        with self._lock:
            self.gateway_status[failed_gateway_id] = GatewayStatus.UNHEALTHY
            
            # Find sessions on failed gateway
            failed_sessions = [
                sid for sid, gw in self.session_gateway_map.items()
                if gw == failed_gateway_id
            ]
            
            migrated_sessions = []
            
            for session_id in failed_sessions:
                # Find new gateway
                new_gateway = self._find_best_gateway(exclude=failed_gateway_id)
                
                if new_gateway:
                    self._migrate_session(session_id, failed_gateway_id, new_gateway)
                    migrated_sessions.append(session_id)
                    self.metrics["failovers_triggered"] += 1
                    
                    logger.warning(
                        f"Session failover: {session_id} "
                        f"{failed_gateway_id} → {new_gateway}"
                    )
            
            return migrated_sessions
    
    def _migrate_session(
        self,
        session_id: str,
        from_gateway: str,
        to_gateway: str,
    ) -> None:
        """Migrate a session from one gateway to another."""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        
        # Mark failover in progress
        self.failover_in_progress[session_id] = to_gateway
        
        # Update session state
        session.backup_gateway = to_gateway
        session.primary_gateway = to_gateway  # After failover complete
        
        # Update mapping
        self.session_gateway_map[session_id] = to_gateway
        
        # Record failover
        self.failover_history.append({
            "session_id": session_id,
            "from_gateway": from_gateway,
            "to_gateway": to_gateway,
            "timestamp": datetime.now().isoformat(),
        })
        
        # Clear failover marker
        del self.failover_in_progress[session_id]
    
    def synchronize_state(
        self,
        data_type: str,
        payload: Dict[str, Any],
        target_gateways: Optional[List[str]] = None,
    ) -> str:
        """
        Synchronize state across gateways.
        
        Args:
            data_type: Type of data ("session", "policy", "rules", etc.)
            payload: Data to synchronize
            target_gateways: Specific gateways to sync to (all if None)
            
        Returns:
            Sync point ID
        """
        with self._lock:
            # Determine target gateways
            if target_gateways is None:
                target_gateways = [
                    gw_id for gw_id, status in self.gateway_status.items()
                    if status in [GatewayStatus.HEALTHY, GatewayStatus.DEGRADED]
                ]
            
            # Create sync point
            sync_id = f"sync-{datetime.now().timestamp()}"
            sync_point = SyncPoint(
                sync_id=sync_id,
                timestamp=datetime.now(),
                gateway_ids=target_gateways,
                data_type=data_type,
                payload=payload,
            )
            
            self.sync_points[sync_id] = sync_point
            self.sync_log.append(sync_point)
            self.metrics["sync_operations"] += 1
            
            logger.info(
                f"State synchronization initiated: {sync_id} "
                f"({data_type}, {len(target_gateways)} gateways)"
            )
            
            return sync_id
    
    def confirm_sync(self, sync_id: str, gateway_id: str) -> bool:
        """
        Confirm sync operation from a gateway.
        
        Args:
            sync_id: Synchronization point ID
            gateway_id: Gateway confirming sync
            
        Returns:
            True if all gateways confirmed
        """
        with self._lock:
            sync_point = self.sync_points.get(sync_id)
            
            if not sync_point:
                return False
            
            if gateway_id not in sync_point.confirmed_gateways:
                sync_point.confirmed_gateways.append(gateway_id)
            
            # Check if all gateways confirmed
            all_confirmed = len(sync_point.confirmed_gateways) == len(sync_point.gateway_ids)
            
            if all_confirmed:
                logger.info(f"Sync point completed: {sync_id}")
            
            return all_confirmed
    
    def get_gateway_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report for all gateways."""
        with self._lock:
            report = {
                "timestamp": datetime.now().isoformat(),
                "total_gateways": len(self.gateways),
                "healthy_gateways": sum(
                    1 for status in self.gateway_status.values()
                    if status == GatewayStatus.HEALTHY
                ),
                "gateways": {},
            }
            
            for gw_id, config in self.gateways.items():
                metrics = self.gateway_metrics.get(gw_id)
                status = self.gateway_status.get(gw_id, GatewayStatus.UNKNOWN)
                
                report["gateways"][gw_id] = {
                    "location": config.location,
                    "status": status.value,
                    "active_sessions": metrics.active_sessions if metrics else 0,
                    "cpu_percent": metrics.cpu_usage_percent if metrics else None,
                    "memory_percent": metrics.memory_usage_percent if metrics else None,
                    "latency_ms": metrics.network_latency_ms if metrics else None,
                }
            
            return report
    
    def get_session_distribution(self) -> Dict[str, int]:
        """Get distribution of sessions across gateways."""
        with self._lock:
            distribution = defaultdict(int)
            
            for gateway_id in self.gateway_load.keys():
                distribution[gateway_id] = self.gateway_load[gateway_id]
            
            return dict(distribution)
    
    def get_failover_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent failover events."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            return [
                event for event in self.failover_history
                if datetime.fromisoformat(event["timestamp"]) > cutoff_time
            ]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator metrics."""
        with self._lock:
            return {
                **self.metrics,
                "active_sessions": len(self.sessions),
                "healthy_gateways": sum(
                    1 for status in self.gateway_status.values()
                    if status == GatewayStatus.HEALTHY
                ),
                "sync_points_pending": sum(
                    1 for sp in self.sync_points.values()
                    if len(sp.confirmed_gateways) < len(sp.gateway_ids)
                ),
            }


# Singleton instance
_edge_orchestrator_instance: Optional[EdgeOrchestrator] = None


def get_edge_orchestrator() -> EdgeOrchestrator:
    """Get or create edge orchestrator singleton."""
    global _edge_orchestrator_instance
    if _edge_orchestrator_instance is None:
        _edge_orchestrator_instance = EdgeOrchestrator()
    return _edge_orchestrator_instance
