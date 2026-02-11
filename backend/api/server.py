"""Main API server module.

This builds on the original JARVIS gateway routers and adds a PQC-backed
token issuance and verification layer using PyJWT for payload handling and
an optional PQC signature adapter. The file also exposes a small gRPC proxy
stub for forwarding REST calls to a gRPC backend when available.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

import jwt as pyjwt  # PyJWT

# Handle both module import and direct script execution
# Ensure the project root is in Python path so 'backend' module can be found
_project_root = Path(__file__).parent.parent.parent  # Go up from backend/api/server.py to project root
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

try:
    # Try relative import first (when called as module)
    from .routes import telemetry, pasm, policy, vocal, forensics, forensics_routes, vpn, auth, admin, self_healing, self_healing_endpoints, packet_capture_routes, dpi_routes, compatibility, ids, federation, federation_hub, deception, metrics, threat_intelligence, tds, ced, ced_dashboard, fl_blockchain, pqc_routes, models, edge_devices, settings_routes
except ImportError:
    # Fallback to absolute import (when called directly)
    try:
        from backend.api.routes import telemetry, pasm, policy, vocal, forensics, forensics_routes, vpn, auth, admin, self_healing, self_healing_endpoints, packet_capture_routes, dpi_routes, compatibility, ids, federation, federation_hub, deception, metrics, threat_intelligence, tds, ced, ced_dashboard, fl_blockchain, pqc_routes, models, edge_devices, settings_routes
    except ModuleNotFoundError:
        # Last resort: ensure parent dir is in path
        _backend_parent = Path(__file__).parent.parent.parent
        if str(_backend_parent) not in sys.path:
            sys.path.insert(0, str(_backend_parent))
        from backend.api.routes import telemetry, pasm, policy, vocal, forensics, forensics_routes, vpn, auth, admin, self_healing, self_healing_endpoints, packet_capture_routes, dpi_routes, compatibility, ids, federation, federation_hub, deception, metrics, threat_intelligence, tds, ced, ced_dashboard, fl_blockchain, pqc_routes, models, edge_devices, settings_routes

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# preserve existing router wiring
app = FastAPI(title="JARVIS Gateway")

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "ok"}

# System status endpoint
@app.get("/api/system/status")
async def system_status():
    return {"status": "ok", "system": "running"}

# Federation status endpoint
@app.get("/api/federation/status")
async def federation_status():
    return {"status": "ok", "federation": "synced"}

# Development: configure CORS. Browsers block wildcard origins when credentials
# are used (credentials='include'), so prefer an explicit dev origin list.
try:
    from starlette.middleware.cors import CORSMiddleware

    # Read allowed origins from env var (comma-separated) for dev convenience.
    # Example: DEV_ALLOWED_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
    raw_allowed = os.environ.get("DEV_ALLOWED_ORIGINS", "http://localhost:5173")
    allowed_origins = [o.strip() for o in raw_allowed.split(",") if o.strip()]

    # If credentials are enabled we must not use the wildcard origin.
    if "*" in allowed_origins:
        # Replace wildcard with a safe default dev origin when credentials are used.
        allowed_origins = ["http://localhost:5173"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS middleware configured for origins: %s", allowed_origins)
except Exception:
    logger.exception("Failed to add CORS middleware (dev)")


# Ensure initial dev users exist with safe hashed passwords (only when placeholders present)
try:
    from backend.core import auth_store

    users = auth_store.load_users()
    changed = False
    # If placeholders present, set dev passwords: acer -> 'acer', bahati -> 'bahati'
    if users.get("acer", {}).get("password") == "__placeholder__":
        auth_store.add_user("acer", "acer", role="admin")
        changed = True
    if users.get("bahati", {}).get("password") == "__placeholder__":
        auth_store.add_user("bahati", "bahati", role="user")
        changed = True
    if changed:
        logger.info("Dev users initialized: acer (admin), bahati (user)")
except Exception:
    logger.exception("Failed to initialize dev users")

# (Removed development-time middleware sanitization/debug instrumentation)

# Register all routers with /api prefix for consistent frontend-backend routing
# Frontend calls: GET /api/system/status maps to GET /api/system/status endpoint
# Backend routes registered as: /system/status in system_status.py
app.include_router(telemetry.router, prefix="/api/telemetry")
app.include_router(pasm.router, prefix="/api/pasm")
app.include_router(policy.router, prefix="/api/policy")
app.include_router(vocal.router, prefix="/api/vocal")
app.include_router(forensics.router, prefix="/api/forensics")
app.include_router(forensics_routes.router, prefix="/api/forensics", tags=["forensics"])
app.include_router(vpn.router, prefix="/api/vpn")
app.include_router(auth.router, prefix="/api/auth")
app.include_router(self_healing.router, prefix="/api/self_healing")
app.include_router(self_healing_endpoints.router, prefix="/api/self_healing")
app.include_router(packet_capture_routes.router, prefix="/api/packet_capture")
app.include_router(dpi_routes.router, prefix="/api/dpi", tags=["dpi"])
app.include_router(tds.router, prefix="/api/tds", tags=["tds"])
app.include_router(ced.router, prefix="/api/ced", tags=["ced"])
app.include_router(ced_dashboard.router, prefix="/api/ced", tags=["ced-dashboard"])
app.include_router(ids.router, prefix="/api", tags=["ids"])
app.include_router(federation_hub.router, prefix="/api", tags=["federation-hub"])
app.include_router(federation.router, prefix="/api/federation", tags=["federation"])
app.include_router(deception.router, prefix="/api/deception", tags=["deception"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
app.include_router(models.router, prefix="/api/metrics", tags=["models"])
app.include_router(edge_devices.router, prefix="/api", tags=["edge-devices"])
app.include_router(threat_intelligence.router, prefix="", tags=["threat-intelligence"])
app.include_router(fl_blockchain.router, tags=["federated-learning"])
app.include_router(pqc_routes.router, prefix="/api/pqc", tags=["pqc"])
app.include_router(settings_routes.router, prefix="/api/settings", tags=["settings"])
app.include_router(admin.router, prefix="/api")
app.include_router(compatibility.router, prefix="/api")


@app.middleware("http")
async def mtls_middleware(request, call_next):
    import os

    if os.environ.get("JARVIS_MTLS_REQUIRED") in ("1", "true", "True"):
        allowed = os.environ.get("JARVIS_MTLS_ALLOWED_FINGERPRINTS", "")
        allowed_set = {x.strip().lower() for x in allowed.split(",") if x.strip()}
        fp = request.headers.get("X-Client-Fingerprint")
        if not fp:
            return JSONResponse({"detail": "client certificate required"}, status_code=401)
        if fp.strip().lower() not in allowed_set:
            return JSONResponse({"detail": "client certificate not authorized"}, status_code=403)

    return await call_next(request)


# --- PQC adapter and JWT helpers (same approach as the dedicated server module) ---
class PQCAdapter:
    def __init__(self):
        self._impl = None
        try:
            import pyspx.sign as pyspx_sign  # type: ignore

            self._impl = ("pyspx", pyspx_sign)
            logger.info("Using pyspx for PQC token signing")
        except Exception:
            try:
                import pqcrypto.sign  # type: ignore

                self._impl = ("pqcrypto", pqcrypto.sign)
                logger.info("Using pqcrypto for PQC token signing")
            except Exception:
                logger.debug("No PQC signing library available; falling back to HMAC")
                self._impl = None

        self.hmac_key = os.environ.get("API_HMAC_KEY", "dev-secret-key")

    def sign(self, data: bytes) -> bytes:
        if self._impl is None:
            import hmac
            import hashlib

            return hmac.new(self.hmac_key.encode("utf-8"), data, hashlib.sha256).digest()
        name, impl = self._impl
        if name == "pyspx":
            sk_b64 = os.environ.get("PQC_SK_B64")
            if not sk_b64:
                raise RuntimeError("PQC private key not configured (PQC_SK_B64)")
            sk = base64.urlsafe_b64decode(sk_b64.encode())
            return impl.sign(data, sk)
        if name == "pqcrypto":
            sk_b64 = os.environ.get("PQC_SK_B64")
            if not sk_b64:
                raise RuntimeError("PQC private key not configured (PQC_SK_B64)")
            sk = base64.urlsafe_b64decode(sk_b64.encode())
            return impl.sign(data, sk)
        raise RuntimeError("Unsupported PQC impl")

    def verify(self, data: bytes, signature: bytes) -> bool:
        if self._impl is None:
            import hmac
            import hashlib

            expected = hmac.new(self.hmac_key.encode("utf-8"), data, hashlib.sha256).digest()
            return hmac.compare_digest(expected, signature)
        name, impl = self._impl
        if name == "pyspx":
            pk_b64 = os.environ.get("PQC_PK_B64")
            if not pk_b64:
                raise RuntimeError("PQC public key not configured (PQC_PK_B64)")
            pk = base64.urlsafe_b64decode(pk_b64.encode())
            return impl.verify(data, signature, pk)
        if name == "pqcrypto":
            pk_b64 = os.environ.get("PQC_PK_B64")
            if not pk_b64:
                raise RuntimeError("PQC public key not configured (PQC_PK_B64)")
            pk = base64.urlsafe_b64decode(pk_b64.encode())
            return impl.verify(data, signature, pk)
        return False


pqc = PQCAdapter()


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    rem = len(s) % 4
    if rem:
        s = s + ("=" * (4 - rem))
    return base64.urlsafe_b64decode(s.encode())


def create_pqc_token(payload: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    data = payload.copy()
    now = datetime.utcnow()
    data["iat"] = int(now.timestamp())
    if expires_delta is None:
        expires_delta = timedelta(minutes=60)
    data["exp"] = int((now + expires_delta).timestamp())

    header = {"alg": "none", "typ": "JWT"}
    header_b = json.dumps(header, separators=(",", ":")).encode()
    payload_b = json.dumps(data, separators=(",", ":")).encode()
    signing_input = _b64url_encode(header_b).encode() + b"." + _b64url_encode(payload_b).encode()
    sig = pqc.sign(signing_input)
    token = signing_input.decode() + "." + _b64url_encode(sig)
    return token


def verify_pqc_token(token: str) -> Dict[str, Any]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="Invalid token format")
        signing_input = (parts[0] + "." + parts[1]).encode()
        sig = _b64url_decode(parts[2])
        if not pqc.verify(signing_input, sig):
            raise HTTPException(status_code=401, detail="Invalid token signature")
        payload_b = _b64url_decode(parts[1])
        payload = json.loads(payload_b.decode())
        if "exp" in payload and int(payload["exp"]) < int(datetime.utcnow().timestamp()):
            raise HTTPException(status_code=401, detail="Token expired")
        return payload
    except HTTPException:
        raise
    except Exception:
        logger.exception("Token verification failed")
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(request: Request) -> Dict[str, Any]:
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing auth token")
    token = auth.split(" ", 1)[1]
    return verify_pqc_token(token)


@app.on_event("startup")
async def _startup():
    try:
        # initialize PQC session store
        try:
            from backend.core.pqcrypto.session_storage import get_session_store
            store = get_session_store()
            logger.info(f"PQC session store initialized: {type(store).__name__}")
        except Exception:
            logger.exception("PQC session store initialization failed")
        
        # initialize telemetry optional backends (Kafka, ROMA)
        try:
            telemetry.init_backends()
        except Exception:
            # init_backends is synchronous by design; log and continue
            logger.exception("Telemetry: init_backends failed during startup")
        # (Startup diagnostic code removed for production-like runs.)
    except Exception:
        logger.exception("Startup hook error")


@app.on_event("shutdown")
async def _shutdown():
    try:
        # close PQC session store
        try:
            from backend.core.pqcrypto.session_storage import close_session_store
            close_session_store()
            logger.info("PQC session store closed")
        except Exception:
            logger.exception("PQC session store shutdown failed")
        
        # gracefully close telemetry backends
        try:
            await telemetry.close_backends()
        except Exception:
            logger.exception("Telemetry: close_backends failed during shutdown")
    except Exception:
        logger.exception("Shutdown hook error")


@app.post("/token")
def issue_token(form: Dict[str, Any]):
    username = form.get("username")
    password = form.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")
    payload = {"sub": username}
    token = create_pqc_token(payload)
    return JSONResponse({"access_token": token, "token_type": "bearer"})


@app.get("/protected")
def protected_route(user: Dict[str, Any] = Depends(get_current_user)):
    return {"ok": True, "user": user}


@app.post("/grpc-proxy")
def grpc_proxy(body: Dict[str, Any]):
    try:
        import grpc  # type: ignore
    except Exception:
        raise HTTPException(status_code=501, detail="gRPC backend not available in this environment")
    raise HTTPException(status_code=501, detail="gRPC proxying not implemented")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
