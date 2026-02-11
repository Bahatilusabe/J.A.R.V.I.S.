## J.A.R.V.I.S. — AI assistance instructions

This is a concise guide for AI agents that work in this repository. Follow the exact code patterns, file locations, and workflows described below — they are discoverable from the repository and represent how contributors expect changes to be made.

Key goals for generated edits:
- Keep API routers consistent: add a new file in `backend/api/routes/` and register it in `backend/api/server.py` using `app.include_router(..., prefix='/api/<name>')`.
- Keep business logic in `backend/core/`, exposing thin FastAPI routes in `backend/api/routes` that call into `backend/core/` modules.
- Avoid heavy imports at module-import time (use lazy initialization like `get_dpi_engine()` in `backend/api/routes/dpi_routes.py`).

Architecture at a glance (what to read first):
- `README.md` - high-level overview and quick start.
- `config/default.yaml` - default configuration values (telemetry, DPI, backend ports).
- `deployment/docker/Dockerfile.backend` & `deployment/docker/docker-compose.yml` - how the backend is containerized.
- `backend/api/server.py` - FastAPI entry-point / router wiring / auth middleware.
- `backend/core/` - domain/business modules (pasm, self_healing, pqcrypto, deception, vocal, etc.).
- `backend/api/routes/dpi_routes.py` - example of route patterns and lazy singleton engine initialization.

Developer workflows (commands and CI):
- Install dependencies: `make deps` (installs `backend/requirements.txt`).
- Run backend locally: `make run-backend` (starts `uvicorn backend.api.server:app`).
- Build the backend image: `make build-backend` (uses `deployment/docker/Dockerfile.backend`).
- Run the DPI service locally (requires container or native build): `make run-dpi`.
- Run tests locally: `make test` or `pytest backend/tests`.
- CI: `.github/workflows/ci-python.yml` runs unit tests at `pytest backend/tests/unit` across Python versions (3.10-3.12).

Security & auth notes (important for PRs that touch auth/crypto):
- The backend uses PQC/HMAC token logic. Look at `backend/api/server.py` for the `PQCAdapter`, `create_pqc_token`, and `verify_pqc_token` helpers.
- The server honors these env vars: `PQC_SK_B64`, `PQC_PK_B64`, `API_HMAC_KEY`.
- mTLS enforcement is implemented using `JARVIS_MTLS_REQUIRED` and a list of `JARVIS_MTLS_ALLOWED_FINGERPRINTS`.
- Tokens are passed as `Authorization: Bearer <token>` header; `verify_pqc_token()` raises HTTP 401 on invalid/expired tokens.

Common patterns & conventions to preserve (examples):
- Route creation: use Pydantic models for request/response; follow patterns in `backend/api/routes/*` files. Example: `dpi_routes` has models such as `PacketData`, returns `AlertResponse`.
- Heavy objects (engines, stateful singletons) must be initialized lazily and stored in a module-level singleton object (see `get_dpi_engine()`). Avoid expensive work at import time.
- Use environment-controlled dev flags: CORS origins via `DEV_ALLOWED_ORIGINS`, telemetry backends via `telemetry.init_backends()` and `telemetry.close_backends()` (see `backend/api/server.py` startup/shutdown hooks).
- Tests live in `backend/tests/unit` and `backend/tests/integration`. Unit tests run in CI; integration tests are more complex and may require additional infra.

Integration & external dependencies:
- Docker images: `deployment/docker/Dockerfile.backend` for backend. Use `deployment/docker/docker-compose.yml` to run local multi-container stacks.
- Kubernetes manifests live in `deployment/kubernetes`.
- Optional external systems: telemetry backends (Kafka/ROMA), gRPC backends (gRPC proxy placeholder in `server.py`), and PQC libraries `pyspx`, `pqcrypto`, `liboqs-python`.

When making code changes, prefer these steps:
1. Identify the module and files to update (`backend/core/*` and `backend/api/routes/*`).
2. Add/modify Pydantic models for public API changes (`backend/api/routes` model classes).
3. Add unit tests under `backend/tests/unit` that cover the new logic. Keep tests isolated (mock heavy external calls) and ensure `pytest -q` passes.
4. Update docs (`docs/`) and README if the public interface or config changes.
5. For backend changes that add a route, register the router in `backend/api/server.py` and also update CORS/MTLS environment examples in `config/default.yaml`.

Small do/don't checklist for AI completions:
- DO keep code style consistent: small functions, strong typing (Pydantic), and single responsibility components.
- DO add tests for new logic and API endpoints (happy path + 1-2 edge cases).
- DO reference environment variables used by the service (PQC keys, MTLS flags, API_HMAC_KEY) when editing auth or startup code.
- DO NOT add heavy initialization at import time (use the `get_*()` lazy pattern).
- DO NOT change global router wiring without updating `server.py` and adding a matching integration test.

Files to reference while coding:
- `backend/api/server.py` — router wiring, token helpers, startup hooks (Telem/MTLS).
- `backend/api/routes/dpi_routes.py` — example API design; protocol classification and alert endpoints.
- `backend/core/*` — business logic modules (prefer changes here, not in route code).
- `Makefile`, `deployment/*` — build/run/test with Docker/compose.
- `docs/API_reference.md`, `docs/DPI_ENGINE.md` — API and architecture documentation to keep in sync.

If anything is unclear: ask the repo owner or create an issue referencing the file(s) you changed and the tests added/updated.

— End of guidance —
