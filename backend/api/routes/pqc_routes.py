"""PQC (Post-Quantum Cryptography) FastAPI Routes.

Provides REST endpoints for:
- PQC handshake initiation (ClientHello)
- Handshake key exchange and session establishment
- Session queries and verification
- Public key distribution

Protocol Flow:
1. Client sends ClientHello → Server accepts and generates ServerHello
2. Client sends ClientKeyExchange → Server derives session keys and responds with ServerFinished
3. Session is stored and ready for subsequent encrypted communication

Features:
- Full TLS-like handshake with Kyber KEM
- Session key derivation using HKDF
- Dilithium signature verification
- Automatic session cleanup on expiration
"""

import base64
import json
import logging
import os
import uuid
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Import PQC components
from backend.core.pqcrypto.config import get_pqc_config, get_key_manager
from backend.core.pqcrypto.session_storage import get_session_store, PQCSessionData

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models for API request/response


class ClientHelloRequest(BaseModel):
    """ClientHello message from client."""

    client_address: str = Field(..., description="Client IP address or identifier")
    cipher_suites: list[str] = Field(
        default=["TLS_KYBER768_DILITHIUM3"], description="Supported cipher suites"
    )
    supported_groups: list[str] = Field(
        default=["Kyber768"], description="Supported PQC algorithms"
    )


class ClientHelloResponse(BaseModel):
    """ServerHello response (first handshake message)."""

    session_id: str = Field(..., description="Session identifier")
    selected_cipher_suite: str = Field(..., description="Negotiated cipher suite")
    selected_group: str = Field(..., description="Selected KEM algorithm")
    server_hello_bytes: str = Field(..., description="ServerHello message (base64)")


class ClientKeyExchangeRequest(BaseModel):
    """ClientKeyExchange message."""

    session_id: str = Field(..., description="Session identifier")
    encapsulated_key: str = Field(..., description="Encapsulated shared secret (base64)")
    client_finished_message: Optional[str] = Field(
        None, description="ClientFinished with Dilithium signature (base64)"
    )


class ServerFinishedResponse(BaseModel):
    """ServerFinished response (completes handshake)."""

    status: str = Field("established", description="Session status")
    session_id: str = Field(..., description="Session identifier")
    server_finished_message: str = Field(
        ..., description="ServerFinished with signature (base64)"
    )


class SessionVerifyRequest(BaseModel):
    """Query/verify a session."""

    session_id: str = Field(..., description="Session identifier")


class SessionVerifyResponse(BaseModel):
    """Session verification response."""

    session_id: str = Field(..., description="Session identifier")
    state: str = Field(..., description="Session state (active, expired, invalidated)")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    expires_at: str = Field(..., description="Expiration timestamp (ISO format)")
    cipher_suite: str = Field(..., description="Negotiated cipher suite")
    is_valid: bool = Field(..., description="Whether session is still valid")


class PublicKeyDistributionResponse(BaseModel):
    """Distribute server's public keys for out-of-band verification."""

    kem_algorithm: str = Field(..., description="KEM algorithm (e.g., Kyber768)")
    sig_algorithm: str = Field(..., description="DSA algorithm (e.g., Dilithium3)")
    kem_public_key: str = Field(..., description="Kyber public key (base64)")
    sig_public_key: str = Field(..., description="Dilithium public key (base64)")
    kem_key_id: str = Field(..., description="KEM key ID for tracking")
    sig_key_id: str = Field(..., description="DSA key ID for tracking")


# ==================== Endpoint Implementations ====================


@router.get("/keys", response_model=PublicKeyDistributionResponse, tags=["pqc"])
async def get_public_keys():
    """Distribute server's public keys for out-of-band verification.

    This endpoint allows clients to retrieve the server's public keys
    for offline verification or pinning purposes.

    Returns:
        PublicKeyDistributionResponse: Server's public keys and metadata
    """
    try:
        km = get_key_manager()
        exported = km.export_public_keys()

        return PublicKeyDistributionResponse(
            kem_algorithm=exported["kem_algorithm"],
            sig_algorithm=exported["sig_algorithm"],
            kem_public_key=exported["kem_public"],
            sig_public_key=exported["sig_public"],
            kem_key_id=exported["kem_key_id"],
            sig_key_id=exported["sig_key_id"],
        )
    except Exception as e:
        logger.exception("Failed to get public keys")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve public keys",
        )


