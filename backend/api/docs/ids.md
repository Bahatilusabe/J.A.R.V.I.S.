# ids

Purpose: Intrusion Detection System (IDS) endpoints and management APIs.

Registered router prefix: registered under `/api` (IDs-specific routes live under the `/api` namespace).

Typical endpoints (examples)

- `GET /api/ids/signatures` — list IDS signatures
- `POST /api/ids/scan` — run signature-based scan
