# telemetry

Purpose: telemetry ingestion and backend telemetry management (metrics, diagnostic forwarding).

Registered router prefix: `/api/telemetry`

Typical endpoints (examples)
- `POST /api/telemetry/ingest` — ingest telemetry events
- `GET /api/telemetry/status` — telemetry subsystem status

Notes: telemetry backends (Kafka, ROMA) are initialized during startup where available.
