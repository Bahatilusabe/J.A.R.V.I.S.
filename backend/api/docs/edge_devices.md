# edge_devices

Purpose: Edge device registration and control APIs.

Registered router prefix: registered under `/api` (edge-device endpoints live under the `/api` namespace).

Typical endpoints (examples)

- `GET /api/devices` — list registered edge devices
- `POST /api/devices/<id>/action` — send control action to a device
