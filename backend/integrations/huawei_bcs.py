"""Lightweight Huawei Blockchain Service (BCS) client wrapper.

This module provides a defensive, test-friendly wrapper around a simple
HTTP-based BCS endpoint. Real Huawei BCS integrations will typically use
an SDK or more elaborate signing (AK/SK) flows; this helper is intentionally
small and uses environment variables for configuration so it can be used in
CI and dry-run modes.

Configuration (env vars):
- HUAWEI_BCS_ENDPOINT: full URL to the BCS REST API (e.g. https://bcs.example.com)
- HUAWEI_BCS_TOKEN: optional bearer token for authentication (if provided)
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger("jarvis.integrations.huawei_bcs")


class HuaweiBCSClient:
    def __init__(self, endpoint: Optional[str] = None, token: Optional[str] = None, dry_run: bool = True):
        self.endpoint = endpoint or os.environ.get("HUAWEI_BCS_ENDPOINT")
        self.token = token or os.environ.get("HUAWEI_BCS_TOKEN")
        self.dry_run = dry_run

    def enabled(self) -> bool:
        return bool(self.endpoint)

    def _post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled() or self.dry_run:
            logger.info("BCS dry-run/disabled: would POST %s -> %s with body size=%d", path, self.endpoint, len(json.dumps(body)))
            return {"ok": False, "reason": "dry_run_or_disabled", "body": body}

        url = f"{self.endpoint.rstrip('/')}/{path.lstrip('/')}"
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        # try requests first for convenience
        try:
            import requests

            r = requests.post(url, data=json.dumps(body).encode("utf-8"), headers=headers, timeout=10)
            try:
                r.raise_for_status()
            except Exception:
                logger.exception("BCS POST failed status=%s body=%s", r.status_code, r.text)
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

                req = _request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
                with _request.urlopen(req, timeout=10) as resp:
                    data = resp.read().decode("utf-8")
                    try:
                        return {"ok": True, "status": resp.status, "result": json.loads(data)}
                    except Exception:
                        return {"ok": True, "status": resp.status, "result": data}
            except Exception as exc:
                logger.exception("BCS post failed: %s", exc)
                return {"ok": False, "reason": str(exc)}

    def submit_transaction(self, chain: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a transaction payload to the BCS service.

        The exact REST path and payload shape depends on your BCS deployment.
        This method uses a conservative shape: {"chain": chain, "payload": <payload>}.
        """
        body = {"chain": chain, "payload": payload}
        return self._post("/transactions/submit", body)


__all__ = ["HuaweiBCSClient"]
