"""
Hands-free routes: wake word + proactive voice.
===========================================================================
  GET  /api/proactive/status          is the wake word listening? how is voice policy set?
  POST /api/proactive/wake/test       simulate a detection (proves the whole chain)
  POST /api/proactive/announce        make Jarvis say something now
  GET  /api/proactive/history         everything it has said, and what it skipped
  POST /api/proactive/pause           silence proactively, without disabling the feature
  POST /api/proactive/resume
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.agents.proactive_voice import proactive_voice
from app.auth.dependencies import get_current_user
from app.integrations.wake_word import wake_word_listener
from app.models.user import User

router = APIRouter(prefix="/api/proactive", tags=["proactive"])


class AnnouncePayload(BaseModel):
    text: str
    priority: Optional[str] = "high"
    source: Optional[str] = "manual"
    force: Optional[bool] = True


@router.get("/status")
def proactive_status(_user: User = Depends(get_current_user)):
    return {
        "wake_word": wake_word_listener.status(),
        "voice": proactive_voice.status(),
    }


@router.post("/wake/test")
async def wake_test(_user: User = Depends(get_current_user)):
    """
    Fire the wake event exactly as a real detection would.

    This exists so "does the whole chain work?" can be answered without shouting
    at your laptop - it exercises the same broadcaster the detector uses.
    """
    from app.services.wake_service import trigger_wake

    result = await trigger_wake(source="wake_word_test")
    return {"success": True, **result}


@router.post("/announce")
def announce(payload: AnnouncePayload, _user: User = Depends(get_current_user)):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Nothing to say.")
    record = proactive_voice.announce(
        payload.text,
        priority=payload.priority or "high",
        source=payload.source or "manual",
        force=bool(payload.force),
    )
    return record


@router.get("/history")
def history(limit: int = 50):
    return proactive_voice.history[: max(1, min(limit, 200))]


@router.post("/pause")
def pause():
    proactive_voice.enabled = False
    proactive_voice.paused_reason = f"paused at {datetime.utcnow().isoformat()}"
    return {"paused": True}


@router.post("/resume")
def resume():
    proactive_voice.enabled = True
    proactive_voice.paused_reason = ""
    return {"paused": False}
