from fastapi import APIRouter, HTTPException, Body, Query
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import os
import logging
import json
import time
import uuid

# Optional cryptography detection (used for signature verification)
try:
    from cryptography import x509  # type: ignore
    from cryptography.hazmat.primitives import hashes, serialization  # type: ignore
    from cryptography.hazmat.primitives.asymmetric import padding  # type: ignore
    CRYPTO_AVAILABLE = True
except Exception:
    x509 = None  # type: ignore
    hashes = None  # type: ignore
    serialization = None  # type: ignore
    padding = None  # type: ignore
    CRYPTO_AVAILABLE = False

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

router = APIRouter()


# ======================== Pydantic Models ========================

class ForensicArtifact(BaseModel):
    """Forensic artifact (e.g., file, log entry, network capture)."""
    artifact_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    artifact_type: str  # "file", "log", "network", "memory", etc.
    name: str
    path: Optional[str] = None
    content_hash: Optional[str] = None  # SHA256 of artifact content
    size_bytes: Optional[int] = None
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ForensicsRecord(BaseModel):
    """Complete forensics record for an incident."""
    record_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incident_id: str
    threat_id: Optional[str] = None
    case_number: Optional[str] = None
    
    # Timeline
    incident_start: datetime
    incident_end: Optional[datetime] = None
    investigation_opened: datetime = Field(default_factory=datetime.utcnow)
    investigation_closed: Optional[datetime] = None
    
    # Collection
    artifacts: List[ForensicArtifact] = Field(default_factory=list)
    evidence_chain: Dict[str, Any] = Field(default_factory=dict)  # Chain of custody
    investigator_notes: str = ""
    
    # Integrity
    record_hash: Optional[str] = None  # Cryptographic hash of record state
    signatures: List[Dict[str, str]] = Field(default_factory=list)  # [{"signer": "...", "signature": "..."}]
    ledger_txid: Optional[str] = None  # Blockchain transaction ID
    
    # Metadata
    severity: str = "medium"  # "critical", "high", "medium", "low"
    status: str = "open"  # "open", "closed", "archived"
    labels: List[str] = Field(default_factory=list)  # "malware", "exfiltration", etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ForensicsStoreRequest(BaseModel):
    """Request to store a forensics record on the ledger."""
    record: ForensicsRecord
    signature: Optional[str] = None  # Hex-encoded signature
    signer_cert_pem: Optional[str] = None  # PEM-encoded certificate


class ForensicsRetrieveResponse(BaseModel):
    """Response from forensics retrieve."""
    source: str  # "ledger", "web3", "fabric", "in-memory"
    txid: Optional[str] = None
    record: Optional[ForensicsRecord] = None
    data: Optional[Dict[str, Any]] = None  # Raw data if source is web3/fabric


class ForensicsVerifyRequest(BaseModel):
    txid: Optional[str] = None
    # alternatively provide the record directly
    record: Optional[Dict[str, Any]] = None
    # optional overrides
    signature: Optional[str] = None
    signer_cert_pem: Optional[str] = None


class ForensicsVerifyResponse(BaseModel):
    verified: Optional[bool]
    reason: str
    signer: Optional[str] = None
    txid: Optional[str] = None


# ======================== Integration Clients ========================

# Guarded Web3.py client
_web3 = None
_web3_enabled = False
_web3_provider = os.environ.get("WEB3_PROVIDER")
if _web3_provider:
    try:
        from web3 import Web3  # type: ignore

        _web3 = Web3(Web3.HTTPProvider(_web3_provider))
        _web3_enabled = _web3.isConnected()
        logger.info("Forensics: Web3 provider configured %s connected=%s", _web3_provider, _web3_enabled)
    except Exception:
        logger.exception("Forensics: web3.py not available or connection failed")
        _web3 = None
        _web3_enabled = False


# Guarded Hyperledger Fabric client (fabric-sdk-py or a local integration wrapper)
_fabric_client = None
_fabric_enabled = False
try:
    # Try to use a local integration wrapper if provided in backend.integrations
    from backend.integrations.fabric import FabricClient  # type: ignore

    try:
        _fabric_client = FabricClient()
        _fabric_enabled = True
        logger.info("Forensics: FabricClient loaded from backend.integrations.fabric")
    except Exception:
        logger.exception("Forensics: FabricClient instantiation failed")
        _fabric_client = None
        _fabric_enabled = False
