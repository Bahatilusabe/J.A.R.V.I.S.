"""Node agent and sync manager for federated training.

This module provides a guarded MindSpore Federated Client wrapper (used when
MindSpore federated APIs are available) and a NodeSyncManager that periodically
synchronizes model parameters with a central aggregator via HTTP/REST
endpoints. All heavy dependencies are optional and the code falls back to
safe no-ops suitable for local development and tests.
"""

from __future__ import annotations

import argparse
import json
import logging
import threading
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("node_agent")
logging.basicConfig(level=logging.INFO)


def _try_import_requests():
    try:
        import requests

        return requests
    except Exception:
        return None


def _try_import_mindspore_federated():
    # Try several possible module names; these imports are best-effort.
    try:
        import mindspore_federated  # type: ignore

        return mindspore_federated
    except Exception:
        try:
            import mindspore as ms  # type: ignore

            # Some MindSpore builds may expose federated APIs under ms.federated
            if hasattr(ms, "federated"):
                return ms.federated
        except Exception:
            pass
    return None


requests = _try_import_requests()
ms_fed = _try_import_mindspore_federated()


class MindSporeFederatedClient:
    """A thin wrapper around MindSpore federated client APIs when available.

    When MindSpore federated APIs are not available the wrapper simulates the
    interface with local no-op implementations so the rest of the system can
    run and be unit-tested.
    """

    def __init__(self, node_id: str, server_url: Optional[str] = None, ms_module: Optional[Any] = None):
        self.node_id = node_id
        self.server_url = server_url
        self._ms = ms_module or ms_fed
        self._registered = False

    def register(self) -> bool:
        if self._ms is None:
            logger.info("MindSpore federated client not available; running in simulated mode")
            self._registered = True
            return True
        try:
            # Attempt to call a hypothetical register API; keep it guarded.
            if hasattr(self._ms, "Client"):
                # preferred API: construct a client object
                try:
                    self._client = self._ms.Client(node_id=self.node_id, server_url=self.server_url)
                except Exception:
                    # some APIs expect different constructor args
                    self._client = self._ms.Client()
                # try register/start variants
                if hasattr(self._client, "register"):
                    self._client.register()
                elif hasattr(self._client, "start"):
                    self._client.start()
                elif hasattr(self._ms, "init"):
                    self._ms.init()
            elif hasattr(self._ms, "init"):
                # older or different API surface
                self._ms.init()
            # After creating client, detect available API methods for get/submit
            self._detect_api()
            self._registered = True
            logger.info("Registered federated client with MindSpore APIs (detected methods: get=%s submit=%s)",
                        getattr(self, "_get_weights_fn", None) is not None,
                        getattr(self, "_submit_update_fn", None) is not None)
            return True
        except Exception:
            logger.exception("Failed to register MindSpore federated client; falling back to simulated mode")
            self._ms = None
            self._registered = True
            return True

    def _detect_api(self):
        """Detects get/submit API method names on the client or ms module and
        stores callable references on the wrapper for later use.
        """
        self._get_weights_fn = None
        self._submit_update_fn = None

        # Potential get_weights method names
        get_names = ["get_weights", "pull_weights", "pull", "get_model", "get_latest_weights", "get_parameters"]
        submit_names = ["submit_update", "push", "push_weights", "submit", "submit_model_update", "upload_update"]

        target_objs = [getattr(self, "_client", None), self._ms]
        for obj in target_objs:
            if obj is None:
                continue
            for name in get_names:
                if hasattr(obj, name):
                    fn = getattr(obj, name)
                    if callable(fn):
                        self._get_weights_fn = fn
                        break
            for name in submit_names:
                if hasattr(obj, name):
                    fn = getattr(obj, name)
                    if callable(fn):
                        self._submit_update_fn = fn
                        break
            if self._get_weights_fn and self._submit_update_fn:
                break

    def get_weights(self) -> Optional[Dict[str, Any]]:
        """Fetch model weights from the federated server via MindSpore API or simulate."""
        if not self._registered:
            self.register()
        if self._ms is None:
            # Simulated weights
            logger.debug("Returning simulated weights")
            return {"version": 0, "weights": {}}
        try:
            if hasattr(self._client, "get_weights"):
                return self._client.get_weights()
            # otherwise no-op
            return None
        except Exception:
            logger.exception("Error fetching weights from MindSpore federated client")
            return None

    def submit_update(self, update: Dict[str, Any]) -> bool:
        """Submit a weight update to the federated server."""
        if not self._registered:
            self.register()
        if self._ms is None:
            logger.info("Simulated submit_update: %s", {k: type(v) for k, v in update.items()})
            return True
        try:
            if hasattr(self._client, "submit_update"):
                self._client.submit_update(update)
                return True
            return False
        except Exception:
            logger.exception("Error submitting update via MindSpore federated client")
            return False


