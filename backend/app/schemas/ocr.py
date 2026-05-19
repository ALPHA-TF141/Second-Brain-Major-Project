from datetime import datetime

from pydantic import BaseModel


class OCRStatus(BaseModel):
    is_running: bool
    queued: int
    last_error: str = ""


class ExtractedTextOut(BaseModel):
    id: int
    screenshot_id: int
    session_id: int
    app_source: str
    source_type: str
    clean_text: str
    language: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SemanticChunkOut(BaseModel):
    id: int
    screenshot_id: int
    session_id: int
    content: str
    topic_label: str
    source_type: str
    app_source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DetectedTopicOut(BaseModel):
    id: int
    session_id: int
    topic_label: str
    keywords: str
    confidence: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ProcessedSessionOut(BaseModel):
    id: int
    session_id: int
    title: str
    summary: str
    source_mix: str
    chunk_count: int
    updated_at: datetime

    model_config = {"from_attributes": True}