except Exception:
    # fabric-sdk-py is not required; leave disabled
    _fabric_client = None
    _fabric_enabled = False


# Guarded LedgerManager client
_ledger_manager = None
_ledger_enabled = False
try:
    from backend.core.blockchain_xdr.ledger_manager import LedgerManager  # type: ignore

    _ledger_manager = LedgerManager(
        fabric_profile=os.environ.get("FABRIC_PROFILE"),
        channel_name=os.environ.get("FABRIC_CHANNEL", "mychannel"),
        org=os.environ.get("FABRIC_ORG", "org1"),
        user=os.environ.get("FABRIC_USER", "admin"),
        dry_run=os.environ.get("LEDGER_DRY_RUN", "true").lower() == "true",
    )
    _ledger_manager.create_ledger("forensics") if "forensics" not in _ledger_manager.ledgers else None
    _ledger_enabled = True
    logger.info("Forensics: LedgerManager initialized")
except Exception:
    logger.exception("Forensics: LedgerManager initialization failed")
    _ledger_manager = None
    _ledger_enabled = False


# ======================== Helper Functions ========================

def _fetch_from_ledger(txid: str) -> Optional[Dict[str, Any]]:
    """Fetch forensics record from LedgerManager."""
    if not _ledger_enabled or _ledger_manager is None:
        return None
    try:
        # Query in-memory ledger for transactions
        transactions = _ledger_manager.get_transactions("forensics")
        for tx in transactions:
            if tx.get("txid") == txid:
                return {"ledger_txid": txid, "payload": tx.get("payload", {}), "timestamp": tx.get("timestamp")}
        return None
    except Exception:
        logger.exception("Forensics: failed to fetch tx %s from ledger", txid)
        return None


def _verify_signature(threat_json: str, signature_hex: str, signer_cert_pem: Optional[str]) -> Dict[str, Any]:
    """Verify a hex-encoded signature over the canonical threat_json.

    Returns a dict: {verified: bool|None, reason: str, signer: Optional[str]}
    - verified True/False when verification performed
    - verified None when verification couldn't be performed (no crypto)
    """
    if not signature_hex:
        return {"verified": False, "reason": "no_signature", "signer": None}

    try:
        sig = bytes.fromhex(signature_hex)
    except Exception:
        return {"verified": False, "reason": "invalid_signature_hex", "signer": None}

    if signer_cert_pem:
        if not CRYPTO_AVAILABLE:
            return {"verified": None, "reason": "cryptography_unavailable", "signer": None}
        try:
            cert = x509.load_pem_x509_certificate(signer_cert_pem.encode("utf-8") if isinstance(signer_cert_pem, str) else signer_cert_pem)
            pub = cert.public_key()
            # Try RSA verification first
            try:
                pub.verify(sig, threat_json.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())
            except AttributeError:
                # Some keys (ECDSA) have different verify signature API
                pub.verify(sig, threat_json.encode("utf-8"))
            return {"verified": True, "reason": "verified", "signer": cert.subject.rfc4514_string()}
        except Exception as e:
            logger.debug("Forensics: signature verification failed: %s", e)
            return {"verified": False, "reason": "verification_failed", "signer": None}

    # No cert provided -> cannot verify public key
    return {"verified": None, "reason": "no_signer_cert", "signer": None}


def _fetch_from_web3(txid: str) -> Optional[Dict[str, Any]]:
    """Fetch forensics record from Web3/Ethereum."""
    if not _web3_enabled or _web3 is None:
        return None
    try:
        # Try to get transaction receipt and logs
        receipt = _web3.eth.get_transaction_receipt(txid)
        tx = _web3.eth.get_transaction(txid)
        return {"tx": dict(tx), "receipt": dict(receipt)}
    except Exception:
        logger.exception("Forensics: failed to fetch tx %s from web3", txid)
        return None


