# Huawei BCS integration and syncing

This project includes a lightweight BCS client and a sync utility to push
ledger transactions to Huawei Blockchain Service (BCS). The implementation
is intentionally small and dry-run friendly so it can run in CI and local
developer environments without cloud credentials.

Files

- `backend/integrations/huawei_bcs.py`: simple HTTP client wrapper. Config via env vars:
  - `HUAWEI_BCS_ENDPOINT` (required for real runs)
  - `HUAWEI_BCS_TOKEN` (optional bearer token)

- `backend/core/blockchain_xdr/bcs_sync.py`: CLI / programmatic sync utility.
  - Records last synced txids in `.bcs_sync_state.json` next to the module.
  - Uses `LedgerManager` (in-memory ledger) as the source of transactions.
  - CLI: `python -m backend.core.blockchain_xdr.bcs_sync --ledger <ledger_id> --no-dry-run`

Syncing with MindSpore Federated nodes

- The project stores federated node metadata in `config/federated_nodes.json`.
- Each federated node is expected to expose a simple HTTP endpoint that can
  return pending federation events. By default `bcs_sync` will probe the
  following paths on each node host (in order) and consume the first one that
  returns a 200 JSON response:

  - `/federation/events`
  - `/ledger/pending`
  - `/api/federation/events`

  Each endpoint should return a JSON array of event objects with fields
  compatible with `LedgerManager.store_signed_threat`, for example:

  ```json
  [
    {
      "threat": {"type":"malware","score":0.9, ...},
      "signature": "<hex-encoded-signature>",
      "signer_cert_pem": "-----BEGIN CERTIFICATE-----..."
    }
  ]
  ```

- If your node exposes a different path or a different JSON shape, call the
  `BCSSync.fetch_and_ingest_nodes(nodes_config_path=...)` method with a
  customized configuration or adapt the node-side agent to the expected
  shape. After ingesting node events the sync utility will push new ledger
  entries to BCS (when run in `--no-dry-run` mode).

How to host on Huawei BCS

1. Provision a BCS instance and obtain the REST endpoint and credentials.
2. Set environment variables:
   - `HUAWEI_BCS_ENDPOINT=https://<your-bcs-endpoint>`
   - `HUAWEI_BCS_TOKEN=<token>` (if your deployment uses bearer token)
3. Run the sync utility in non-dry-run mode to push transactions:

```bash
python -m backend.core.blockchain_xdr.bcs_sync --no-dry-run
```

Notes and next steps

- This is a minimal integration. For production you should:
  - Replace the simple HTTP client with Huawei's official BCS SDK (if
    available) and implement proper AK/SK signing flows.
  - Use a persistent ledger backend (e.g., a database) rather than the
    in-memory ledger used for testing here.
  - Implement robust retry and idempotency semantics aligned with your
    BCS deployment's transaction model.
# Huawei BCS integration and syncing

This project includes a lightweight BCS client and a sync utility to push
ledger transactions to Huawei Blockchain Service (BCS). The implementation
is intentionally small and dry-run friendly so it can run in CI and local
developer environments without cloud credentials.

Files

- `backend/integrations/huawei_bcs.py`: simple HTTP client wrapper. Config via env vars:
  - `HUAWEI_BCS_ENDPOINT` (required for real runs)
  - `HUAWEI_BCS_TOKEN` (optional bearer token)

- `backend/core/blockchain_xdr/bcs_sync.py`: CLI / programmatic sync utility.
  - Records last synced txids in `.bcs_sync_state.json` next to the module.
  - Uses `LedgerManager` (in-memory ledger) as the source of transactions.
  - CLI: `python -m backend.core.blockchain_xdr.bcs_sync --ledger <ledger_id> --no-dry-run`

Syncing with MindSpore Federated nodes

- The project stores federated node metadata in `config/federated_nodes.json`.
- Each federated node is expected to expose a simple HTTP endpoint that can
  return pending federation events. By default `bcs_sync` will probe the
  following paths on each node host (in order) and consume the first one that
  returns a 200 JSON response:

  - `/federation/events`
  - `/ledger/pending`
  - `/api/federation/events`

  Each endpoint should return a JSON array of event objects with fields
  compatible with `LedgerManager.store_signed_threat`, for example:

  ```json
  [
    {
      "threat": {"type":"malware","score":0.9, ...},
      "signature": "<hex-encoded-signature>",
      "signer_cert_pem": "-----BEGIN CERTIFICATE-----..."
    }
  ]
  ```

