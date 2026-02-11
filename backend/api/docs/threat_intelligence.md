# threat_intelligence

Purpose: Threat intelligence ingestion and enrichment endpoints. Registered without an `/api` prefix so some endpoints may be root-level or proxied.

Registered router prefix: (registered without `/api` prefix in server wiring)

Typical endpoints (examples)

- `POST /ti/enrich` — submit enrichment request
- `GET /ti/indicators` — list threat indicators
