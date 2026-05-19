from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.security import decode_token
from app.database.session import get_db
from app.models.capture import ActivityLog, MemorySession, Screenshot
from app.models.user import User
from app.schemas.capture import ActivityLogOut, CaptureSessionOut, CaptureStartRequest, CaptureStatus, ScreenshotOut
from app.services.capture_service import capture_manager


router = APIRouter()


@router.post("/start", response_model=CaptureStatus)
async def start_capture(payload: CaptureStartRequest, user: User = Depends(get_current_user)):
    return await capture_manager.start(
        user_id=user.id,
        session_type=payload.session_type,
        screenshot_interval=payload.screenshot_interval_seconds,
        excluded_apps=payload.excluded_apps,
        watched_folders=payload.watched_folders,
    )


@router.post("/stop", response_model=CaptureStatus)
async def stop_capture(_user: User = Depends(get_current_user)):
    return await capture_manager.stop()


@router.post("/pause", response_model=CaptureStatus)
async def pause_capture(_user: User = Depends(get_current_user)):
    return await capture_manager.pause()


@router.post("/resume", response_model=CaptureStatus)
async def resume_capture(_user: User = Depends(get_current_user)):
    return await capture_manager.resume()


@router.get("/status", response_model=CaptureStatus)
def capture_status(_user: User = Depends(get_current_user)):
    return capture_manager.status()


@router.get("/sessions", response_model=list[CaptureSessionOut])
def list_capture_sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(MemorySession)
        .filter(MemorySession.user_id == user.id)
        .order_by(MemorySession.started_at.desc())
        .limit(20)
        .all()
    )


@router.get("/activity", response_model=list[ActivityLogOut])
def list_capture_activity(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    if not capture_manager.session_id:
        return []
    return (
        db.query(ActivityLog)
        .filter(ActivityLog.session_id == capture_manager.session_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(50)
        .all()
    )


@router.get("/screenshots", response_model=list[ScreenshotOut])
def list_screenshots(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    if not capture_manager.session_id:
        return []
    return (
        db.query(Screenshot)
        .filter(Screenshot.session_id == capture_manager.session_id)
        .order_by(Screenshot.captured_at.desc())
        .limit(12)
        .all()
    )


@router.get("/screenshots/{screenshot_id}/image")
def get_screenshot_image(screenshot_id: int, token: str = "", db: Session = Depends(get_db)):
    if not decode_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")

    screenshot = db.query(Screenshot).filter(Screenshot.id == screenshot_id).first()
    if not screenshot:
        raise HTTPException(status_code=404, detail="Screenshot not found")

    path = Path(screenshot.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Screenshot file missing")

    return FileResponse(path, media_type="image/jpeg")
