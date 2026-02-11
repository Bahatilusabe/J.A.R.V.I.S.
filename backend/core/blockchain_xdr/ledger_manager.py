"""Simple ledger manager scaffold.

This module provides a small in-memory LedgerManager class intended as a
scaffold for higher-level blockchain/ledger integrations. It is not a full
consensus or persistence implementation — just a deterministic, testable
component for integration and examples.
"""

from typing import Dict, Any, List, Optional
import json
import time
import hashlib
import logging

# Gate heavy/optional dependencies so this module can be imported in CI/docs
# without installing Hyperledger Fabric SDK or cryptography packages.
try:
    # Hyperledger Fabric Python SDK (hfc) - optional
    # Typical import: from hfc.fabric import Client as FabricClient
    from hfc.fabric import Client as FabricClient  # type: ignore
    FABRIC_AVAILABLE = True
except Exception:  # pragma: no cover - optional in CI
    FabricClient = None  # type: ignore
    FABRIC_AVAILABLE = False

try:
    from cryptography import x509  # type: ignore
    from cryptography.hazmat.primitives import hashes, serialization  # type: ignore
    from cryptography.hazmat.primitives.asymmetric import padding  # type: ignore
    CRYPTO_AVAILABLE = True
except Exception:  # pragma: no cover - optional in CI
    x509 = None  # type: ignore
    hashes = None  # type: ignore
    serialization = None  # type: ignore
    padding = None  # type: ignore
    CRYPTO_AVAILABLE = False

logger = logging.getLogger(__name__)


