"""
Extinction Logic - Memory Cell Lifecycle Management

Similar to immune system T-regulatory cells:
- Identify and suppress false positives (auto-immunity)
- Remove irrelevant memory (immune tolerance)
- Manage memory cell populations (homeostasis)
- Prevent resource exhaustion
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import statistics

from .memory_cells import MemoryCell, CellState, CellType


class ExtinctionReason(Enum):
    """Why a memory cell was eliminated"""
    STRENGTH_DECAY = "strength_decay"        # Natural decay below threshold
    LOW_EFFECTIVENESS = "low_effectiveness"  # Antibodies not effective
    AUTO_IMMUNE = "auto_immune"              # Too many false positives
    RESOURCE_PRESSURE = "resource_pressure"  # Population control
    IRRELEVANCE = "irrelevance"              # No detection in long time
    CONFLICT = "conflict"                    # Conflicts with other cells


@dataclass
class ExtinctionRecord:
    """Record of a memory cell extinction event"""
    extinction_id: str = field(default_factory=lambda: __import__('uuid').uuid4().__str__())
    cell_id: str = ""
    reason: ExtinctionReason = ExtinctionReason.STRENGTH_DECAY
    
    # Why it was eliminated
    final_strength: float = 0.0
    final_effectiveness: float = 0.0
    false_positive_ratio: float = 0.0
    days_since_activation: int = 0
    
    # Statistics
    total_activations: int = 0
    useful_detections: int = 0
    false_detections: int = 0
    
    extinct_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'extinction_id': self.extinction_id,
            'cell_id': self.cell_id,
            'reason': self.reason.value,
            'final_strength': self.final_strength,
            'final_effectiveness': self.final_effectiveness,
            'false_positive_ratio': self.false_positive_ratio,
            'days_since_activation': self.days_since_activation,
            'total_activations': self.total_activations,
            'useful_detections': self.useful_detections,
            'false_detections': self.false_detections,
            'extinct_at': self.extinct_at.isoformat(),
        }


class ExtinctionLogic:
    """
    Manage memory cell lifecycle and population.
    
    Functions:
    - Detect weak/irrelevant cells for removal
    - Suppress auto-immune responses
    - Prevent memory explosion
    - Balance exploration vs. exploitation
    """
    
    def __init__(self):
        self.extinction_records: List[ExtinctionRecord] = []
        self.extinction_threshold = 0.2      # Strength threshold for extinction
        self.fp_tolerance = 0.2              # False positive tolerance (FP/TP ratio)
        self.max_population = 10000          # Max total memory cells
        self.max_per_attack_type = 100       # Max variants per attack type
        self.max_irrelevance_days = 90       # How long before irrelevant cells die
        self.conflict_threshold = 0.95       # Similarity threshold for conflicts
    
    def evaluate_for_extinction(self, cell: MemoryCell) -> Optional[Tuple[ExtinctionReason, float]]:
        """
        Evaluate if a memory cell should be marked for extinction.
        
        Returns (reason, confidence) if should extinct, None otherwise.
        """
        
        # Check 1: Natural decay - strength too low
        if cell.strength < self.extinction_threshold:
            confidence = 1.0 - (cell.strength / self.extinction_threshold)
            return (ExtinctionReason.STRENGTH_DECAY, confidence)
        
        # Check 2: Auto-immunity - too many false positives
        fp_ratio = self._compute_false_positive_ratio(cell)
        if fp_ratio > self.fp_tolerance:
            confidence = min(1.0, fp_ratio / (self.fp_tolerance * 2))
            return (ExtinctionReason.AUTO_IMMUNE, confidence)
        
        # Check 3: Low effectiveness - antibodies don't work
        effectiveness = self._compute_antibody_effectiveness(cell)
        if effectiveness < 0.3 and cell.activation_count > 10:
            return (ExtinctionReason.LOW_EFFECTIVENESS, 0.7)
        
        # Check 4: Irrelevance - not used for long time
        days_inactive = (datetime.now() - cell.last_activated).days
        if days_inactive > self.max_irrelevance_days:
            confidence = min(1.0, days_inactive / (self.max_irrelevance_days * 2))
            return (ExtinctionReason.IRRELEVANCE, confidence)
        
        return None
    
    def _compute_false_positive_ratio(self, cell: MemoryCell) -> float:
        """Compute false positive / true positive ratio"""
        total_fp = sum(ab.false_positives for ab in cell.antibodies)
        total_tp = sum(ab.true_positives for ab in cell.antibodies)
        
        if total_tp == 0:
            return 1.0 if total_fp > 0 else 0.0
        
        return total_fp / max(1, total_tp)
    
    def _compute_antibody_effectiveness(self, cell: MemoryCell) -> float:
        """Compute average antibody effectiveness"""
        if not cell.antibodies:
            return 0.0
        
        total_effectiveness = sum(ab.compute_effectiveness() for ab in cell.antibodies)
        return total_effectiveness / len(cell.antibodies)
    
    def suppress_auto_immune(self, cells: List[MemoryCell]) -> List[MemoryCell]:
        """
        Suppress false positive generators (auto-immunity).
        
        Cells with high false positive rates are marked ANERGIC.
        """
        suppressed = []
        
        for cell in cells:
            fp_ratio = self._compute_false_positive_ratio(cell)
            
            if fp_ratio > self.fp_tolerance:
                # Suppress this cell (like T-regulatory cells)
                cell.cell_state = CellState.ANERGIC
                suppressed.append(cell)
        
        return suppressed
    
    def manage_population(
        self,
        cells: List[MemoryCell],
        attack_type_map: Dict[str, List[str]]
    ) -> Tuple[List[MemoryCell], List[ExtinctionRecord]]:
        """
        Manage memory population to prevent explosion.
        
        Returns:
        - Surviving cells
        - Extinction records
        """
        surviving_cells = []
        extinctions = []
        
        # Check total population limit
        if len(cells) > self.max_population:
            cells = self._prune_weakest(cells, len(cells) - self.max_population)
        
        # Check per-attack-type limits
        for attack_type, cell_ids in attack_type_map.items():
            if len(cell_ids) > self.max_per_attack_type:
                # Keep strongest, mark rest for extinction
                attack_cells = [c for c in cells if c.cell_id in cell_ids]
                keep_cells = sorted(attack_cells, key=lambda c: c.strength, reverse=True)[
                    :self.max_per_attack_type
                ]
                
                for cell in attack_cells:
                    if cell not in keep_cells:
                        # Mark for extinction
                        record = self._create_extinction_record(
                            cell, ExtinctionReason.RESOURCE_PRESSURE
                        )
                        extinctions.append(record)
                    else:
                        surviving_cells.append(cell)
            else:
                surviving_cells = [c for c in cells if c.cell_id in cell_ids]
        
        return surviving_cells, extinctions
    
    def remove_conflicts(self, cells: List[MemoryCell]) -> Tuple[List[MemoryCell], List[ExtinctionRecord]]:
        """
        Remove conflicting memory cells.
        
        When two cells for the same attack have contradictory rules,
        keep the stronger one.
        """
        extinctions = []
        cells_by_attack = {}
        
        # Group by attack type
        for cell in cells:
            attack = cell.attack_signature.attack_type
            if attack not in cells_by_attack:
                cells_by_attack[attack] = []
            cells_by_attack[attack].append(cell)
        
        # Find conflicts within each attack type
        surviving_cells = []
        
        for attack_type, group in cells_by_attack.items():
            # Sort by strength
            sorted_group = sorted(group, key=lambda c: c.strength, reverse=True)
            
            # Keep strongest, check if others conflict
            kept = [sorted_group[0]]
            
            for candidate in sorted_group[1:]:
                conflicts = False
                
                for kept_cell in kept:
                    # Check if they have contradictory antibody rules
                    similarity = self._compute_rule_similarity(
                        kept_cell, candidate
                    )
                    
                    if similarity > self.conflict_threshold:
                        # Similar rules - conflict detected
                        conflicts = True
                        break
                
                if conflicts:
                    # Mark weaker cell for extinction
                    record = self._create_extinction_record(
                        candidate, ExtinctionReason.CONFLICT
                    )
                    extinctions.append(record)
                else:
                    kept.append(candidate)
            
            surviving_cells.extend(kept)
        
        return surviving_cells, extinctions
    
    def _compute_rule_similarity(self, cell1: MemoryCell, cell2: MemoryCell) -> float:
        """Compute similarity between antibody rule sets"""
        if not cell1.antibodies or not cell2.antibodies:
            return 0.0
        
        # Simple similarity: matching detection rules
        common_rules = len(set(
            (ab.rule_type, ab.deployment_status)
            for ab in cell1.antibodies
        ) & set(
            (ab.rule_type, ab.deployment_status)
            for ab in cell2.antibodies
        ))
        
        total_rules = len(set(
            (ab.rule_type, ab.deployment_status)
            for ab in cell1.antibodies + cell2.antibodies
        ))
        
        if total_rules == 0:
            return 0.0
        
        return common_rules / total_rules
    
    def _prune_weakest(self, cells: List[MemoryCell], num_to_remove: int) -> List[MemoryCell]:
        """Remove weakest cells"""
        sorted_cells = sorted(cells, key=lambda c: c.strength, reverse=True)
        return sorted_cells[:-num_to_remove] if num_to_remove > 0 else sorted_cells
    
    def _create_extinction_record(
        self,
        cell: MemoryCell,
        reason: ExtinctionReason
    ) -> ExtinctionRecord:
        """Create extinction record for a cell"""
        fp_ratio = self._compute_false_positive_ratio(cell)
        
        record = ExtinctionRecord(
            cell_id=cell.cell_id,
            reason=reason,
            final_strength=cell.strength,
            final_effectiveness=self._compute_antibody_effectiveness(cell),
            false_positive_ratio=fp_ratio,
            days_since_activation=(datetime.now() - cell.created_at).days,
            total_activations=cell.activation_count,
            useful_detections=sum(ab.true_positives for ab in cell.antibodies),
            false_detections=sum(ab.false_positives for ab in cell.antibodies),
        )
        
        self.extinction_records.append(record)
        return record
    
    def execute_extinction(self, cells: List[MemoryCell]) -> Tuple[List[MemoryCell], List[ExtinctionRecord]]:
        """
        Execute full extinction cycle.
        
        Process:
        1. Evaluate each cell
        2. Suppress auto-immune responses
        3. Manage population limits
        4. Remove conflicts
        """
        extinctions = []
        surviving_cells = []
        
        # Evaluate each cell
        for cell in cells:
            eval_result = self.evaluate_for_extinction(cell)
            
            if eval_result:
                reason, confidence = eval_result
                if confidence > 0.7:
                    # Mark cell for extinction
                    record = self._create_extinction_record(cell, reason)
                    extinctions.append(record)
                    cell.cell_state = CellState.APOPTOTIC
                else:
                    surviving_cells.append(cell)
            else:
                surviving_cells.append(cell)
        
        # Suppress auto-immune
        self.suppress_auto_immune(surviving_cells)
        
        return surviving_cells, extinctions
    
    def get_extinction_stats(self) -> Dict[str, Any]:
        """Get extinction statistics"""
        if not self.extinction_records:
            return {
                'total_extinctions': 0,
                'extinctions_by_reason': {}
            }
        
        extinctions_by_reason = {}
        for record in self.extinction_records:
            reason = record.reason.value
            if reason not in extinctions_by_reason:
                extinctions_by_reason[reason] = 0
            extinctions_by_reason[reason] += 1
        
        avg_activation_count = statistics.mean(
            r.total_activations for r in self.extinction_records
        )
        avg_usefulness = statistics.mean(
            r.useful_detections / max(1, r.useful_detections + r.false_detections)
            for r in self.extinction_records
        )
        
        return {
            'total_extinctions': len(self.extinction_records),
            'extinctions_by_reason': extinctions_by_reason,
            'avg_activation_count_at_extinction': avg_activation_count,
            'avg_usefulness_ratio': avg_usefulness,
            'most_recent_extinction': (
                self.extinction_records[-1].extinct_at.isoformat()
                if self.extinction_records else None
            )
        }
