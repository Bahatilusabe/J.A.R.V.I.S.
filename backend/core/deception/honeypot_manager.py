"""
Honeypot manager utilities (safe emulator-style implementation).

This module provides a lightweight, in-memory HoneypotManager for test
and simulation purposes. It intentionally does NOT start real network
services or provide instructions for deploying real honeypots. It's
meant for unit tests, simulations, and analytics pipelines.

Features:
- start/stop simulated honeypots (no real sockets opened)
- record and store interaction events
- export logs to JSON
- simple in-memory statistics

Ethics & safety: Do not use this module to facilitate unauthorized
access or to automate attacks. It's a defensive simulation aid.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class InteractionEvent:
    honeypot_name: str
    timestamp: float
    client_ip: Optional[str]
    client_port: Optional[int]
    payload_summary: str
    notes: Optional[str] = None


class HoneypotManager:
    """Manage simulated honeypot instances and record interactions.

    This class intentionally does not bind to any network ports. Use
    it to simulate startup/shutdown and to gather recorded interaction
    events for analysis or testing.
    """

    def __init__(self) -> None:
        self._running: Dict[str, dict] = {}
        self._events: List[InteractionEvent] = []

    def start_honeypot(self, name: str, config: Optional[dict] = None) -> None:
        """Register a simulated honeypot instance.

        Args:
            name: Friendly name for the honeypot.
            config: Optional configuration dict (for metadata only).
        """
        if name in self._running:
            logger.debug("honeypot %s already running", name)
            return
        self._running[name] = {
            "started_at": time.time(),
            "config": config or {},
        }
        logger.info("Started simulated honeypot: %s", name)

    def stop_honeypot(self, name: str) -> None:
        """Stop (deregister) a simulated honeypot instance."""
        if name in self._running:
            self._running.pop(name, None)
            logger.info("Stopped simulated honeypot: %s", name)
        else:
            logger.debug("honeypot %s not found", name)

    def list_honeypots(self) -> List[str]:
        return list(self._running.keys())

    def record_interaction(
        self,
        honeypot_name: str,
        client_ip: Optional[str],
        client_port: Optional[int],
        payload_summary: str,
        notes: Optional[str] = None,
    ) -> None:
        """Record a single interaction event against a simulated honeypot.

        payload_summary should be a short description (no raw secrets).
        """
        evt = InteractionEvent(
            honeypot_name=honeypot_name,
            timestamp=time.time(),
            client_ip=client_ip,
            client_port=client_port,
            payload_summary=payload_summary,
            notes=notes,
        )
        self._events.append(evt)
        logger.debug("Recorded event for %s: %s", honeypot_name, payload_summary)
        # Optionally emit to Huawei AOM for visualization/OPS if integration is configured.
        try:
            try:
                from backend.integrations.huawei_aom import send_event  # type: ignore
            except Exception:
                send_event = None

            if send_event is not None:
                payload = {
                    "honeypot": honeypot_name,
                    "client_ip": client_ip,
                    "client_port": client_port,
                    "summary": (payload_summary or "")[:512],
                    "notes": notes,
                }
                try:
                    send_event("honeypot_interaction", payload)
                except Exception:
                    logger.debug("Huawei AOM send_event failed in HoneypotManager.record_interaction")
        except Exception:
            # swallow any unexpected errors from optional telemetry
            logger.debug("Error while attempting to send Huawei AOM event from HoneypotManager")

    def events(self) -> List[InteractionEvent]:
        return list(self._events)

    def export_logs(self, path: str) -> str:
        """Export events to a JSON file. Returns path written.

        The output is safe for analysis but omits large raw payloads by
        design (payload_summary only).
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(e) for e in self._events]
        with p.open("w", encoding="utf-8") as fh:
            json.dump({"events": data, "exported_at": time.time()}, fh, indent=2)
        logger.info("Exported %d honeypot events to %s", len(data), p)
        return str(p)

    def get_stats(self) -> dict:
        """Return a small set of in-memory stats about recorded events."""
        by_honeypot: Dict[str, int] = {}
        for e in self._events:
            by_honeypot.setdefault(e.honeypot_name, 0)
            by_honeypot[e.honeypot_name] += 1
        return {
            "num_honeypots": len(self._running),
            "num_events": len(self._events),
            "events_by_honeypot": by_honeypot,
        }


__all__ = ["HoneypotManager", "InteractionEvent"]


