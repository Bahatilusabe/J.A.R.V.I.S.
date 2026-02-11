from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Optional
import os
import base64
import json
import time
import hmac
import hashlib

from backend.core.tds.vpn_gateway import VPNGateway
from backend.core.tds import zero_trust

router = APIRouter()

# Authentication/authorization adapter
# Two modes supported:
# - JWT mode: set JARVIS_JWT_SECRET and tokens with a `role` claim are accepted
# - API key mode (legacy): JARVIS_API_KEYS env var mapping token:role


def _load_api_keys() -> Dict[str, str]:
    raw = os.environ.get("JARVIS_API_KEYS", "")
    out = {}
    if not raw:
        return out
    for part in raw.split(","):
        if ":" in part:
            t, r = part.split(":", 1)
            out[t.strip()] = r.strip()
    return out


API_KEYS = _load_api_keys()


def _verify_jwt(token: str) -> Optional[dict]:
    """Verify JWT using PyJWT when available.

    Behavior:
    - If `JARVIS_JWT_PUBLIC_KEY` is set, attempt RS256 verification using the
      provided PEM public key.
    - Else if `JARVIS_JWT_SECRET` is set, verify HMAC-SHA256 (HS256).
    - Enforces `exp` (expiry) claim if present.
    - Falls back to the minimal builtin verifier if PyJWT is not installed.
    """
    pubkey = os.environ.get("JARVIS_JWT_PUBLIC_KEY")
    secret = os.environ.get("JARVIS_JWT_SECRET")

    # Prefer PyJWT if available
    try:
        import jwt as _pyjwt
        # If JWKS URL configured, use PyJWT's PyJWKClient to fetch the key
        jwks_url = os.environ.get("JARVIS_JWKS_URL")
        if jwks_url:
            try:
                from jwt import PyJWKClient

                jwk_client = PyJWKClient(jwks_url)
                signing_key = jwk_client.get_signing_key_from_jwt(token)
                payload = _pyjwt.decode(token, signing_key.key, algorithms=["RS256"], options={})
                return payload
            except Exception:
                # fall through to other methods
                pass

        options = {"require_exp": False}
        algorithms = []
        key = None
        if pubkey:
            algorithms = ["RS256"]
            key = pubkey
        elif secret:
            algorithms = ["HS256"]
            key = secret
        else:
            return None

        # perform decode with audience/issuer checks if configured
        audience = os.environ.get("JARVIS_JWT_AUDIENCE")
        issuer = os.environ.get("JARVIS_JWT_ISSUER")
        kwargs = {"options": options}
        if audience:
            kwargs["audience"] = audience
        if issuer:
            kwargs["issuer"] = issuer

        payload = _pyjwt.decode(token, key=key, algorithms=algorithms, **kwargs)
        return payload
    except Exception:
        # fallback to minimal verifier only for HS256
        try:
            if not secret:
                return None
            # minimal validation: use HMAC-SHA256 to verify signature and check exp
            parts = token.split(".")
            if len(parts) != 3:
                return None
            signing_input = (parts[0] + "." + parts[1]).encode("ascii")
            sig = base64.urlsafe_b64decode(parts[2] + "=")
            expected = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
            if not hmac.compare_digest(sig, expected):
                return None
            payload_json = base64.urlsafe_b64decode(parts[1] + "=").decode("utf-8")
            payload = json.loads(payload_json)
            # check exp
            exp = payload.get("exp")
            if exp and time.time() > float(exp):
                return None
            return payload
        except Exception:
            return None


def get_current_role(request: Request) -> Optional[str]:
    # Prefer JWT when configured
    jwt_secret = os.environ.get("JARVIS_JWT_SECRET")
    auth = request.headers.get("Authorization")
    if jwt_secret and auth and auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1].strip()
        payload = _verify_jwt(token)
        if payload and isinstance(payload, dict):
            role = payload.get("role")
            if role:
                return role

    # Fallback to API key header
    token = request.headers.get("X-API-Key")
    return API_KEYS.get(token)


gw = VPNGateway()