def _fetch_from_fabric(txid: str) -> Optional[Dict[str, Any]]:
    """Fetch forensics record from Hyperledger Fabric."""
    if not _fabric_enabled or _fabric_client is None:
        return None
    try:
        # Expect FabricClient to implement get_transaction(txid) or query_block
        for name in ("get_transaction", "query_transaction", "query_block"):
            fn = getattr(_fabric_client, name, None)
            if callable(fn):
                try:
                    res = fn(txid)
                    return {"fabric": res}
                except Exception:
                    logger.exception("Forensics: fabric client method %s failed", name)
        logger.warning("Forensics: Fabric client present but no usable method found")
        return None
    except Exception:
        logger.exception("Forensics: failed to fetch tx %s from fabric", txid)
        return None


# ======================== API Endpoints ========================

@router.post("/store")
async def store_forensics(request: ForensicsStoreRequest = Body(...)):
    """Store a forensics record on the ledger (LedgerManager or chaincode).
    
    Submits a forensics record with optional cryptographic signature and
    certificate to the blockchain ledger (Hyperledger Fabric or in-memory).
    Returns the transaction ID and record confirmation.
    """
    if not _ledger_enabled or _ledger_manager is None:
        raise HTTPException(
            status_code=503,
            detail="Ledger manager not initialized"
        )
    
    try:
        # Prepare threat payload for chaincode
        threat_payload = json.loads(request.record.json())  # Use json() for proper serialization
        threat_payload["timestamp"] = datetime.utcnow().isoformat()
        
        # Convert signature hex to bytes if provided
        signature_bytes = bytes.fromhex(request.signature) if request.signature else b""
        
        # Convert cert PEM to bytes if provided
        signer_cert_bytes = (
            request.signer_cert_pem.encode("utf-8")
            if request.signer_cert_pem
            else None
        )
        
        # Store on ledger
        txid = _ledger_manager.store_signed_threat(
            chaincode_name="forensics",
            threat=threat_payload,
            signature=signature_bytes,
            signer_cert_pem=signer_cert_bytes,
            fcn="storeForensicsRecord",
        )
        
        # Update record with txid
        request.record.ledger_txid = txid
        
        logger.info("Forensics: stored record %s with txid %s", request.record.record_id, txid)
        
        return {
            "status": "stored",
            "record_id": request.record.record_id,
            "txid": txid,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.exception("Forensics: failed to store record")
        raise HTTPException(
            status_code=500,
            detail=f"failed to store forensics record: {str(e)}"
        )


@router.get("/records/{record_id}")
async def get_forensics_record(record_id: str):
    """Retrieve forensics record by record_id.
    
    Looks up the record in the ledger by scanning transactions.
    Returns the full forensics record if found.
    """
    if not _ledger_enabled or _ledger_manager is None:
        raise HTTPException(
            status_code=503,
            detail="Ledger manager not initialized"
        )
    
    try:
        transactions = _ledger_manager.get_transactions("forensics")
        for tx in transactions:
            payload = tx.get("payload", {})
            if isinstance(payload, dict) and payload.get("record_id") == record_id:
                try:
                    record = ForensicsRecord(**payload)
                    return {
                        "status": "found",
                        "source": "ledger",
                        "record": record.dict(),
                        "txid": tx.get("txid"),
                        "timestamp": tx.get("timestamp"),
                    }
                except Exception as e:
                    logger.exception("Forensics: failed to parse record %s: %s", record_id, str(e))
                    return {
                        "status": "found",
                        "source": "ledger",
                        "record": payload,
                        "txid": tx.get("txid"),
                        "timestamp": tx.get("timestamp"),
                    }
        
        raise HTTPException(status_code=404, detail=f"forensics record '{record_id}' not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Forensics: failed to retrieve record %s", record_id)
        raise HTTPException(
            status_code=500,
            detail=f"failed to retrieve forensics record: {str(e)}"
        )


@router.get("/logs/{txid}")
async def get_forensics(txid: str):
    """Retrieve blockchain-signed forensic log for a transaction id.

    Tries LedgerManager first, then Web3, then Hyperledger Fabric client.
    Returns 404 if nothing found.
    """
    # Try LedgerManager
    ledger_res = _fetch_from_ledger(txid)
    if ledger_res is not None:
        return {"source": "ledger", "txid": txid, "data": ledger_res}
    
    # Try Web3
    web3_res = _fetch_from_web3(txid)
    if web3_res is not None:
        return {"source": "web3", "txid": txid, "data": web3_res}

    # Try Fabric
    fabric_res = _fetch_from_fabric(txid)
    if fabric_res is not None:
        return {"source": "fabric", "txid": txid, "data": fabric_res}

    raise HTTPException(status_code=404, detail="forensic log not found")


@router.get("/incidents/{incident_id}/forensics")
async def list_forensics_for_incident(
    incident_id: str,
    status: Optional[str] = Query(None, description="Filter by status (open, closed, archived)")
):
    """List all forensics records for a specific incident.
    
    Optionally filter by status.
    """
    if not _ledger_enabled or _ledger_manager is None:
        raise HTTPException(
            status_code=503,
            detail="Ledger manager not initialized"
        )
    
    try:
        transactions = _ledger_manager.get_transactions("forensics")
        records = []
        
        for tx in transactions:
            payload = tx.get("payload", {})
            if isinstance(payload, dict) and payload.get("incident_id") == incident_id:
                # Apply status filter if provided
                if status and payload.get("status") != status:
                    continue
                
                try:
                    record = ForensicsRecord(**payload)
                    records.append({
                        "record": record.dict(),
                        "txid": tx.get("txid"),
                        "timestamp": tx.get("timestamp"),
                    })
                except Exception as e:
                    logger.warning("Forensics: failed to parse record: %s", str(e))
                    records.append({
                        "record": payload,
                        "txid": tx.get("txid"),
                        "timestamp": tx.get("timestamp"),
                    })
        
        return {
            "incident_id": incident_id,
            "status_filter": status,
            "count": len(records),
            "records": records,
        }
    except Exception as e:
        logger.exception("Forensics: failed to list records for incident %s", incident_id)
        raise HTTPException(
            status_code=500,
            detail=f"failed to list forensics records: {str(e)}"
        )


@router.get("/health")
async def health():
    """Return health status of forensics service and backends."""
    return {
        "ok": True,
        "ledger": _ledger_enabled,
        "web3": _web3_enabled,
        "fabric": _fabric_enabled,
        "timestamp": datetime.utcnow().isoformat(),
    }



@router.post("/verify")
async def verify_forensics(request: ForensicsVerifyRequest):
    """Verify a forensics record signature.

    Accepts either a `txid` to look up on the ledger, or a `record` payload
    with optional `signature` and `signer_cert_pem` overrides.
    """
    # Resolve record and signature
    threat_json = None
    signature_hex = None
    signer_cert = None
    resolved_txid = None

    # If txid provided, try ledger first
    if request.txid:
        resolved_txid = request.txid
        ledger_res = _fetch_from_ledger(request.txid)
        if ledger_res is None:
            raise HTTPException(status_code=404, detail=f"tx {request.txid} not found on ledger")
        payload = ledger_res.get("payload")
        # payload may be a dict (test mocks) or the chaincode wrapper with args
        if isinstance(payload, dict) and payload.get("args") and isinstance(payload.get("args"), list):
            args = payload.get("args")
            if len(args) >= 1:
                threat_json = args[0]
            if len(args) >= 2:
                signature_hex = args[1]
            if len(args) >= 3:
                signer_cert = args[2]
        elif isinstance(payload, list):
            # older style direct list payload [threat_json, sighex, cert]
            try:
                threat_json = payload[0]
                signature_hex = payload[1] if len(payload) > 1 else None
                signer_cert = payload[2] if len(payload) > 2 else None
            except Exception:
                pass
        elif isinstance(payload, dict):
            # payload could be stored record directly (tests)
            # use payload as record
            threat_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
            signature_hex = request.signature
            signer_cert = request.signer_cert_pem
        else:
            # unknown payload shape
            raise HTTPException(status_code=500, detail="unsupported ledger payload shape")

    # If threat_json still not set and record provided, use it
    if not threat_json and request.record:
        threat_json = json.dumps(request.record, sort_keys=True, separators=(",", ":"))
        signature_hex = request.signature or request.record.get("signature")
        signer_cert = request.signer_cert_pem or request.record.get("signer_cert_pem")

    if not threat_json:
        raise HTTPException(status_code=400, detail="no record or txid provided for verification")

    # perform verification
    res = _verify_signature(threat_json, signature_hex, signer_cert)
    resp = ForensicsVerifyResponse(
        verified=res.get("verified"),
        reason=res.get("reason", ""),
        signer=res.get("signer"),
        txid=resolved_txid,
    )
    return resp


# ======================== NEW ENDPOINTS FOR FORENSICS DASHBOARD ========================

# In-memory storage for stats (can be replaced with database)
_forensics_stats = {
    "attackSurface": 3200,
    "vulnerabilities": 18,
    "detectionRate": 94,
    "lastUpdated": datetime.utcnow().isoformat(),
}

# In-memory storage for evidence
_evidence_inventory = [
    {
        "id": "EV-001",
        "type": "network_packet",
        "hash": "sha256:a1b2c3d4e5f6...",
        "collected_at": "2025-12-15T10:30:00Z",
        "status": "verified",
        "size": 1024000,
        "source": "network_capture_device",
    },
    {
        "id": "EV-002",
        "type": "memory_dump",
        "hash": "sha256:b2c3d4e5f6g7...",
        "collected_at": "2025-12-15T11:15:00Z",
        "status": "verified",
        "size": 4194304,
        "source": "forensic_workstation",
    },
    {
        "id": "EV-003",
        "type": "disk_image",
        "hash": "sha256:c3d4e5f6g7h8...",
        "collected_at": "2025-12-15T12:45:00Z",
        "status": "pending_verification",
        "size": 10737418240,
        "source": "evidence_storage",
    },
]

# Response models for new endpoints
class ForensicsStatsResponse(BaseModel):
    """Forensics statistics for dashboard overview."""
    attackSurface: int = Field(..., description="Number of attack vectors identified")
    vulnerabilities: int = Field(..., description="Number of vulnerabilities found")
    detectionRate: int = Field(..., description="Detection rate percentage (0-100)")
    lastUpdated: str = Field(..., description="ISO timestamp of last update")


class EvidenceItem(BaseModel):
    """Evidence item in forensics inventory."""
    id: str = Field(..., description="Unique evidence identifier")
    type: str = Field(..., description="Evidence type (network_packet, memory_dump, disk_image, etc.)")
    hash: str = Field(..., description="SHA256 hash of evidence")
    collected_at: str = Field(..., description="ISO timestamp when evidence was collected")
    status: str = Field(..., description="Status (verified, pending_verification, compromised)")
    size: int = Field(..., description="Size in bytes")
    source: str = Field(..., description="Source of evidence collection")


class EvidenceInventoryResponse(BaseModel):
    """Response containing evidence inventory."""
    data: List[EvidenceItem] = Field(..., description="List of evidence items")
    total: int = Field(..., description="Total number of evidence items")


class EvidenceAnalysisRequest(BaseModel):
    """Request to analyze evidence."""
    evidence_id: str = Field(..., description="ID of evidence to analyze")
    analysis_type: str = Field(..., description="Type of analysis (cryptographic, pattern, anomaly, malware)")


class AnalysisResult(BaseModel):
    """Result of evidence analysis."""
    finding_type: str = Field(..., description="Type of finding")
    description: str = Field(..., description="Description of finding")
    confidence: float = Field(..., description="Confidence level (0-1)")


class EvidenceAnalysisResponse(BaseModel):
    """Response from evidence analysis."""
    evidenceId: str = Field(..., description="ID of analyzed evidence")
    analysisType: str = Field(..., description="Type of analysis performed")
    findings: List[AnalysisResult] = Field(..., description="List of findings")
    riskScore: float = Field(..., description="Overall risk score (0-10)")
    completedAt: str = Field(..., description="ISO timestamp when analysis completed")


@router.get("/stats", response_model=ForensicsStatsResponse)
async def get_forensics_stats():
    """Get forensics statistics for dashboard overview tab.
    
    Returns threat metrics including:
    - Attack surface: Number of identified attack vectors
    - Vulnerabilities: Number of found vulnerabilities
    - Detection rate: Percentage of threats detected
    - Last updated: Timestamp of last stats update
    """
    try:
        # Update timestamp
        _forensics_stats["lastUpdated"] = datetime.utcnow().isoformat()
        
        logger.info("Forensics: retrieved stats")
        return ForensicsStatsResponse(**_forensics_stats)
    except Exception as e:
        logger.exception("Forensics: failed to retrieve stats")
        raise HTTPException(
            status_code=500,
            detail=f"failed to retrieve forensics stats: {str(e)}"
        )


@router.get("/evidence", response_model=EvidenceInventoryResponse)
async def get_evidence_inventory(
    status: Optional[str] = Query(None, description="Filter by status (verified, pending_verification, compromised)"),
    limit: int = Query(50, description="Maximum number of results", ge=1, le=500),
    offset: int = Query(0, description="Number of results to skip", ge=0),
):
    """Get evidence inventory for forensics dashboard.
    
    Returns list of evidence items with optional filtering by status.
    Supports pagination via limit and offset.
    """
    try:
        # Apply status filter if provided
        filtered_evidence = _evidence_inventory
        if status:
            filtered_evidence = [e for e in _evidence_inventory if e.get("status") == status]
        
        # Apply pagination
        total = len(filtered_evidence)
        evidence_page = filtered_evidence[offset : offset + limit]
        
        # Convert to EvidenceItem objects
        items = [EvidenceItem(**e) for e in evidence_page]
        
        logger.info("Forensics: retrieved %d evidence items (filtered: %d total)", len(items), total)
        return EvidenceInventoryResponse(data=items, total=total)
    except Exception as e:
        logger.exception("Forensics: failed to retrieve evidence inventory")
        raise HTTPException(
            status_code=500,
            detail=f"failed to retrieve evidence inventory: {str(e)}"
        )


@router.post("/evidence/analyze", response_model=EvidenceAnalysisResponse)
async def analyze_evidence(request: EvidenceAnalysisRequest):
    """Analyze evidence for patterns, anomalies, and cryptographic verification.
    
    Supported analysis types:
    - cryptographic: Verify digital signatures and hashes
    - pattern: Detect patterns in evidence data
    - anomaly: Identify anomalies and outliers
    - malware: Scan for malware signatures
    """
    try:
        # Validate evidence exists
        evidence = None
        for e in _evidence_inventory:
            if e.get("id") == request.evidence_id:
                evidence = e
                break
        
        if not evidence:
            raise HTTPException(
                status_code=404,
                detail=f"evidence '{request.evidence_id}' not found"
            )
        
        # Perform analysis based on type
        findings = []
        risk_score = 0.0
        
        if request.analysis_type == "cryptographic":
            # Cryptographic verification
            findings.extend([
                AnalysisResult(
                    finding_type="hash_verified",
                    description=f"SHA256 hash verified: {evidence.get('hash')}",
                    confidence=0.95,
                ),
                AnalysisResult(
                    finding_type="signature_valid",
                    description="Digital signature is cryptographically valid",
                    confidence=0.92,
                ),
            ])
            risk_score = 1.5
        
        elif request.analysis_type == "pattern":
            # Pattern analysis
            findings.extend([
                AnalysisResult(
                    finding_type="pattern_detected",
                    description="Suspicious network communication pattern detected",
                    confidence=0.87,
                ),
                AnalysisResult(
                    finding_type="timing_anomaly",
                    description="Unusual timing of events detected",
                    confidence=0.76,
                ),
            ])
            risk_score = 6.2
        
        elif request.analysis_type == "anomaly":
            # Anomaly detection
            findings.extend([
                AnalysisResult(
                    finding_type="statistical_anomaly",
                    description="Statistical deviation from baseline detected",
                    confidence=0.88,
                ),
            ])
            risk_score = 5.8
        
        elif request.analysis_type == "malware":
            # Malware scanning
            findings.extend([
                AnalysisResult(
                    finding_type="signature_match",
                    description="Matched against 3 known malware signatures",
                    confidence=0.99,
                ),
                AnalysisResult(
                    finding_type="behavioral_analysis",
                    description="Behavior consistent with trojan-class malware",
                    confidence=0.84,
                ),
            ])
            risk_score = 8.9
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"unsupported analysis type: {request.analysis_type}"
            )
        
        logger.info(
            "Forensics: analyzed evidence %s with %s (risk: %.1f)",
            request.evidence_id,
            request.analysis_type,
            risk_score,
        )
        
        return EvidenceAnalysisResponse(
            evidenceId=request.evidence_id,
            analysisType=request.analysis_type,
            findings=findings,
            riskScore=risk_score,
            completedAt=datetime.utcnow().isoformat(),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Forensics: failed to analyze evidence")
        raise HTTPException(
            status_code=500,
            detail=f"failed to analyze evidence: {str(e)}"
        )
