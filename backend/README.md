# Backend (JARVIS Gateway)

This directory contains the FastAPI-based backend for the JARVIS Gateway.

Key points
- App entrypoint: `backend/api/server.py` (runs an embedded uvicorn when executed directly).
- Default API port: 8000
- Health endpoints available:
  - `GET /health` — basic health check
  - `GET /api/system/status` — system status
  - `GET /api/federation/status` — federation status

Quick start (developer machine)

1. Use a supported Python version. If you encounter build failures for packages such as PyYAML on newer Python (3.12+), switch to Python 3.11 or install system libyaml first (examples below).

2. Create and activate a virtual environment (recommended):

   python3 -m venv .venv
   source .venv/bin/activate

3. Install dependencies:

   python3 -m pip install --upgrade pip setuptools wheel
   python3 -m pip install -r backend/requirements.txt

If `pyyaml==6.0` fails to build (common on some macOS + newer Python versions) try one of:
- Install system libyaml (macOS Homebrew):
  - `brew install libyaml` then retry `pip install -r backend/requirements.txt`
- Use Python 3.11 (prebuilt wheels are more likely to be available):
  - `pyenv install 3.11.6` (or your preferred installer) and use that Python for the venv

Run the server (development):

    # from repo root
    python3 backend/api/server.py

Alternatively, run via uvicorn for automatic reloads while editing:

    uvicorn backend.api.server:app --reload --host 0.0.0.0 --port 8000

Authentication & tokens
- `POST /token` — accepts JSON `{"username": "...", "password": "..."}` and returns a PQC-backed bearer token. The app uses a PQC adapter that falls back to HMAC if PQC libs are missing.
- `GET /protected` — example protected route that requires `Authorization: Bearer <token>`.

Registered router prefixes (extracted from `backend/api/server.py`)

- /api/telemetry
- /api/pasm
- /api/policy
- /api/vocal
- /api/forensics
- /api/vpn
- /api/auth
- /api/self_healing
- /api/packet_capture
- /api/dpi
- /api/tds
- /api/ced
- /api/metrics
- /api/federation
- /api/deception
- /api/pqc
- /api/settings
- /api (admin, ids, edge devices and other top-level routes)
- threat-intelligence (registered without `/api` prefix)
- fl_blockchain (federated-learning)

Notes & troubleshooting
- If the server starts but endpoints are unreachable from the browser, check CORS settings: `DEV_ALLOWED_ORIGINS` environment variable controls allowed dev origins.
- For production-like runs, make sure PQC keys are configured if you need PQC token signatures (env vars: `PQC_SK_B64`, `PQC_PK_B64`).

Where to next
- The top-level `DOCUMENTATION_FULL.md` in the repo root summarizes run steps and points to the backup of original `.md` files.
