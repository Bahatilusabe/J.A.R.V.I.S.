# JARVIS Gateway — Full README

Brief
-----
JARVIS Gateway is a multi-component project providing a backend REST API and a Vite-powered frontend dashboard. This README documents how to install, run, and develop the project locally, lists important endpoints, troubleshooting tips, and dev workflows.

Repository layout (important)
- backend/ — Python backend (FastAPI / uvicorn)
  - backend/api/ — API routes
  - backend/core/ — core services (policy engine, self-healing, etc.)
- frontend/web_dashboard/ — React + Vite frontend
- docs/_backup/ — (if present) previous markdown backups
- DOCUMENTATION_FULL.md — consolidated repo documentation

Prerequisites
-------------
- macOS or Linux
- Git
- Python 3.11 recommended for backend (some dependencies like PyYAML have better wheel support)
- Node.js 18+ (use nvm to manage versions)
- npm (comes with Node)
- (Optional) Docker Desktop if you prefer containerized frontend
- Xcode CLI tools on macOS: `xcode-select --install`

Quick setup (recommended)
-------------------------
1. Clone and enter repo:
```bash
(https://github.com/Bahatilusabe/J.A.R.V.I.S..git)
```

2. Backend — create and activate venv:
```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r backend/requirements.txt
```
If PyYAML fails to build, see Troubleshooting below.

3. Frontend — use nvm and Node 18:
```bash
# install nvm if needed, then:
nvm install 18
nvm use 18
cd frontend/web_dashboard
npm ci
```

Run locally
-----------
Backend (development)
```bash
# from repo root, with venv active
uvicorn backend.api.server:app --reload --host 0.0.0.0 --port 8000
# or
python3 backend/api/server.py
```
Health check:
```bash
curl http://127.0.0.1:8000/health
# expected: {"status":"ok"}
```

Frontend (development)
```bash
cd frontend/web_dashboard
npm run dev
# open http://localhost:5173
```

Alternatively run frontend Docker (requires Docker):
```bash
cd frontend/web_dashboard
npm run docker:build
npm run docker:run
# then open http://localhost:5173
```

API overview (common endpoints)
-------------------------------
Note: exact paths and available APIs can be found in `backend/api/`.
- GET /health
- GET /api/system/status
- GET /api/federation/status
- POST /token  — token issuance (PQC/HMAC mechanisms)
- Example protected route: GET /protected

Example token request:
```bash
curl -X POST http://127.0.0.1:8000/token -d "username=admin&password=..." 
# returns JSON bearer token
```

Integration points
------------------
- Frontend by default expects backend at `http://127.0.0.1:8000`. Adjust env/config if needed.
- Policy template engine is available at `backend/core/policy_templates.py` for deterministic rule-based policies while RL (MindSpore) is not in use.
  - Example usage (python):
    - `from backend.core.policy_templates import PolicyTemplateEngine`
    - `engine.load_from_file("backend/core/policy_templates_example.yaml")`
    - `engine.evaluate(context)`

Testing
-------
- Playwright smoke test exists: `frontend/web_dashboard/scripts/admin_smoke_test.js`
  - Requires Node >=18 (Playwright package requires Node 18+).
  - Run: `npx playwright test` (after Playwright install or `npm ci`)
- Backend unit tests (if present) run via `pytest`:
```bash
# from repo root
source .venv/bin/activate
pytest -q
```

Troubleshooting
---------------
PyYAML build errors on macOS/Python 3.12
- Symptom: pip fails building pyyaml wheel or raises compile errors.
- Fixes:
  - Use Python 3.11: install with pyenv or system package, create a new venv.
  - Install libyaml before pip install:
    ```bash
    brew install libyaml
    python -m pip install -r backend/requirements.txt
    ```
  - Or try an only-binary install:
    ```bash
    python -m pip install pyyaml==6.0 --only-binary=:all:
    ```

Node engine warnings / Playwright errors
- If `npm install` emits EBADENGINE warnings, switch Node to 18+:
```bash
nvm install 18
nvm use 18
cd frontend/web_dashboard
npm ci
```
- If `vite: command not found` — run `npm ci` in `frontend/web_dashboard` to install local binaries or run `npx vite`.

Common commands to inspect logs and processes
- Kill backend by port:
```bash
lsof -i :8000
kill <PID>
```
- View logs if started with nohup:
```bash
tail -f backend.log
tail -f frontend.log
```

Docs & maintenance
------------------
- Generated docs: `backend/README.md`, `frontend/web_dashboard/README.md`, `DOCUMENTATION_FULL.md`.
- Old .md files were moved into a backup (if present) before removal. If you need to restore, check git history or the backup tar (if created earlier).

Git workflow (recommended)
--------------------------
- Use feature branches:
```bash
git checkout -b feat/<feature-name>
# commit changes
git push -u origin feat/<feature-name>
# create PR
```
- To update main:
```bash
git checkout main
git pull --rebase origin main
git merge --no-ff feat/<feature-name>
git push origin main
```

MindSpore / RL notes
--------------------
- MindSpore is optional for RL-based policies. For production RL you will need a compatible OS, Python version, and possibly GPU/CUDA on Linux.
- For installing MindSpore, provide OS and GPU details and a recommended pip install command will be supplied. For development, the project includes a template-based policy engine to operate without RL.

Contributing
------------
- Open issues or PRs for bugs or feature work.
- Follow coding standards present in repo and run linters/tests before PR.

License & contact
-----------------
- Check project LICENSE file for terms.
- For help, open an issue or contact the repository maintainer.

Appendix: quick command summary
-------------------------------
```bash
# Backend
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
uvicorn backend.api.server:app --reload

# Frontend
nvm install 18
nvm use 18
cd frontend/web_dashboard
npm ci
npm run dev
```

If you want, I can:
- Extract all API routes and add more detailed endpoint docs into `backend/api/docs/`.
- Create sample Postman/Insomnia collection.
- Add CI steps for running tests and linting.
