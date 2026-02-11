"""PASM package exports for simple access in tests and scripts.

This file keeps exports minimal and avoids heavy imports at package
import-time.
"""
from __future__ import annotations

from .model import get_mindspore_model, FallbackModel
from .infer import PASMTGNNPredictor
from .train_pasm_tgnn import train_and_export

__all__ = ["get_mindspore_model", "FallbackModel", "PASMTGNNPredictor", "train_and_export"]