- If your node exposes a different path or a different JSON shape, call the
  `BCSSync.fetch_and_ingest_nodes(nodes_config_path=...)` method with a
  customized configuration or adapt the node-side agent to the expected
  shape. After ingesting node events the sync utility will push new ledger
  entries to BCS (when run in `--no-dry-run` mode).

How to host on Huawei BCS

1. Provision a BCS instance and obtain the REST endpoint and credentials.
2. Set environment variables:
   - `HUAWEI_BCS_ENDPOINT=https://<your-bcs-endpoint>`
   - `HUAWEI_BCS_TOKEN=<token>` (if your deployment uses bearer token)
3. Run the sync utility in non-dry-run mode to push transactions:

```bash
python -m backend.core.blockchain_xdr.bcs_sync --no-dry-run
```

Syncing with MindSpore Federated nodes

- The project stores federated node metadata in `config/federated_nodes.json`.
- This repository provides `LedgerManager` which higher-level code (for
  example the federation coordinator) can call to append signed threat or
  model exchange events. To sync those ledger entries to BCS, run the
  `bcs_sync` utility.

Notes and next steps

- This is a minimal integration. For production you should:
  - Replace the simple HTTP client with Huawei's official BCS SDK (if
    available) and implement proper AK/SK signing flows.
  - Use a persistent ledger backend (e.g., a database) rather than the
    in-memory ledger used for testing here.
  - Implement robust retry and idempotency semantics aligned with your
    BCS deployment's transaction model.
Huawei BCS integration and syncing

This project includes a lightweight BCS client and a sync utility to push
ledger transactions to Huawei Blockchain Service (BCS). The implementation
is intentionally small and dry-run friendly so it can run in CI and local
developer environments without cloud credentials.

Files
- `backend/integrations/huawei_bcs.py`: simple HTTP client wrapper. Config via env vars:
  - `HUAWEI_BCS_ENDPOINT` (required for real runs)
  - `HUAWEI_BCS_TOKEN` (optional bearer token)

- `backend/core/blockchain_xdr/bcs_sync.py`: CLI / programmatic sync utility.
  - Records last synced txids in `.bcs_sync_state.json` next to the module.
  - Uses `LedgerManager` (in-memory ledger) as the source of transactions.
  - CLI: `python -m backend.core.blockchain_xdr.bcs_sync --ledger <ledger_id> --no-dry-run`

Syncing with MindSpore Federated nodes
- The project stores federated node metadata in `config/federated_nodes.json`.
- Each federated node is expected to expose a simple HTTP endpoint that can
  return pending federation events. By default `bcs_sync` will probe the
  following paths on each node host (in order) and consume the first one that
  returns a 200 JSON response:

  - `/federation/events`
  - `/ledger/pending`
  - `/api/federation/events`

  Each endpoint should return a JSON array of event objects with fields
  compatible with `LedgerManager.store_signed_threat`, for example:

  ```json
  [
    {
      "threat": {"type":"malware","score":0.9, ...},
      "signature": "<hex-encoded-signature>",
      "signer_cert_pem": "-----BEGIN CERTIFICATE-----..."
    }
  ]
  ```

  If your node exposes a different path or a different JSON shape, call the
  `BCSSync.fetch_and_ingest_nodes(nodes_config_path=...)` method with a
  customized configuration or adapt the node-side agent to the expected
  shape. After ingesting node events the sync utility will push new ledger
  entries to BCS (when run in `--no-dry-run` mode).

How to host on Huawei BCS
1. Provision a BCS instance and obtain the REST endpoint and credentials.
2. Set environment variables:
   - `HUAWEI_BCS_ENDPOINT=https://<your-bcs-endpoint>`
   - `HUAWEI_BCS_TOKEN=<token>` (if your deployment uses bearer token)
3. Run the sync utility in non-dry-run mode to push transactions:

```bash
python -m backend.core.blockchain_xdr.bcs_sync --no-dry-run
```

Syncing with MindSpore Federated nodes
- The project stores federated node metadata in `config/federated_nodes.json`.
- This repository provides `LedgerManager` which higher-level code (for
  example the federation coordinator) can call to append signed threat or
  model exchange events. To sync those ledger entries to BCS, run the
  `bcs_sync` utility.

Notes and next steps
- This is a minimal integration. For production you should:
  - Replace the simple HTTP client with Huawei's official BCS SDK (if
    available) and implement proper AK/SK signing flows.
  - Use a persistent ledger backend (e.g., a database) rather than the
    in-memory ledger used for testing here.
  - Implement robust retry and idempotency semantics aligned with your
    BCS deployment's transaction model.
