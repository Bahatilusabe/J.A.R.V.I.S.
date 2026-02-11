# forensics

Purpose: Forensics and evidence export endpoints used by the investigations UI.

Registered router prefix: `/api/forensics`

Typical endpoints (examples)

- `GET /api/forensics/cases` — list forensic cases
- `POST /api/forensics/export` — export case artifacts (ZIP/PDF)

Notes: there are two forensics route modules in the codebase (`forensics.py` and `forensics_routes.py`) that share the `/api/forensics` prefix.
