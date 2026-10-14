import asyncio
from datetime import datetime

from sqlalchemy.orm import Session

from app.capture.screenshot_service import ScreenshotService
from app.database.session import SessionLocal
from app.models.capture import MemorySession, Screenshot
from app.websocket.manager import manager


class CaptureManager:
    """
    Screen-capture pipeline: periodic screenshots -> OCR -> memories.

    Activity tracking (window/clipboard/file logs) was removed together with
    the features built on it; the capture pipeline keeps exactly the path the
    research layer consumes: screenshot rows feeding the OCR worker.
    """

    def __init__(self):
        self.is_active = False
        self.is_paused = False
        self.session_id = None
        self.user_id = None
        self.session_type = "study"
        self.started_at = None
        self.screenshot_interval = 5
        self.excluded_apps = []
        self.current_app = ""
        self.current_title = ""
        self.screenshot_count = 0
        self._task = None
        self._screenshot_service = ScreenshotService()

    async def start(self, user_id: int, session_type: str, screenshot_interval: int, excluded_apps: list[str], watched_folders: list[str]):
        if self.is_active:
            return self.status()

        db = SessionLocal()
        try:
            session = MemorySession(user_id=user_id, session_type=session_type, is_active=True)
            db.add(session)
            db.commit()
            db.refresh(session)
            self.session_id = session.id
        finally:
            db.close()

        self.user_id = user_id
        self.session_type = session_type
        self.started_at = datetime.utcnow()
        self.screenshot_interval = max(3, screenshot_interval)
        self.excluded_apps = excluded_apps
        self.screenshot_count = 0
        self.is_active = True
        self.is_paused = False
        self._task = asyncio.create_task(self._run())
        await self._broadcast("capture_status", self.status())
        return self.status()

    async def stop(self):
        if not self.is_active:
            return self.status()

        self.is_active = False
        self.is_paused = False
        if self._task:
            self._task.cancel()

        db = SessionLocal()
        try:
            session = db.query(MemorySession).filter(MemorySession.id == self.session_id).first()
            if session:
                session.is_active = False
                session.ended_at = datetime.utcnow()
                session.dominant_activity = self._dominant_activity(db)
                db.commit()
        finally:
            db.close()

        await self._broadcast("capture_status", self.status())
        return self.status()

    async def pause(self):
        self.is_paused = True
        await self._broadcast("capture_status", self.status())
        return self.status()

    async def resume(self):
        self.is_paused = False
        await self._broadcast("capture_status", self.status())
        return self.status()

    def status(self):
        return {
            "is_active": self.is_active,
            "is_paused": self.is_paused,
            "session_id": self.session_id,
            "session_type": self.session_type if self.session_id else None,
            "started_at": self.started_at,
            "current_app": self.current_app,
            "current_title": self.current_title,
            "screenshot_count": self.screenshot_count,
        }

    async def _run(self):
        last_screenshot_at = 0.0

        while self.is_active:
            if self.is_paused:
                await asyncio.sleep(1)
                continue

            now = asyncio.get_event_loop().time()
            if now - last_screenshot_at >= self.screenshot_interval:
                await self._capture_screenshot()
                last_screenshot_at = now

            await asyncio.sleep(1)

    async def _capture_screenshot(self):
        result = await asyncio.to_thread(self._screenshot_service.capture, self.session_id)
        if not result:
            return

        db = SessionLocal()
        try:
            screenshot = Screenshot(session_id=self.session_id, **result)
            db.add(screenshot)
            db.commit()
            db.refresh(screenshot)
            self.screenshot_count += 1
            payload = {
                "id": screenshot.id,
                "url": f"/api/capture/screenshots/{screenshot.id}/image",
                "captured_at": screenshot.captured_at.isoformat(),
            }
        finally:
            db.close()

        await self._broadcast("screenshot", payload)
        await self._queue_ocr(screenshot.id)

    def _dominant_activity(self, db: Session):
        return ""

    async def _broadcast(self, event_type: str, data: dict):
        await manager.broadcast({"type": event_type, "data": data, "timestamp": datetime.utcnow().isoformat()})

    async def _queue_ocr(self, screenshot_id: int):
        try:
            from app.services.ocr_service import ocr_processor

            await ocr_processor.enqueue_screenshot(screenshot_id)
        except Exception:
            pass


capture_manager = CaptureManager()