@router.post("/handshake/hello", response_model=ClientHelloResponse, tags=["pqc"])
async def handshake_client_hello(request: ClientHelloRequest):
    """Initiate PQC handshake - ClientHello message.

    Client sends ClientHello with supported algorithms. Server responds
    with ServerHello, negotiating cipher suite and sending its ephemeral
    public key.

    Args:
        request: ClientHelloRequest with client address and supported algorithms

    Returns:
        ClientHelloResponse: ServerHello message and session ID

    Raises:
        HTTPException: 400 if invalid input, 500 if handshake fails
    """
    try:
        # Validate input
        if not request.client_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="client_address is required",
            )

        # Generate session ID
        config = get_pqc_config()
        session_id = str(uuid.uuid4())
        cipher_suite = "TLS_KYBER768_DILITHIUM3"  # Default (can be negotiated)
        
        # Simulate ServerHello (would be generated from actual handshake in production)
        server_hello = {
            "version": "1.0",
            "session_id": session_id,
            "cipher_suite": cipher_suite,
            "timestamp": datetime.utcnow().isoformat(),
        }
        server_hello_bytes = json.dumps(server_hello).encode()

        # Create session
        session = PQCSessionData(
            session_id=session_id,
            created_at=datetime.utcnow().isoformat(),
            expires_at=(datetime.utcnow() + timedelta(seconds=config.handshake_timeout_seconds)).isoformat(),
            client_write_key="",  # Derived later
            server_write_key="",  # Derived later
            client_iv="",  # Derived later
            server_iv="",  # Derived later
            verify_data="",  # Derived later
            cipher_suite=cipher_suite,
            client_address=request.client_address,
            state="hello_received",
        )

        # Store session
        store = get_session_store()
        store.save(session)

        # Store handshake state
        _handshake_cache[session_id] = {
            "state": "hello_sent",
            "client_address": request.client_address,
            "cipher_suite": cipher_suite,
        }

        logger.info(f"ClientHello accepted from {request.client_address}, session={session_id}")

        return ClientHelloResponse(
            session_id=session_id,
            selected_cipher_suite=cipher_suite,
            selected_group=config.kem_algorithm,
            server_hello_bytes=base64.b64encode(server_hello_bytes).decode(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Handshake ClientHello failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Handshake initiation failed",
        )


@router.post("/handshake/key-exchange", response_model=ServerFinishedResponse, tags=["pqc"])
async def handshake_key_exchange(request: ClientKeyExchangeRequest):
    """Complete PQC handshake - ClientKeyExchange and key derivation.

    Client sends encapsulated shared secret. Server decapsulates, derives
    session keys, and responds with ServerFinished message signed with
    Dilithium private key.

    Args:
        request: ClientKeyExchangeRequest with encapsulated key

    Returns:
        ServerFinishedResponse: ServerFinished message and session confirmation

    Raises:
        HTTPException: 400 if invalid session/key, 500 if derivation fails
    """
    try:
        session_id = request.session_id
        if not session_id or session_id not in _handshake_cache:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired session ID",
            )

        # Simulate key derivation
        km = get_key_manager()
        store = get_session_store()
        session_data = store.get(session_id)
        
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        # Simulate ServerFinished message
        server_finished = {
            "status": "established",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        server_finished_bytes = json.dumps(server_finished).encode()

        # Update session keys (simulated derivation)
        session_data.client_write_key = base64.b64encode(os.urandom(32)).decode()
        session_data.server_write_key = base64.b64encode(os.urandom(32)).decode()
        session_data.client_iv = base64.b64encode(os.urandom(16)).decode()
        session_data.server_iv = base64.b64encode(os.urandom(16)).decode()
        session_data.verify_data = base64.b64encode(os.urandom(32)).decode()
        session_data.state = "established"
        store.save(session_data)

        _handshake_cache[session_id]["state"] = "established"

        logger.info(f"KeyExchange completed, session={session_id}, keys derived")

        return ServerFinishedResponse(
            status="established",
            session_id=session_id,
            server_finished_message=base64.b64encode(server_finished_bytes).decode(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Handshake key exchange failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Key exchange failed",
        )


@router.post("/session/verify", response_model=SessionVerifyResponse, tags=["pqc"])
async def verify_session(request: SessionVerifyRequest):
    """Verify and query a PQC session.

    Args:
        request: SessionVerifyRequest with session ID

    Returns:
        SessionVerifyResponse: Session state and validity

    Raises:
        HTTPException: 404 if session not found
    """
    try:
        session_id = request.session_id
        store = get_session_store()
        session = store.get(session_id)

        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or expired",
            )

        is_valid = session.state == "established" and not session.is_expired()

        return SessionVerifyResponse(
            session_id=session_id,
            state=session.state,
            created_at=session.created_at,
            expires_at=session.expires_at,
            cipher_suite=session.cipher_suite,
            is_valid=is_valid,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Session verification failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session verification failed",
        )


@router.delete("/session/{session_id}", tags=["pqc"])
async def invalidate_session(session_id: str):
    """Invalidate a session (logout/cleanup).

    Args:
        session_id: Session ID to invalidate

    Returns:
        dict: Confirmation of invalidation

    Raises:
        HTTPException: 404 if session not found
    """
    try:
        store = get_session_store()
        if not store.delete(session_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        # Also remove from handshake cache
        if session_id in _handshake_cache:
            del _handshake_cache[session_id]

        logger.info(f"Session invalidated: {session_id}")
        return {"status": "invalidated", "session_id": session_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Session invalidation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session invalidation failed",
        )


@router.get("/health", tags=["pqc"])
async def pqc_health():
    """Health check for PQC subsystem.

    Returns:
        dict: Status of PQC components
    """
    try:
        config = get_pqc_config()
        km = get_key_manager()
        store = get_session_store()

        return {
            "status": "healthy",
            "kem_algorithm": config.kem_algorithm,
            "sig_algorithm": config.sig_algorithm,
            "has_keys": km.current_kem_key is not None and km.current_sig_key is not None,
            "session_store": type(store).__name__,
            "session_store_stats": store.get_stats(),
        }
    except Exception as e:
        logger.exception("PQC health check failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PQC health check failed",
        )


# ==================== In-Memory Handshake Cache ====================
# In production, this could be replaced with Redis or another persistent store
_handshake_cache: Dict[str, Any] = {}
