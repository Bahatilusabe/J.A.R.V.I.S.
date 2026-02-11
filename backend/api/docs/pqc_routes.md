# pqc_routes

Purpose: Post-quantum cryptography (PQC) token endpoints and helpers.

Registered router prefix: `/api/pqc`

Typical endpoints (examples)

- `POST /api/pqc/generate` — generate PQC material (when enabled)
- `GET /api/pqc/status` — PQC subsystem status

Notes: The main server implements a PQC adapter that falls back to HMAC when PQC libraries are not present.
