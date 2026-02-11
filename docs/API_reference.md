# API Reference (stub)

This document will be expanded with full REST and gRPC endpoint descriptions.

Endpoints
- POST /telemetry/events — telemetry ingestion
- POST /pasm/predict — predict attack surface changes
- POST /policy/simulate — simulate policy changes
- POST /vocal/intent — voice command intent processing
- GET /forensics/{id} — retrieve forensic report

Authentication
- Services use JWT with mutual TLS for sensitive endpoints (TBD).