class CowrieConnector:
    """Safe connector to ingest Cowrie JSON logs and provide adaptive hooks.

    This connector intentionally does NOT deploy, configure, or expose
    Cowrie instances. It reads Cowrie-style JSON log lines from a
    directory or individual strings and converts them into
    InteractionEvent objects for analysis and adaptive simulation.

    Usage (safe):
      - point `log_dir` at a local directory containing Cowrie JSON logs
      - call `ingest_directory_once()` to parse all JSON lines
      - register adaptive policies with `register_policy()` to react
        to parsed events. Policies may only operate on the
        HoneypotManager simulation state.
    """

    def __init__(self, log_dir: Optional[str] = None) -> None:
        self.log_dir = Path(log_dir) if log_dir else None
        # simple policy registry: name -> callable(event, manager)
        self._policies = {}

    def parse_cowrie_json_line(self, line: str) -> Optional[InteractionEvent]:
        """Parse a single Cowrie JSON event line into InteractionEvent.

        The implementation is robust to missing fields and will return
        None for lines that are not valid JSON.
        """
        try:
            payload = json.loads(line)
        except Exception:
            logger.debug("Invalid JSON line in CowrieConnector")
            return None

        # Cowrie emits many event types; synthesize a payload_summary
        event_type = payload.get("eventid") or payload.get("event") or payload.get("event_type")
        src_ip = payload.get("src_ip") or payload.get("src_addr") or payload.get("src_ip_addr")
        src_port = payload.get("src_port") or payload.get("src_port_int")
        username = payload.get("username") or payload.get("user")
        message = payload.get("message") or payload.get("msg") or ""

        summary_parts = [str(event_type)]
        if username:
            summary_parts.append(f"user={username}")
        if message:
            # keep summary short
            summary_parts.append(message[:120])
        payload_summary = " | ".join([p for p in summary_parts if p])

        # Map Cowrie event types to a honeypot name if present
        honeypot_name = payload.get("sensor") or payload.get("honeypot") or "cowrie"

        return InteractionEvent(
            honeypot_name=honeypot_name,
            timestamp=payload.get("timestamp") or time.time(),
            client_ip=src_ip,
            client_port=src_port,
            payload_summary=payload_summary,
            notes=json.dumps({"cowrie_event": event_type}) if event_type else None,
        )

    def ingest_directory_once(self, manager: HoneypotManager) -> int:
        """Parse all .log/.json lines in `log_dir` once and feed events to manager.

        Returns the number of events ingested. Does not delete files.
        """
        if not self.log_dir:
            raise ValueError("log_dir is not set for CowrieConnector")
        count = 0
        for p in self.log_dir.iterdir():
            if not p.is_file():
                continue
            if not p.suffix.lower() in {".log", ".json", ".txt", ""}:
                continue
            try:
                with p.open("r", encoding="utf-8", errors="ignore") as fh:
                    for line in fh:
                        evt = self.parse_cowrie_json_line(line)
                        if evt:
                            manager.record_interaction(
                                evt.honeypot_name,
                                evt.client_ip,
                                evt.client_port,
                                evt.payload_summary,
                                notes=evt.notes,
                            )
                            count += 1
                            self._run_policies(evt, manager)
            except Exception as exc:
                logger.debug("Failed to read log file %s: %s", p, exc)
        logger.info("Ingested %d events from Cowrie logs in %s", count, self.log_dir)
        return count

    def register_policy(self, name: str, func) -> None:
        """Register an adaptive policy callable(event, manager).

        Policies must be safe and must only modify the simulation state
        (HoneypotManager). They should NOT perform network deployment.
        """
        self._policies[name] = func

    def unregister_policy(self, name: str) -> None:
        self._policies.pop(name, None)

    def _run_policies(self, event: InteractionEvent, manager: HoneypotManager) -> None:
        for name, func in list(self._policies.items()):
            try:
                func(event, manager)
            except Exception:
                logger.exception("policy %s raised", name)


def sample_ssh_bruteforce_policy(threshold: int = 5):
    """Return a policy closure that reacts to repeated failed-logins.

    This example policy is intentionally conservative: instead of
    changing network configuration it will only simulate adding a new
    in-memory honeypot record in the HoneypotManager.
    """

    counts: Dict[str, int] = {}

    def policy(event: InteractionEvent, manager: HoneypotManager) -> None:
        key = event.client_ip or "unknown"
        if "login.failed" in (event.payload_summary or "").lower() or "authentication failed" in (event.payload_summary or "").lower():
            counts[key] = counts.get(key, 0) + 1
            logger.debug("ssh brute force candidate from %s count=%d", key, counts[key])
            if counts[key] >= threshold:
                # Simulate deployment of an adaptive honeypot instance (in-memory only)
                name = f"adaptive-{key.replace(':','-')}"
                if name not in manager.list_honeypots():
                    manager.start_honeypot(name, config={"reason": "ssh_bruteforce_detected", "source_ip": key})
                    logger.info("Simulated adaptive honeypot started for %s", key)

    return policy


__all__.extend(["CowrieConnector", "sample_ssh_bruteforce_policy"]) 
