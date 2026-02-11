"""Neural contract scaffolds and chain-backed adapters.

This module provides a simple `NeuralContract` interface plus two adapters
that illustrate how a neural contract might be backed by either:
- an Ethereum smart contract written in Solidity (accessed via web3.py), or
- a Hyperledger Fabric Go chaincode (invoked via the Fabric SDK / ledger manager).

Both adapters are gated: heavy dependencies (web3, Fabric SDK) are optional
and the classes fall back to a deterministic, dependency-free emulation
when those libraries or networks are not available. The aim is to provide a
clear integration surface for ethics & provenance enforcement without
preventing CI/docs imports.
"""

from typing import Any, Dict, Optional
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

# Optional: web3 (Ethereum) - used to interact with deployed Solidity contracts
try:
    from web3 import Web3  # type: ignore
    WEB3_AVAILABLE = True
except Exception:  # pragma: no cover - optional in CI
    Web3 = None  # type: ignore
    WEB3_AVAILABLE = False

# Optional: Fabric ledger manager integration is provided by our local module
try:
    from . import ledger_manager as _ledger_manager  # type: ignore
    FABRIC_LEDGER_AVAILABLE = True
except Exception:  # pragma: no cover - optional in CI
    _ledger_manager = None  # type: ignore
    FABRIC_LEDGER_AVAILABLE = False


class NeuralContract:
    """Base interface for model-backed contracts.

    Concrete implementations should implement `evaluate(input_data)` which
    returns a serializable dict with at least `score` and `raw` fields.
    """

    def __init__(self, model_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.model_id = model_id
        self.metadata = metadata or {}

    def evaluate(self, input_data: str) -> Dict[str, Any]:
        """Deterministic fallback evaluation used when heavy backends aren't present.

        This ensures imports and tests remain fast and deterministic.
        """
        h = hashlib.sha256(input_data.encode("utf-8")).hexdigest()
        score = int(h[:8], 16) / float(0xFFFFFFFF)
        return {"model_id": self.model_id, "score": score, "raw": h}


class EthereumNeuralContract(NeuralContract):
    """Adapter to call a Solidity smart contract via web3.py.

    This class expects an already-deployed contract address and ABI. It will
    attempt to call a read-only `evaluate(string)` method on the contract.
    If `web3` is unavailable, or the contract call fails, the method falls
    back to the deterministic `NeuralContract.evaluate` implementation.
    """

    def __init__(
        self,
        model_id: str,
        contract_address: Optional[str] = None,
        contract_abi: Optional[Any] = None,
        web3_provider: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(model_id, metadata=metadata)
        self.contract_address = contract_address
        self.contract_abi = contract_abi
        self.web3_provider = web3_provider
        self._w3 = None

    def _init_web3(self):
        if not WEB3_AVAILABLE:
            raise RuntimeError("web3.py is not installed")
        if self._w3 is None:
            provider = self.web3_provider or "http://localhost:8545"
            self._w3 = Web3(Web3.HTTPProvider(provider))

    def evaluate(self, input_data: str) -> Dict[str, Any]:
        if not WEB3_AVAILABLE or not self.contract_address or not self.contract_abi:
            logger.debug("Ethereum backend unavailable or no contract configured, using fallback")
            return super().evaluate(input_data)

        try:
            self._init_web3()
            contract = self._w3.eth.contract(address=self.contract_address, abi=self.contract_abi)
            # Expect the contract to implement a read-only `evaluate(string)` method
            res = contract.functions.evaluate(input_data).call()
            # Normalize the return value if it's a simple numeric score
            if isinstance(res, (int, float)):
                return {"model_id": self.model_id, "score": float(res), "raw": str(res)}
            # If the contract returns JSON-serializable structures, attempt to parse
            try:
                parsed = json.loads(res) if isinstance(res, (str, bytes)) else res
                return {"model_id": self.model_id, "score": parsed.get("score"), "raw": parsed}
            except Exception:
                return {"model_id": self.model_id, "score": None, "raw": res}
        except Exception as e:  # pragma: no cover - heavy integration
            logger.exception("Ethereum contract call failed, falling back: %s", e)
            return super().evaluate(input_data)


class FabricNeuralContract(NeuralContract):
    """Adapter that invokes a Go chaincode on Hyperledger Fabric.

    The class uses the local `ledger_manager` submit wrapper when available
    to invoke a chaincode function `Evaluate` (or configurable `fcn`). If the
    Fabric libraries or network are unavailable it falls back to the
    deterministic evaluate.
    """

    def __init__(
        self,
        model_id: str,
        chaincode_name: Optional[str] = None,
        fcn: str = "Evaluate",
        ledger: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(model_id, metadata=metadata)
        self.chaincode_name = chaincode_name or "neuralcc"
        self.fcn = fcn
        # ledger can be an instance of LedgerManager or None; if None we will
        # use the module-level ledger_manager if available
        self.ledger = ledger

    def _get_ledger(self):
        if self.ledger:
            return self.ledger
        if FABRIC_LEDGER_AVAILABLE and hasattr(_ledger_manager, "LedgerManager"):
            # default to an in-memory ledger manager if present
            return _ledger_manager.LedgerManager(dry_run=True)
        return None

    def evaluate(self, input_data: str) -> Dict[str, Any]:
        lm = self._get_ledger()
        if lm is None:
            logger.debug("Fabric ledger unavailable, using fallback evaluate")
            return super().evaluate(input_data)

        try:
            # Submit the chaincode invocation and interpret the result if any
            txid = lm.submit_chaincode(chaincode_name=self.chaincode_name, fcn=self.fcn, args=[input_data, self.model_id])
            # In many Fabric contracts the evaluate call may return data via
            # query/chaincode query; here we return a provenance record with txid
            return {"model_id": self.model_id, "score": None, "raw": {"txid": txid}}
        except Exception as e:  # pragma: no cover - integration path
            logger.exception("Fabric evaluate failed, using fallback: %s", e)
            return super().evaluate(input_data)

