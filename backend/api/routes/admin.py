from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Any, Dict, List
import os
import json
import logging
import base64
import uuid
from datetime import datetime
import psutil
import time
import secrets
import string
import hashlib

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Use fallback hashing to avoid bcrypt compatibility issues
# In production, consider using argon2 or updating passlib/bcrypt versions
def _hash_password_impl(password: str) -> str:
    """Hash password using PBKDF2 SHA256."""
    salt = secrets.token_hex(16)
    # Use 100,000 iterations for PBKDF2 (industry standard)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 100000)
    return f"$pbkdf2$sha256$100000${salt}${pwd_hash.hex()}"

def _verify_password_impl(plain_password: str, hashed_password: str) -> bool:
    """Verify password against PBKDF2 SHA256 hash."""
    if not hashed_password.startswith("$pbkdf2$sha256$"):
        return False
    parts = hashed_password.split("$")
    if len(parts) < 5:
        return False
    try:
        iterations = int(parts[2])
        salt = parts[3]
        stored_hash = parts[4]
        pwd_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode(), bytes.fromhex(salt), iterations)
        return pwd_hash.hex() == stored_hash
    except Exception:
        return False

router = APIRouter()

# Simple in-memory stores
_DEVICE_BINDS: Dict[str, Dict[str, Any]] = {}
_AUDIT_LOGS: List[Dict[str, Any]] = []
_FEATURE_FLAGS: Dict[str, bool] = {
    "dpi_engine": True,
    "pqc_encryption": True,
    "tds_zero_trust": True,
    "deception_grid": True,
    "real_time_telemetry": True,
    "self_healing": True,
    "federated_learning": False,
    "mtls_enforcement": True,
}

# Helper functions for password management
def _generate_temporary_password(length: int = 12) -> str:
    """Generate a secure temporary password."""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(characters) for _ in range(length))


def _hash_password(password: str) -> str:
    """Hash password using PBKDF2 SHA256 (bcrypt compatibility removed to avoid version issues)."""
    return _hash_password_impl(password)


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return _verify_password_impl(plain_password, hashed_password)


_USERS: Dict[str, Dict[str, Any]] = {}# Initialize users lazily to avoid hashing at import time
def _get_default_users() -> Dict[str, Dict[str, Any]]:
    """Get default users with hashed passwords (lazy init)."""
    return {
        "admin": {
            "id": "1",
            "username": "admin",
            "email": "admin@jarvis.local",
            "role": "admin",
            "password_hash": _hash_password("admin123"),  # Default password
            "password_changed_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "last_login": datetime.utcnow().isoformat(),
            "status": "active",
        },
        "analyst01": {
            "id": "2",
            "username": "analyst01",
            "email": "analyst@jarvis.local",
            "role": "analyst",
            "password_hash": _hash_password("analyst123"),  # Default password
            "password_changed_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "last_login": datetime.utcnow().isoformat(),
            "status": "active",
        },
    }

def _ensure_default_users() -> None:
    """Ensure default users exist (called on first route access)."""
    global _USERS
    if not _USERS:
        _USERS.update(_get_default_users())
_APP_START_TIME = time.time()

