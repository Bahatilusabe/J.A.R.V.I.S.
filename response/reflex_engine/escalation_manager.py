"""
Escalation Manager: Routes threats to appropriate human responders

Concept:
- CRITICAL → Security team lead + CISO + Incident commander
- HIGH → Security team + Incident response
- MEDIUM → Security monitoring
- LOW → Threat database (automated)

Ensures right person gets right alert at right time.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
import logging
import uuid

logger = logging.getLogger(__name__)


class EscalationLevel(Enum):
    """Escalation severity"""
    CRITICAL = "critical"  # P1 - Immediate
    HIGH = "high"          # P2 - Urgent
    MEDIUM = "medium"      # P3 - Soon
    LOW = "low"            # P4 - Background


class EscalationStatus(Enum):
    """Escalation status"""
    CREATED = "created"
    ASSIGNED = "assigned"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    ESCALATED_FURTHER = "escalated_further"


@dataclass
class EscalationNotification:
    """Notification to send to responder"""
    notification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    escalation_id: str = ""
    recipient_id: str = ""
    recipient_name: str = ""
    recipient_email: str = ""
    
    # Content
    subject: str = ""
    body: str = ""
    severity: str = ""
    
    # Tracking
    created_at: datetime = field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    
    def mark_sent(self):
        """Mark notification as sent"""
        self.sent_at = datetime.utcnow()
    
    def mark_acknowledged(self):
        """Mark notification as acknowledged"""
        self.acknowledged_at = datetime.utcnow()
    
    def time_to_acknowledge_sec(self) -> Optional[float]:
        """Time from sent to acknowledged"""
        if not self.sent_at or not self.acknowledged_at:
            return None
        return (self.acknowledged_at - self.sent_at).total_seconds()


@dataclass
class Escalation:
    """Escalated threat requiring human decision"""
    escalation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    threat_id: str = ""
    threat_level: str = ""
    threat_score: float = 0.0
    
    # Escalation details
    level: EscalationLevel = EscalationLevel.MEDIUM
    reason: str = ""
    
    # Status
    status: EscalationStatus = EscalationStatus.CREATED
    assigned_to: Optional[str] = None
    priority: str = "P3"
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    assigned_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    approval_deadline: Optional[datetime] = None
    
    # Tracking
    notifications_sent: List[EscalationNotification] = field(default_factory=list)
    requires_approval: bool = False
    approval_given: bool = False
    resolution_notes: str = ""
    
    def assign_to(self, responder_id: str, responder_name: str):
        """Assign escalation to responder"""
        self.assigned_to = responder_id
        self.status = EscalationStatus.ASSIGNED
        self.assigned_at = datetime.utcnow()
    
    def acknowledge(self):
        """Mark as acknowledged"""
        self.status = EscalationStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.utcnow()
    
    def resolve(self, notes: str = ""):
        """Mark as resolved"""
        self.status = EscalationStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
        self.resolution_notes = notes
    
    def escalate_further(self):
        """Escalate to higher level"""
        self.status = EscalationStatus.ESCALATED_FURTHER
    
    def is_overdue(self) -> bool:
        """Check if approval is overdue"""
        if not self.approval_deadline:
            return False
        return datetime.utcnow() > self.approval_deadline
    
    def time_to_resolve_sec(self) -> Optional[float]:
        """Time from creation to resolution"""
        if not self.resolved_at:
            return None
        return (self.resolved_at - self.created_at).total_seconds()


class EscalationManager:
    """
    Routes threats to appropriate responders.
    
    Like a biological immune response dispatcher:
    - CRITICAL: Full emergency response (all hands)
    - HIGH: Rapid response team
    - MEDIUM: Specialists
    - LOW: Automated systems
    """
    
    def __init__(self):
        self.escalations: Dict[str, Escalation] = {}
        self.responders: Dict[str, Dict] = {}
        self.escalation_history: List[Dict] = []
        
        # Notification log
        self.notifications_sent: List[EscalationNotification] = []
        
        # Response times (for SLA tracking)
        self.response_times: List[float] = []
        self.resolution_times: List[float] = []
    
    def register_responder(
        self,
        responder_id: str,
        name: str,
        email: str,
        role: str,
        team: str,
        on_call: bool = False
    ):
        """Register on-call responder"""
        self.responders[responder_id] = {
            "responder_id": responder_id,
            "name": name,
            "email": email,
            "role": role,
            "team": team,
            "on_call": on_call,
            "active_escalations": 0,
            "registered_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Responder registered: {name} ({role}, on_call={on_call})")
    
    def create_escalation(
        self,
        threat_id: str,
        threat_level: str,
        threat_score: float,
        reason: str,
        requires_approval: bool = False
    ) -> Escalation:
        """Create escalation for threat"""
        
        # Determine escalation level
        if threat_score >= 0.85:
            level = EscalationLevel.CRITICAL
            priority = "P1"
            approval_deadline = datetime.utcnow() + timedelta(seconds=60)
        elif threat_score >= 0.60:
            level = EscalationLevel.HIGH
            priority = "P2"
            approval_deadline = datetime.utcnow() + timedelta(minutes=5)
        elif threat_score >= 0.30:
            level = EscalationLevel.MEDIUM
            priority = "P3"
            approval_deadline = None
        else:
            level = EscalationLevel.LOW
            priority = "P4"
            approval_deadline = None
        
        escalation = Escalation(
            threat_id=threat_id,
            threat_level=threat_level,
            threat_score=threat_score,
            level=level,
            priority=priority,
            reason=reason,
            requires_approval=requires_approval,
            approval_deadline=approval_deadline
        )
        
        self.escalations[escalation.escalation_id] = escalation
        
        logger.info(
            f"Escalation created: {escalation.escalation_id} "
            f"({level.value}, P={priority}, score={threat_score:.2f})"
        )
        
        return escalation
    
    def assign_escalation(
        self,
        escalation_id: str,
        responder_id: Optional[str] = None
    ) -> Optional[str]:
        """Assign escalation to responder"""
        if escalation_id not in self.escalations:
            logger.error(f"Escalation not found: {escalation_id}")
            return None
        
        escalation = self.escalations[escalation_id]
        
        # Find best responder if not specified
        if responder_id is None:
            responder_id = self._find_best_responder(escalation)
        
        if responder_id is None:
            logger.error("No responders available")
            return None
        
        if responder_id not in self.responders:
            logger.error(f"Responder not found: {responder_id}")
            return None
        
        responder = self.responders[responder_id]
        escalation.assign_to(responder_id, responder["name"])
        responder["active_escalations"] += 1
        
        logger.info(f"Escalation assigned to {responder['name']}: {escalation_id}")
        
        return responder_id
    
    def send_notification(
        self,
        escalation_id: str,
        recipient_id: str,
        subject: str,
        body: str
    ) -> EscalationNotification:
        """Send notification to responder"""
        if escalation_id not in self.escalations:
            logger.error(f"Escalation not found: {escalation_id}")
            return None
        
        if recipient_id not in self.responders:
            logger.error(f"Responder not found: {recipient_id}")
            return None
        
        escalation = self.escalations[escalation_id]
        responder = self.responders[recipient_id]
        
        notification = EscalationNotification(
            escalation_id=escalation_id,
            recipient_id=recipient_id,
            recipient_name=responder["name"],
            recipient_email=responder["email"],
            subject=subject,
            body=body,
            severity=escalation.level.value
        )
        
        notification.mark_sent()
        escalation.notifications_sent.append(notification)
        self.notifications_sent.append(notification)
        
        logger.info(f"Notification sent to {responder['name']}: {notification.notification_id}")
        
        return notification
    
    def acknowledge_escalation(
        self,
        escalation_id: str,
        responder_id: str
    ) -> bool:
        """Responder acknowledges escalation"""
        if escalation_id not in self.escalations:
            return False
        
        escalation = self.escalations[escalation_id]
        
        if escalation.assigned_to != responder_id:
            logger.warning(f"Responder {responder_id} not assigned to {escalation_id}")
            return False
        
        escalation.acknowledge()
        
        # Track response time
        if escalation.assigned_at:
            response_time = (datetime.utcnow() - escalation.assigned_at).total_seconds()
            self.response_times.append(response_time)
        
        logger.info(f"Escalation acknowledged: {escalation_id}")
        
        return True
    
    def approve_escalation(
        self,
        escalation_id: str,
        responder_id: str,
        notes: str = ""
    ) -> bool:
        """Responder approves reflex action"""
        if escalation_id not in self.escalations:
            return False
        
        escalation = self.escalations[escalation_id]
        
        if not escalation.requires_approval:
            logger.warning(f"Escalation doesn't require approval: {escalation_id}")
            return False
        
        escalation.approval_given = True
        escalation.resolve(notes)
        
        logger.info(f"Escalation approved: {escalation_id}")
        
        return True
    
    def deny_escalation(
        self,
        escalation_id: str,
        responder_id: str,
        reason: str = ""
    ) -> bool:
        """Responder denies reflex action"""
        if escalation_id not in self.escalations:
            return False
        
        escalation = self.escalations[escalation_id]
        
        if not escalation.requires_approval:
            logger.warning(f"Escalation doesn't require approval: {escalation_id}")
            return False
        
        escalation.approval_given = False
        escalation.resolve(f"Denied: {reason}")
        
        logger.info(f"Escalation denied: {escalation_id}")
        
        return True
    
    def resolve_escalation(
        self,
        escalation_id: str,
        responder_id: str,
        notes: str = ""
    ) -> bool:
        """Mark escalation as resolved"""
        if escalation_id not in self.escalations:
            return False
        
        escalation = self.escalations[escalation_id]
        
        if escalation.assigned_to != responder_id:
            logger.warning(f"Responder {responder_id} not assigned to {escalation_id}")
            return False
        
        escalation.resolve(notes)
        self.responders[responder_id]["active_escalations"] -= 1
        
        # Track resolution time
        if escalation.created_at:
            resolution_time = (datetime.utcnow() - escalation.created_at).total_seconds()
            self.resolution_times.append(resolution_time)
        
        logger.info(f"Escalation resolved: {escalation_id} ({resolution_time:.1f}s)")
        
        return True
    
    def _find_best_responder(self, escalation: Escalation) -> Optional[str]:
        """Find best responder for escalation"""
        on_call_responders = [
            r for r in self.responders.values()
            if r["on_call"]
        ]
        
        if not on_call_responders:
            return None
        
        # Assign to responder with fewest active escalations
        best_responder = min(on_call_responders, key=lambda r: r["active_escalations"])
        
        return best_responder["responder_id"]
    
    def get_escalation_status(self, escalation_id: str) -> Optional[Dict]:
        """Get status of escalation"""
        if escalation_id not in self.escalations:
            return None
        
        esc = self.escalations[escalation_id]
        
        return {
            "escalation_id": escalation_id,
            "threat_id": esc.threat_id,
            "level": esc.level.value,
            "priority": esc.priority,
            "status": esc.status.value,
            "assigned_to": esc.assigned_to,
            "requires_approval": esc.requires_approval,
            "approval_given": esc.approval_given,
            "created_at": esc.created_at.isoformat(),
            "assigned_at": esc.assigned_at.isoformat() if esc.assigned_at else None,
            "acknowledged_at": esc.acknowledged_at.isoformat() if esc.acknowledged_at else None,
            "resolved_at": esc.resolved_at.isoformat() if esc.resolved_at else None,
            "is_overdue": esc.is_overdue(),
            "resolution_notes": esc.resolution_notes
        }
    
    def get_escalation_summary(self) -> Dict:
        """Get summary of all escalations"""
        total_esc = len(self.escalations)
        active_esc = sum(1 for e in self.escalations.values() if e.status != EscalationStatus.RESOLVED)
        critical_esc = sum(1 for e in self.escalations.values() if e.level == EscalationLevel.CRITICAL)
        overdue_esc = sum(1 for e in self.escalations.values() if e.is_overdue())
        
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        avg_resolution_time = sum(self.resolution_times) / len(self.resolution_times) if self.resolution_times else 0
        
        return {
            "total_escalations": total_esc,
            "active_escalations": active_esc,
            "critical_escalations": critical_esc,
            "overdue_escalations": overdue_esc,
            "average_response_time_sec": avg_response_time,
            "average_resolution_time_sec": avg_resolution_time,
            "total_responders": len(self.responders),
            "on_call_responders": sum(1 for r in self.responders.values() if r["on_call"]),
            "notifications_sent": len(self.notifications_sent)
        }
