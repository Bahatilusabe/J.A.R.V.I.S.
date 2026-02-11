"""
Recall Optimizer - Memory Retrieval System

Similar to immune system antigen presentation:
- Fast recall of memory cells for known threats
- Semantic search for similar attack patterns
- Priority-based retrieval (memory pool items first)
- Vector embeddings for attack similarity
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import json
from uuid import uuid4

from .memory_cells import MemoryCell, AttackSignature, CellType, CellState


@dataclass
class RecallQuery:
    """Query to search for relevant memory cells"""
    query_id: str = field(default_factory=lambda: str(uuid4()))
    query_type: str = ""              # "exact", "semantic", "behavioral"
    
    # Exact match
    attack_type: Optional[str] = None
    protocol: Optional[str] = None
    source_ip: Optional[str] = None
    target_port: Optional[int] = None
    
    # Semantic match
    payload_characteristics: Dict[str, Any] = field(default_factory=dict)
    entropy: Optional[float] = None
    packet_rate: Optional[float] = None
    connection_count: Optional[int] = None
    
    # Behavioral match
    behavioral_signature: Dict[str, Any] = field(default_factory=dict)
    
    # Filtering
    min_strength: float = 0.0
    threat_level_filter: Optional[str] = None
    in_memory_pool_only: bool = False
    
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RecallResult:
    """Result from memory cell recall"""
    result_id: str = field(default_factory=lambda: str(uuid4()))
    query_id: str = ""
    
    matched_cells: List[Tuple[MemoryCell, float]] = field(default_factory=list)  # (cell, confidence)
    total_candidates_evaluated: int = 0
    search_time_ms: float = 0.0
    
    # Aggregated response
    recommended_action: str = ""      # "block", "investigate", "monitor"
    combined_confidence: float = 0.0
    
    def get_top_matches(self, k: int = 5) -> List[MemoryCell]:
        """Get top K best-matching memory cells"""
        sorted_matches = sorted(self.matched_cells, key=lambda x: x[1], reverse=True)
        return [cell for cell, _ in sorted_matches[:k]]
    
    def get_confidence_distribution(self) -> Dict[str, float]:
        """Get confidence score distribution"""
        confidences = [conf for _, conf in self.matched_cells]
        if not confidences:
            return {}
        
        return {
            'min': min(confidences),
            'max': max(confidences),
            'avg': sum(confidences) / len(confidences),
            'median': sorted(confidences)[len(confidences) // 2]
        }


class RecallOptimizer:
    """
    Memory cell retrieval and ranking system.
    
    Implements:
    - Two-tier search (fast memory pool + full search)
    - Semantic similarity scoring
    - Behavioral pattern matching
    - Confidence-ranked results
    """
    
    def __init__(self):
        self.memory_cells: Dict[str, MemoryCell] = {}  # cell_id -> MemoryCell
        self.memory_pool: List[str] = []               # cell_ids in fast-response pool
        self.attack_index: Dict[str, List[str]] = {}   # attack_type -> [cell_ids]
        self.embedding_cache: Dict[str, List[float]] = {}  # cell_id -> embedding
    
    def add_cell(self, cell: MemoryCell) -> None:
        """Add a memory cell to the recall system"""
        self.memory_cells[cell.cell_id] = cell
        
        # Index by attack type for fast lookup
        attack_type = cell.attack_signature.attack_type
        if attack_type not in self.attack_index:
            self.attack_index[attack_type] = []
        self.attack_index[attack_type].append(cell.cell_id)
        
        # Add to memory pool if applicable
        if cell.in_memory_pool:
            self._add_to_memory_pool(cell)
    
    def _add_to_memory_pool(self, cell: MemoryCell) -> None:
        """Add cell to fast-response memory pool"""
        if cell.cell_id not in self.memory_pool:
            self.memory_pool.append(cell.cell_id)
            # Sort by priority
            self.memory_pool.sort(
                key=lambda cid: self.memory_cells[cid].memory_pool_priority,
                reverse=True
            )
    
    def recall_exact(self, attack_type: str, protocol: str = None) -> List[MemoryCell]:
        """
        Exact recall: fast lookup for known attack types.
        
        Used when attack matches a known threat exactly.
        """
        if attack_type not in self.attack_index:
            return []
        
        cells = [
            self.memory_cells[cid]
            for cid in self.attack_index[attack_type]
            if self.memory_cells[cid].is_alive()
        ]
        
        # Filter by protocol if specified
        if protocol:
            cells = [c for c in cells if c.attack_signature.protocol == protocol]
        
        # Sort by strength (most mature first)
        return sorted(cells, key=lambda c: c.strength, reverse=True)
    
    def recall_semantic(self, query: RecallQuery) -> RecallResult:
        """
        Semantic recall: find similar attacks using payload characteristics.
        
        Used when attack doesn't match exactly but has similar patterns.
        """
        result = RecallResult(query_id=query.query_id)
        candidates = []
        
        # Filter candidates
        for cell_id, cell in self.memory_cells.items():
            if not cell.is_alive():
                continue
            if cell.strength < query.min_strength:
                continue
            if query.threat_level_filter and cell.threat_level != query.threat_level_filter:
                continue
            
            # Compute similarity score
            confidence = self._compute_semantic_similarity(cell, query)
            
            if confidence > 0.5:  # Threshold for match
                candidates.append((cell, confidence))
        
        # Sort by confidence
        candidates.sort(key=lambda x: x[1], reverse=True)
        result.matched_cells = candidates
        result.total_candidates_evaluated = len(self.memory_cells)
        
        # Compute combined confidence
        if candidates:
            confidences = [c for _, c in candidates]
            result.combined_confidence = sum(confidences) / len(confidences)
            result.recommended_action = self._recommend_action(result.combined_confidence)
        
        return result
    
    def recall_behavioral(self, query: RecallQuery) -> RecallResult:
        """
        Behavioral recall: match based on attack behavior patterns.
        
        Used for polymorphic/obfuscated variants.
        """
        result = RecallResult(query_id=query.query_id)
        candidates = []
        
        for cell_id, cell in self.memory_cells.items():
            if not cell.is_alive():
                continue
            if cell.cell_type != CellType.T_CELL:
                continue
            
            # Behavioral match
            confidence = self._compute_behavioral_similarity(cell, query)
            
            if confidence > 0.6:
                candidates.append((cell, confidence))
        
        # Sort by confidence
        candidates.sort(key=lambda x: x[1], reverse=True)
        result.matched_cells = candidates
        result.total_candidates_evaluated = len(self.memory_cells)
        
        if candidates:
            confidences = [c for _, c in candidates]
            result.combined_confidence = sum(confidences) / len(confidences)
            result.recommended_action = self._recommend_action(result.combined_confidence)
        
        return result
    
    def recall_memory_pool(self) -> List[MemoryCell]:
        """
        Ultra-fast recall: get high-priority memory cells.
        
        Used for immediate response before full search.
        """
        pool_cells = [
            self.memory_cells[cid]
            for cid in self.memory_pool
            if self.memory_cells[cid].is_alive()
        ]
        
        return sorted(
            pool_cells,
            key=lambda c: (c.memory_pool_priority, c.strength),
            reverse=True
        )
    
    def _compute_semantic_similarity(self, cell: MemoryCell, query: RecallQuery) -> float:
        """
        Compute semantic similarity between attack patterns.
        
        Factors:
        - Entropy similarity
        - Packet rate similarity
        - Protocol match
        - Port match
        """
        score = 0.0
        factors = 0
        
        # Protocol match (exact)
        if query.protocol and cell.attack_signature.protocol == query.protocol:
            score += 0.2
        factors += 0.2
        
        # Port match
        if query.target_port and query.target_port in cell.attack_signature.target_ports:
            score += 0.2
        factors += 0.2
        
        # Entropy similarity
        if query.entropy is not None:
            payload_entropy = cell.attack_signature.payload_characteristics.get('entropy', 0.5)
            entropy_diff = abs(query.entropy - payload_entropy)
            entropy_similarity = max(0.0, 1.0 - entropy_diff)
            score += entropy_similarity * 0.3
            factors += 0.3
        
        # Packet rate similarity
        if query.packet_rate is not None:
            query_rate = query.packet_rate
            cell_rate = cell.attack_signature.payload_characteristics.get('packet_rate', 0)
            if cell_rate > 0:
                rate_ratio = min(query_rate, cell_rate) / max(query_rate, cell_rate)
                score += rate_ratio * 0.3
                factors += 0.3
        
        # Normalize by factors present
        if factors > 0:
            return score / factors
        
        return 0.0
    
    def _compute_behavioral_similarity(self, cell: MemoryCell, query: RecallQuery) -> float:
        """
        Compute behavioral similarity using pattern matching.
        
        T-Cell style: behavior-based recognition vs. exact pattern.
        """
        score = 0.0
        factors = 0
        
        # Connection pattern similarity
        query_conn = query.behavioral_signature.get('connection_count')
        cell_conn = cell.attack_signature.payload_characteristics.get('connection_count')
        
        if query_conn and cell_conn:
            conn_ratio = min(query_conn, cell_conn) / max(query_conn, cell_conn)
            score += conn_ratio * 0.4
            factors += 0.4
        
        # Attack pattern complexity
        query_complexity = query.behavioral_signature.get('pattern_complexity', 0)
        cell_complexity = cell.attack_signature.payload_characteristics.get('pattern_complexity', 0)
        
        if query_complexity > 0 and cell_complexity > 0:
            complexity_similarity = 1.0 - abs(query_complexity - cell_complexity)
            score += max(0, complexity_similarity) * 0.3
            factors += 0.3
        
        # Use cell affinity as weight
        score *= cell.affinity
        factors += 0.3
        
        if factors > 0:
            return score / factors
        
        return 0.0
    
    def _recommend_action(self, confidence: float) -> str:
        """Recommend action based on confidence level"""
        if confidence > 0.85:
            return "block"
        elif confidence > 0.65:
            return "investigate"
        else:
            return "monitor"
    
    def get_recall_stats(self) -> Dict[str, Any]:
        """Get recall system statistics"""
        alive_cells = [c for c in self.memory_cells.values() if c.is_alive()]
        
        return {
            'total_cells': len(self.memory_cells),
            'alive_cells': len(alive_cells),
            'memory_pool_size': len(self.memory_pool),
            'attack_types_indexed': len(self.attack_index),
            'avg_cell_strength': (
                sum(c.strength for c in alive_cells) / max(1, len(alive_cells))
            ),
            'memory_pool_priority_range': (
                min((self.memory_cells[cid].memory_pool_priority for cid in self.memory_pool), default=0),
                max((self.memory_cells[cid].memory_pool_priority for cid in self.memory_pool), default=0)
            )
        }
