"""Utility to sync in-memory ledger state to Huawei BCS.

This script is intentionally conservative and idempotent: it keeps a small
sync-state file under the same directory to record the last synced txids
for each ledger so repeated runs only push new transactions.

Usage (programmatic):
    from backend.core.blockchain_xdr.bcs_sync import BCSSync
    sync = BCSSync(dry_run=True)
    sync.sync_all()

CLI usage:
    python -m backend.core.blockchain_xdr.bcs_sync --ledger threats
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from backend.core.blockchain_xdr.ledger_manager import LedgerManager
from backend.integrations.huawei_bcs import HuaweiBCSClient

logger = logging.getLogger(__name__)


class BCSSync:
    def __init__(self, state_file: Optional[str] = None, dry_run: bool = True):
        self.state_file = state_file or str(Path(__file__).parent / ".bcs_sync_state.json")
        self.dry_run = dry_run
        self.bcs = HuaweiBCSClient(dry_run=dry_run)
        self.ledger = LedgerManager(dry_run=True)  # use in-memory ledger instance as source

        # ensure state exists
        if not os.path.exists(self.state_file):
            with open(self.state_file, "w") as f:
                json.dump({}, f)

    def _load_state(self) -> Dict[str, List[str]]:
        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_state(self, state: Dict[str, List[str]]) -> None:
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    def sync_ledger(self, ledger_id: str, chain: Optional[str] = None) -> int:
        """Sync new transactions from an in-memory ledger to BCS.

        Returns the number of transactions pushed.
        """
        txs = self.ledger.get_transactions(ledger_id)
        state = self._load_state()
        seen = set(state.get(ledger_id, []))

        pushed = 0
        for tx in txs:
            txid = tx.get("txid")
            if txid in seen:
                continue
            payload = tx.get("payload")
            # Submit to BCS
            resp = self.bcs.submit_transaction(chain=chain or ledger_id, payload=payload)
            logger.info("Submitted tx %s to BCS resp=%s", txid, resp)
            # optimistic update: mark as seen regardless of remote response to avoid duplicates
            seen.add(txid)
            pushed += 1

        state[ledger_id] = list(seen)
        self._save_state(state)
        return pushed

    def sync_all(self, chain_map: Optional[Dict[str, str]] = None) -> Dict[str, int]:
        """Sync all ledgers in the ledger manager. Returns a map ledger_id->pushed_count."""
        results: Dict[str, int] = {}
        for ledger_id in list(self.ledger.ledgers.keys()):
            chain = (chain_map or {}).get(ledger_id)
            try:
                pushed = self.sync_ledger(ledger_id, chain=chain)
                results[ledger_id] = pushed
            except Exception as e:
                logger.exception("Failed to sync ledger %s: %s", ledger_id, e)
                results[ledger_id] = 0
        return results

    # ------------------ Federated nodes ingestion ---------------------
    def fetch_and_ingest_nodes(self, nodes_config_path: Optional[str] = None, endpoints: Optional[List[str]] = None) -> Dict[str, int]:
        """Fetch pending events from federated nodes and ingest them into the local ledger.

        The nodes config defaults to `config/federated_nodes.json` and must
        contain an array under the `nodes` key, each with at least `id` and `host`.

        For each node we attempt a few default HTTP paths to fetch pending
        events (node-specific implementations can expose these endpoints):
          - /federation/events
          - /ledger/pending
          - /api/federation/events

        Each node endpoint is expected to return a JSON array of event objects
        with fields compatible with `LedgerManager.store_signed_threat`, e.g.
        {"threat": {...}, "signature": "<hex>", "signer_cert_pem": "PEM..."}

        Returns a map node_id -> number of events ingested.
        """
        cfg_path = nodes_config_path or os.path.join(os.getcwd(), "config", "federated_nodes.json")
        try:
            with open(cfg_path, "r") as f:
                cfg = json.load(f)
        except Exception as e:
            logger.warning("Could not read federated nodes config %s: %s", cfg_path, e)
            return {}

        nodes = cfg.get("nodes", []) if isinstance(cfg, dict) else []

        default_paths = endpoints or ["/federation/events", "/ledger/pending", "/api/federation/events"]
        results: Dict[str, int] = {}

        for node in nodes:
            node_id = node.get("id") or node.get("host")
            host = node.get("host")
            if not host:
                continue
            ingested = 0
            for path in default_paths:
                url = f"http://{host.rstrip('/')}{path}"
                logger.debug("Fetching events from %s -> %s", node_id, url)
                try:
                    # try requests then urllib
                    try:
                        import requests

                        r = requests.get(url, timeout=5)
                        if r.status_code != 200:
                            continue
                        data = r.json()
                    except Exception:
                        from urllib import request as _request

                        req = _request.Request(url, method="GET")
                        with _request.urlopen(req, timeout=5) as resp:
                            text = resp.read().decode("utf-8")
                            data = json.loads(text)

                    if not isinstance(data, list):
                        # node returned single object or unexpected format
                        # try to interpret as dict with 'events' key
                        if isinstance(data, dict) and "events" in data and isinstance(data["events"], list):
                            data = data["events"]
                        else:
                            logger.debug("Unexpected events format from %s: %s", url, type(data))
                            continue

                    for ev in data:
                        try:
                            threat = ev.get("threat") if isinstance(ev, dict) else None
                            signature = ev.get("signature") if isinstance(ev, dict) else None
                            signer_cert = ev.get("signer_cert_pem") if isinstance(ev, dict) else None
                            if threat is None:
                                logger.debug("Skipping event without threat field: %s", ev)
                                continue
                            threat_json = json.dumps(threat, sort_keys=True, separators=(",", ":"))
                            sig_hex = signature if isinstance(signature, str) else (signature.hex() if isinstance(signature, (bytes, bytearray)) else "")
                            cert_pem = signer_cert.encode("utf-8") if isinstance(signer_cert, str) else signer_cert

                            args = [threat_json, sig_hex, cert_pem.decode("utf-8") if isinstance(cert_pem, (bytes, bytearray)) else (cert_pem or "")]
                            # ingest into ledger as a deterministic tx
                            self.ledger.submit_chaincode(chaincode_name="threats", fcn="storeThreat", args=args)
                            ingested += 1
                        except Exception as ie:
                            logger.exception("Failed to ingest event from %s: %s", node_id, ie)

                    # if we successfully consumed events from this path, break to next node
                    break
                except Exception as e:
                    logger.debug("Could not fetch events from %s path %s: %s", node_id, path, e)
                    continue

            results[node_id] = ingested

        return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sync in-memory ledgers to Huawei BCS")
    parser.add_argument("--ledger", help="Ledger id to sync (default: all)", default=None)
    parser.add_argument("--state-file", help="Path to sync-state file", default=None)
    parser.add_argument("--no-dry-run", help="Actually call BCS instead of dry-run", action="store_true")
    args = parser.parse_args()

    sync = BCSSync(state_file=args.state_file, dry_run=not args.no_dry_run)
    if args.ledger:
        pushed = sync.sync_ledger(args.ledger)
        print(f"Pushed {pushed} transactions for ledger {args.ledger}")
    else:
        res = sync.sync_all()
        print("Sync results:")
        print(json.dumps(res, indent=2))