class LedgerManager:
    """Ledger manager with optional Hyperledger Fabric backing.

    If the Hyperledger Fabric Python SDK is available and `dry_run` is False,
    `store_signed_threat` will attempt to submit a chaincode invocation to a
    Fabric network. If the SDK or network config isn't available the manager
    falls back to a deterministic in-memory ledger useful for tests and CI.
    """

    def __init__(
        self,
        fabric_profile: Optional[str] = None,
        channel_name: Optional[str] = None,
        org: Optional[str] = None,
        user: Optional[str] = None,
        dry_run: bool = True,
    ) -> None:
        self.fabric_profile = fabric_profile
        self.channel_name = channel_name
        self.org = org
        self.user = user
        self.dry_run = dry_run

        # in-memory fallback storage
        self.ledgers: Dict[str, Dict[str, Any]] = {}

        # fabric client is lazily initialized only when needed
        self._fabric_client = None

    # ----------------------------- Fabric helpers -------------------------
    def _init_fabric(self):
        """Initialize the Fabric client if available and not already created.

        This method purposely keeps initialization lightweight and defensive -
        real deployments should call `connect` with a validated network
        profile and requester identity.
        """
        if not FABRIC_AVAILABLE:
            raise RuntimeError("Hyperledger Fabric SDK (hfc) is not installed")
        if self._fabric_client is None:
            logger.debug("Initializing Fabric Client (net profile=%s)", self.fabric_profile)
            self._fabric_client = FabricClient(net_profile=self.fabric_profile)  # type: ignore

    def connect(self, org: Optional[str] = None, user: Optional[str] = None):
        """Connect and set requester identity for subsequent invocations.

        In a full implementation you'd set up crypto materials and ensure the
        user is enrolled. Here we store the requested values for calls that
        need them. If `dry_run` is False and the SDK is available we try to
        initialize the client.
        """
        self.org = org or self.org
        self.user = user or self.user
        if not self.dry_run and FABRIC_AVAILABLE:
            self._init_fabric()

    # -------------------------- chaincode interaction ---------------------
    def submit_chaincode(
        self,
        chaincode_name: str,
        fcn: str,
        args: List[str],
        peers: Optional[List[str]] = None,
        transient_map: Optional[Dict[str, bytes]] = None,
    ) -> str:
        """Submit a chaincode invoke and return a txid-like string.

        When running in `dry_run` mode or when the Fabric SDK is missing this
        stores the payload in-memory and returns a deterministic txid.
        """
        payload = {"chaincode": chaincode_name, "fcn": fcn, "args": args}
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))

        if self.dry_run or not FABRIC_AVAILABLE:
            logger.info("Dry-run or Fabric SDK missing: storing payload in-memory")
            ledger_id = chaincode_name
            self.ledgers.setdefault(ledger_id, {"transactions": [], "created": time.time()})
            txid = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
            tx_rec = {"txid": txid, "payload": payload, "timestamp": time.time()}
            self.ledgers[ledger_id]["transactions"].append(tx_rec)
            return txid

        # Real Fabric submit path - best-effort wrapper. The actual invocation
        # call signatures differ between SDK versions; keep guarded and
        # descriptive error messages.
        try:
            self._init_fabric()
            req_user = self.user
            if not req_user:
                raise RuntimeError("requester user identity not set; call connect() first")

            # The hfc client's chaincode_invoke() may be used like this:
            # self._fabric_client.chaincode_invoke(
            #     requestor=req_user, channel_name=self.channel_name,
            #     peers=peers, args=args, cc_name=chaincode_name, fcn=fcn,
            # )
            logger.debug("Invoking chaincode %s.%s peers=%s", chaincode_name, fcn, peers)
            invoke_result = self._fabric_client.chaincode_invoke(
                requestor=req_user,
                channel_name=self.channel_name,
                peers=peers,
                args=args,
                cc_name=chaincode_name,
                fcn=fcn,
                transient_map=transient_map,
            )
            # Depending on SDK/version the result may be a dict or a txid string
            if isinstance(invoke_result, dict) and "txid" in invoke_result:
                return invoke_result["txid"]
            return str(invoke_result)

        except Exception as e:  # pragma: no cover - integration path
            logger.exception("Fabric invocation failed, falling back to in-memory: %s", e)
            # fallback deterministic txid
            txid = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
            ledger_id = chaincode_name
            self.ledgers.setdefault(ledger_id, {"transactions": [], "created": time.time()})
            tx_rec = {"txid": txid, "payload": payload, "timestamp": time.time(), "error": str(e)}
            self.ledgers[ledger_id]["transactions"].append(tx_rec)
            return txid

    # ------------------------ threat-specific API ------------------------
    def store_signed_threat(
        self,
        chaincode_name: str,
        threat: Dict[str, Any],
        signature: bytes,
        signer_cert_pem: Optional[bytes] = None,
        fcn: str = "storeThreat",
        peers: Optional[List[str]] = None,
    ) -> str:
        """Store a signed threat record on the ledger (chaincode invocation).

        Parameters
        - chaincode_name: target chaincode
        - threat: threat payload (serializable dict)
        - signature: raw signature bytes over the canonical serialized threat
        - signer_cert_pem: PEM-encoded certificate bytes containing the public key

        The method will attempt to verify the signature if cryptography is
        installed and a certificate is provided. Verification failure will
        raise ValueError. On dry-run or missing Fabric SDK the payload will be
        stored in-memory and a deterministic txid will be returned.
        """
        threat_json = json.dumps(threat, sort_keys=True, separators=(",", ":"))

        # Optional signature verification
        if signer_cert_pem and CRYPTO_AVAILABLE:
            try:
                cert = x509.load_pem_x509_certificate(signer_cert_pem)
                pub = cert.public_key()
                # Try RSA verification (common case). If it fails, try to call
                # verify on the public key and let it raise if unsupported.
                try:
                    pub.verify(
                        signature,
                        threat_json.encode("utf-8"),
                        padding.PKCS1v15(),
                        hashes.SHA256(),
                    )
                except AttributeError:
                    # Some public key objects (ECDSA) expose a different API
                    # call `verify` generically and allow exceptions to bubble.
                    pub.verify(signature, threat_json.encode("utf-8"))
            except Exception as e:  # pragma: no cover - depends on runtime libs
                logger.exception("Signature verification failed: %s", e)
                raise ValueError("signature verification failed")
        elif signer_cert_pem and not CRYPTO_AVAILABLE:
            logger.warning("cryptography not available; skipping signature verification")

        payload = [threat_json, signature.hex(), (signer_cert_pem.decode("utf-8") if isinstance(signer_cert_pem, (bytes, bytearray)) else signer_cert_pem or "")]

        # Submit to chaincode
        txid = self.submit_chaincode(chaincode_name=chaincode_name, fcn=fcn, args=payload, peers=peers)
        return txid

    # ----------------------------- utilities -----------------------------
    def create_ledger(self, ledger_id: str) -> None:
        if ledger_id in self.ledgers:
            raise ValueError(f"ledger '{ledger_id}' already exists")
        self.ledgers[ledger_id] = {"transactions": [], "created": time.time()}

    def get_transactions(self, ledger_id: str) -> List[Dict[str, Any]]:
        if ledger_id not in self.ledgers:
            raise KeyError(f"ledger '{ledger_id}' not found")
        return list(self.ledgers[ledger_id]["transactions"])

    def export_state(self, ledger_id: str) -> str:
        """Return a JSON string representing the ledger state for export."""
        if ledger_id not in self.ledgers:
            raise KeyError(f"ledger '{ledger_id}' not found")
        return json.dumps(self.ledgers[ledger_id], sort_keys=True)

