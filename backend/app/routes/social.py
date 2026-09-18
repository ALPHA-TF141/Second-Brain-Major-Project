import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict

from app.agents.social_ingestion_agent import native_social_scraper
from app.auth.dependencies import get_current_user
from app.config import settings

router = APIRouter(prefix="/api/social", tags=["social"])


class IngestUrlPayload(BaseModel):
    url: str
    user_notes: Optional[str] = ""


class ConnectAccountPayload(BaseModel):
    platform: str  # 'instagram' | 'twitter' | 'youtube'
    username: Optional[str] = ""
    session_data: Optional[Dict] = None


@router.get("/status")
def get_social_status():
    """Returns status of 100% free, native social media scraper engine."""
    return native_social_scraper.get_status()


@router.post("/ingest-url")
async def ingest_url_endpoint(payload: IngestUrlPayload):
    """Ingests any YouTube video, Tweet, Instagram reel, or Web Article URL with ZERO paid API fees."""
    try:
        result = await native_social_scraper.ingest_url(payload.url, payload.user_notes or "")
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/connect-account")
def connect_account_endpoint(payload: ConnectAccountPayload):
    """Saves user's own account credentials / session cookies 100% locally on PC."""
    data = payload.session_data or {"username": payload.username}
    success = native_social_scraper.save_account_session(payload.platform, data)
    return {
        "status": "connected" if success else "failed",
        "platform": payload.platform,
        "storage": "100% local on-device (Zero cloud transfer)"
    }
