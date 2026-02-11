"""NLU processor for Voice-Activated SOC (Vocalsoc).

This module provides a gated wrapper around Rasa and MindFormers for
intent parsing and entity extraction. Both heavy dependencies are optional
and the module falls back to a small rule-based parser so it can run in
CI and developer environments without large installs.

Public functions:
- train_rasa_model(data_path, output_path, dry_run=True)
- load_rasa_interpreter(model_path) -> Optional[object]
- parse_intent(text, interpreter=None) -> Dict[str, Any]

The parse result is a simple dict:
{
  "text": original_text,
  "intent": {"name": str, "confidence": float},
  "entities": [{"entity": name, "value": str, "start": int, "end": int}, ...]
}
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable

logger = logging.getLogger("jarvis.vocalsoc.nlu")

# Try to import Rasa and MindFormers; keep imports optional so tests don't
# require heavy installs. We only use them if available and the user opts to.
# simple caches for loaded models/pipelines
_rasa_available = False
_mindformers_available = False
_rasa_interpreter_cache: Dict[str, Any] = {}
_mf_pipeline_cache: Dict[str, Any] = {}
try:
    import rasa  # type: ignore
    from rasa.nlu.model import Interpreter  # type: ignore

    _rasa_available = True
except Exception:
    rasa = None  # type: ignore
    Interpreter = None  # type: ignore

try:
    import mindformers  # type: ignore

    _mindformers_available = True
except Exception:
    mindformers = None  # type: ignore


def train_rasa_model(data_path: str, output_path: str, dry_run: bool = True) -> Optional[str]:
    """Train a Rasa NLU model from training data.

    This is a convenience wrapper. When `dry_run` is True the function
    will only log the intended action and return the path where a model
    would be written. If Rasa is not available and dry_run is False it
    raises RuntimeError.
    """
    logger.info("train_rasa_model dry_run=%s data=%s -> out=%s", dry_run, data_path, output_path)
    if dry_run:
        return output_path

    if not _rasa_available:
        raise RuntimeError("Rasa is not available in this environment; cannot train model")

    # Real training code would go here; keep the API stable for callers.
    # We intentionally avoid implementing a full Rasa training flow in the
    # repository to keep CI lightweight.
    raise NotImplementedError("Training via Rasa is not implemented in this wrapper; use dry_run or provide a pre-trained model")


def load_rasa_interpreter(model_path: str) -> Optional[Any]:
    """Load a Rasa `Interpreter` from `model_path` if Rasa is available.

    Returns the interpreter object or None when unavailable.
    """
    if not _rasa_available:
        logger.debug("Rasa not available; cannot load interpreter %s", model_path)
        return None

    try:
        # Rasa provides utilities to load models; for unit tests we won't
        # invoke this path unless the SDK is present.
        if model_path in _rasa_interpreter_cache:
            return _rasa_interpreter_cache[model_path]
        interpreter = Interpreter.load(model_path)  # type: ignore
        _rasa_interpreter_cache[model_path] = interpreter
        logger.info("Loaded Rasa interpreter from %s", model_path)
        return interpreter
    except Exception as e:
        logger.warning("Failed to load Rasa interpreter %s: %s", model_path, e)
        return None


def _rule_based_parse(text: str) -> Dict[str, Any]:
    """Simple, fast fallback intent and entity parser used when heavy deps are missing.

    This uses regex heuristics to recognise a small set of SOC-related intents.
    """
    t = text.strip()
    intent = {"name": "unknown", "confidence": 0.0}
    entities: List[Dict[str, Any]] = []

    # Lowercase for matching
    l = t.lower()

    # Intent heuristics
    if re.search(r"\b(open|connect|start)\b.*\b(vpn|vpn connection)\b", l):
        intent = {"name": "open_vpn", "confidence": 0.9}
    elif re.search(r"\b(close|disconnect|stop)\b.*\b(vpn)\b", l):
        intent = {"name": "close_vpn", "confidence": 0.9}
    elif re.search(r"\b(verify|check|status)\b.*\b(node|vpn|connection)\b", l):
        intent = {"name": "check_status", "confidence": 0.85}
    elif re.search(r"\b(deploy|start)\b.*\b(sensor|agent)\b", l):
        intent = {"name": "deploy_agent", "confidence": 0.8}
    elif re.search(r"\b(list|show)\b.*\b(nodes|agents|connections)\b", l):
        intent = {"name": "list_resources", "confidence": 0.8}

    # Simple entity extraction: look for numeric node ids and IPs
    for m in re.finditer(r"\bnode\s*(?:id\s*)?(\d+)\b", l):
        entities.append({"entity": "node_id", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    for m in re.finditer(r"(\b\d{1,3}(?:\.\d{1,3}){3}\b)", l):
        entities.append({"entity": "ip_address", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    # CIDR-style network matches
    for m in re.finditer(r"(\b\d{1,3}(?:\.\d{1,3}){3}/\d{1,2}\b)", l):
        entities.append({"entity": "network", "value": m.group(1), "start": m.start(1), "end": m.end(1)})

    # Put together the response
    return {"text": t, "intent": intent, "entities": entities}


@dataclass
class ParseResult:
    text: str
    intent: Dict[str, Any]
    entities: List[Dict[str, Any]]


def _normalize_mf_entities(mf_output: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
    """Normalize a MindFormers-like output into our entity dict shape.

    Expected input items may contain keys like 'entity', 'start', 'end', 'word'.
    This function is permissive to allow tests to pass a simple fake pipeline.
    """
    out: List[Dict[str, Any]] = []
    for item in mf_output:
        ent = {}
        ent_name = item.get("entity") or item.get("label") or item.get("type")
        ent_text = item.get("word") or item.get("value")
        start = item.get("start")
        end = item.get("end")
        # if start/end missing, try to locate the entity text in the utterance
        if (start is None or end is None) and ent_text:
            idx = text.lower().find(str(ent_text).lower())
            if idx >= 0:
                start = idx
                end = idx + len(str(ent_text))

        ent["entity"] = ent_name
        ent["value"] = ent_text
        ent["start"] = start
        ent["end"] = end
        out.append(ent)
    return out


def parse_intent(text: str, interpreter: Optional[Any] = None, mf_pipeline: Optional[Callable[[str], List[Dict[str, Any]]]] = None) -> ParseResult:
    """Parse a user utterance and return intent + entities.

    If a `rasa` interpreter is provided and available it will be used. If
    not, the function falls back to a rule-based parser that is fast and
    dependency-free (suitable for unit tests and CI).
    """
    # 1) If Rasa interpreter present, use it
    if interpreter is not None and _rasa_available:
        try:
            res = interpreter.parse(text)  # type: ignore
            # Map into our stable shape
            intent = {"name": res.get("intent", {}).get("name"), "confidence": res.get("intent", {}).get("confidence", 0.0)}
            entities = []
            for e in res.get("entities", []):
                entities.append({"entity": e.get("entity"), "value": e.get("value"), "start": e.get("start"), "end": e.get("end")})
            # If MF pipeline provided, merge its entities too
            if mf_pipeline:
                try:
                    mf_out = mf_pipeline(text)
                    mf_entities = _normalize_mf_entities(mf_out, text)
                    # merge unique by span
                    spans = {(ent.get("start"), ent.get("end")) for ent in entities}
                    for me in mf_entities:
                        span = (me.get("start"), me.get("end"))
                        if span not in spans:
                            entities.append(me)
                            spans.add(span)
                except Exception:
                    logger.debug("MindFormers pipeline failed during parse; ignoring")

            return ParseResult(text=text, intent=intent, entities=entities)
        except Exception as e:  # pragma: no cover - only if Rasa is available and fails
            logger.warning("Rasa interpreter failed to parse text; falling back: %s", e)

    # 2) Use MindFormers pipeline if explicitly provided or available
    entities: List[Dict[str, Any]] = []
    if mf_pipeline is not None:
        try:
            mf_out = mf_pipeline(text)
            entities = _normalize_mf_entities(mf_out, text)
        except Exception:
            logger.warning("Provided MindFormers pipeline failed; falling back to rules")

    elif _mindformers_available:
        # If a MindFormers pipeline is available system-wide we would
        # instantiate and run it here. For now we only log that it's
        # available to avoid unexpected side effects in CI.
        logger.debug("MindFormers available in environment but no pipeline provided; falling back to rules")

    # 3) Always compute rule-based entities and heuristics and merge
    rule = _rule_based_parse(text)
    # Merge entities, preferring MF-detected spans when present
    existing_spans = {(e.get("start"), e.get("end")) for e in entities}
    for e in rule["entities"]:
        span = (e.get("start"), e.get("end"))
        if span not in existing_spans:
            entities.append(e)

    # Heuristic intent: prefer rule's intent if MF/Rasa didn't set one
    intent = rule["intent"]
    return ParseResult(text=text, intent=intent, entities=entities)


def cli_parse():
    """Simple CLI helper for quick manual testing of parse_intent()."""
    import argparse

    p = argparse.ArgumentParser("Vocalsoc NLU parse helper")
    p.add_argument("text", help="Utterance to parse")
    p.add_argument("--rasa-model", help="Optional Rasa model path to load and use")
    args = p.parse_args()

    interpreter = None
    if args.rasa_model:
        interpreter = load_rasa_interpreter(args.rasa_model)

    out = parse_intent(args.text, interpreter=interpreter)
    print(out)


if __name__ == "__main__":
    cli_parse()
