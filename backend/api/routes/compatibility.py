from fastapi import APIRouter, HTTPException, Body
from typing import Any, Dict, List
from pydantic import BaseModel
import logging

from backend.api.routes import forensics as forensics_module
from backend.api.routes import dpi_routes

logger = logging.getLogger(__name__)
router = APIRouter()


class BulkDevicesRequest(BaseModel):
    device_ids: List[str]
    operation: str
    parameters: Dict[str, Any] = {}


@router.post("/devices/bulk")
async def devices_bulk(req: BulkDevicesRequest):
    """Compatibility endpoint: perform bulk operations on devices.

    This is a lightweight compatibility shim to satisfy frontend calls.
    It performs no real device operations in this environment and returns
    a stubbed success per device.
    """
    results = []
    for d in req.device_ids:
        results.append({"device_id": d, "success": True, "result": "shimbed"})
    return {"results": results}


@router.get("/security/compliance")
async def security_compliance(device_id: str = None):
    """Return a mocked compliance status for a device or global summary."""
    if device_id:
        return {
            "device_id": device_id,
            "tee_status": "enabled",
            "tpm_status": "attested",
            "encryption_status": "on",
            "compliance_score": 98,
            "last_check": "2025-01-01T00:00:00Z",
        }
    return {
        "total_devices": 120,
        "secure_devices": 118,
        "attestation_success": 115,
        "encryption_enabled": 120,
        "seal_status": "ok",
        "device_binding": 120,
    }


@router.get("/alerts")
async def alerts_proxy(max_alerts: int = 100, clear: bool = False):
    """Proxy /alerts to the DPI alerts endpoint implementation."""
    try:
        # Call the dpi_routes get_alerts function directly
        res = await dpi_routes.get_alerts(max_alerts=max_alerts, clear=clear)
        return res
    except Exception:
        logger.exception("Compatibility: failed to fetch DPI alerts")
        raise HTTPException(status_code=500, detail="failed to fetch alerts")


class ForensicsExportRequest(BaseModel):
    record: Dict[str, Any]
    signature: str = None
    signer_cert_pem: str = None


@router.post("/forensics/export/audit-trail")
async def forensics_export(req: ForensicsExportRequest = Body(...)):
    """Compatibility endpoint that forwards to forensics.store when possible."""
    try:
        body = forensics_module.ForensicsStoreRequest(record=req.record, signature=req.signature, signer_cert_pem=req.signer_cert_pem)
        return await forensics_module.store_forensics(body)
    except Exception:
        logger.exception("Compatibility: failed to forward forensics export to store")
        raise HTTPException(status_code=500, detail="forensics export failed")


@router.post("/metrics/export/csv")
async def metrics_export_csv(payload: Dict[str, Any] = Body(...)):
    """Compatibility endpoint: produce a small CSV stub or return not implemented.

    For now, return a JSON placeholder indicating the export was accepted.
    """
    return {"status": "accepted", "rows": 0, "note": "export stub"}
