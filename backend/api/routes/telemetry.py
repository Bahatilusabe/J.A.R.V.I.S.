from fastapi import APIRouter, Request
from typing import Any, Dict
import os
import json
import logging
import asyncio
import atexit
from datetime import datetime

from backend.integrations.huawei_lts import HuaweiLTSClient

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

router = APIRouter()


# --- guarded integrations (Kafka and Huawei ROMA MQ) ---
# These are configured during explicit initialization (init_backends)
_lts_client = HuaweiLTSClient()

# Kafka globals (populated by init_backends)
_kafka_producer = None
_kafka_enabled = False
_kafka_topic = "jarvis.telemetry"

# ROMA MQ globals
_roma_url = None
_roma_token = None
_roma_enabled = False


def init_backends():
    """Initialize optional telemetry backends. Safe to call multiple times.

    This moves SDK initialization out of import-time so the application can
    deterministically control lifecycle (startup/shutdown handlers).
    """
    global _kafka_producer, _kafka_enabled, _kafka_topic, _roma_url, _roma_token, _roma_enabled

    _kafka_topic = os.environ.get("TELEMETRY_KAFKA_TOPIC", "jarvis.telemetry")
    _kafka_bootstrap = os.environ.get("TELEMETRY_KAFKA_BOOTSTRAP")
    if _kafka_bootstrap:
        try:
            from kafka import KafkaProducer  # type: ignore

            _kafka_producer = KafkaProducer(bootstrap_servers=_kafka_bootstrap.split(","),
                                            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                                            linger_ms=5)
            _kafka_enabled = True
            logger.info("Telemetry: Kafka producer configured for %s", _kafka_bootstrap)
        except Exception:
            logger.exception("Telemetry: kafka-python not available or Kafka connection failed; disabling Kafka producer")
            _kafka_producer = None
            _kafka_enabled = False

    _roma_url = os.environ.get("ROMA_MQ_URL")
    _roma_token = os.environ.get("ROMA_MQ_TOKEN")
    _roma_enabled = bool(_roma_url and _roma_token)
    if _roma_enabled:
        try:
            import requests  # type: ignore

            logger.info("Telemetry: ROMA MQ forwarding enabled to %s", _roma_url)
        except Exception:
            logger.exception("Telemetry: requests library not available; disabling ROMA MQ forwarding")
            _roma_enabled = False


async def close_backends():
    """Gracefully close optional backends (flush/close Kafka producer)."""
    global _kafka_producer, _kafka_enabled
    try:
        if _kafka_producer is not None:
            loop = asyncio.get_running_loop()
            # run the blocking close/flush in executor
            await loop.run_in_executor(None, lambda: (_kafka_producer.flush(timeout=5), _kafka_producer.close()))
            logger.info("Telemetry: Kafka producer closed")
    except Exception:
        logger.exception("Telemetry: error while closing Kafka producer")


async def _send_to_kafka(payload: Dict[str, Any]):
    if not _kafka_enabled or _kafka_producer is None:
        return
    try:
        loop = asyncio.get_running_loop()
        # kafka-python is blocking; run in threadpool
        await loop.run_in_executor(None, lambda: _kafka_producer.send(_kafka_topic, payload))
        # do a quick flush in executor to avoid losing a small number of messages
        await loop.run_in_executor(None, lambda: _kafka_producer.flush(timeout=1))
        logger.debug("Telemetry: sent payload to Kafka topic %s", _kafka_topic)
    except Exception:
        logger.exception("Telemetry: failed to send to Kafka")


async def _send_to_roma(payload: Dict[str, Any]):
    if not _roma_enabled:
        return
    try:
        import requests  # type: ignore

        headers = {"Authorization": f"Bearer {_roma_token}", "Content-Type": "application/json"}
        body = {"timestamp": int(datetime.utcnow().timestamp()), "payload": payload}
        loop = asyncio.get_running_loop()
        # requests is blocking; run in executor
        def post():
            try:
                r = requests.post(_roma_url, headers=headers, json=body, timeout=3)
                r.raise_for_status()
                return r.status_code
            except Exception:
                logger.exception("Telemetry: ROMA MQ post failed")
                return None

        await loop.run_in_executor(None, post)
        logger.debug("Telemetry: forwarded payload to ROMA MQ %s", _roma_url)
    except Exception:
        logger.exception("Telemetry: failed to send to ROMA MQ")


async def _send_to_lts(payload: Dict[str, Any]):
    try:
        loop = asyncio.get_running_loop()
        # HuaweiLTSClient may be blocking; run in executor
        await loop.run_in_executor(None, lambda: _lts_client.send_log({"ts": int(datetime.utcnow().timestamp()), "payload": payload}))
        logger.debug("Telemetry: forwarded payload to Huawei LTS")
    except Exception:
        logger.exception("Telemetry: failed to send to Huawei LTS")


@router.post("/events")
async def ingest(request: Request):
    payload = await request.json()

    # best-effort, non-blocking forwards
    try:
        loop = asyncio.get_running_loop()
        if _kafka_enabled:
            loop.create_task(_send_to_kafka(payload))
        if _roma_enabled:
            loop.create_task(_send_to_roma(payload))
        try:
            if _lts_client.enabled():
                loop.create_task(_send_to_lts(payload))
        except Exception:
            # some stubbed/incomplete LTS clients might not implement enabled()
            loop.create_task(_send_to_lts(payload))
    except Exception:
        logger.exception("Telemetry: error scheduling background forwards")

    return {"status": "received", "size": len(str(payload)), "backends": {"kafka": _kafka_enabled, "roma": _roma_enabled, "lts": getattr(_lts_client, 'enabled', lambda: False)()}}


@router.get("/health")
async def health():
    return {"ok": True, "kafka": _kafka_enabled, "roma": _roma_enabled, "lts_configured": getattr(_lts_client, 'enabled', lambda: False)()}
