"""
Latency Controller: Ensures reflex responses meet biological timing constraints

Concept:
- CRITICAL (<10ms):  Spinal reflex, no brain latency
- HIGH (<100ms):     Fast trained reflex
- MEDIUM (<500ms):   Quick decision + execution
- LOW (<2s):         Full AI reasoning

This ensures fast threats don't wait for slow analysis.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat severity levels"""
    CRITICAL = "critical"  # <10ms
    HIGH = "high"          # <100ms
    MEDIUM = "medium"      # <500ms
    LOW = "low"            # <2s


class LatencyBudgetStatus(Enum):
    """Budget status"""
    WITHIN_BUDGET = "within_budget"
    APPROACHING_LIMIT = "approaching_limit"
    EXCEEDED = "exceeded"


@dataclass
class LatencyBudget:
    """Tracks time spent on decision"""
    threat_level: ThreatLevel
    start_time: float
    budget_ms: int
    actions_taken: List[str] = field(default_factory=list)
    
    def elapsed_ms(self) -> float:
        """Time elapsed since start"""
        return (time.time() - self.start_time) * 1000
    
    def remaining_ms(self) -> float:
        """Time remaining in budget"""
        return max(0, self.budget_ms - self.elapsed_ms())
    
    def status(self) -> LatencyBudgetStatus:
        """Check budget status"""
        elapsed = self.elapsed_ms()
        if elapsed > self.budget_ms:
            return LatencyBudgetStatus.EXCEEDED
        elif elapsed > self.budget_ms * 0.8:
            return LatencyBudgetStatus.APPROACHING_LIMIT
        else:
            return LatencyBudgetStatus.WITHIN_BUDGET
    
    def is_over_budget(self) -> bool:
        """Check if we exceeded budget"""
        return self.elapsed_ms() > self.budget_ms


@dataclass
class ReflexDecision:
    """Autonomous reflex decision"""
    threat_id: str
    threat_level: ThreatLevel
    threat_score: float
    
    # Decision
    reflex_action: str                      # What to do
    confidence: float                       # 0-1 confidence in action
    
    # Timing
    decision_time_ms: float                 # Time to make decision
    latency_budget_ms: int                  # Budget for this level
    
    # Execution
    executed: bool = False
    execution_time_ms: float = 0.0
    execution_result: Optional[str] = None
    
    # Escalation
    requires_approval: bool = False
    approval_deadline: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    reflex_arc_id: str = ""


