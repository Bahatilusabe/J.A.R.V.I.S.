"""MindSpore-aware federated server and secure aggregation helpers.

This module provides a guarded wrapper for creating a simple federated
server that can accept model updates from clients and perform secure-ish
aggregation. Heavy dependencies (MindSpore) are optional; when missing the
module falls back to pure-NumPy implementations suitable for unit tests and
local development.

Notes:
- This is NOT a production-ready secure aggregation implementation. It
  provides a tested, deterministic fallback and small simulated masking
  primitives so the rest of the system can be exercised without dedicated
  cryptographic infrastructure. If you provide the exact MindSpore federated
  component API available in your environment I will add a strict adapter.
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Any, Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def _try_import_mindspore():
    try:
        import mindspore as ms  # type: ignore

        return ms
    except Exception:
        logger.debug("MindSpore not available; using NumPy fallbacks")
        return None


ms = _try_import_mindspore()


class MindSporeAdapter:
    """Strict adapter that wraps a real MindSpore federated client object.

    This adapter expects the SDK to expose a module named either
    `mindspore_federated` or `mindspore.federated` with a `Client` class
    whose instance supports methods like `register()`, `get_weights()` or
    `get_parameters()`, and `submit_update()` or `push_update()`.

    The adapter is intentionally conservative: it probes for several
    common method names and raises AttributeError if essential methods are
    missing.
    """

    def __init__(self, client_obj: object):
        self._client = client_obj
        # detect required callables; support many common variants and
        # consider methods available on the client object or on the module
        get_names = [
            "get_weights",
            "get_parameters",
            "pull_weights",
            "pull",
            "get_model",
            "get_global_parameters",
            "query_parameters",
        ]
        submit_names = [
            "submit_update",
            "push_update",
            "submit",
            "push",
            "upload_update",
            "send_update",
        ]

        # helper to find a callable on multiple candidate objects
        def _find_callable(objs, names):
            for obj in objs:
                if obj is None:
                    continue
                for name in names:
                    if hasattr(obj, name):
                        fn = getattr(obj, name)
                        if callable(fn):
                            return fn
            return None

        # candidates: client object, and module if client has __module__ attr
        candidates = [self._client]
        try:
            mod_name = getattr(self._client, "__module__", None)
            if mod_name:
                import importlib

                try:
                    mod = importlib.import_module(mod_name.split(".")[0])
                    candidates.append(mod)
                except Exception:
                    pass
        except Exception:
            pass

        self._get_fn = _find_callable(candidates, get_names)
        self._submit_fn = _find_callable(candidates, submit_names)

        # Some SDKs provide a single `get` or `submit` that accepts args; support
        if self._get_fn is None and hasattr(self._client, "get"):
            self._get_fn = getattr(self._client, "get")
        if self._submit_fn is None and hasattr(self._client, "submit"):
            self._submit_fn = getattr(self._client, "submit")

        if self._get_fn is None or self._submit_fn is None:
            raise AttributeError("Provided MindSpore client missing required get/submit methods")

    def register(self, *args, **kwargs):
        if hasattr(self._client, "register"):
            return self._client.register(*args, **kwargs)
        if hasattr(self._client, "start"):
            return self._client.start(*args, **kwargs)
        # no-op if neither exists
        return None

    def get_weights(self, *args, **kwargs):
        # call the discovered get function and normalize results to a dict
        res = self._get_fn(*args, **kwargs)
        # common SDKs may return an object with .parameters or .weights
        if isinstance(res, dict):
            return res
        if hasattr(res, "parameters"):
            return dict(res.parameters)
        if hasattr(res, "weights"):
            return dict(res.weights)
        # fallback: try to coerce to dict
        try:
            return dict(res)
        except Exception:
            return {"model": res}

    def submit_update(self, *args, **kwargs):
        # some SDKs expect (weights_dict) others expect a payload; delegate
        try:
            return self._submit_fn(*args, **kwargs)
        except TypeError:
            # try to collapse args into a single dict if possible
            if len(args) == 1 and isinstance(args[0], dict):
                return self._submit_fn(args[0])
            # try kwargs fallback
            if kwargs:
                return self._submit_fn(kwargs)
            # last resort: call with no args
            return self._submit_fn()


def make_mindspore_server_from_sdk(network_config: Optional[str] = None) -> Optional[MindSporeAdapter]:
    """Attempt to construct a MindSporeAdapter by importing and instantiating
    the expected MindSpore federated client.

    This function checks a few candidate module paths and constructor
    signatures. It returns a MindSporeAdapter if successful or None if no
    suitable SDK is present.
    """
    import importlib
    # prefer the dotted package path (e.g. mindspore.federated) which is
    # more likely to represent the official namespace, then fall back to
    # alternate candidate names
    candidates = ["mindspore.federated", "mindspore_federated", "mindspore_federate"]
    for mod_name in candidates:
        try:
            mod = importlib.import_module(mod_name)
        except Exception:
            continue
        # prefer a Client class
        Client = None
        if hasattr(mod, "Client"):
            Client = getattr(mod, "Client")
        elif hasattr(mod, "client") and hasattr(getattr(mod, "client"), "Client"):
            Client = getattr(getattr(mod, "client"), "Client")
        if Client is None:
            continue
        # try constructing
        try:
            try:
                client_obj = Client(net_profile=network_config)  # type: ignore
            except Exception:
                client_obj = Client()  # type: ignore
            adapter = MindSporeAdapter(client_obj)
            return adapter
        except Exception:
            # try next candidate
            continue
    return None


class MindSporeFederatedServer:
    """Minimal federated server that accepts client updates and aggregates them.

    The server stores updates in-memory and exposes a secure_aggregate method
    which will combine client weight dictionaries into an averaged weight
    dict. If a cryptography library is available the module may simulate
    encrypted transfers; otherwise it uses a simple additive-masking protocol
    implemented locally for testing.
    """

    def __init__(self):
        self._clients: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._aggregated: Optional[Dict[str, Any]] = None
        # If a real MindSpore federated SDK is present, build an adapter and
        # use it for registration/submit/get operations. This makes the server
        # automatically delegate to the production SDK when available.
        try:
            self._adapter = make_mindspore_server_from_sdk()
            if self._adapter is not None:
                logger.info("Using MindSpore SDK adapter for federated server")
        except Exception:
            self._adapter = None

    def register_client(self, client_id: str) -> None:
        with self._lock:
            if client_id in self._clients:
                logger.debug("client %s already registered", client_id)
                return
            self._clients[client_id] = {}
            logger.info("Registered client %s", client_id)
            if getattr(self, "_adapter", None) is not None:
                # delegate registration to SDK adapter when available
                try:
                    # adapter.register may accept client_id or not; call with best-effort
                    try:
                        self._adapter.register(client_id)
                    except TypeError:
                        self._adapter.register()
                except Exception:
                    logger.exception("Adapter registration failed for client %s", client_id)

    def receive_update(self, client_id: str, weights: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> None:
        """Receive a client's model update (weights as dict of arrays/lists).

        The server will store the update for later aggregation. We copy the
        arrays into numpy arrays for deterministic behavior.
        """
        with self._lock:
            if client_id not in self._clients:
                raise KeyError(f"client {client_id} not registered")
            # If adapter is present, delegate submission to SDK; otherwise
            # store locally for later aggregation.
            if getattr(self, "_adapter", None) is not None:
                try:
                    payload = {"node": client_id, "weights": {k: _from_numpy(_to_numpy(v)) for k, v in weights.items()}, "metadata": metadata}
                    # adapter.submit_update may accept different shapes; best-effort
                    try:
                        self._adapter.submit_update(payload)
                    except TypeError:
                        # try to pass weights directly
                        self._adapter.submit_update(weights)
                    logger.info("Delegated update from client %s to MindSpore SDK adapter", client_id)
                    # still keep a local copy for compatibility
                    self._clients[client_id] = {k: _to_numpy(v) for k, v in weights.items()}
                    return
                except Exception:
                    logger.exception("Adapter submit_update failed; falling back to local store")
            self._clients[client_id] = {k: _to_numpy(v) for k, v in weights.items()}
            logger.info("Received update from client %s (keys=%s)", client_id, list(weights.keys()))

    def secure_aggregate(self, mask: bool = True) -> Dict[str, Any]:
        """Aggregate client updates.

        If mask=True the server will simulate a masking-based secure
        aggregation (clients add random masks that cancel when summed).
        In this local implementation the server performs the mask simulation
        itself for deterministic behavior in tests.
        """
        with self._lock:
            # If adapter exists, attempt to fetch aggregated weights from SDK
            if getattr(self, "_adapter", None) is not None:
                try:
                    sdk_weights = self._adapter.get_weights()
                    # normalize to Python lists
                    logger.info("Fetched aggregated weights from MindSpore SDK adapter")
                    return {k: _from_numpy(_to_numpy(v)) for k, v in sdk_weights.items()}
                except Exception:
                    logger.exception("Failed to fetch aggregated weights from adapter; falling back to local aggregation")
            if not self._clients:
                raise RuntimeError("no client updates to aggregate")
            # collect keys
            client_ids = list(self._clients.keys())
            keys = set()
            for c in client_ids:
                keys.update(self._clients[c].keys())

            aggregated: Dict[str, Any] = {}
            for k in keys:
                # stack arrays (missing keys treated as zeros)
                arrays = []
                for c in client_ids:
                    v = self._clients[c].get(k)
                    if v is None:
                        arrays.append(np.zeros_like(next(iter(self._clients.values()))[k]))
                    else:
                        arrays.append(np.array(v, dtype=float))
                stacked = np.stack(arrays, axis=0)
                if mask:
                    # simulate masks: clients add masks that cancel in aggregate
                    rng = np.random.RandomState(0)
                    masks = rng.normal(scale=1e-6, size=stacked.shape)
                    stacked = stacked + masks
                    # when summing, masks cancel in expectation; here we just
                    # subtract the mean mask to simulate unmasking.
                    stacked = stacked - np.mean(masks, axis=0)
                agg = np.mean(stacked, axis=0)
                aggregated[k] = agg
            # store aggregated
            self._aggregated = aggregated
            logger.info("Aggregated weights from %d clients", len(self._clients))
            return {k: _from_numpy(v) for k, v in aggregated.items()}

    def get_aggregated(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            return None if self._aggregated is None else {k: _from_numpy(v) for k, v in self._aggregated.items()}


def _to_numpy(x: Any) -> Any:
    if isinstance(x, np.ndarray):
        return x.copy()
    if isinstance(x, (list, tuple)):
        return np.array(x)
    try:
        return np.array(x)
    except Exception:
        return x


def _from_numpy(x: Any) -> Any:
    if isinstance(x, np.ndarray):
        return x.tolist()
    return x


__all__ = ["MindSporeFederatedServer"]
