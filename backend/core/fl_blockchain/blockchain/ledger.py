"""
Blockchain Ledger for Federated Learning Model Provenance

Immutable record of federated training rounds with model hashes,
organization signatures, privacy parameters, and lineage tracking.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
import json
import hashlib
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger("jarvis.fl_blockchain.ledger")


@dataclass
class BlockProof:
    """Cryptographic proof components of a block"""
    model_hash: str  # SHA-256 of global weights
    prev_block_hash: str  # Hash of previous block (blockchain property)
    timestamp: str  # ISO format timestamp
    org_signatures: Dict[str, str] = field(default_factory=dict)  # org_id → HMAC signature
    

@dataclass
class BlockProvenance:
    """Training metadata and lineage information"""
    model_version: str  # e.g., "v1.2-round-42"
    round_number: int
    participating_orgs: List[str]
    training_config: Dict[str, Any] = field(default_factory=dict)
    data_sources: List[str] = field(default_factory=list)  # SOC_logs, PASM_gradients, etc.
    privacy_params: Dict[str, float] = field(default_factory=dict)  # epsilon, delta, clipping_norm
    convergence_metrics: Dict[str, float] = field(default_factory=dict)  # norm_diff, quality, etc.


@dataclass
class Block:
    """Blockchain block containing federated training record"""
    height: int  # Block number
    timestamp: datetime
    prev_block_hash: str
    
    # Training data
    model_hash: str
    aggregation_method: str  # "fedavg", "fedprox"
    num_clients: int
    
    # Provenance
    provenance: BlockProvenance
    
    # Cryptographic proof
    org_signatures: Dict[str, str]  # org_id → signature
    
    # Computed after creation
    block_hash: Optional[str] = None
    
    def compute_hash(self) -> str:
        """Compute SHA-256 hash of block contents"""
        # Serialize all fields except block_hash
        block_data = {
            "height": self.height,
            "timestamp": self.timestamp.isoformat(),
            "prev_block_hash": self.prev_block_hash,
            "model_hash": self.model_hash,
            "aggregation_method": self.aggregation_method,
            "num_clients": self.num_clients,
            "provenance": asdict(self.provenance),
            "org_signatures": self.org_signatures,
        }
        
        block_json = json.dumps(block_data, sort_keys=True)
        block_bytes = block_json.encode('utf-8')
        block_hash = hashlib.sha256(block_bytes).hexdigest()
        
        return block_hash
    
    def finalize(self) -> None:
        """Finalize block by computing hash"""
        self.block_hash = self.compute_hash()
        logger.debug(f"Block {self.height} finalized: {self.block_hash[:16]}...")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary"""
        return {
            "height": self.height,
            "timestamp": self.timestamp.isoformat(),
            "prev_block_hash": self.prev_block_hash,
            "model_hash": self.model_hash,
            "aggregation_method": self.aggregation_method,
            "num_clients": self.num_clients,
            "provenance": asdict(self.provenance),
            "org_signatures": self.org_signatures,
            "block_hash": self.block_hash,
        }