class LatencyController:
    """
    Controls decision latency to match threat severity.
    
    Mirrors biological reflex arcs:
    - Critical: Immediate spinal response
    - High: Fast trained reflex
    - Medium: Quick cognitive response
    - Low: Deliberate thinking
    """
    
    # Latency budgets (milliseconds)
    BUDGET_CRITICAL = 10      # <10ms spinal reflex
    BUDGET_HIGH = 100         # <100ms fast reflex
    BUDGET_MEDIUM = 500       # <500ms medium reasoning
    BUDGET_LOW = 2000         # <2s full reasoning
    
    def __init__(self):
        self.budgets: Dict[str, LatencyBudget] = {}
        self.decisions: Dict[str, ReflexDecision] = {}
        self.reflex_arcs: List[Dict] = []
    
    def start_budget(self, threat_id: str, threat_level: ThreatLevel) -> LatencyBudget:
        """Start a new latency budget"""
        budget_map = {
            ThreatLevel.CRITICAL: self.BUDGET_CRITICAL,
            ThreatLevel.HIGH: self.BUDGET_HIGH,
            ThreatLevel.MEDIUM: self.BUDGET_MEDIUM,
            ThreatLevel.LOW: self.BUDGET_LOW,
        }
        
        budget_ms = budget_map[threat_level]
        budget = LatencyBudget(
            threat_level=threat_level,
            start_time=time.time(),
            budget_ms=budget_ms
        )
        
        self.budgets[threat_id] = budget
        logger.info(f"Started latency budget for {threat_id}: {budget_ms}ms ({threat_level.value})")
        
        return budget
    
    def check_budget(self, threat_id: str) -> bool:
        """Check if we're still within budget"""
        if threat_id not in self.budgets:
            return True
        
        budget = self.budgets[threat_id]
        status = budget.status()
        
        if status == LatencyBudgetStatus.EXCEEDED:
            logger.warning(f"Latency budget exceeded for {threat_id}: {budget.elapsed_ms()}ms > {budget.budget_ms}ms")
            return False
        
        if status == LatencyBudgetStatus.APPROACHING_LIMIT:
            logger.warning(f"Latency budget approaching limit for {threat_id}: {budget.elapsed_ms()}ms / {budget.budget_ms}ms")
        
        return True
    
    def record_action(self, threat_id: str, action: str):
        """Record action taken within budget"""
        if threat_id in self.budgets:
            self.budgets[threat_id].actions_taken.append(action)
            logger.debug(f"Action recorded: {action} ({self.budgets[threat_id].elapsed_ms():.1f}ms)")
    
    def make_decision(
        self,
        threat_id: str,
        threat_level: ThreatLevel,
        threat_score: float,
        reflex_action: str,
        confidence: float = 0.95
    ) -> ReflexDecision:
        """Make a reflex decision within latency budget"""
        budget = self.start_budget(threat_id, threat_level)
        
        # Make decision within budget
        decision_start = time.time()
        
        decision = ReflexDecision(
            threat_id=threat_id,
            threat_level=threat_level,
            threat_score=threat_score,
            reflex_action=reflex_action,
            confidence=confidence,
            decision_time_ms=0,
            latency_budget_ms=budget.budget_ms,
            requires_approval=(threat_level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH])
        )
        
        if decision.requires_approval:
            decision.approval_deadline = datetime.utcnow() + timedelta(seconds=budget.budget_ms / 1000)
        
        decision.decision_time_ms = (time.time() - decision_start) * 1000
        
        # Check budget
        if decision.decision_time_ms > budget.budget_ms:
            logger.error(f"Decision time exceeded budget: {decision.decision_time_ms}ms > {budget.budget_ms}ms")
            decision.confidence *= 0.5  # Reduce confidence if over budget
        
        self.decisions[threat_id] = decision
        logger.info(
            f"Reflex decision: {reflex_action} for {threat_id} "
            f"({decision.decision_time_ms:.1f}ms / {budget.budget_ms}ms, confidence={confidence:.1%})"
        )
        
        return decision
    
    def execute_action(
        self,
        decision: ReflexDecision,
        action_func: Callable
    ) -> bool:
        """Execute reflex action within remaining budget"""
        threat_id = decision.threat_id
        budget = self.budgets.get(threat_id)
        
        if not budget:
            logger.error(f"No budget found for {threat_id}")
            return False
        
        if budget.is_over_budget():
            logger.error(f"Cannot execute action: budget exceeded for {threat_id}")
            return False
        
        # Execute action
        exec_start = time.time()
        try:
            action_func()
            decision.executed = True
            decision.execution_result = "success"
            decision.execution_time_ms = (time.time() - exec_start) * 1000
            
            logger.info(
                f"Action executed: {decision.reflex_action} in {decision.execution_time_ms:.1f}ms "
                f"(budget: {budget.budget_ms}ms)"
            )
            
            return True
        except Exception as e:
            decision.executed = False
            decision.execution_result = f"error: {str(e)}"
            logger.error(f"Action execution failed: {e}")
            return False
    
    def create_reflex_arc(
        self,
        threat_id: str,
        threat_level: ThreatLevel,
        threat_score: float,
        stimulus: str,
        response: str
    ) -> Dict:
        """Create a complete reflex arc"""
        reflex_arc = {
            "reflex_arc_id": f"reflex_{threat_id}_{int(time.time() * 1000)}",
            "threat_id": threat_id,
            "threat_level": threat_level.value,
            "threat_score": threat_score,
            "stimulus": stimulus,          # What triggered it
            "response": response,           # What it does
            "created_at": datetime.utcnow().isoformat(),
            "latency_ms": 0,
            "status": "active"
        }
        
        self.reflex_arcs.append(reflex_arc)
        logger.info(f"Reflex arc created: {reflex_arc['reflex_arc_id']} ({threat_level.value} level)")
        
        return reflex_arc
    
    def get_remaining_time(self, threat_id: str) -> Optional[float]:
        """Get remaining time in budget"""
        if threat_id not in self.budgets:
            return None
        return self.budgets[threat_id].remaining_ms()
    
    def should_defer(self, threat_id: str) -> bool:
        """Check if we should defer analysis to full AI reasoning"""
        if threat_id not in self.budgets:
            return False
        
        budget = self.budgets[threat_id]
        
        # If less than 20% of budget remains, defer to full reasoning
        if budget.remaining_ms() < budget.budget_ms * 0.2:
            logger.info(f"Deferring to full AI reasoning for {threat_id} (only {budget.remaining_ms()}ms left)")
            return True
        
        return False
    
    def get_reflex_arc_latency(self, reflex_arc_id: str) -> Optional[float]:
        """Get latency of a reflex arc"""
        for arc in self.reflex_arcs:
            if arc["reflex_arc_id"] == reflex_arc_id:
                return arc["latency_ms"]
        return None
    
    def summarize_budget(self, threat_id: str) -> Dict:
        """Summarize budget usage"""
        if threat_id not in self.budgets:
            return {"error": "Budget not found"}
        
        budget = self.budgets[threat_id]
        return {
            "threat_id": threat_id,
            "threat_level": budget.threat_level.value,
            "budget_ms": budget.budget_ms,
            "elapsed_ms": budget.elapsed_ms(),
            "remaining_ms": budget.remaining_ms(),
            "status": budget.status().value,
            "actions": budget.actions_taken,
            "over_budget": budget.is_over_budget()
        }
    
    def reflex_latency_report(self) -> Dict:
        """Report on reflex latencies"""
        return {
            "total_reflex_arcs": len(self.reflex_arcs),
            "total_decisions": len(self.decisions),
            "critical_within_budget": sum(
                1 for d in self.decisions.values()
                if d.threat_level == ThreatLevel.CRITICAL
                and d.decision_time_ms <= self.BUDGET_CRITICAL
            ),
            "high_within_budget": sum(
                1 for d in self.decisions.values()
                if d.threat_level == ThreatLevel.HIGH
                and d.decision_time_ms <= self.BUDGET_HIGH
            ),
            "medium_within_budget": sum(
                1 for d in self.decisions.values()
                if d.threat_level == ThreatLevel.MEDIUM
                and d.decision_time_ms <= self.BUDGET_MEDIUM
            ),
            "low_within_budget": sum(
                1 for d in self.decisions.values()
                if d.threat_level == ThreatLevel.LOW
                and d.decision_time_ms <= self.BUDGET_LOW
            ),
            "average_decision_time_ms": sum(d.decision_time_ms for d in self.decisions.values()) / len(self.decisions) if self.decisions else 0
        }
