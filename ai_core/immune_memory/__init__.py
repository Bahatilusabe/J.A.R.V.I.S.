"""
Adaptive Immune Memory System

Inspired by biological immune system memory (B-cells, T-cells, T-regulatory cells):
- Memory cells: Store attack signatures and improve with reuse
- Mutation engine: Create variants to recognize attack mutations
- Recall optimizer: Fast retrieval of relevant memory cells
- Extinction logic: Remove irrelevant/false positive memories

This is NOT just logging or embeddings.
This is adaptive memory that learns, mutates, and evolves with each attack.
"""

from .memory_cells import (
    MemoryCell,
    CellType,
    CellState,
    AttackSignature,
    Antibody,
)

from .mutation_engine import (
    MutationEngine,
    MutationEvent,
)

from .recall_optimizer import (
    RecallOptimizer,
    RecallQuery,
    RecallResult,
)

from .extinction_logic import (
    ExtinctionLogic,
    ExtinctionRecord,
    ExtinctionReason,
)

__all__ = [
    # Memory cells
    'MemoryCell',
    'CellType',
    'CellState',
    'AttackSignature',
    'Antibody',
    
    # Mutation
    'MutationEngine',
    'MutationEvent',
    
    # Recall
    'RecallOptimizer',
    'RecallQuery',
    'RecallResult',
    
    # Extinction
    'ExtinctionLogic',
    'ExtinctionRecord',
    'ExtinctionReason',
]
