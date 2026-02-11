"""
Mutation Engine - Adaptive Evolution of Memory Cells

Similar to immune system somatic hypermutation:
- Creates variants to recognize attack mutations
- Strengthens effective mutations
- Prunes weak variants
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import random
import hashlib
from uuid import uuid4

from .memory_cells import MemoryCell, Antibody, CellState


@dataclass
class MutationEvent:
    """Record of a mutation applied to a memory cell"""
    mutation_id: str = field(default_factory=lambda: str(uuid4()))
    parent_cell_id: str = ""
    child_cell_id: str = ""
    
    mutation_type: str = ""         # parameter_variation, signature_drift, pattern_expansion
    mutation_description: str = ""  # Human-readable description
    mutation_data: Dict[str, Any] = field(default_factory=dict)
    
    applied_at: datetime = field(default_factory=datetime.now)
    
    # Effectiveness of mutation
    effectiveness_delta: float = 0.0  # +0.05 if mutation improves detection
    variant_detections: int = 0      # Attacks blocked by this mutation
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'mutation_id': self.mutation_id,
            'parent_cell_id': self.parent_cell_id,
            'child_cell_id': self.child_cell_id,
            'mutation_type': self.mutation_type,
            'mutation_description': self.mutation_description,
            'effectiveness_delta': self.effectiveness_delta,
            'variant_detections': self.variant_detections,
            'applied_at': self.applied_at.isoformat(),
        }


class MutationEngine:
    """
    Evolve memory cells to recognize attack variations.
    
    Processes:
    - Somatic hypermutation: point mutations in detection rules
    - Affinity maturation: strengthen effective variants
    - Clonal selection: expand effective mutations
    - Negative selection: eliminate non-functional variants
    """
    
    def __init__(self):
        self.mutation_history: List[MutationEvent] = []
        self.active_mutations: Dict[str, MutationEvent] = {}
        self.mutation_effectiveness_threshold = 0.0
        self.max_variants_per_cell = 10
    
    def detect_attack_variant(
        self,
        parent_cell: MemoryCell,
        observed_signature: Dict[str, Any],
        similarity_score: float
    ) -> Optional[MemoryCell]:
        """
        Detect if this is a variant of known attack.
        If ~80% similar but not exact match, create mutation.
        """
        # If exact match, strengthen parent
        if similarity_score > 0.95:
            parent_cell.strengthen()
            return None
        
        # If partial match and parent has capacity, create variant
        if 0.7 <= similarity_score < 0.95:
            if parent_cell.variant_count < self.max_variants_per_cell:
                variant = self._create_somatic_hypermutation(parent_cell, observed_signature)
                return variant
        
        # If no match, decay parent
        parent_cell.decay()
        return None
    
    def _create_somatic_hypermutation(
        self,
        parent_cell: MemoryCell,
        variant_signature: Dict[str, Any]
    ) -> MemoryCell:
        """
        Somatic hypermutation: create variant with modified detection rules.
        
        Similar to antibody gene hypermutation in bone marrow.
        """
        mutation_type = random.choice([
            'parameter_variation',    # Adjust thresholds
            'signature_drift',        # Modify detection rule
            'pattern_expansion',      # Broaden matching pattern
            'entropy_adjustment'      # Adjust entropy thresholds
        ])
        
        # Apply mutation based on type
        mutation_data = self._generate_mutation(mutation_type, variant_signature)
        
        # Create variant cell
        variant_cell = parent_cell.create_variant(mutation_data)
        
        # Record mutation
        mutation = MutationEvent(
            parent_cell_id=parent_cell.cell_id,
            child_cell_id=variant_cell.cell_id,
            mutation_type=mutation_type,
            mutation_description=f"Somatic hypermutation: {mutation_type}",
            mutation_data=mutation_data
        )
        
        self.mutation_history.append(mutation)
        self.active_mutations[variant_cell.cell_id] = mutation
        
        return variant_cell
    
    def _generate_mutation(
        self,
        mutation_type: str,
        variant_signature: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate specific mutation parameters"""
        mutation_data = {'type': mutation_type}
        
        if mutation_type == 'parameter_variation':
            # Adjust detection thresholds
            mutation_data['threshold_adjustment'] = random.uniform(0.8, 1.2)
            mutation_data['parameter_name'] = random.choice([
                'packet_rate_threshold',
                'entropy_threshold',
                'payload_size_threshold',
                'connection_count_threshold'
            ])
        
        elif mutation_type == 'signature_drift':
            # Modify payload matching pattern
            mutation_data['pattern_relaxation'] = random.uniform(0.1, 0.3)
            mutation_data['new_entropy_range'] = (
                variant_signature.get('entropy', 0.5) - 0.1,
                variant_signature.get('entropy', 0.5) + 0.1
            )
        
        elif mutation_type == 'pattern_expansion':
            # Broaden the detection pattern
            mutation_data['expansion_factor'] = random.uniform(1.1, 1.5)
            mutation_data['additional_ports'] = random.sample(range(1024, 65535), k=3)
            mutation_data['additional_protocols'] = ['DNS', 'HTTP', 'HTTPS']
        
        elif mutation_type == 'entropy_adjustment':
            # Handle obfuscated/encrypted variants
            mutation_data['entropy_tolerance'] = 0.1
            mutation_data['compression_detection'] = True
            mutation_data['encoding_detection'] = ['base64', 'hex', 'unicode']
        
        return mutation_data
    
    def affinity_maturation(
        self,
        variant_cell: MemoryCell,
        detection_success: bool,
        confidence: float
    ) -> None:
        """
        Affinity maturation: strengthen effective variants.
        
        If mutation successfully detects attacks, increase its affinity.
        """
        mutation = self.active_mutations.get(variant_cell.cell_id)
        
        if detection_success and confidence > 0.7:
            # Strengthen the variant
            variant_cell.strength = min(1.0, variant_cell.strength + 0.1)
            variant_cell.affinity = min(1.0, variant_cell.affinity + 0.15)
            variant_cell.variant_count += 1
            
            if mutation:
                mutation.effectiveness_delta = 0.1
                mutation.variant_detections += 1
        else:
            # Weaken ineffective variant
            variant_cell.strength *= 0.9
            variant_cell.affinity *= 0.85
            
            if mutation:
                mutation.effectiveness_delta = -0.05
    
    def clonal_selection(self, parent_cell: MemoryCell) -> List[MemoryCell]:
        """
        Clonal selection: expand successful variants.
        
        If a variant is highly effective, create multiple copies for deployment.
        """
        selected_variants = []
        
        # Find variants with high effectiveness
        effective_antibodies = parent_cell.get_antibodies(effective_only=True)
        
        for antibody in effective_antibodies:
            if antibody.effectiveness > 0.75:
                # Clone this variant
                num_clones = min(3, int(antibody.effectiveness * 5))
                for _ in range(num_clones):
                    clone = MemoryCell(
                        cell_type=parent_cell.cell_type,
                        attack_signature=parent_cell.attack_signature,
                        strength=antibody.effectiveness,
                        affinity=parent_cell.affinity,
                        in_memory_pool=True,
                        memory_pool_priority=parent_cell.memory_pool_priority,
                        threat_level=parent_cell.threat_level,
                        tags=parent_cell.tags.copy()
                    )
                    clone.antibodies = [antibody]
                    selected_variants.append(clone)
        
        return selected_variants
    
    def negative_selection(self, cells: List[MemoryCell]) -> List[MemoryCell]:
        """
        Negative selection: eliminate non-functional variants.
        
        Remove cells that:
        - Have strength < 0.2 (weak)
        - Have high false positive rate (auto-immune)
        - Are in APOPTOTIC state (scheduled for death)
        """
        surviving_cells = []
        
        for cell in cells:
            # Check for survival
            should_survive = True
            
            # Weakness: strength too low
            if cell.strength < 0.2:
                should_survive = False
            
            # Auto-immunity: too many false positives
            for antibody in cell.antibodies:
                if antibody.false_positives > antibody.true_positives * 2:
                    should_survive = False
                    cell.cell_state = CellState.ANERGIC
            
            # Apoptosis: scheduled for death
            if cell.cell_state == CellState.APOPTOTIC:
                should_survive = False
            
            if should_survive:
                surviving_cells.append(cell)
        
        return surviving_cells
    
    def get_mutation_stats(self) -> Dict[str, Any]:
        """Get mutation statistics"""
        successful_mutations = [
            m for m in self.mutation_history
            if m.effectiveness_delta > 0
        ]
        
        return {
            'total_mutations': len(self.mutation_history),
            'successful_mutations': len(successful_mutations),
            'success_rate': len(successful_mutations) / max(1, len(self.mutation_history)),
            'active_mutations': len(self.active_mutations),
            'total_variant_detections': sum(
                m.variant_detections for m in self.mutation_history
            ),
            'avg_effectiveness': (
                sum(m.effectiveness_delta for m in self.mutation_history) /
                max(1, len(self.mutation_history))
            )
        }
    
    def prune_ineffective_mutations(self, threshold: float = 0.3) -> int:
        """Remove mutations with effectiveness below threshold"""
        before = len(self.active_mutations)
        
        to_remove = [
            cell_id for cell_id, mutation in self.active_mutations.items()
            if mutation.effectiveness_delta < threshold
        ]
        
        for cell_id in to_remove:
            del self.active_mutations[cell_id]
        
        return before - len(self.active_mutations)
