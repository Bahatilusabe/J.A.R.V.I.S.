"""Platform detection helpers for Atlas 500 Edge cluster and HiSilicon devices.

This module provides pragmatic runtime checks that try to detect whether the
current host is an Atlas 500 Edge node (Ascend/Atlas) or a HiSilicon-based
device. Detection uses a combination of environment variables (preferred
for containerized environments), common filesystem markers (Ascend SDK
install locations) and /proc/cpuinfo heuristics.

Use `is_atlas()` and `is_hisilicon()` in hardware integration code to guard
platform-specific code paths. For CI/development you can override using
`ATLAS_EDGE=1` or `HISILICON_DEVICE=1` environment variables.
"""

from __future__ import annotations

import os
import pathlib
import logging

logger = logging.getLogger("jarvis.platform_detector")


def _check_env(var: str) -> bool:
    return os.environ.get(var, "").lower() in ("1", "true", "yes")


def is_atlas() -> bool:
    """Return True if we heuristically detect an Atlas/Ascend environment.

    Checks (in order):
    - ATLAS_EDGE env var override
    - ASCEND_HOME or presence of /usr/local/Ascend
    - 'Ascend' or 'Atlas' string present in /proc/device-tree/model or /proc/cpuinfo
    """
    if _check_env("ATLAS_EDGE"):
        return True

    if os.environ.get("ASCEND_HOME"):
        return True

    if pathlib.Path("/usr/local/Ascend").exists() or pathlib.Path("/usr/local/atlas").exists():
        return True

    # /proc/device-tree/model exists on some ARM devices
    try:
        for path in ("/proc/device-tree/model", "/proc/cpuinfo"):
            p = pathlib.Path(path)
            if p.exists():
                text = p.read_text(errors="ignore").lower()
                if "ascend" in text or "atlas" in text or "kunpeng" in text:
                    return True
    except Exception:
        pass

    return False


def is_hisilicon() -> bool:
    """Return True when running on HiSilicon/HiAI hardware.

    Checks (in order):
    - HISILICON_DEVICE env var override
    - presence of common HiSilicon library paths
    - 'hisilicon' or 'hi6220' strings in /proc/cpuinfo
    """
    if _check_env("HISILICON_DEVICE"):
        return True

    # Common HiSilicon install paths
    if pathlib.Path("/usr/lib/hisilicon").exists() or pathlib.Path("/usr/lib/hiacc").exists():
        return True

    try:
        p = pathlib.Path("/proc/cpuinfo")
        if p.exists():
            text = p.read_text(errors="ignore").lower()
            if "hisilicon" in text or "hi6220" in text or "hihope" in text:
                return True
    except Exception:
        pass

    return False


def detect_platform() -> str:
    """Return a string: 'atlas', 'hisilicon', or 'unknown'."""
    if is_atlas():
        return "atlas"
    if is_hisilicon():
        return "hisilicon"
    return "unknown"


def require_platform(allowed: list[str]) -> None:
    """Raise RuntimeError if current platform is not in allowed list.

    Use sparingly; prefer soft checks + informative logging. The env
    variable `ALLOW_PLATFORM_MISMATCH=1` will disable enforcement for
    development/testing.
    """
    if os.environ.get("ALLOW_PLATFORM_MISMATCH", "").lower() in ("1", "true", "yes"):
        logger.warning("Platform mismatch enforcement disabled by ALLOW_PLATFORM_MISMATCH")
        return
    plat = detect_platform()
    if plat not in allowed:
        raise RuntimeError(f"Unsupported platform: {plat}. Expected one of: {allowed}")
