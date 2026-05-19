from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.ocr import DetectedTopic, ExtractedText, ProcessedSession, SemanticChunk
from app.models.user import User
from app.schemas.ocr import DetectedTopicOut, ExtractedTextOut, OCRStatus, ProcessedSessionOut, SemanticChunkOut
from app.services.ocr_service import ocr_processor


router = APIRouter()


@router.get("/status", response_model=OCRStatus)
def get_ocr_status(_user: User = Depends(get_current_user)):
    return ocr_processor.status()


@router.post("/screenshots/{screenshot_id}/process")
async def process_screenshot(screenshot_id: int, _user: User = Depends(get_current_user)):
    return await ocr_processor.process_screenshot_now(screenshot_id)


@router.post("/sessions/{session_id}/process")
async def process_session(session_id: int, _user: User = Depends(get_current_user)):
    return await ocr_processor.process_session(session_id)


@router.post("/queue-unprocessed")
async def queue_unprocessed(_user: User = Depends(get_current_user)):
    return await ocr_processor.queue_unprocessed()


@router.get("/texts", response_model=list[ExtractedTextOut])
def list_extracted_text(
    q: str = "",
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(ExtractedText).order_by(ExtractedText.created_at.desc())
    if q:
        query = query.filter(or_(ExtractedText.clean_text.contains(q), ExtractedText.app_source.contains(q)))
    return query.limit(50).all()


@router.get("/chunks", response_model=list[SemanticChunkOut])
def list_chunks(
    q: str = "",
    source_type: str = "",
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(SemanticChunk).order_by(SemanticChunk.created_at.desc())
    if q:
        query = query.filter(or_(SemanticChunk.content.contains(q), SemanticChunk.topic_label.contains(q)))
    if source_type:
        query = query.filter(SemanticChunk.source_type == source_type)
    return query.limit(80).all()


@router.get("/topics", response_model=list[DetectedTopicOut])
def list_topics(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return db.query(DetectedTopic).order_by(DetectedTopic.created_at.desc()).limit(40).all()


@router.get("/sessions", response_model=list[ProcessedSessionOut])
def list_processed_sessions(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return db.query(ProcessedSession).order_by(ProcessedSession.updated_at.desc()).limit(20).all()
