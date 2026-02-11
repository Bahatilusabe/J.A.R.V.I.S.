"""Minimal Huawei Cloud LTS (Log Tank Service) client.

This module provides a small, test-friendly client that can send single
telemetry events or batches to a configured Huawei LTS endpoint. It's
designed to be defensive: if the environment is not configured, calls
become no-ops and return a descriptive result.

Configuration (via env vars):
- HUAWEI_LTS_ENDPOINT: full HTTP(S) URL for the LTS ingest API
- HUAWEI_LTS_TOKEN: optional bearer token for auth (if provided, used)
- HUAWEI_LTS_PROJECT: optional project id / stream identifier

The real Huawei LTS APIs are richer (AK/SK signing, project/resource ids);
this client is intentionally small and easy to mock in tests. For production
use, replace auth with proper AK/SK signing or SDK.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger("jarvis.integrations.huawei_lts")


class HuaweiLTSClient:
    def __init__(self, endpoint: Optional[str] = None, token: Optional[str] = None, project: Optional[str] = None):
        self.endpoint = endpoint or os.environ.get("HUAWEI_LTS_ENDPOINT")
        self.token = token or os.environ.get("HUAWEI_LTS_TOKEN")
        self.project = project or os.environ.get("HUAWEI_LTS_PROJECT")

    def enabled(self) -> bool:
        return bool(self.endpoint)

    def _post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled():
            logger.debug("Huawei LTS not configured; skipping post to %s", path)
            return {"ok": False, "reason": "not_configured"}

        url = f"{self.endpoint.rstrip('/')}/{path.lstrip('/')}"
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        payload = json.dumps(body).encode("utf-8")

        # try requests first
        try:
            import requests

            r = requests.post(url, data=payload, headers=headers, timeout=5)
            try:
                r.raise_for_status()
            except Exception:
                logger.exception("Huawei LTS post failed status=%s body=%s", r.status_code, r.text)
                return {"ok": False, "status": r.status_code, "body": r.text}
            try:
                return {"ok": True, "status": r.status_code, "result": r.json()}
            except Exception:
                return {"ok": True, "status": r.status_code, "result": r.text}
        except Exception:
            # fallback to urllib
            try:
                from urllib import request as _request
                from urllib.error import HTTPError

                req = _request.Request(url, data=payload, headers=headers, method="POST")
                with _request.urlopen(req, timeout=5) as resp:
                    data = resp.read().decode("utf-8")
                    try:
                        return {"ok": True, "status": resp.status, "result": json.loads(data)}
                    except Exception:
                        return {"ok": True, "status": resp.status, "result": data}
            except Exception as exc:
                logger.exception("Huawei LTS post failed: %s", exc)
                return {"ok": False, "reason": str(exc)}

    def send_log(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Send a single telemetry event to LTS.

        The implementation wraps the record and attaches project/context
        information if configured.
        """
        body = {"project": self.project, "event": record}
        return self._post("ingest/event", body)

    def send_batch(self, records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        body = {"project": self.project, "events": list(records)}
        return self._post("ingest/batch", body)


__all__ = ["HuaweiLTSClient"]
