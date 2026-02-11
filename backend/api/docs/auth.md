# auth

Purpose: Authentication endpoints for issuing tokens and managing users.

Registered router prefix: `/api/auth` (token endpoint also present at `/token` in `server.py`).

Typical endpoints (examples)

- `POST /api/auth/login` — perform login and obtain token
- `POST /token` — token issuance (PQC/HMAC token issued by `server.py`)

Notes: development users are auto-initialized on first run if placeholders are present in the auth store.
