

# JARVIS Gateway — Consolidated Documentation

This file summarizes the repository's development run steps, the documentation backup, and quick references for getting the system running locally.

Backup of original Markdown files
- All original `.md` files detected across the repository were moved to a safe backup folder to allow regeneration and clean documentation rollout.

Backup path:

    docs/_backup/md-archive-20260211T200411Z

Generated README files (created by this run)
- `backend/README.md` — quick start and router prefix list for the backend API.
- `frontend/web_dashboard/README.md` — quick start for the Vite-based frontend.

Quick checklist to bring up development environment

1. Backend
   - Create a Python venv and activate it.
   - Install dependencies: `python3 -m pip install -r backend/requirements.txt`.
   - If `pyyaml` fails to build, prefer using Python 3.11 or install `libyaml` via Homebrew: `brew install libyaml`.
   - Start server: `python3 backend/api/server.py` or `uvicorn backend.api.server:app --reload`.

2. Frontend
   - Change to `frontend/web_dashboard`
   - Run `npm install`, then `npm run dev`
   - Open `http://localhost:5173`

Key runtime notes
- The backend exposes the following health endpoints: `/health`, `/api/system/status`, `/api/federation/status`.
- Main token issuance endpoint: `POST /token` (returns a PQC/HMAC-backed bearer token). Example protected route: `GET /protected`.
- The frontend expects the backend at `http://127.0.0.1:8000` by default.

Next steps you may want me to take
- (A) Generate more detailed per-module README files (e.g., `backend/api/forensics/README.md`) using extracted source comments and function signatures.
- (B) Attempt to fix the backend dependency installation for the current environment (try Homebrew libyaml installation or install a Python 3.11 venv and re-run pip). Note: Homebrew commands require local environment access and privileges.
- (C) Run `npm install` and `npm run dev` in `frontend/web_dashboard` here (if allowed). If the environment can't run Node or Docker, I can instead create more run instructions and a small Dockerfile.

Status of generated artifacts
- Created: `backend/README.md`, `frontend/web_dashboard/README.md`, `DOCUMENTATION_FULL.md` (this file).
- Original docs moved to: `docs/_backup/md-archive-20260211T200411Z` (safe backup).

If you'd like me to continue I can:
- Generate per-module READMEs automatically now (option A), or
- Try to resolve the PyYAML build and bring up the backend and frontend (option B/C). 

Tell me which option you prefer and I will continue.
