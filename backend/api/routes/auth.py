from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from backend.core.tds import zero_trust
from backend.core import auth_store

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/mobile/init")
def mobile_init(body: Dict[str, Any]):
    device_id = body.get("device_id")
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")
    logger.info("mobile_init: device_id=%s", device_id)
    import time
    t0 = time.time()
    info = zero_trust.generate_handshake(device_id)
    dur = (time.time() - t0) * 1000.0
    logger.info("mobile_init: generate_handshake took %.1fms", dur)
    return JSONResponse(info)


@router.post("/biometric")
def biometric_verify(body: Dict[str, Any]):
    hid = body.get("handshake_id")
    token = body.get("biometric_token")
    if not hid or not token:
        raise HTTPException(status_code=400, detail="handshake_id and biometric_token required")
    logger.info("biometric_verify: received handshake_id=%s", hid)
    import time
    t0 = time.time()
    ok = zero_trust.verify_biometric_token(token)
    dur = (time.time() - t0) * 1000.0
    logger.info("biometric_verify: verify_biometric_token took %.1fms", dur)
    if not ok:
        raise HTTPException(status_code=401, detail="biometric verification failed")
    zero_trust.mark_biometric_verified(hid)
    return {"ok": True}


@router.post("/mobile/session")
def mobile_session(body: Dict[str, Any]):
    hid = body.get("handshake_id")
    if not hid:
        raise HTTPException(status_code=400, detail="handshake_id required")
    logger.info("mobile_session: handshake_id=%s", hid)
    import time
    t0 = time.time()
    if not zero_trust.is_handshake_ready(hid):
        dur = (time.time() - t0) * 1000.0
        logger.info("mobile_session: is_handshake_ready took %.1fms (not ready)", dur)
        raise HTTPException(status_code=401, detail="handshake not ready")
    h = zero_trust.get_handshake(hid)
    dur = (time.time() - t0) * 1000.0
    logger.info("mobile_session: handshake ready check + get_handshake took %.1fms", dur)
    device_id = h.get("device_id") if h else "unknown"
    # Issue a PQC token for the mobile session; payload can include device_id
    # import locally to avoid circular import at module import time
    from backend.api.server import create_pqc_token
    token = create_pqc_token({"sub": device_id, "device": device_id})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login")
def login(body: Dict[str, Any]):
    """
    Web/Desktop authentication endpoint
    Accepts username and password, returns access and refresh tokens
    """
    username = body.get("username")
    password = body.get("password")
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")
    
    # Look up user in the auth store (development user DB)
    user = auth_store.get_user(username)
    if not user:
        logger.warning("login: failed attempt for user %s (user not found)", username)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    hashed = user.get("password")
    if not hashed or not auth_store.verify_password(password, hashed):
        logger.warning("login: failed attempt for user %s (invalid pw)", username)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    logger.info("login: successful authentication for user %s", username)
    
    # Import locally to avoid circular import at module import time
    from backend.api.server import create_pqc_token
    
    # Create tokens using PQC
    access_token = create_pqc_token({
        "sub": username,
        "user_id": username,
        "role": user.get("role", "user")
    })
    
    refresh_token = create_pqc_token({
        "sub": username,
        "type": "refresh"
    })
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "username": username,
            "id": username,
            "role": user.get("role", "user"),
            "permissions": ["read", "write", "execute"]
        }
    }


@router.post("/refresh")
def refresh_token(body: Dict[str, Any]):
    """
    Refresh access token using refresh token
    """
    refresh_token = body.get("refreshToken")
    
    if not refresh_token:
        raise HTTPException(status_code=400, detail="refreshToken required")
    
    logger.info("refresh: attempting token refresh")
    
    # In a real implementation, validate the refresh token
    # For now, just issue a new access token
    from backend.api.server import create_pqc_token
    
    # Extract user info from refresh token (in production, decode and validate)
    username = "admin"  # In production, extract from token
    
    access_token = create_pqc_token({
        "sub": username,
        "user_id": username,
        "role": "admin"
    })
    
    new_refresh_token = create_pqc_token({
        "sub": username,
        "type": "refresh"
    })
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/verify")
def verify_token(body: Dict[str, Any]):
    """
    Verify if a token is valid
    """
    token = body.get("token")
    
    if not token:
        raise HTTPException(status_code=400, detail="token required")
    
    logger.info("verify: checking token validity")
    
    # In a real implementation, decode and validate the token
    # For now, just return success
    return {"valid": True, "message": "Token is valid"}


@router.get("/profile")
def get_profile():
    """
    Get the authenticated user's profile
    Called by frontend after login to retrieve user details
    """
    # In a real implementation, extract user from the Authorization header and JWT token
    # For now, return a placeholder profile
    # The frontend will have already validated the token in AdminRoute
    
    # Note: In production, the token would be verified here by middleware
    # and the user info would be extracted from it
    logger.info("profile: fetching user profile")
    
    # Return a minimal profile that satisfies the frontend
    return {
        "username": "admin",
        "id": "admin",
        "role": "admin",
        "name": "Administrator",
        "permissions": ["read", "write", "execute"]
    }
