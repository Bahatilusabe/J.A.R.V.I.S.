"""blockchain_xdr package

Light-weight scaffolding for blockchain-related helpers used by the project.
This package contains experimental helpers for ledger management, neural "smart"
contracts and a homomorphic-layer interface (placeholders only).

These modules are intentionally lightweight and free of heavy ML/crypto
dependencies so they can be imported safely in CI and documentation builds.
"""

from .ledger_manager import LedgerManager
from .neural_contracts import NeuralContract
from .homomorphic_layer import HomomorphicLayer

__all__ = ["LedgerManager", "NeuralContract", "HomomorphicLayer"]