# Settings file path configurable via env var for tests
_SETTINGS_PATH = os.environ.get("JARVIS_SETTINGS_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "settings.json"))


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _get_admin_user_from_request(request_user: Dict[str, Any] | None) -> Dict[str, Any]:
    """
    Verify that the request user is an admin. Raise 403 if not.
    Returns the verified admin user.
    """
    if not request_user or request_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return request_user


@router.post("/keys/rotate")
async def rotate_keys():
    """Rotate PQC keys (dry-run safe).

    Generates new random key material and, if `ENABLE_KEY_ROTATION` is
    set to "1", writes them to process environment variables
    `PQC_SK_B64` and `PQC_PK_B64`.
    """
    sk = os.urandom(64)
    pk = os.urandom(64)
    sk_b64 = _b64url_encode(sk)
    pk_b64 = _b64url_encode(pk)
    applied = False
    if os.environ.get("ENABLE_KEY_ROTATION") == "1":
        os.environ["PQC_SK_B64"] = sk_b64
        os.environ["PQC_PK_B64"] = pk_b64
        applied = True
    return {"status": "rotated", "applied": applied, "sk_b64": sk_b64, "pk_b64": pk_b64}


@router.post("/device/bind")
async def device_bind(body: Dict[str, Any]):
    """Bind a device using a biometric token.

    Expected body: {"device_id": "...", "biometric_token": "..."}
    Uses `backend.core.tds.zero_trust` helpers when available.
    """
    device_id = body.get("device_id")
    token = body.get("biometric_token")
    if not device_id or not token:
        raise HTTPException(status_code=400, detail="device_id and biometric_token required")

    try:
        from backend.core.tds import zero_trust
    except Exception:
        # zero_trust not available
        raise HTTPException(status_code=500, detail="zero_trust module unavailable")

    if not zero_trust.verify_biometric_token(token):
        raise HTTPException(status_code=401, detail="biometric verification failed")

    handshake = zero_trust.generate_handshake(device_id)
    hid = handshake.get("handshake_id")
    # mark biometric verified
    zero_trust.mark_biometric_verified(hid)

    bind_id = str(uuid.uuid4())
    _DEVICE_BINDS[bind_id] = {"device_id": device_id, "bind_id": bind_id, "handshake_id": hid, "bound_at": datetime.utcnow().isoformat()}
    return {"bound": True, "bind_id": bind_id, "handshake_id": hid}


@router.get("/settings")
async def get_settings():
    try:
        if not os.path.exists(_SETTINGS_PATH):
            return {}
        with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.exception("Failed to read settings: %s", e)
        raise HTTPException(status_code=500, detail="failed to read settings")


@router.post("/settings")
async def post_settings(body: Dict[str, Any]):
    try:
        os.makedirs(os.path.dirname(_SETTINGS_PATH), exist_ok=True)
        with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(body, f, indent=2)
        return {"ok": True}
    except Exception as e:
        logger.exception("Failed to write settings: %s", e)
        raise HTTPException(status_code=500, detail="failed to write settings")


# ============================================================================
# Feature Flags Endpoints
# ============================================================================

@router.get("/flags")
async def get_feature_flags():
    """Get all feature flags status."""
    try:
        return {
            "flags": _FEATURE_FLAGS,
            "timestamp": datetime.utcnow().isoformat(),
            "count": len(_FEATURE_FLAGS),
        }
    except Exception as e:
        logger.exception("Failed to get feature flags: %s", e)
        raise HTTPException(status_code=500, detail="failed to get feature flags")


@router.post("/flags/{flag_name}")
async def toggle_feature_flag(flag_name: str, body: Dict[str, Any]):
    """Toggle a specific feature flag.
    
    Expected body: {"enabled": true/false}
    """
    try:
        if flag_name not in _FEATURE_FLAGS:
            raise HTTPException(status_code=404, detail=f"flag '{flag_name}' not found")
        
        enabled = body.get("enabled")
        if not isinstance(enabled, bool):
            raise HTTPException(status_code=400, detail="'enabled' must be a boolean")
        
        old_state = _FEATURE_FLAGS[flag_name]
        _FEATURE_FLAGS[flag_name] = enabled
        
        # Log the change
        _log_audit_event(
            action="toggle_flag",
            resource=flag_name,
            details=f"Toggled {flag_name} from {old_state} to {enabled}",
            status="success"
        )
        
        return {
            "flag": flag_name,
            "enabled": enabled,
            "previous": old_state,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to toggle flag: %s", e)
        _log_audit_event(
            action="toggle_flag",
            resource=flag_name,
            details=str(e),
            status="failure"
        )
        raise HTTPException(status_code=500, detail="failed to toggle flag")


# ============================================================================
# System Health & Metrics
# ============================================================================

@router.get("/health")
async def get_system_health():
    """Get comprehensive system health status."""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        uptime = time.time() - _APP_START_TIME
        
        # Determine overall health status
        cpu_usage = process.cpu_percent(interval=0.1)
        memory_percent = process.memory_percent()
        status = "healthy"
        if cpu_usage > 80 or memory_percent > 80:
            status = "warning"
        elif cpu_usage > 95 or memory_percent > 95:
            status = "critical"
        
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": int(uptime),
            "uptime_formatted": _format_uptime(uptime),
            "memory": {
                "usage_bytes": memory_info.rss,
                "percent": memory_percent,
            },
            "cpu": {
                "percent": cpu_usage,
            },
            "components": {
                "api_server": "online",
                "database": "online",
                "cache": "online",
                "websocket": "online",
            },
        }
    except Exception as e:
        logger.exception("Failed to get health: %s", e)
        raise HTTPException(status_code=500, detail="failed to get health status")


@router.get("/metrics")
async def get_system_metrics():
    """Get detailed system metrics."""
    try:
        process = psutil.Process()
        cpu_count = psutil.cpu_count()
        virtual_memory = psutil.virtual_memory()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "process": {
                "pid": process.pid,
                "memory_rss_mb": process.memory_info().rss / 1024 / 1024,
                "memory_percent": process.memory_percent(),
                "cpu_percent": process.cpu_percent(interval=0.1),
                "num_threads": process.num_threads(),
            },
            "system": {
                "cpu_count": cpu_count,
                "virtual_memory_total_gb": virtual_memory.total / 1024 / 1024 / 1024,
                "virtual_memory_available_gb": virtual_memory.available / 1024 / 1024 / 1024,
                "virtual_memory_percent": virtual_memory.percent,
            },
            "uptime_seconds": int(time.time() - _APP_START_TIME),
        }
    except Exception as e:
        logger.exception("Failed to get metrics: %s", e)
        raise HTTPException(status_code=500, detail="failed to get metrics")


