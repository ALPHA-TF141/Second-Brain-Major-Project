from datetime import datetime

from pydantic import BaseModel


class CaptureStartRequest(BaseModel):
    session_type: str = "study"
    screenshot_interval_seconds: int = 5
    watched_folders: list[str] = []
    excluded_apps: list[str] = ["password", "1password", "bitwarden", "keepass", "authenticator"]


class CaptureStatus(BaseModel):
    is_active: bool
    is_paused: bool
    session_id: int | None = None
    session_type: str | None = None
    started_at: datetime | None = None
    current_app: str = ""
    current_title: str = ""
    screenshot_count: int = 0


class CaptureSessionOut(BaseModel):
    id: int
    session_type: str
    dominant_activity: str
    is_active: bool
    started_at: datetime
    ended_at: datetime | None = None

    model_config = {"from_attributes": True}


class ScreenshotOut(BaseModel):
    id: int
    file_path: str
    width: int
    height: int
    captured_at: datetime

    model_config = {"from_attributes": True}


class ActivityLogOut(BaseModel):
    id: int
    activity_type: str
    title: str
    details: str
    created_at: datetime

    model_config = {"from_attributes": True}
