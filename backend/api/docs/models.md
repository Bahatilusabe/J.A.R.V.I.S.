# models

Purpose: Model registry endpoints (models metadata and metrics).

Registered router prefix: `/api/metrics` (models endpoints are registered on the metrics router namespace).

Typical endpoints (examples)

- `GET /api/metrics/models` — list available ML models
- `POST /api/metrics/models/deploy` — deploy a model