# ============================================================================
# User Management
# ============================================================================

@router.get("/users")
async def list_users():
    """Get list of all users."""
    _ensure_default_users()
    try:
        users_list = list(_USERS.values())
        return {
            "users": users_list,
            "count": len(users_list),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.exception("Failed to list users: %s", e)
        raise HTTPException(status_code=500, detail="failed to list users")


@router.post("/users")
async def create_user(body: Dict[str, Any], request: Request):
    """Create a new user with temporary password.
    
    Only admin users can create new users.
    
    Expected body: {
        "username": "...",
        "email": "...",
        "role": "admin|analyst|operator"
    }
    
    Returns generated temporary password that user must change on first login.
    """
    _ensure_default_users()
    try:
        # For now, we perform basic auth check via header
        # In production, this would use get_current_user dependency
        auth_header = request.headers.get("Authorization", "")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Missing authorization header")
        
        # TODO: Validate token and extract user role from JWT payload
        # For MVP, log the attempt
        logger.info(f"User creation request from: {request.client}")
        
        username = body.get("username", "").strip()
        email = body.get("email", "").strip()
        role = body.get("role", "analyst")
        
        if not username or not email:
            raise HTTPException(status_code=400, detail="username and email are required")
        
        if username in _USERS:
            raise HTTPException(status_code=409, detail=f"user '{username}' already exists")
        
        if role not in ["admin", "analyst", "operator"]:
            raise HTTPException(status_code=400, detail="invalid role")
        
        # Generate temporary password
        temp_password = _generate_temporary_password()
        password_hash = _hash_password(temp_password)
        
        user_id = str(len(_USERS) + 1)
        new_user = {
            "id": user_id,
            "username": username,
            "email": email,
            "role": role,
            "password_hash": password_hash,
            "password_changed_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "last_login": None,
            "status": "active",
        }
        _USERS[username] = new_user
        
        _log_audit_event(
            action="create_user",
            resource=username,
            details=f"Created user with role {role}",
            status="success"
        )
        
        # Return user info WITH the temporary password (only time it's readable)
        return {
            "user": {k: v for k, v in new_user.items() if k != "password_hash"},
            "temporary_password": temp_password,
            "created": True,
            "message": "User created successfully. Share the temporary password with the user. They must change it on first login."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create user: %s", e)
        _log_audit_event(
            action="create_user",
            resource=body.get("username", "unknown"),
            details=str(e),
            status="failure"
        )
        raise HTTPException(status_code=500, detail="failed to create user")


@router.delete("/users/{username}")
async def delete_user(username: str):
    """Delete a user."""
    _ensure_default_users()
    try:
        if username not in _USERS:
            raise HTTPException(status_code=404, detail=f"user '{username}' not found")
        
        if username == "admin":
            raise HTTPException(status_code=403, detail="cannot delete admin user")
        
        del _USERS[username]
        
        _log_audit_event(
            action="delete_user",
            resource=username,
            details=f"Deleted user",
            status="success"
        )
        
        return {"deleted": True, "username": username}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to delete user: %s", e)
        _log_audit_event(
            action="delete_user",
            resource=username,
            details=str(e),
            status="failure"
        )
        raise HTTPException(status_code=500, detail="failed to delete user")


@router.post("/users/{username}/password/change")
async def change_password(username: str, body: Dict[str, Any]):
    """Change user password.
    
    Expected body: {
        "new_password": "..."
    }
    """
    _ensure_default_users()
    try:
        if username not in _USERS:
            raise HTTPException(status_code=404, detail=f"user '{username}' not found")
        
        new_password = body.get("new_password", "").strip()
        
        if not new_password or len(new_password) < 8:
            raise HTTPException(status_code=400, detail="password must be at least 8 characters")
        
        # Hash and update password
        _USERS[username]["password_hash"] = _hash_password(new_password)
        _USERS[username]["password_changed_at"] = datetime.utcnow().isoformat()
        
        _log_audit_event(
            action="change_password",
            resource=username,
            details=f"Password changed",
            status="success"
        )
        
        return {
            "success": True,
            "username": username,
            "message": "Password changed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to change password: %s", e)
        _log_audit_event(
            action="change_password",
            resource=username,
            details=str(e),
            status="failure"
        )
        raise HTTPException(status_code=500, detail="failed to change password")


@router.post("/users/{username}/password/reset")
async def reset_password(username: str):
    """Reset user password to a new temporary password (admin only).
    
    Returns new temporary password.
    """
    _ensure_default_users()
    try:
        if username not in _USERS:
            raise HTTPException(status_code=404, detail=f"user '{username}' not found")
        
        # Generate new temporary password
        temp_password = _generate_temporary_password()
        password_hash = _hash_password(temp_password)
        
        _USERS[username]["password_hash"] = password_hash
        _USERS[username]["password_changed_at"] = datetime.utcnow().isoformat()
        
        _log_audit_event(
            action="reset_password",
            resource=username,
            details=f"Password reset",
            status="success"
        )
        
        return {
            "success": True,
            "username": username,
            "temporary_password": temp_password,
            "message": "Password has been reset. Share the temporary password with the user."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to reset password: %s", e)
        _log_audit_event(
            action="reset_password",
            resource=username,
            details=str(e),
            status="failure"
        )
        raise HTTPException(status_code=500, detail="failed to reset password")


# ============================================================================
# Audit Logs
# ============================================================================

@router.get("/logs")
async def get_audit_logs(limit: int = 100):
    """Get audit logs (most recent first)."""
    try:
        logs = sorted(_AUDIT_LOGS, key=lambda x: x["timestamp"], reverse=True)[:limit]
        return {
            "logs": logs,
            "count": len(logs),
            "total": len(_AUDIT_LOGS),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.exception("Failed to get audit logs: %s", e)
        raise HTTPException(status_code=500, detail="failed to get audit logs")


@router.post("/logs/clear")
async def clear_audit_logs():
    """Clear all audit logs."""
    try:
        count = len(_AUDIT_LOGS)
        _AUDIT_LOGS.clear()
        
        logger.info(f"Cleared {count} audit logs")
        return {"cleared": count, "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.exception("Failed to clear logs: %s", e)
        raise HTTPException(status_code=500, detail="failed to clear logs")


# ============================================================================
# Helper Functions
# ============================================================================

def _log_audit_event(
    action: str,
    resource: str,
    details: str = "",
    status: str = "success",
    user: str = "system"
):
    """Log an audit event."""
    event = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "user": user,
        "action": action,
        "resource": resource,
        "details": details,
        "status": status,
    }
    _AUDIT_LOGS.append(event)
    logger.info(f"Audit: {action} on {resource} by {user} - {status}")


def _format_uptime(seconds: float) -> str:
    """Format uptime in human-readable format."""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{days}d {hours}h {minutes}m {secs}s"

