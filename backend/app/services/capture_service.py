import asyncio
from collections import Counter
from datetime import datetime

from sqlalchemy.orm import Session

from app.capture.screenshot_service import ScreenshotService
from app.database.session import SessionLocal
from app.models.capture import ActivityLog, AppUsage, ClipboardLog, MemorySession, Screenshot
from app.tracking.clipboard_tracker import ClipboardTracker
from app.tracking.file_tracker import FileTracker
from app.tracking.window_tracker import WindowTracker
from app.websocket.manager import manager


class CaptureManager:
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
        self._window_tracker = WindowTracker()
        self._clipboard_tracker = ClipboardTracker()
        self._file_tracker = FileTracker(self._record_file_event)

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
        self._file_tracker.start(watched_folders)
        self._task = asyncio.create_task(self._run())
        await self._broadcast("capture_status", self.status())
        return self.status()

    async def stop(self):
        if not self.is_active:
            return self.status()

        self.is_active = False
        self.is_paused = False
        self._file_tracker.stop()
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

            await self._track_window()
            await self._track_clipboard()

            now = asyncio.get_event_loop().time()
            if now - last_screenshot_at >= self.screenshot_interval:
                await self._capture_screenshot()
                last_screenshot_at = now

            await asyncio.sleep(1)

    async def _track_window(self):
        active = self._window_tracker.get_active_window()
        app_name = active["app_name"]
        title = active["window_title"]

        if self._window_tracker.is_excluded(app_name, title, self.excluded_apps):
            app_name = "excluded"
            title = "Hidden by privacy rule"

        if app_name == self.current_app and title == self.current_title:
            return

        db = SessionLocal()
        try:
            previous = (
                db.query(AppUsage)
                .filter(AppUsage.session_id == self.session_id, AppUsage.ended_at == None)
                .order_by(AppUsage.started_at.desc())
                .first()
            )
            if previous:
                previous.ended_at = datetime.utcnow()
                previous.duration_seconds = int((previous.ended_at - previous.started_at).total_seconds())

            usage = AppUsage(
                session_id=self.session_id,
                app_name=app_name,
                window_title=title,
                is_browser=active["is_browser"],
            )
            db.add(usage)
            db.add(ActivityLog(session_id=self.session_id, activity_type="window", title=app_name, details=title))
            db.commit()
        finally:
            db.close()

        self.current_app = app_name
        self.current_title = title
        await self._broadcast("active_window", {"app_name": app_name, "window_title": title, "is_browser": active["is_browser"]})

    async def _track_clipboard(self):
        change = self._clipboard_tracker.read_change()
        if not change:
            return

        db = SessionLocal()
        try:
            db.add(ClipboardLog(session_id=self.session_id, **change))
            db.add(ActivityLog(session_id=self.session_id, activity_type="clipboard", title="Clipboard copied", details=change["text_preview"]))
            db.commit()
        finally:
            db.close()

        await self._broadcast("clipboard", {"preview": change["text_preview"]})

    async def _capture_screenshot(self):
        result = await asyncio.to_thread(self._screenshot_service.capture, self.session_id)
        if not result:
            return

        db = SessionLocal()
        try:
            screenshot = Screenshot(session_id=self.session_id, **result)
            db.add(screenshot)
            db.add(ActivityLog(session_id=self.session_id, activity_type="screenshot", title="Screenshot captured", details=result["file_path"]))
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

    def _record_file_event(self, event_type: str, file_path: str):
        if not self.is_active or self.is_paused or not self.session_id:
            return

        db = SessionLocal()
        try:
            db.add(ActivityLog(session_id=self.session_id, activity_type=event_type, title=event_type.replace("_", " ").title(), details=file_path))
            db.commit()
        finally:
            db.close()

    def _dominant_activity(self, db: Session):
        rows = db.query(AppUsage.app_name).filter(AppUsage.session_id == self.session_id).all()
        if not rows:
            return ""
        return Counter(row[0] for row in rows).most_common(1)[0][0]

    async def _broadcast(self, event_type: str, data: dict):
        await manager.broadcast({"type": event_type, "data": data, "timestamp": datetime.utcnow().isoformat()})

    async def _queue_ocr(self, screenshot_id: int):
        try:
            from app.services.ocr_service import ocr_processor

            await ocr_processor.enqueue_screenshot(screenshot_id)
        except Exception:
            pass


capture_manager = CaptureManager()
