# pasm

Purpose: Policy-as-a-Service and rule management that integrate with the DPI and firewall engines.

Registered router prefix: `/api/pasm`

Typical endpoints (examples)

- `GET /api/pasm/policies` — list configured policies
- `POST /api/pasm/policies` — create/update a policy

Notes: used by policy automation pipelines and the frontend policy editor.