class NodeSyncManager:
    """Manages periodic synchronization between the node and an aggregator.

    The manager can use either the MindSpore federated client wrapper (preferred
    when available) or HTTP REST endpoints (if `requests` is present) for
    registration, pull, and push. All network I/O is optional and failures are
    logged without crashing the node.
    """

    def __init__(self, node_id: str, server_url: Optional[str] = None, interval: int = 30):
        self.node_id = node_id
        self.server_url = server_url
        self.interval = int(interval)
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.client = MindSporeFederatedClient(node_id=node_id, server_url=server_url)

    def start(self):
        logger.info("Starting NodeSyncManager for node %s", self.node_id)
        self.client.register()
        self._stop.clear()
        self._thread = threading.Thread(target=self._sync_loop, name=f"NodeSync-{self.node_id}", daemon=True)
        self._thread.start()

    def stop(self):
        logger.info("Stopping NodeSyncManager for node %s", self.node_id)
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)

    def _sync_loop(self):
        while not self._stop.is_set():
            try:
                self._do_sync_once()
            except Exception:
                logger.exception("Unhandled error during sync loop")
            # wait with early exit
            for _ in range(max(1, int(self.interval))):
                if self._stop.is_set():
                    break
                time.sleep(1)

    def _do_sync_once(self):
        logger.debug("Sync: fetching global weights")
        weights = None
        # prefer MindSpore federated client
        try:
            weights = self.client.get_weights()
        except Exception:
            logger.exception("client.get_weights failed")

        # If ms client did not provide weights, try REST endpoint
        if weights is None and requests is not None and self.server_url is not None:
            try:
                url = f"{self.server_url.rstrip('/')}/model/latest"
                r = requests.get(url, timeout=5.0)
                if r.status_code == 200:
                    weights = r.json()
                    logger.debug("Pulled weights via REST: version=%s", weights.get("version"))
            except Exception:
                logger.exception("Failed to pull weights from REST endpoint %s", self.server_url)

        # Simulate local training/update step (plugin point)
        local_update = {"node": self.node_id, "delta": {}, "timestamp": int(time.time())}

        # Submit update using client or REST
        submitted = False
        try:
            submitted = self.client.submit_update(local_update)
        except Exception:
            logger.exception("client.submit_update failed")

        if not submitted and requests is not None and self.server_url is not None:
            try:
                url = f"{self.server_url.rstrip('/')}/model/submit"
                r = requests.post(url, json=local_update, timeout=5.0)
                submitted = r.status_code == 200
                logger.debug("Submitted update via REST: status=%s", r.status_code)
            except Exception:
                logger.exception("Failed to submit update to REST endpoint %s", self.server_url)

        if submitted:
            logger.info("Sync cycle completed: weights pulled=%s, submitted=%s", bool(weights), submitted)
        else:
            logger.info("Sync cycle completed: no submission made")


def run_agent(node_id: str, server_url: Optional[str], interval: int, run_time: Optional[int] = None):
    mgr = NodeSyncManager(node_id=node_id, server_url=server_url, interval=interval)
    mgr.start()
    try:
        if run_time is None:
            # run indefinitely until KeyboardInterrupt
            while True:
                time.sleep(1)
        else:
            time.sleep(run_time)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received; stopping agent")
    finally:
        mgr.stop()


def main():
    parser = argparse.ArgumentParser(description="Federation node agent (MindSpore Federated client wrapper + sync manager)")
    parser.add_argument("--node-id", default="node-1", help="Unique ID for this node")
    parser.add_argument("--server-url", default=None, help="Aggregator server base URL for REST fallback (e.g., http://host:port)")
    parser.add_argument("--interval", type=int, default=30, help="Sync interval in seconds")
    parser.add_argument("--run-time", type=int, default=None, help="If set, run the agent for this many seconds then exit")
    args = parser.parse_args()
    run_agent(node_id=args.node_id, server_url=args.server_url, interval=args.interval, run_time=args.run_time)


if __name__ == "__main__":
    main()
