"""Compatibility shim: `tpm_wrapper` re-exports the newer `tpm_client` module.

Older modules imported `backend.core.vocalsoc.tpm_wrapper`. During refactors
the implementation moved to `tpm_client.py`. This file provides a small
backwards-compatible proxy so existing imports keep working and avoids
collection-time syntax errors.
"""

from .tpm_client import (
    get_tpm_client,
    SimpleTPMEmulator,
    Tpm2ToolsClient,
    PytssTPMClient,
)

__all__ = ["get_tpm_client", "SimpleTPMEmulator", "Tpm2ToolsClient", "PytssTPMClient"]
