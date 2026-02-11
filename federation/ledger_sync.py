"""Ledger replication helpers for Hyperledger Fabric.

This module implements a guarded Fabric client wrapper and a LedgerReplicator
that can pull blocks/transactions from a Fabric network and replicate them to
another node or a local store. Heavy dependencies (the Python Fabric SDK)
are optional; when missing the module falls back to a simulated client so
the rest of the system can be tested without native SDKs.

Design contract (minimal):
- FabricClient: connect to network (if SDK available), fetch block by number
  and fetch latest height. Methods may be best-effort wrappers over SDK
  variants.
- LedgerReplicator: given a FabricClient, pull blocks in order and either POST
  them to a remote HTTP endpoint (if requests available) or append to a local
  JSONL file as the replication target.

This implementation is defensive and logs what it can. If you provide the
exact Fabric SDK package/version used in your environment I can add a
deterministic adapter for that API surface.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, Optional, Iterable

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def _try_import_fabric() -> Optional[object]:
    """Try to import a Python Hyperledger Fabric SDK (best-effort).

    Returns the imported module/object or None if not available.
    Known candidate packages:
    - hfc.fabric (fabric-sdk-py)
    """
    try:
        # fabric-sdk-py
        import hfc.fabric.client as _hfc_client  # type: ignore

        return _hfc_client
    except Exception:
        try:
            # some installs expose Client at hfc.fabric
            from hfc.fabric import client as _hfc_client2  # type: ignore

            return _hfc_client2
        except Exception:
            logger.debug("Hyperledger Fabric Python SDK not available (hfc.fabric)\n")
            return None


def _try_import_requests() -> Optional[object]:
    try:
        import requests

        return requests
    except Exception:
        logger.debug("requests not available; replication will write to local file")
        return None


class FabricClient:
    """A minimal, guarded wrapper around a Fabric SDK client.

    If no SDK is available this becomes a simulated client that emits fake
    blocks so the replication logic can be exercised in tests.
    """

    def __init__(self, network_config: Optional[str] = None, peer: Optional[str] = None):
        self._sdk = _try_import_fabric()
        self.network_config = network_config
        self.peer = peer
        self._connected = False
        self._channel = None
        # simple in-memory simulated ledger for fallback
        self._sim_blocks = [
            {"number": i, "data": {"txs": [{"id": f"tx{i}", "payload": {"n": i}}]}} for i in range(5)
        ]

    def connect(self) -> bool:
        if self._sdk is None:
            logger.info("Fabric SDK not present; using simulated client")
            self._connected = True
            return True
        try:
            # SDK-specific connect logic (best-effort)
            # fabric-sdk-py exposes a Client class
            if hasattr(self._sdk, "Client"):
                Client = getattr(self._sdk, "Client")
                # try to construct with network config
                try:
                    self._client = Client(net_profile=self.network_config)  # type: ignore
                except Exception:
                    self._client = Client()  # type: ignore
                self._connected = True
                logger.info("Connected to Fabric network via SDK")
                return True
            logger.warning("Fabric SDK imported but no Client class detected")
            self._connected = True
            return True
        except Exception:
            logger.exception("Failed to connect with Fabric SDK; falling back to simulated client")
            self._sdk = None
            self._connected = True
            return True

    def get_height(self, channel: str) -> int:
        """Return the current block height for the channel (best-effort).

        With SDK: try to call channel.query_info or similar. Fallback: return
        len(sim_blocks).
        """
        if not self._connected:
            self.connect()
        if self._sdk is None:
            return len(self._sim_blocks)
        try:
            # fabric-sdk-py: client.get_channel('mychannel').query_info()
            if hasattr(self._client, "get_channel"):
                ch = self._client.get_channel(channel)
                if hasattr(ch, "query_info"):
                    info = ch.query_info()  # may raise
                    # info.height may be an int or a BlockInfo object
                    h = getattr(info, "height", None)
                    if h is None:
                        return int(info)
                    return int(h)
        except Exception:
            logger.exception("Failed to query channel height via SDK")
        # fallback
        return len(self._sim_blocks)

    def get_block_by_number(self, channel: str, number: int) -> Dict[str, Any]:
        """Fetch a block by number (best-effort)."""
        if not self._connected:
            self.connect()
        if self._sdk is None:
            if 0 <= number < len(self._sim_blocks):
                return self._sim_blocks[number]
            raise IndexError("block out of range")
        try:
            if hasattr(self._client, "get_channel"):
                ch = self._client.get_channel(channel)
                # many SDKs expose a query_block or query_block_by_number
                if hasattr(ch, "query_block"):
                    blk = ch.query_block(number)
                    return self._normalize_sdk_block(blk)
                if hasattr(ch, "query_block_by_number"):
                    blk = ch.query_block_by_number(number)
                    return self._normalize_sdk_block(blk)
        except Exception:
            logger.exception("Failed to fetch block from SDK, falling back to simulated block if available")
        # fallback try
        if 0 <= number < len(self._sim_blocks):
            return self._sim_blocks[number]
        raise IndexError("block not found")

    def _normalize_sdk_block(self, blk: Any) -> Dict[str, Any]:
        """Convert SDK block object into a JSON-serializable dict (best-effort)."""
        try:
            # try to access attributes commonly present
            number = getattr(blk, "number", getattr(blk, "header", {}).get("number", None))
            data = getattr(blk, "data", None)
            if data is None and hasattr(blk, "transactions"):
                data = {"txs": list(getattr(blk, "transactions", []))}
            return {"number": int(number) if number is not None else None, "data": data}
        except Exception:
            logger.exception("Failed to normalize SDK block")
            return {"raw": str(blk)}


class LedgerReplicator:
    """Replicates ledger entries from a FabricClient to a target.

    Target behavior:
    - If `target_url` and `requests` are available, POST blocks to target_url
      as JSON (one POST per block) to endpoint /replicate or user-specified.
    - Otherwise append blocks to a local JSONL file named
      replicated_ledger_<channel>.jsonl in the current working directory.
    """

    def __init__(self, client: FabricClient, target_url: Optional[str] = None, endpoint: str = "/replicate"):
        self.client = client
        self.target_url = target_url
        self.endpoint = endpoint
        self.requests = _try_import_requests()

    def replicate(self, channel: str, start_block: int = 0, end_block: Optional[int] = None, poll_interval: float = 1.0) -> Iterable[Dict[str, Any]]:
        """Replicate blocks from start_block up to end_block (inclusive). If
        end_block is None, replicate up to the latest known block at time of
        each poll.

        Yields each replicated block (dict) for callers who want to inspect
        progress. This method is synchronous and intended for small-to-moderate
        runs; for long-running replication run it in a background thread/process.
        """
        if not self.client._connected:
            self.client.connect()

        current = start_block
        while True:
            height = self.client.get_height(channel)
            last_block = height - 1
            if end_block is not None and current > end_block:
                logger.info("Reached end_block %s, stopping replication", end_block)
                break
            if last_block < current:
                # nothing new yet
                logger.debug("No new blocks (current=%s last=%s); sleeping %s", current, last_block, poll_interval)
                time.sleep(poll_interval)
                continue
            # iterate available blocks
            to_block = last_block if end_block is None else min(last_block, end_block)
            for bnum in range(current, to_block + 1):
                try:
                    blk = self.client.get_block_by_number(channel, bnum)
                except Exception as e:
                    logger.exception("Failed to fetch block %s: %s", bnum, e)
                    continue
                self._send_block(channel, blk)
                yield blk
                current = bnum + 1
            if end_block is not None and current > end_block:
                break
            # if not finished, poll again
            time.sleep(poll_interval)

    def _send_block(self, channel: str, block: Dict[str, Any]) -> None:
        payload = {"channel": channel, "block": block}
        if self.target_url and self.requests:
            url = self.target_url.rstrip("/") + self.endpoint
            try:
                resp = self.requests.post(url, json=payload, timeout=5)
                if resp.status_code >= 400:
                    logger.warning("Replication POST returned %s: %s", resp.status_code, resp.text)
                else:
                    logger.debug("Replicated block %s to %s", block.get("number"), url)
                return
            except Exception:
                logger.exception("Failed to POST block to %s; falling back to local write", url)
        # local append
        fname = f"replicated_ledger_{channel}.jsonl"
        try:
            with open(fname, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(payload, default=str) + "\n")
            logger.debug("Appended block %s to %s", block.get("number"), fname)
        except Exception:
            logger.exception("Failed to write block to local file %s", fname)


def run_once(channel: str = "mychannel", start_block: int = 0, target_url: Optional[str] = None) -> None:
    """Convenience runner that instantiates a FabricClient and LedgerReplicator
    and runs a single replication pass up to the then-current height.
    """
    client = FabricClient()
    client.connect()
    # replicate up to latest known height at call time
    replicator = LedgerReplicator(client, target_url=target_url)
    height = client.get_height(channel)
    logger.info("Starting replication for channel %s from %s to %s", channel, start_block, height - 1)
    for blk in replicator.replicate(channel, start_block=start_block, end_block=height - 1, poll_interval=0.2):
        logger.info("Replicated block %s", blk.get("number"))


def main():
    import argparse

    p = argparse.ArgumentParser(description="Replicate Hyperledger Fabric ledger entries (guarded SDK)")
    p.add_argument("--channel", default="mychannel")
    p.add_argument("--start", default=0, type=int)
    p.add_argument("--target-url", default=None)
    args = p.parse_args()
    run_once(channel=args.channel, start_block=args.start, target_url=args.target_url)


if __name__ == "__main__":
    main()
