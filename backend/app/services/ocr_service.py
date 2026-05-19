import asyncio
from collections import Counter
from datetime import datetime

from sqlalchemy.orm import Session

from app.chunking.semantic_chunker import SemanticChunker
from app.database.session import SessionLocal
from app.extraction.text_cleaner import TextCleaner
from app.metadata.metadata_extractor import MetadataExtractor
from app.models.capture import AppUsage, MemorySession, Screenshot
from app.models.ocr import DetectedTopic, ExtractedText, OCRMetadata, ProcessedSession, SemanticChunk
from app.ocr.ocr_engine import OCREngine
from app.preprocessing.image_preprocessor import ImagePreprocessor
from app.websocket.manager import manager


class OCRProcessor:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.worker_task = None
        self.is_running = False
        self.last_error = ""
        self.preprocessor = ImagePreprocessor()
        self.engine = OCREngine()
        self.cleaner = TextCleaner()
        self.chunker = SemanticChunker()
        self.metadata = MetadataExtractor()

    def start_worker(self):
        if self.worker_task:
            return
        self.is_running = True
        self.worker_task = asyncio.create_task(self._worker())

    async def enqueue_screenshot(self, screenshot_id: int):
        await self.queue.put(screenshot_id)
        await self._broadcast("ocr_status", self.status())

    def status(self):
        return {
            "is_running": self.is_running,
            "queued": self.queue.qsize(),
            "last_error": self.last_error,
        }

    async def process_screenshot_now(self, screenshot_id: int):
        return await asyncio.to_thread(self._process_screenshot, screenshot_id)

    async def process_session(self, session_id: int):
        db = SessionLocal()
        try:
            screenshot_ids = [
                row.id
                for row in db.query(Screenshot.id).filter(Screenshot.session_id == session_id).order_by(Screenshot.captured_at.asc()).all()
            ]
        finally:
            db.close()

        for screenshot_id in screenshot_ids:
            await self.enqueue_screenshot(screenshot_id)
        return {"queued": len(screenshot_ids)}

    async def queue_unprocessed(self):
        db = SessionLocal()
        try:
            processed_ids = {row.screenshot_id for row in db.query(OCRMetadata.screenshot_id).all()}
            screenshot_ids = [row.id for row in db.query(Screenshot.id).order_by(Screenshot.captured_at.asc()).all() if row.id not in processed_ids]
        finally:
            db.close()

        for screenshot_id in screenshot_ids:
            await self.enqueue_screenshot(screenshot_id)
        return {"queued": len(screenshot_ids)}

    async def _worker(self):
        while True:
            screenshot_id = await self.queue.get()
            try:
                await self.process_screenshot_now(screenshot_id)
            except Exception as exc:
                self.last_error = str(exc)
            finally:
                self.queue.task_done()
                await self._broadcast("ocr_status", self.status())

    def _process_screenshot(self, screenshot_id: int):
        db = SessionLocal()
        try:
            existing = db.query(OCRMetadata).filter(
                OCRMetadata.screenshot_id == screenshot_id,
                OCRMetadata.status == "completed",
            ).first()
            if existing:
                return {"status": "already_processed", "screenshot_id": screenshot_id}

            screenshot = db.query(Screenshot).filter(Screenshot.id == screenshot_id).first()
            if not screenshot:
                return {"status": "missing", "screenshot_id": screenshot_id}

            app_source = self._latest_app_source(db, screenshot.session_id)
            prepared = self.preprocessor.prepare_for_ocr(screenshot.file_path)
            result = self.engine.extract_text(prepared, language="eng+tam")
            clean_text = self.cleaner.clean(result["text"])
            quality = self.metadata.quality_score(clean_text)

            extracted = ExtractedText(
                screenshot_id=screenshot.id,
                session_id=screenshot.session_id,
                app_source=app_source,
                source_type=self._source_type_from_app(app_source),
                raw_text=result["text"],
                clean_text=clean_text,
                language=result["language"],
            )
            db.add(extracted)
            db.flush()

            chunks = self.chunker.chunk(clean_text)
            for chunk in chunks:
                db.add(
                    SemanticChunk(
                        extracted_text_id=extracted.id,
                        screenshot_id=screenshot.id,
                        session_id=screenshot.session_id,
                        content=chunk["content"],
                        topic_label=chunk["topic_label"],
                        source_type=chunk["source_type"],
                        app_source=app_source,
                    )
                )

            keywords = self.metadata.extract_keywords(clean_text)
            if keywords:
                db.add(
                    DetectedTopic(
                        session_id=screenshot.session_id,
                        topic_label=chunks[0]["topic_label"] if chunks else keywords[0].title(),
                        keywords=", ".join(keywords),
                        confidence=quality,
                    )
                )

            db.add(
                OCRMetadata(
                    screenshot_id=screenshot.id,
                    session_id=screenshot.session_id,
                    engine=result["engine"],
                    status="completed" if clean_text else "empty",
                    language=result["language"],
                    quality_score=quality,
                )
            )
            self._refresh_processed_session(db, screenshot.session_id)
            db.commit()
            self._refresh_memory_archive(screenshot.session_id)
            return {"status": "completed", "screenshot_id": screenshot_id, "chunks": len(chunks)}
        except Exception as exc:
            db.rollback()
            self._store_error(db, screenshot_id, str(exc))
            raise
        finally:
            db.close()

    def _store_error(self, db: Session, screenshot_id: int, message: str):
        screenshot = db.query(Screenshot).filter(Screenshot.id == screenshot_id).first()
        if not screenshot:
            return
        db.add(
            OCRMetadata(
                screenshot_id=screenshot_id,
                session_id=screenshot.session_id,
                status="failed",
                error_message=message[:1000],
            )
        )
        db.commit()

    def _latest_app_source(self, db: Session, session_id: int):
        usage = db.query(AppUsage).filter(AppUsage.session_id == session_id).order_by(AppUsage.started_at.desc()).first()
        return usage.app_name if usage else "unknown"

    def _source_type_from_app(self, app_name: str):
        lowered = app_name.lower()
        if any(name in lowered for name in ["chrome", "edge", "firefox", "brave"]):
            return "browser"
        if any(name in lowered for name in ["code", "pycharm", "idea"]):
            return "code"
        if any(name in lowered for name in ["pdf", "acrobat"]):
            return "document"
        return "screen"

    def _refresh_processed_session(self, db: Session, session_id: int):
        chunks = db.query(SemanticChunk).filter(SemanticChunk.session_id == session_id).all()
        if not chunks:
            return

        source_counts = Counter(chunk.source_type for chunk in chunks)
        topic_counts = Counter(chunk.topic_label for chunk in chunks)
        title = topic_counts.most_common(1)[0][0]
        summary = self._build_summary(chunks)

        processed = db.query(ProcessedSession).filter(ProcessedSession.session_id == session_id).first()
        if not processed:
            processed = ProcessedSession(session_id=session_id)
            db.add(processed)

        processed.title = title
        processed.summary = summary
        processed.source_mix = ", ".join(f"{name}:{count}" for name, count in source_counts.most_common())
        processed.chunk_count = len(chunks)
        processed.updated_at = datetime.utcnow()

    def _build_summary(self, chunks: list[SemanticChunk]):
        labels = []
        for chunk in chunks[:5]:
            if chunk.topic_label not in labels:
                labels.append(chunk.topic_label)
        return "Captured learning material around " + ", ".join(labels) if labels else "Processed screen knowledge."

    async def _broadcast(self, event_type: str, data: dict):
        await manager.broadcast({"type": event_type, "data": data, "timestamp": datetime.utcnow().isoformat()})

    def _refresh_memory_archive(self, session_id: int):
        db = SessionLocal()
        try:
            from app.memory.archive import memory_archive

            memory_archive.rebuild_session(db, session_id)
        finally:
            db.close()


ocr_processor = OCRProcessor()
