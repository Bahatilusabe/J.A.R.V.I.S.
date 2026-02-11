"""
Blockchain Module

Immutable ledger for federated learning model provenance and verification.
"""

from .ledger import (
    Block,
    BlockProvenance,
    BlockProof,
    BlockchainLedger,
    get_blockchain_ledger,
)

__all__ = [
    "Block",
    "BlockProvenance",
    "BlockProof",
    "BlockchainLedger",
    "get_blockchain_ledger",
]
