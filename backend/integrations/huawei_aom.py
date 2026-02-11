"""Simple Huawei Cloud AOM integration helper.

This module implements a small, safe wrapper to send JSON "events" to a
configured Huawei AOM HTTP endpoint. It's intentionally minimal:

- Uses environment variables `HUAWEI_AOM_URL` and `HUAWEI_AOM_TOKEN` if
  present. If not present, the send_event() becomes a no-op but still logs.
- Posts events as JSON with an Authorization Bearer token when configured.
- Uses a background threadpool to avoid blocking producers in the deception
  code paths. Retries are limited and exceptions are swallowed (but logged)
  to avoid crashing honeypots or trainers.

NOTE: For security, do NOT hardcode secrets. Configure the runtime or CI
environment with the AOM URL and token. This file intentionally avoids
provider-specific heavy SDKs to keep it lightweight.
"""
from __future__ import annotations

import os
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional

try:
    import requests
except Exception:  # pragma: no cover - requests may be missing in minimal envs
    requests = None

logger = logging.getLogger(__name__)

# Read configuration from environment. If unset, the integration is a safe no-op.
_AOM_URL = os.environ.get("HUAWEI_AOM_URL")
_AOM_TOKEN = os.environ.get("HUAWEI_AOM_TOKEN")

# Thread pool for async sending. Small fixed pool to avoid runaway threads.
_POOL = ThreadPoolExecutor(max_workers=2)


def _is_configured() -> bool:
    return bool(_AOM_URL and _AOM_TOKEN and requests is not None)


def send_event(event_type: str, payload: Dict[str, Any], timestamp: Optional[str] = None) -> None:
    """Send an event to Huawei AOM if configured.

    Parameters
    - event_type: short string describing the event (e.g. 'honeypot_interaction')
    - payload: JSON-serializable dict with event details
    - timestamp: optional ISO timestamp string; if provided it's added to payload

    This function returns immediately; sending happens in background. Errors
    are logged and swallowed.
    """
    if not _is_configured():
        logger.debug("Huawei AOM not configured; skipping send_event(%s)", event_type)
        return

    event = {
        "type": event_type,
        "payload": payload,
    }
    if timestamp:
        event["timestamp"] = timestamp

    def _post():
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {_AOM_TOKEN}",
            }
            # Post the event. AOM endpoint contracts vary; this generic
            # approach expects a simple event-ingest endpoint that accepts
            # application/json. Users should set HUAWEI_AOM_URL accordingly.
            resp = requests.post(_AOM_URL, data=json.dumps(event), headers=headers, timeout=5)
            if not (200 <= resp.status_code < 300):
                logger.warning("Huawei AOM send returned %s: %s", resp.status_code, resp.text)
            else:
                logger.debug("Huawei AOM event %s sent successfully", event_type)
        except Exception as exc:  # keep integration fault-tolerant
            logger.exception("Failed to send event to Huawei AOM: %s", exc)

    # Schedule the post in background.
    try:
        _POOL.submit(_post)
    except Exception:
        # In rare cases pool.submit may fail; attempt synchronous fallback but swallow errors
        try:
            _post()
        except Exception:
            logger.exception("Huawei AOM synchronous fallback failed")


def is_available() -> bool:
    """Return whether the integration is active in this environment."""
    return _is_configured()
