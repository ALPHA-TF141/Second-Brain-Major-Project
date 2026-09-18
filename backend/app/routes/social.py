import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.agents.social_ingestion_agent import social_agent
from app.auth.dependencies import get_current_user
from app.config import settings
from app.models.user import User

router = APIRouter(prefix="/api/social", tags=["social"])


class IngestUrlPayload(BaseModel):
    url: str
    user_notes: Optional[str] = ""


class ApiKeysPayload(BaseModel):
    apify_api_token: Optional[str] = None
    supadata_api_key: Optional[str] = None


@router.get("/status")
def get_social_status():
    """Returns configuration status for social media scrapers."""
    return {
        "status": "online",
        "services": social_agent.get_configured_services(),
        "apify_connected": bool(settings.apify_api_token),
        "supadata_connected": bool(settings.supadata_api_key),
    }


@router.post("/ingest-url")
async def ingest_url_endpoint(payload: IngestUrlPayload):
    """Ingests any YouTube video, Tweet, Instagram reel, or Web Article URL into the Second Brain."""
    try:
        result = await social_agent.ingest_url(payload.url, payload.user_notes or "")
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/keys")
def update_api_keys(payload: ApiKeysPayload):
    """Updates user's Apify & SupaData API keys in live settings and persists to .env."""
    if payload.apify_api_token is not None:
        settings.apify_api_token = payload.apify_api_token.strip()
    if payload.supadata_api_key is not None:
        settings.supadata_api_key = payload.supadata_api_key.strip()

    # Append or update .env file
    env_path = ".env"
    try:
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

        keys_set = {"apify_api_token": False, "supadata_api_key": False}
        new_lines = []
        for line in lines:
            if line.startswith("apify_api_token=") or line.startswith("APIFY_API_TOKEN="):
                new_lines.append(f"apify_api_token={settings.apify_api_token}\n")
                keys_set["apify_api_token"] = True
            elif line.startswith("supadata_api_key=") or line.startswith("SUPADATA_API_KEY="):
                new_lines.append(f"supadata_api_key={settings.supadata_api_key}\n")
                keys_set["supadata_api_key"] = True
            else:
                new_lines.append(line)

        if not keys_set["apify_api_token"]:
            new_lines.append(f"apify_api_token={settings.apify_api_token}\n")
        if not keys_set["supadata_api_key"]:
            new_lines.append(f"supadata_api_key={settings.supadata_api_key}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"[SocialRoutes] .env persistence notice: {e}")

    return {
        "status": "success",
        "apify_connected": bool(settings.apify_api_token),
        "supadata_connected": bool(settings.supadata_api_key),
    }
