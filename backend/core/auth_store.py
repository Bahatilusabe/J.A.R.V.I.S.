"""Simple credential store for development.

Provides a minimal user store backed by JSON and password hashing.
Uses passlib (bcrypt) when available, otherwise falls back to PBKDF2-HMAC-SHA256.

NOT FOR PRODUCTION: replace with a real user DB and argon2/bcrypt verification.
"""
from __future__ import annotations

import base64
import json
import os
import hashlib
import hmac
from typing import Dict, Optional

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "users.json")


def _ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)


def _use_passlib() -> bool:
    try:
        import passlib.hash  # type: ignore

        return True
    except Exception:
        return False


def hash_password(password: str) -> str:
    """Hash password, prefer bcrypt via passlib if available.

    Returns a string token that encodes algorithm/material for verification.
    """
    if _use_passlib():
        from passlib.hash import bcrypt  # type: ignore

        return "bcrypt$" + bcrypt.hash(password)

    # Fallback: PBKDF2-HMAC-SHA256 with 100k iterations
    salt = os.urandom(16)
    iterations = 100_000
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return "pbkdf2$%d$%s$%s" % (iterations, base64.b64encode(salt).decode("ascii"), base64.b64encode(dk).decode("ascii"))


def verify_password(password: str, hashed: str) -> bool:
    if hashed.startswith("bcrypt$"):
        if not _use_passlib():
            # cannot verify bcrypt without passlib
            return False
        from passlib.hash import bcrypt  # type: ignore

        return bcrypt.verify(password, hashed.split("$", 1)[1])

    if hashed.startswith("pbkdf2$"):
        try:
            _, iterations_s, salt_b64, dk_b64 = hashed.split("$", 3)
            iterations = int(iterations_s)
            salt = base64.b64decode(salt_b64)
            expected = base64.b64decode(dk_b64)
            dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
            return hmac.compare_digest(dk, expected)
        except Exception:
            return False

    return False


def load_users() -> Dict[str, Dict[str, str]]:
    path = os.path.abspath(DATA_PATH)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_users(users: Dict[str, Dict[str, str]]) -> None:
    path = os.path.abspath(DATA_PATH)
    _ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def get_user(username: str) -> Optional[Dict[str, str]]:
    users = load_users()
    return users.get(username)


def add_user(username: str, password: str, role: str = "user") -> None:
    users = load_users()
    users[username] = {"password": hash_password(password), "role": role}
    save_users(users)
