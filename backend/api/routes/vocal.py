from fastapi import APIRouter, HTTPException
from typing import Any, Dict, Optional
import os
import logging
import base64
import json
import asyncio

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

router = APIRouter()


class MindSporeASRClient:
    """Guarded MindSpore Speech SDK + ASR API client with REST fallback.

    Tries to use a local MindSpore Speech SDK if available, otherwise a
    REST endpoint if `VOCAL_ASR_REST_URL` is set. If neither is available,
    falling back to requiring textual input.
    """

    def __init__(self):
        self._impl = None
        self._rest_url = os.environ.get("VOCAL_ASR_REST_URL")
        self._api_key = os.environ.get("VOCAL_ASR_API_KEY")

        # Try common MindSpore speech SDK imports
        try:
            import mindspore_speech  # type: ignore

            # expect a recognizer factory or client
            recognizer = None
            try:
                recognizer = mindspore_speech.Recognizer()
            except Exception:
                try:
                    # alternative naming
                    recognizer = mindspore_speech.AsrClient()
                except Exception:
                    recognizer = None
            if recognizer is not None:
                self._impl = ("ms_sdk", recognizer)
                logger.info("Vocal: using MindSpore Speech SDK recognizer")
        except Exception:
            self._impl = None

        # REST fallback
        if self._impl is None and self._rest_url:
            try:
                import requests  # type: ignore

                self._impl = ("rest", requests.Session())
                logger.info("Vocal: using REST ASR endpoint %s", self._rest_url)
            except Exception:
                logger.exception("Vocal: requests not available; REST ASR disabled")

    def transcribe(self, audio_bytes: bytes, fmt: Optional[str] = None) -> Dict[str, Any]:
        """Return dict {text, confidence}.

        Synchronous call — some SDKs are blocking; callers may run in executor.
        """
        if self._impl is None:
            return {"text": "", "confidence": 0.0, "model": "none"}

        kind, impl = self._impl
        if kind == "ms_sdk":
            recog = impl
            for method_name in ("recognize", "transcribe", "infer", "predict"):
                fn = getattr(recog, method_name, None)
                if fn:
                    try:
                        res = fn(audio_bytes)
                        # res may be str or dict
                        if isinstance(res, str):
                            return {"text": res, "confidence": 0.9, "model": "mindspore"}
                        if isinstance(res, dict):
                            return {"text": res.get("text", ""), "confidence": res.get("confidence", 0.0), "model": "mindspore"}
                    except Exception:
                        logger.exception("Vocal: MindSpore recognizer.%s failed", method_name)
            raise RuntimeError("Vocal: MindSpore SDK present but no usable recognizer method")

        if kind == "rest":
            sess = impl
            try:
                url = self._rest_url.rstrip("/") + "/asr"
                headers = {"Content-Type": "application/json"}
                if self._api_key:
                    headers["Authorization"] = f"Bearer {self._api_key}"
                payload = {"audio_b64": base64.b64encode(audio_bytes).decode("ascii")}
                r = sess.post(url, json=payload, headers=headers, timeout=10)
                r.raise_for_status()
                return r.json()
            except Exception:
                logger.exception("Vocal: REST ASR call failed")
                return {"text": "", "confidence": 0.0, "model": "rest_error"}

        return {"text": "", "confidence": 0.0, "model": "unknown"}


# module-level client (lazy init)
_asr_client: Optional[MindSporeASRClient] = None


def init_asr():
    global _asr_client
    if _asr_client is None:
        _asr_client = MindSporeASRClient()


async def close_asr():
    return


def _intent_classifier(text: str) -> Dict[str, Any]:
    # simple keyword-based classifier as a fallback
    t = text.lower() if text else ""
    keywords = {
        "attack": "attack_alert",
        "intrusion": "attack_alert",
        "malware": "malware_alert",
        "block": "action_block",
        "allow": "action_allow",
        "status": "query_status",
        "help": "request_help",
    }
    for k, intent in keywords.items():
        if k in t:
            # confidence heuristic
            conf = min(0.95, 0.5 + 0.1 * t.count(k))
            return {"intent": intent, "confidence": conf}
    # default
    return {"intent": "unknown", "confidence": 0.0}


@router.post("/intent")
async def intent(payload: dict):
    """Accepts either:
    - {"audio_b64": "...", "format": "wav"}
    - {"text": "..."}

    Transcribes audio via MindSpore Speech SDK or REST ASR and returns an intent.
    """
    global _asr_client
    text = payload.get("text")
    audio_b64 = payload.get("audio_b64")
    fmt = payload.get("format")

    if audio_b64 and not text:
        try:
            audio_bytes = base64.b64decode(audio_b64.encode())
        except Exception:
            raise HTTPException(status_code=400, detail="invalid base64 audio")

        if _asr_client is None:
            init_asr()

        loop = asyncio.get_running_loop()
        try:
            res = await loop.run_in_executor(None, lambda: _asr_client.transcribe(audio_bytes, fmt))
            text = res.get("text", "")
            asr_conf = res.get("confidence", 0.0)
        except Exception:
            logger.exception("Vocal: ASR transcription failed")
            text = ""
            asr_conf = 0.0

    if not text:
        # fallback: require text input
        if not payload.get("text"):
            raise HTTPException(status_code=400, detail="no audio or text provided")
        text = payload.get("text", "")
        asr_conf = 1.0

    intent_res = _intent_classifier(text)
    return {"ok": True, "text": text, "asr_confidence": asr_conf, "intent": intent_res}


@router.get("/health")
async def health():
    global _asr_client
    if _asr_client is None:
        init_asr()
    available = _asr_client._impl is not None if _asr_client else False
    return {"ok": True, "asr_available": available}


@router.post("/auth")
async def auth(payload: dict):
    """Verify a speaker audio sample against an enrolled user.

    Expected payload:
    - {"audio_b64": "...", "format": "wav", "user_id": "alice"}
    """
    audio_b64 = payload.get("audio_b64")
    user_id = payload.get("user_id")
    if not audio_b64 or not user_id:
        raise HTTPException(status_code=400, detail="audio_b64 and user_id are required")
    try:
        audio_bytes = base64.b64decode(audio_b64.encode())
    except Exception:
        raise HTTPException(status_code=400, detail="invalid base64 audio")

    # perform verification using VoiceAuthenticator
    try:
        from backend.core.vocalsoc.voice_auth import VoiceAuthenticator

        authn = VoiceAuthenticator(dry_run=True)
        res = authn.verify(user_id, audio_bytes)
        return {"ok": True, "matched": res.get("matched", False), "score": res.get("score", 0.0), "reason": res.get("reason", "")}
    except Exception as e:
        logger.exception("Voice auth error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enroll")
async def enroll(payload: dict):
    """Enroll a user with provided WAV audio bytes.

    Expected payload:
    - {"user_id": "alice", "audio_b64": "...", "format": "wav"}
    """
    user_id = payload.get("user_id")
    audio_b64 = payload.get("audio_b64")
    if not user_id or not audio_b64:
        raise HTTPException(status_code=400, detail="user_id and audio_b64 required")
    try:
        audio_bytes = base64.b64decode(audio_b64.encode())
    except Exception:
        raise HTTPException(status_code=400, detail="invalid base64 audio")

    try:
        from backend.core.vocalsoc.voice_auth import VoiceAuthenticator

        authn = VoiceAuthenticator(dry_run=True)
        meta = authn.enroll(user_id, audio_bytes)
        return {"ok": True, "meta": meta}
    except Exception as e:
        logger.exception("Enroll error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
