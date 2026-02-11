from fastapi import APIRouter, HTTPException
from typing import Any, Dict, Optional
import os
import logging
import asyncio

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

router = APIRouter()


class MindSporeServingClient:
    """Guarded client for calling a MindSpore Serving TGNN model.

    Tries multiple backends:
    - direct mindspore_serving.client if available
    - remote REST endpoint if PASM_MSSERVING_URL is set
    - deterministic numpy stub as fallback
    """

    def __init__(self):
        self._impl = None
        self._model_name = os.environ.get("PASM_TGNN_MODEL_NAME", "tgnn")
        self._rest_url = os.environ.get("PASM_MSSERVING_URL")

        # Try native MindSpore Serving client
        try:
            import mindspore_serving.client as msc  # type: ignore

            # common client constructors vary; try to instantiate with model name
            try:
                client = msc.Client(self._model_name)
            except Exception:
                try:
                    client = msc.Client()  # some versions use default client
                except Exception:
                    client = None
            if client is not None:
                self._impl = ("ms_client", client)
                logger.info("PASM: using local MindSpore Serving client for model %s", self._model_name)
        except Exception:
            # not available; fall through
            self._impl = None

        # If no native client, but a REST URL is provided, use that
        if self._impl is None and self._rest_url:
            try:
                import requests  # type: ignore

                self._impl = ("rest", requests.Session())
                logger.info("PASM: using REST serving endpoint %s", self._rest_url)
            except Exception:
                logger.exception("PASM: requests not available; cannot use REST serving endpoint")

    def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous predict call. Returns a dict result."""
        if self._impl is None:
            # deterministic stub: echo with a pseudo-score
            s = len(str(payload)) % 100 / 100.0
            return {"prediction": "noop", "score": s, "model": "stub"}

        kind, impl = self._impl
        if kind == "ms_client":
            client = impl
            # try common method names
            for method_name in ("predict", "run", "request", "infer"):
                fn = getattr(client, method_name, None)
                if fn:
                    try:
                        res = fn(payload)
                        return self._normalize_result(res)
                    except Exception:
                        logger.exception("PASM: error calling MindSpore Serving client.%s", method_name)
            raise RuntimeError("PASM: MindSpore Serving client present but no usable method succeeded")

        if kind == "rest":
            sess = impl
            try:
                url = self._rest_url.rstrip("/") + "/predict"
                r = sess.post(url, json=payload, timeout=5)
                r.raise_for_status()
                return r.json()
            except Exception:
                logger.exception("PASM: REST predict failed")
                raise

        # fallback
        s = len(str(payload)) % 100 / 100.0
        return {"prediction": "noop", "score": s, "model": "stub"}

    def _normalize_result(self, res: Any) -> Dict[str, Any]:
        # Normalize common response shapes to a dict
        if isinstance(res, dict):
            return res
        # some clients return lists/tuples
        try:
            return {"prediction": res}
        except Exception:
            return {"prediction": str(res)}


# module-level client instance (initialized lazily)
_pasm_client: Optional[MindSporeServingClient] = None


def init_model():
    global _pasm_client
    if _pasm_client is None:
        _pasm_client = MindSporeServingClient()


async def close_model():
    # nothing to close for now; placeholder for future lifecycle
    return


@router.post("/predict")
async def predict(payload: dict):
    """Call TGNN model for attack prediction. Uses MindSpore Serving when available."""
    global _pasm_client
    if _pasm_client is None:
        init_model()

    loop = asyncio.get_running_loop()
    try:
        # run the blocking predict in threadpool if necessary
        res = await loop.run_in_executor(None, lambda: _pasm_client.predict(payload))
        return {"ok": True, "result": res}
    except Exception as e:
        logger.exception("PASM predict failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    global _pasm_client
    if _pasm_client is None:
        init_model()
    ready = _pasm_client._impl is not None and _pasm_client._impl[0] != "stub"
    return {"ok": True, "model_ready": ready, "model_name": os.environ.get("PASM_TGNN_MODEL_NAME", "tgnn")}
