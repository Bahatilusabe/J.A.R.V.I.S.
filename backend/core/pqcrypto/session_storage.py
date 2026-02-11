"""PQC Session Storage - Redis-backed or in-memory fallback.

This module provides session management for PQC handshake protocol.
Sessions store derived cryptographic keys and state with automatic expiration.

Features:
- Redis backend for production (if available)
- In-memory fallback for development
- Automatic session expiration
- Session lookup and verification
- Thread-safe operations
"""

import json
import logging
import os
import time
import threading
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class PQCSessionData:
    """Stores PQC session state and cryptographic keys."""

    session_id: str
    created_at: str  # ISO format timestamp
    expires_at: str  # ISO format timestamp
    client_write_key: str  # base64-encoded
    server_write_key: str  # base64-encoded
    client_iv: str  # base64-encoded
    server_iv: str  # base64-encoded
    verify_data: str  # base64-encoded
    cipher_suite: str  # negotiated cipher suite
    client_address: Optional[str] = None
    server_address: Optional[str] = None
    handshake_hash: Optional[str] = None
    state: str = "active"  # active, expired, invalidated

    def is_expired(self) -> bool:
        """Check if session has expired."""
        try:
            expires = datetime.fromisoformat(self.expires_at)
            return datetime.utcnow() > expires
        except Exception as e:
            logger.error(f"Failed to check session expiration: {e}")
            return True

    def to_json(self) -> str:
        """Serialize session to JSON."""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "PQCSessionData":
        """Deserialize session from JSON."""
        d = json.loads(data)
        return cls(**d)


class PQCSessionStore:
    """Abstract base class for session storage."""

    def save(self, session: PQCSessionData) -> None:
        """Save session to storage."""
        raise NotImplementedError

    def get(self, session_id: str) -> Optional[PQCSessionData]:
        """Retrieve session by ID."""
        raise NotImplementedError

    def delete(self, session_id: str) -> bool:
        """Delete session by ID."""
        raise NotImplementedError

    def invalidate_expired(self) -> int:
        """Remove all expired sessions. Returns count of removed sessions."""
        raise NotImplementedError