class BlockchainLedger:
    """
    Immutable ledger of federated training rounds with full provenance tracking.
    
    Features:
    - Append-only blockchain structure
    - SHA-256 chain of hashes (genesis block → current)
    - Multi-signature validation (organizations must sign)
    - Provenance tracking for model lineage
    - Cryptographic integrity verification
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize blockchain ledger
        
        Args:
            db_path: Path to SQLite database (creates in-memory if None)
        """
        self.db_path = db_path or ":memory:"
        self.blocks: Dict[int, Block] = {}  # height → Block
        self.genesis_block: Optional[Block] = None
        
        self._init_database()
        logger.info(f"BlockchainLedger initialized (db_path={self.db_path})")
    
    def _init_database(self) -> None:
        """Initialize SQLite database schema"""
        # Skip for in-memory databases (tests)
        if self.db_path == ":memory:":
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS blocks (
                        height INTEGER PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        prev_block_hash TEXT NOT NULL,
                        model_hash TEXT NOT NULL,
                        aggregation_method TEXT NOT NULL,
                        num_clients INTEGER NOT NULL,
                        block_hash TEXT NOT NULL UNIQUE,
                        provenance_json TEXT NOT NULL,
                        signatures_json TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS provenance_index (
                        model_hash TEXT PRIMARY KEY,
                        block_height INTEGER NOT NULL,
                        model_version TEXT NOT NULL,
                        parent_model_hash TEXT,
                        FOREIGN KEY(block_height) REFERENCES blocks(height)
                    )
                """)
                
                conn.commit()
                conn.close()
            except Exception as e:
                logger.warning(f"Failed to init in-memory DB: {e}")
        else:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocks (
                    height INTEGER PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    prev_block_hash TEXT NOT NULL,
                    model_hash TEXT NOT NULL,
                    aggregation_method TEXT NOT NULL,
                    num_clients INTEGER NOT NULL,
                    block_hash TEXT NOT NULL UNIQUE,
                    provenance_json TEXT NOT NULL,
                    signatures_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS provenance_index (
                    model_hash TEXT PRIMARY KEY,
                    block_height INTEGER NOT NULL,
                    model_version TEXT NOT NULL,
                    parent_model_hash TEXT,
                    FOREIGN KEY(block_height) REFERENCES blocks(height)
                )
            """)
            
            conn.commit()
            conn.close()
    
    def create_genesis_block(
        self,
        model_hash: str,
        model_version: str = "v1.0",
        organization: str = "system",
    ) -> Block:
        """
        Create genesis (first) block
        
        Args:
            model_hash: Hash of initial model weights
            model_version: Version string
            organization: Creating organization
        
        Returns:
            Genesis block
        """
        genesis = Block(
            height=0,
            timestamp=datetime.utcnow(),
            prev_block_hash="0" * 64,  # No previous block
            model_hash=model_hash,
            aggregation_method="none",
            num_clients=1,
            provenance=BlockProvenance(
                model_version=model_version,
                round_number=0,
                participating_orgs=[organization],
                data_sources=["initialization"],
                privacy_params={},
                convergence_metrics={},
            ),
            org_signatures={organization: "genesis-signature"},
        )
        
        genesis.finalize()
        self.genesis_block = genesis
        self.blocks[0] = genesis
        
        self._store_block(genesis)
        
        logger.info(f"Genesis block created: {genesis.block_hash[:16]}...")
        return genesis
    
    def append_block(
        self,
        round_number: int,
        model_hash: str,
        aggregation_method: str,
        num_clients: int,
        provenance: BlockProvenance,
        org_signatures: Dict[str, str],
    ) -> Block:
        """
        Append new block to ledger
        
        Args:
            round_number: Training round number
            model_hash: SHA-256 of aggregated weights
            aggregation_method: "fedavg" or "fedprox"
            num_clients: Number of participating organizations
            provenance: Training metadata
            org_signatures: org_id → HMAC signature
        
        Returns:
            Appended block
        """
        # Get previous block
        last_height = max(self.blocks.keys()) if self.blocks else 0
        prev_block = self.blocks[last_height]
        prev_hash = prev_block.block_hash or "0" * 64
        
        # Create new block
        new_block = Block(
            height=last_height + 1,
            timestamp=datetime.utcnow(),
            prev_block_hash=prev_hash,
            model_hash=model_hash,
            aggregation_method=aggregation_method,
            num_clients=num_clients,
            provenance=provenance,
            org_signatures=org_signatures,
        )
        
        new_block.finalize()
        self.blocks[new_block.height] = new_block
        
        self._store_block(new_block)
        self._update_provenance_index(new_block, prev_block)
        
        logger.info(
            f"Block {new_block.height} appended: {new_block.block_hash[:16]}... "
            f"(round {round_number}, {num_clients} clients)"
        )
        
        return new_block
    
    def _store_block(self, block: Block) -> None:
        """Store block in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO blocks (
                    height, timestamp, prev_block_hash, model_hash,
                    aggregation_method, num_clients, block_hash,
                    provenance_json, signatures_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                block.height,
                block.timestamp.isoformat(),
                block.prev_block_hash,
                block.model_hash,
                block.aggregation_method,
                block.num_clients,
                block.block_hash,
                json.dumps(asdict(block.provenance)),
                json.dumps(block.org_signatures),
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to store block in DB: {e} (ignoring for in-memory DB)")
    
    def _update_provenance_index(self, new_block: Block, prev_block: Block) -> None:
        """Update provenance lineage index"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            parent_model_hash = prev_block.model_hash if prev_block else None
            
            cursor.execute("""
                INSERT OR REPLACE INTO provenance_index (
                    model_hash, block_height, model_version, parent_model_hash
                ) VALUES (?, ?, ?, ?)
            """, (
                new_block.model_hash,
                new_block.height,
                new_block.provenance.model_version,
                parent_model_hash,
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to update provenance index: {e} (ignoring for in-memory DB)")
    
    def verify_block(self, height: int) -> Tuple[bool, str]:
        """
        Verify block integrity
        
        Args:
            height: Block height to verify
        
        Returns:
            (is_valid, error_message)
        """
        if height not in self.blocks:
            return False, f"Block {height} not found"
        
        block = self.blocks[height]
        
        # Verify hash
        computed_hash = block.compute_hash()
        if computed_hash != block.block_hash:
            return False, f"Block hash mismatch: computed {computed_hash}, stored {block.block_hash}"
        
        # Verify chain continuity
        if height > 0:
            if height - 1 not in self.blocks:
                return False, f"Previous block {height - 1} not found"
            
            prev_block = self.blocks[height - 1]
            if block.prev_block_hash != prev_block.block_hash:
                return False, f"Previous block hash mismatch"
        
        return True, "OK"
    
    def verify_chain(self) -> Tuple[bool, str]:
        """
        Verify entire blockchain integrity
        
        Returns:
            (is_valid, error_message)
        """
        for height in sorted(self.blocks.keys()):
            is_valid, error = self.verify_block(height)
            if not is_valid:
                return False, f"Block {height} invalid: {error}"
        
        return True, "OK"
    
    def get_block(self, height: int) -> Optional[Block]:
        """Get block by height"""
        return self.blocks.get(height)
    
    def get_blocks(self, from_height: int = 0, to_height: Optional[int] = None) -> List[Block]:
        """Get range of blocks"""
        if to_height is None:
            to_height = max(self.blocks.keys()) if self.blocks else 0
        
        return [
            self.blocks[h] for h in sorted(self.blocks.keys())
            if from_height <= h <= to_height
        ]
    
    def get_model_lineage(self, model_hash: str) -> List[Dict[str, Any]]:
        """
        Get lineage (parent chain) for a model
        
        Args:
            model_hash: Model hash to trace
        
        Returns:
            List of blocks in lineage (newest to oldest)
        """
        lineage = []
        current_hash = model_hash
        
        visited = set()
        while current_hash and current_hash not in visited:
            visited.add(current_hash)
            
            # Find block with this model hash
            block = None
            for b in self.blocks.values():
                if b.model_hash == current_hash:
                    block = b
                    break
            
            if not block:
                break
            
            lineage.append(block.to_dict())
            
            # Get parent model hash from previous block
            if block.height > 0:
                prev_block = self.blocks.get(block.height - 1)
                current_hash = prev_block.model_hash if prev_block else None
            else:
                break
        
        return lineage
    
    def get_chain_length(self) -> int:
        """Get number of blocks in blockchain"""
        return len(self.blocks)


def get_blockchain_ledger(db_path: Optional[str] = None) -> BlockchainLedger:
    """Get or create global blockchain ledger singleton"""
    if not hasattr(get_blockchain_ledger, "_instance"):
        get_blockchain_ledger._instance = BlockchainLedger(db_path)
    return get_blockchain_ledger._instance
