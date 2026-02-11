"""
Auto-Containment: Autonomous isolation and threat response

Concept:
- Critical threats → Isolate first, explain later
- High threats → Partial containment, escalate for approval
- Medium threats → Monitor, prepare for action
- Low threats → Log and continue

This is the "response" in Defense Reflex Arc.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import logging
import uuid

logger = logging.getLogger(__name__)


class IsolationMode(Enum):
    """Network isolation modes"""
    FULL = "full_isolation"              # Complete disconnection
    RESTRICTED = "restricted_isolation"  # Management only
    RATE_LIMITED = "rate_limited"        # Limited bandwidth
    NONE = "no_isolation"


class ContainmentAction(Enum):
    """Types of containment actions"""
    NETWORK_ISOLATE = "network_isolate"
    BLOCK_FLOW = "block_flow"
    KILL_PROCESS = "kill_process"
    RATE_LIMIT = "rate_limit"
    THROTTLE = "throttle"
    BLOCK_HOST = "block_host"
    ALERT = "alert"
    LOG = "log"


@dataclass
class ContainmentResult:
    """Result of containment action"""
    action: ContainmentAction
    target: str
    success: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0
    details: str = ""
    error: Optional[str] = None


@dataclass
class IsolatedHost:
    """Host under containment"""
    host_id: str
    isolation_mode: IsolationMode
    reason: str
    isolated_at: datetime = field(default_factory=datetime.utcnow)
    isolation_expires: Optional[datetime] = None
    
    # Tracking
    actions_taken: List[ContainmentResult] = field(default_factory=list)
    approval_status: str = "pending"       # pending, approved, denied, auto_extended
    
    def is_active(self) -> bool:
        """Check if isolation is still active"""
        if self.isolation_expires is None:
            return True
        return datetime.utcnow() < self.isolation_expires
    
    def remaining_duration_sec(self) -> float:
        """Get remaining isolation time"""
        if self.isolation_expires is None:
            return float('inf')
        remaining = (self.isolation_expires - datetime.utcnow()).total_seconds()
        return max(0, remaining)


class AutoContainmentEngine:
    """
    Autonomous threat containment system.
    
    Implements spinal reflex behavior:
    1. Detect threat
    2. Isolate immediately
    3. Escalate for approval
    4. Await human decision
    """
    
    def __init__(self):
        self.isolated_hosts: Dict[str, IsolatedHost] = {}
        self.containment_history: List[Dict] = []
        self.blocked_flows: Dict[str, Dict] = {}
        self.rate_limited_targets: Dict[str, Dict] = {}
    
    def isolate_host(
        self,
        host_id: str,
        threat_level: str,
        threat_score: float,
        reason: str,
        mode: IsolationMode = IsolationMode.FULL,
        duration_sec: int = 300
    ) -> IsolatedHost:
        """Isolate a host from network"""
        iso_host = IsolatedHost(
            host_id=host_id,
            isolation_mode=mode,
            reason=reason,
            isolation_expires=datetime.utcnow() + timedelta(seconds=duration_sec)
        )
        
        self.isolated_hosts[host_id] = iso_host
        
        # Log action
        result = ContainmentResult(
            action=ContainmentAction.NETWORK_ISOLATE,
            target=host_id,
            success=True,
            details=f"Isolated {host_id} ({mode.value}): {reason}"
        )
        iso_host.actions_taken.append(result)
        
        logger.info(f"Host isolated: {host_id} ({mode.value}), duration={duration_sec}s, reason={reason}")
        
        self.containment_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "host_isolation",
            "host_id": host_id,
            "threat_level": threat_level,
            "threat_score": threat_score,
            "mode": mode.value,
            "duration_sec": duration_sec
        })
        
        return iso_host
    
    def block_flow(
        self,
        flow_id: str,
        source_ip: str,
        dest_ip: str,
        threat_type: str,
        duration_sec: int = 300
    ) -> ContainmentResult:
        """Block a network flow"""
        block_entry = {
            "flow_id": flow_id,
            "source_ip": source_ip,
            "dest_ip": dest_ip,
            "threat_type": threat_type,
            "blocked_at": datetime.utcnow().isoformat(),
            "expires": (datetime.utcnow() + timedelta(seconds=duration_sec)).isoformat()
        }
        
        self.blocked_flows[flow_id] = block_entry
        
        result = ContainmentResult(
            action=ContainmentAction.BLOCK_FLOW,
            target=flow_id,
            success=True,
            details=f"Blocked {source_ip} -> {dest_ip} ({threat_type})"
        )
        
        logger.info(f"Flow blocked: {flow_id} ({source_ip} -> {dest_ip}), threat={threat_type}")
        
        self.containment_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "flow_blocked",
            "flow_id": flow_id,
            "source_ip": source_ip,
            "dest_ip": dest_ip,
            "threat_type": threat_type,
            "duration_sec": duration_sec
        })
        
        return result
    
    def kill_process(
        self,
        host_id: str,
        process_id: int,
        process_name: str,
        reason: str
    ) -> ContainmentResult:
        """Kill malicious process"""
        result = ContainmentResult(
            action=ContainmentAction.KILL_PROCESS,
            target=f"{host_id}:{process_id}",
            success=True,
            details=f"Killed process {process_name} ({process_id}): {reason}"
        )
        
        logger.info(f"Process killed: {process_name}({process_id}) on {host_id}")
        
        self.containment_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "process_killed",
            "host_id": host_id,
            "process_id": process_id,
            "process_name": process_name,
            "reason": reason
        })
        
        return result
    
    def rate_limit(
        self,
        target: str,
        packets_per_sec: int,
        duration_sec: int = 300
    ) -> ContainmentResult:
        """Apply rate limiting to target"""
        rate_limit_entry = {
            "target": target,
            "packets_per_sec": packets_per_sec,
            "applied_at": datetime.utcnow().isoformat(),
            "expires": (datetime.utcnow() + timedelta(seconds=duration_sec)).isoformat()
        }
        
        self.rate_limited_targets[target] = rate_limit_entry
        
        result = ContainmentResult(
            action=ContainmentAction.RATE_LIMIT,
            target=target,
            success=True,
            details=f"Rate limited {target} to {packets_per_sec} pkt/s"
        )
        
        logger.info(f"Rate limit applied: {target} ({packets_per_sec} pkt/s)")
        
        return result
    
    def throttle_bandwidth(
        self,
        connection_id: str,
        max_mbps: int,
        duration_sec: int = 300
    ) -> ContainmentResult:
        """Throttle bandwidth for connection"""
        result = ContainmentResult(
            action=ContainmentAction.THROTTLE,
            target=connection_id,
            success=True,
            details=f"Throttled to {max_mbps} Mbps"
        )
        
        logger.info(f"Bandwidth throttled: {connection_id} ({max_mbps} Mbps)")
        
        self.containment_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "bandwidth_throttled",
            "connection_id": connection_id,
            "max_mbps": max_mbps,
            "duration_sec": duration_sec
        })
        
        return result
    
    def execute_critical_reflex(
        self,
        threat_id: str,
        host_id: str,
        threat_score: float,
        attack_type: str
    ) -> Dict:
        """
        Execute immediate isolation (spinal reflex).
        
        This happens in <10ms, no human approval yet.
        Approval is requested in parallel.
        """
        logger.critical(f"🔥 CRITICAL REFLEX TRIGGERED: {threat_id} on {host_id} (score={threat_score:.2f})")
        
        # Immediate isolation
        iso_host = self.isolate_host(
            host_id=host_id,
            threat_level="critical",
            threat_score=threat_score,
            reason=f"CRITICAL threat: {attack_type}",
            mode=IsolationMode.FULL,
            duration_sec=300
        )
        
        return {
            "reflex_type": "critical_isolation",
            "threat_id": threat_id,
            "host_id": host_id,
            "action": "immediate_isolation",
            "isolation_mode": IsolationMode.FULL.value,
            "approval_required": True,
            "approval_deadline": (datetime.utcnow() + timedelta(seconds=60)).isoformat()
        }
    
    def execute_high_risk_reflex(
        self,
        threat_id: str,
        host_id: str,
        threat_type: str
    ) -> Dict:
        """
        Execute conditional high-risk reflex.
        
        Actions depend on threat type.
        """
        logger.warning(f"⚡ HIGH RISK REFLEX: {threat_id} ({threat_type})")
        
        actions_taken = []
        
        if threat_type == "port_scan":
            self.isolate_host(
                host_id=host_id,
                threat_level="high",
                threat_score=0.75,
                reason="Active port scanning detected",
                mode=IsolationMode.RESTRICTED,
                duration_sec=600
            )
            actions_taken.append("restricted_isolation")
        
        elif threat_type == "data_exfiltration":
            self.throttle_bandwidth(f"conn_{host_id}", max_mbps=1, duration_sec=300)
            actions_taken.append("bandwidth_throttled")
        
        elif threat_type == "malware_execution":
            self.isolate_host(
                host_id=host_id,
                threat_level="high",
                threat_score=0.80,
                reason="Malware execution detected",
                mode=IsolationMode.RESTRICTED,
                duration_sec=600
            )
            actions_taken.append("restricted_isolation")
        
        return {
            "reflex_type": "high_risk_response",
            "threat_id": threat_id,
            "host_id": host_id,
            "threat_type": threat_type,
            "actions": actions_taken,
            "approval_required": True
        }
    
    def execute_medium_risk_reflex(
        self,
        threat_id: str,
        host_id: str,
        threat_type: str
    ) -> Dict:
        """Monitor without taking action (inform human)"""
        logger.info(f"🔹 MEDIUM RISK DETECTED: {threat_id} ({threat_type})")
        
        return {
            "reflex_type": "medium_monitoring",
            "threat_id": threat_id,
            "host_id": host_id,
            "threat_type": threat_type,
            "action": "enhanced_monitoring",
            "approval_required": False
        }
    
    def release_host(
        self,
        host_id: str,
        reason: str
    ) -> bool:
        """Release host from isolation"""
        if host_id not in self.isolated_hosts:
            logger.warning(f"Host not in isolation: {host_id}")
            return False
        
        iso_host = self.isolated_hosts[host_id]
        iso_host.isolation_expires = datetime.utcnow()
        iso_host.approval_status = "released"
        
        logger.info(f"Host released from isolation: {host_id} ({reason})")
        
        self.containment_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "host_released",
            "host_id": host_id,
            "reason": reason,
            "isolated_duration_sec": (datetime.utcnow() - iso_host.isolated_at).total_seconds()
        })
        
        return True
    
    def approve_isolation(self, host_id: str) -> bool:
        """Approve continued isolation"""
        if host_id not in self.isolated_hosts:
            return False
        
        self.isolated_hosts[host_id].approval_status = "approved"
        logger.info(f"Isolation approved for: {host_id}")
        
        return True
    
    def deny_isolation(self, host_id: str) -> bool:
        """Deny isolation, release host"""
        return self.release_host(host_id, "isolation denied by human")
    
    def is_host_isolated(self, host_id: str) -> bool:
        """Check if host is isolated"""
        if host_id not in self.isolated_hosts:
            return False
        return self.isolated_hosts[host_id].is_active()
    
    def get_containment_status(self, host_id: str) -> Optional[Dict]:
        """Get containment status for host"""
        if host_id not in self.isolated_hosts:
            return None
        
        iso_host = self.isolated_hosts[host_id]
        return {
            "host_id": host_id,
            "is_isolated": iso_host.is_active(),
            "isolation_mode": iso_host.isolation_mode.value,
            "isolated_at": iso_host.isolated_at.isoformat(),
            "isolation_expires": iso_host.isolation_expires.isoformat() if iso_host.isolation_expires else None,
            "remaining_duration_sec": iso_host.remaining_duration_sec(),
            "reason": iso_host.reason,
            "approval_status": iso_host.approval_status,
            "actions_taken": len(iso_host.actions_taken)
        }
    
    def get_containment_summary(self) -> Dict:
        """Get summary of all containments"""
        active_isolated = sum(1 for h in self.isolated_hosts.values() if h.is_active())
        total_blocked_flows = len(self.blocked_flows)
        total_rate_limited = len(self.rate_limited_targets)
        
        return {
            "active_isolated_hosts": active_isolated,
            "total_isolations": len(self.isolated_hosts),
            "blocked_flows": total_blocked_flows,
            "rate_limited_targets": total_rate_limited,
            "total_containment_actions": len(self.containment_history),
            "pending_approvals": sum(
                1 for h in self.isolated_hosts.values()
                if h.approval_status == "pending" and h.is_active()
            )
        }