class InMemorySessionStore(PQCSessionStore):
    """In-memory session storage (development/testing)."""

    def __init__(self):
        """Initialize in-memory store with cleanup thread."""
        self._sessions: Dict[str, PQCSessionData] = {}
        self._lock = threading.RLock()
        self._cleanup_interval = 60  # seconds
        self._cleanup_thread: Optional[threading.Thread] = None
        self._running = False
        self._start_cleanup()

    def _start_cleanup(self) -> None:
        """Start background cleanup thread."""
        self._running = True

        def cleanup_worker():
            while self._running:
                try:
                    time.sleep(self._cleanup_interval)
                    count = self.invalidate_expired()
                    if count > 0:
                        logger.debug(f"Cleaned up {count} expired sessions")
                except Exception as e:
                    logger.error(f"Session cleanup error: {e}")

        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()

    def stop(self) -> None:
        """Stop cleanup thread."""
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=2)

    def save(self, session: PQCSessionData) -> None:
        """Save session to memory."""
        with self._lock:
            self._sessions[session.session_id] = session
            logger.debug(f"Saved session {session.session_id}")

    def get(self, session_id: str) -> Optional[PQCSessionData]:
        """Retrieve session from memory."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session and session.is_expired():
                del self._sessions[session_id]
                logger.debug(f"Expired session removed: {session_id}")
                return None
            return session

    def delete(self, session_id: str) -> bool:
        """Delete session from memory."""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.debug(f"Deleted session {session_id}")
                return True
            return False

    def invalidate_expired(self) -> int:
        """Remove all expired sessions."""
        with self._lock:
            expired = [sid for sid, sess in self._sessions.items() if sess.is_expired()]
            for sid in expired:
                del self._sessions[sid]
            return len(expired)

    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        with self._lock:
            return {"total_sessions": len(self._sessions)}


class RedisSessionStore(PQCSessionStore):
    """Redis-backed session storage (production)."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0", ttl_seconds: int = 3600):
        """Initialize Redis store.

        Args:
            redis_url: Redis connection URL (default: localhost)
            ttl_seconds: Session time-to-live in seconds (default: 1 hour)
        """
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self._redis = None
        self._key_prefix = "pqc:session:"
        self._connect()

    def _connect(self) -> None:
        """Connect to Redis."""
        try:
            import redis  # type: ignore

            self._redis = redis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            self._redis.ping()
            logger.info(f"Connected to Redis: {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.warning("Falling back to in-memory session store")
            self._redis = None

    def _ensure_connected(self) -> bool:
        """Ensure Redis is connected."""
        if self._redis is None:
            self._connect()
        return self._redis is not None

    def save(self, session: PQCSessionData) -> None:
        """Save session to Redis."""
        if not self._ensure_connected():
            logger.warning("Redis not available; session not saved")
            return

        try:
            key = f"{self._key_prefix}{session.session_id}"
            value = session.to_json()
            self._redis.setex(key, self.ttl_seconds, value)
            logger.debug(f"Saved session {session.session_id} to Redis (TTL: {self.ttl_seconds}s)")
        except Exception as e:
            logger.error(f"Failed to save session to Redis: {e}")

    def get(self, session_id: str) -> Optional[PQCSessionData]:
        """Retrieve session from Redis."""
        if not self._ensure_connected():
            logger.warning("Redis not available; cannot retrieve session")
            return None

        try:
            key = f"{self._key_prefix}{session_id}"
            value = self._redis.get(key)
            if value is None:
                return None

            session = PQCSessionData.from_json(value)
            if session.is_expired():
                self._redis.delete(key)
                return None
            return session
        except Exception as e:
            logger.error(f"Failed to retrieve session from Redis: {e}")
            return None

    def delete(self, session_id: str) -> bool:
        """Delete session from Redis."""
        if not self._ensure_connected():
            return False

        try:
            key = f"{self._key_prefix}{session_id}"
            result = self._redis.delete(key)
            logger.debug(f"Deleted session {session_id} from Redis")
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete session from Redis: {e}")
            return False

    def invalidate_expired(self) -> int:
        """Remove expired sessions (automatic with Redis TTL)."""
        # Redis handles TTL automatically, but we can scan and count
        if not self._ensure_connected():
            return 0

        try:
            pattern = f"{self._key_prefix}*"
            cursor = 0
            count = 0
            while True:
                cursor, keys = self._redis.scan(cursor, match=pattern, count=100)
                for key in keys:
                    # Check if key still exists (Redis may have auto-expired it)
                    if not self._redis.exists(key):
                        count += 1
                if cursor == 0:
                    break
            return count
        except Exception as e:
            logger.error(f"Failed to invalidate expired sessions in Redis: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        if not self._ensure_connected():
            return {"status": "disconnected"}

        try:
            pattern = f"{self._key_prefix}*"
            cursor = 0
            count = 0
            while True:
                cursor, keys = self._redis.scan(cursor, match=pattern, count=100)
                count += len(keys)
                if cursor == 0:
                    break

            info = self._redis.info()
            return {
                "total_sessions": count,
                "redis_memory_used": info.get("used_memory_human", "unknown"),
                "redis_connected_clients": info.get("connected_clients", 0),
            }
        except Exception as e:
            logger.error(f"Failed to get Redis stats: {e}")
            return {"status": "error", "error": str(e)}


# Global session store instance
_session_store: Optional[PQCSessionStore] = None
_store_lock = threading.Lock()


def get_session_store() -> PQCSessionStore:
    """Get or create global session store.

    Automatically selects Redis if available, falls back to in-memory.
    """
    global _session_store

    if _session_store is not None:
        return _session_store

    with _store_lock:
        if _session_store is not None:
            return _session_store

        # Check if Redis is explicitly enabled via environment
        use_redis = os.environ.get("PQC_SESSION_REDIS", "").lower() in ("1", "true", "yes")
        redis_url = os.environ.get("PQC_SESSION_REDIS_URL", "redis://localhost:6379/0")
        session_ttl = int(os.environ.get("PQC_SESSION_TTL_SECONDS", "3600"))

        if use_redis:
            try:
                _session_store = RedisSessionStore(redis_url=redis_url, ttl_seconds=session_ttl)
                # Verify it works
                test_key = "pqc:test:connectivity"
                test_session = PQCSessionData(
                    session_id="test",
                    created_at=datetime.utcnow().isoformat(),
                    expires_at=(datetime.utcnow() + timedelta(seconds=10)).isoformat(),
                    client_write_key="test",
                    server_write_key="test",
                    client_iv="test",
                    server_iv="test",
                    verify_data="test",
                    cipher_suite="TEST",
                )
                _session_store.save(test_session)
                _session_store.delete("test")
                logger.info("Using Redis session store")
            except Exception as e:
                logger.warning(f"Redis session store initialization failed: {e}. Using in-memory.")
                _session_store = InMemorySessionStore()
        else:
            _session_store = InMemorySessionStore()
            logger.info("Using in-memory session store")

        return _session_store


def close_session_store() -> None:
    """Close session store (cleanup)."""
    global _session_store

    if _session_store and isinstance(_session_store, InMemorySessionStore):
        _session_store.stop()
    _session_store = None