def _audit_event(action: str, request: Request, session_id: Optional[str] = None, extra: Optional[dict] = None) -> None:
    """Write a structured audit entry to logs and optionally to a local audit file.

    Use env var AUDIT_LOG_PATH to enable writing newline-delimited JSON audit
    events for external ingestion. This avoids external dependencies and is
    easy to forward to centralized logging in production.
    """
    actor = None
    try:
        actor = get_current_role(request)
    except Exception:
        actor = None
    entry = {
        "ts": time.time(),
        "action": action,
        "actor_role": actor,
        "session_id": session_id,
        "path": str(request.url.path) if request and hasattr(request, "url") else None,
    }
    if extra:
        entry["extra"] = extra
    logger = __import__("logging").getLogger("jarvis.audit")
    logger.info("AUDIT %s", json.dumps(entry))
    path = os.environ.get("AUDIT_LOG_PATH")
    if path:
        try:
            with open(path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            logger.exception("failed to write audit log")


def require_role(role: str):
    def _dep(request: Request):
        r = get_current_role(request)
        if r is None:
            raise HTTPException(status_code=401, detail="missing credentials")
        # admin > user
        if role == "admin" and r != "admin":
            raise HTTPException(status_code=403, detail="insufficient role")
        return r
    # Return the dependency callable; FastAPI will wrap it with Depends when
    # used in endpoint signatures (e.g., role=Depends(require_role("user"))).
    return _dep


@router.post("/session")
async def create_session(req: Request, session_id: Optional[str] = None, role=Depends(require_role("user"))):
    sid = session_id or f"s-{os.urandom(4).hex()}"
    # If attestation enforcement is enabled, expect optional device_info in
    # the request body and validate it. Backwards compatible: enforcement is
    # disabled by default and will not break existing clients.
    enforce = os.environ.get("JARVIS_ENFORCE_ATTESTATION", "0") in ("1", "true", "True")
    if enforce:
        try:
            body = await req.json()
        except Exception:
            body = {}
        device_info = body.get("device_info") or {}
        att = zero_trust.attest_device(device_info or {})
        if not att.get("attested"):
            # audit the failed attestation and reject creation
            try:
                _audit_event("create_session_attestation_failed", req, session_id=sid, extra={"attestation": att})
            except Exception:
                pass
            raise HTTPException(status_code=403, detail={"reason": "attestation_failed", "attestation": att})

    try:
        gw.create_session(sid)
    except ValueError:
        raise HTTPException(status_code=409, detail="session exists")
    # audit
    try:
        _audit_event("create_session", req, session_id=sid)
    except Exception:
        pass
    return JSONResponse({"session_id": sid})


@router.post("/session/{session_id}/rekey")
async def rekey_session(session_id: str, request: Request, role=Depends(require_role("admin"))):
    ok = gw.rekey_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="unknown session")
    try:
        _audit_event("rekey_session", request, session_id=session_id)
    except Exception:
        pass
    return JSONResponse({"status": "rekeyed", "session_id": session_id})


@router.delete("/session/{session_id}")
async def close_session(session_id: str, request: Request, role=Depends(require_role("admin"))):
    ok = gw.close_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="unknown session")
    try:
        _audit_event("close_session", request, session_id=session_id)
    except Exception:
        pass
    return JSONResponse({"status": "closed", "session_id": session_id})


@router.post("/session/{session_id}/process")
async def process(session_id: str, payload: Dict[str, str], request: Request, role=Depends(require_role("user"))):
    # payload expects {'blob': base64}
    b64 = payload.get("blob")
    if not b64:
        raise HTTPException(status_code=400, detail="missing blob")
    try:
        blob = base64.b64decode(b64)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid base64")
    try:
        res = gw.process_incoming(session_id, blob)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown session")
    except PermissionError:
        raise HTTPException(status_code=403, detail="session suspended")
    # convert plaintext to base64 for safe JSON transport
    pt = res.get("plaintext", b"")
    if isinstance(pt, bytes):
        res["plaintext_b64"] = base64.b64encode(pt).decode("ascii")
        del res["plaintext"]
    try:
        _audit_event("process_incoming", request, session_id=session_id, extra={"anomaly_score": res.get("anomaly_score")})
    except Exception:
        pass
    return JSONResponse(res)


@router.get("/policy")
async def get_policy():
    return JSONResponse(gw.policy)


@router.post("/policy")
async def set_policy(policy: Dict[str, float], request: Request, role=Depends(require_role("admin"))):
    # simple policy dict: {'anomaly_threshold': float, 'suspend_seconds': int}
    gw.policy.update(policy)
    try:
        _audit_event("set_policy", request, extra={"policy": gw.policy})
    except Exception:
        pass
    return JSONResponse({"status": "ok", "policy": gw.policy})
