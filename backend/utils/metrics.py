"""Basic metrics helpers with optional Prometheus integration.

This module provides small helpers used across the codebase. It attempts
to import `prometheus_client` if available and falls back to no-op stubs
when not installed so callers don't need to guard imports.
"""
from typing import Optional
try:
    from prometheus_client import Counter, Gauge
    _PROM_AVAILABLE = True
except Exception:
    _PROM_AVAILABLE = False

_counters = {}  # name -> Counter
_gauges = {}

def increment(metric_name: str, value: int = 1, labels: Optional[dict] = None):
    """Increment a named counter. If Prometheus client is present this
    will create and increment a Counter, otherwise it's a no-op.
    """
    if not _PROM_AVAILABLE:
        return
    if metric_name not in _counters:
        # naive creation without label support; callers may extend this
        _counters[metric_name] = Counter(metric_name, f"Counter for {metric_name}")
    _counters[metric_name].inc(value)


def set_gauge(metric_name: str, value: float):
    """Set a gauge value (if prometheus available)."""
    if not _PROM_AVAILABLE:
        return
    if metric_name not in _gauges:
        _gauges[metric_name] = Gauge(metric_name, f"Gauge for {metric_name}")
    _gauges[metric_name].set(value)


def push_to_gateway(*_, **__):
    # placeholder for Pushgateway integration if needed
    return
