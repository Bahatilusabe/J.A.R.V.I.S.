"""
Adaptive Memory Cells - Inspired by B-Cells & T-Cells in the Immune System

Every confirmed attack spawns a memory cell that:
- Strengthens if reused (antibody production)
- Decays if irrelevant (immune tolerance)
- Mutates to recognize variants
- Forms memory pools for rapid response

This is NOT just logging or embeddings.
This is memory that improves with each attack.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import hashlib
import json
from uuid import uuid4


class CellType(Enum):
    """Memory cell types analogous to immune system"""
    B_CELL = "b_cell"          # Antibody production - exact pattern matching
    T_CELL = "t_cell"          # Cellular response - behavioral pattern
    MEMORY_POOL = "memory_pool"  # Rapid response cells
    REGULATORY = "regulatory"   # Suppression - false positives


class CellState(Enum):
    """Memory cell lifecycle states"""
    ACTIVATED = "activated"      # Just discovered/confirmed
    MATURE = "mature"            # Strengthened by reuse
    RESTING = "resting"          # Low activation
    ANERGIC = "anergic"          # Suppressed/irrelevant
    APOPTOTIC = "apoptotic"      # Scheduled for death


@dataclass
class AttackSignature:
    """Canonical attack pattern - what the memory recognizes"""
    signature_hash: str              # MD5/SHA1 of attack pattern
    attack_type: str                 # "DDoS", "SQLInjection", "PortScan", etc.
    protocol: str                    # TCP/UDP/ICMP
    
    # Attack characteristics
    source_ips: List[str]            # Attacker IPs seen
    target_ports: List[int]          # Targeted ports
    payload_characteristics: Dict[str, Any]  # Size, entropy, content patterns
    
    # Detection context
    detection_method: str            # How it was detected (IDS/DPI/Firewall)
    confidence: float                # 0.0-1.0 detection confidence
    
    timestamp_first_seen: datetime   # When first detected
    
    def compute_hash(self) -> str:
        """Compute immutable signature hash"""
        data = {
            'attack_type': self.attack_type,
            'protocol': self.protocol,
            'ports': sorted(self.target_ports),
            'payload_hash': hashlib.md5(
                json.dumps(self.payload_characteristics, sort_keys=True).encode()
            ).hexdigest()
        }
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()


@dataclass
class Antibody:
    """Defense mechanism - rule/pattern to block similar attacks"""
    antibody_id: str = field(default_factory=lambda: str(uuid4()))
    cell_id: str = ""               # Parent memory cell
    
    # Detection rule
    detection_rule: Dict[str, Any]  # Firewall rule, IDS signature, DPI pattern
    rule_type: str = "firewall"     # firewall, ids_signature, dpi_rule, etc.
    
    # Effectiveness metrics
    true_positives: int = 0         # Blocked actual attacks
    false_positives: int = 0        # False alarms
    effectiveness: float = 0.0      # (TP / (TP + FN)) confidence
    
    # Mutations
    variants_detected: int = 0      # How many attack variants blocked
    mutations_applied: List[str] = field(default_factory=list)
    
    # Deployment
    deployed_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    deployment_status: str = "staged"  # staged, active, deprecated
    
    def compute_effectiveness(self) -> float:
        """Calculate antibody effectiveness"""
        if self.true_positives + self.false_positives == 0:
            return 0.0
        precision = self.true_positives / (self.true_positives + self.false_positives)
        return max(0.0, min(1.0, precision - (0.1 * self.false_positives)))


@dataclass
class MemoryCell:
    """
    Adaptive Memory Cell - B-Cell/T-Cell equivalent
    
    Stores attack knowledge and improves with reuse.
    """
    cell_id: str = field(default_factory=lambda: str(uuid4()))
    cell_type: CellType = CellType.B_CELL
    cell_state: CellState = CellState.ACTIVATED
    
    # What does it remember?
    attack_signature: AttackSignature = field(default_factory=lambda: AttackSignature(
        signature_hash="",
        attack_type="",
        protocol="",
        source_ips=[],
        target_ports=[],
        payload_characteristics={},
        detection_method="",
        confidence=0.0,
        timestamp_first_seen=datetime.now()
    ))
    
    # Defensive capability
    antibodies: List[Antibody] = field(default_factory=list)  # Rules/signatures
    antibody_count: int = 0         # Total antibodies produced
    
    # Lifecycle metrics
    created_at: datetime = field(default_factory=datetime.now)
    last_activated: datetime = field(default_factory=datetime.now)
    activation_count: int = 1       # How many times has it detected this
    
    # Strength metrics (adaptive immunity)
    strength: float = 0.5           # 0.0-1.0: How mature/reliable
    affinity: float = 0.8           # 0.0-1.0: How well it matches attack
    proliferation_rate: float = 1.0 # How quickly it creates variants
    
    # Decay (immune tolerance)
    decay_rate: float = 0.01        # Per day, if not reused
    last_decay_check: datetime = field(default_factory=datetime.now)
    
    # Mutations (evolutionary adaptation)
    mutations: List[str] = field(default_factory=list)
    variant_count: int = 0          # How many attack variants detected
    
    # Memory pool assignment
    in_memory_pool: bool = False    # Fast-response pool?
    memory_pool_priority: int = 0   # 0-10, higher = faster response
    
    # Metadata
    threat_level: str = "medium"    # low, medium, high, critical
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    
    def strengthen(self) -> None:
        """Strengthen memory when attack reoccurs (positive feedback)"""
        self.activation_count += 1
        self.last_activated = datetime.now()
        self.strength = min(1.0, self.strength + 0.1)
        self.affinity = min(1.0, self.affinity + 0.05)
        
        if self.activation_count >= 5:
            self.cell_state = CellState.MATURE
        if self.activation_count >= 10:
            self.in_memory_pool = True
            self.memory_pool_priority = min(10, (self.activation_count - 10) // 5)
    
    def decay(self) -> None:
        """Decay memory if not reused (immune tolerance)"""
        days_since_activation = (datetime.now() - self.last_activated).days
        
        # Decay: halves every 30 days if not reused
        decay_factor = (0.5) ** (days_since_activation / 30.0)
        self.strength *= decay_factor
        self.affinity *= decay_factor
        
        if self.strength < 0.3:
            self.cell_state = CellState.ANERGIC
        if self.strength < 0.1:
            self.cell_state = CellState.APOPTOTIC
        
        self.last_decay_check = datetime.now()
    
    def create_variant(self, variant_signature: Dict[str, Any]) -> 'MemoryCell':
        """Create mutated variant for attack variations"""
        variant = MemoryCell(
            cell_type=self.cell_type,
            attack_signature=self.attack_signature,
            strength=self.strength * 0.9,
            affinity=0.7,
            variant_count=self.variant_count + 1,
            threat_level=self.threat_level,
            tags=self.tags.copy(),
            in_memory_pool=self.in_memory_pool,
            memory_pool_priority=max(0, self.memory_pool_priority - 1)
        )
        variant.mutations = self.mutations + [str(variant_signature)]
        self.variant_count += 1
        return variant
    
    def get_antibodies(self, effective_only: bool = True) -> List[Antibody]:
        """Get antibodies, optionally filtering by effectiveness"""
        if effective_only:
            return [ab for ab in self.antibodies if ab.effectiveness > 0.5]
        return self.antibodies
    
    def is_alive(self) -> bool:
        """Check if memory cell is still relevant"""
        return self.cell_state != CellState.APOPTOTIC
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'cell_id': self.cell_id,
            'cell_type': self.cell_type.value,
            'cell_state': self.cell_state.value,
            'attack_type': self.attack_signature.attack_type,
            'activation_count': self.activation_count,
            'strength': self.strength,
            'affinity': self.affinity,
            'in_memory_pool': self.in_memory_pool,
            'memory_pool_priority': self.memory_pool_priority,
            'variant_count': self.variant_count,
            'antibody_count': len(self.antibodies),
            'threat_level': self.threat_level,
            'created_at': self.created_at.isoformat(),
            'last_activated': self.last_activated.isoformat(),
        }
