# policy

Purpose: Central policy APIs used by firewall, IDS, and enforcement components.

Registered router prefix: `/api/policy`

Typical endpoints (examples)

- `GET /api/policy` — list active policies
- `POST /api/policy/apply` — apply a policy change

Notes: integrates with `pasm` and DPI modules for enforcement.
