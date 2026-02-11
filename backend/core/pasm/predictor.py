"""Predictor wrapper for PASM.

This module exposes a Predictor class that will attempt to use a
MindSpore Serving inference client when available (configured via
environment or explicit URL). If the serving client is unavailable or the
call fails, it falls back to a local `TGNNModel` based predictor.

The serving integration is gated behind optional imports so tests and
dev environments without MindSpore can continue to function.
"""
from __future__ import annotations

import concurrent.futures
import logging
import os
import time
from typing import Any, Dict, Optional

from .tgnn_model import TGNNModel

logger = logging.getLogger("jarvis.pasm.predictor")

# Config from env
_SERVING_TIMEOUT = float(os.environ.get("JARVIS_SERVING_TIMEOUT", "2.0"))
_SERVING_RETRIES = int(os.environ.get("JARVIS_SERVING_RETRIES", "2"))
_SERVING_BACKOFF = float(os.environ.get("JARVIS_SERVING_BACKOFF", "0.5"))


class Predictor:
    def __init__(self, serving_url: Optional[str] = None, model_dir: Optional[str] = None):
        """Try to initialize a MindSpore Serving client if possible.

        serving_url: optional URL to a running MindSpore Serving endpoint.
        model_dir: optional local model directory (not used by default but
                   kept for compatibility).
        """
        self.serving_url = serving_url or os.environ.get("JARVIS_MSSERVING_URL")
        self.model_dir = model_dir or os.environ.get("JARVIS_TGNN_MODEL_DIR")
        self._serving_client = None
        self._local_model = TGNNModel()

        # Lazy attempt to import MindSpore Serving client
        try:
            import mindspore_serving.client as mssclient  # type: ignore

            # Prefer explicit serving_url if provided, else try to create a
            # local client if API provides one. We defensively attempt a
            # Client(serving_url) call and guard any failures.
            if self.serving_url:
                try:
                    self._serving_client = mssclient.Client(self.serving_url)
                except Exception:
                    logger.exception("failed to initialize MindSpore Serving client with URL; will fallback")
                    self._serving_client = None
            else:
                # Try to create a default client if supported
                try:
                    # Some serving client libs expose a default Client() or LocalClient
                    if hasattr(mssclient, "Client"):
                        self._serving_client = mssclient.Client()
                    elif hasattr(mssclient, "LocalClient"):
                        self._serving_client = mssclient.LocalClient(self.model_dir)
                except Exception:
                    logger.exception("failed to initialize default MindSpore Serving client; will fallback")
                    self._serving_client = None
        except Exception:
            # MindSpore Serving not installed; continue with local model
            self._serving_client = None

    def predict(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """Perform prediction using the serving client or fall back locally.

        The graph structure matches what TGNNModel.predict expects.
        """
        # Try serving client first with retries, backoff and timeout
        if self._serving_client is not None:
            payload = {"inputs": graph}
            methods = ["predict", "infer", "request"]
            for attempt in range(max(1, _SERVING_RETRIES)):
                for method in methods:
                    if not hasattr(self._serving_client, method):
                        continue

                    call = getattr(self._serving_client, method)

                    try:
                        # run the call with a timeout using a worker thread
                        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                            fut = ex.submit(call, payload)
                            resp = fut.result(timeout=_SERVING_TIMEOUT)

                        # normalize response
                        if isinstance(resp, dict) and "score" in resp:
                            return resp
                        if isinstance(resp, dict) and "outputs" in resp:
                            out = resp.get("outputs")
                            if isinstance(out, dict) and "score" in out:
                                return out

                        logger.debug("serving client returned unexpected response on method %s", method)
                    except concurrent.futures.TimeoutError:
                        logger.warning("serving client %s timed out (attempt %d)", method, attempt + 1)
                    except Exception:
                        logger.debug("serving client call %s failed on attempt %d", method, attempt + 1)

                # backoff before next attempt
                if attempt < max(1, _SERVING_RETRIES) - 1:
                    backoff = _SERVING_BACKOFF * (2 ** attempt)
                    time.sleep(backoff)
            logger.debug("serving client exhausted retries; falling back to local model")

        # Local fallback
        return self._local_model.predict(graph)

    def health_check(self, timeout: Optional[float] = None) -> bool:
        """Check if serving client is healthy (if present).

        Returns True if the serving client responded positively or a
        lightweight predict succeeded. Otherwise False.
        """
        if self._serving_client is None:
            return False

        t = timeout or _SERVING_TIMEOUT

        # check explicit health method names
        for name in ("health", "health_check", "ping", "status"):
            if hasattr(self._serving_client, name):
                try:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                        fut = ex.submit(getattr(self._serving_client, name))
                        res = fut.result(timeout=t)
                    # interpret a truthy response as healthy
                    return bool(res)
                except Exception:
                    continue

        # fallback: try a lightweight predict with empty graph
        try:
            payload = {"inputs": {"nodes": []}}
            if hasattr(self._serving_client, "predict"):
                call = self._serving_client.predict
            elif hasattr(self._serving_client, "infer"):
                call = self._serving_client.infer
            else:
                call = None

            if call is not None:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    fut = ex.submit(call, payload)
                    resp = fut.result(timeout=t)
                if isinstance(resp, dict):
                    return True
        except Exception:
            return False

        return False


# module-level default predictor
_default = Predictor()


def predict(graph: Dict[str, Any]) -> Dict[str, Any]:
    return _default.predict(graph)


__all__ = ["Predictor", "predict"]

