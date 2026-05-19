from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.session import Base


class ExtractedText(Base):
    __tablename__ = "extracted_text"

    id = Column(Integer, primary_key=True, index=True)
    screenshot_id = Column(Integer, ForeignKey("screenshots.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("memory_sessions.id"), nullable=False)
    app_source = Column(String(160), default="")
    source_type = Column(String(80), default="screen")
    raw_text = Column(Text, default="")
    clean_text = Column(Text, default="")
    language = Column(String(80), default="eng+tam")
    created_at = Column(DateTime, default=datetime.utcnow)

    chunks = relationship("SemanticChunk", back_populates="extracted_text")


class SemanticChunk(Base):
    __tablename__ = "semantic_chunks"

    id = Column(Integer, primary_key=True, index=True)
    extracted_text_id = Column(Integer, ForeignKey("extracted_text.id"), nullable=False)
    screenshot_id = Column(Integer, ForeignKey("screenshots.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("memory_sessions.id"), nullable=False)
    content = Column(Text, nullable=False)
    topic_label = Column(String(160), default="General")
    source_type = Column(String(80), default="screen")
    app_source = Column(String(160), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    extracted_text = relationship("ExtractedText", back_populates="chunks")


class DetectedTopic(Base):
    __tablename__ = "detected_topics"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("memory_sessions.id"), nullable=False)
    topic_label = Column(String(160), nullable=False)
    keywords = Column(Text, default="")
    confidence = Column(Integer, default=50)
    created_at = Column(DateTime, default=datetime.utcnow)


class OCRMetadata(Base):
    __tablename__ = "ocr_metadata"

    id = Column(Integer, primary_key=True, index=True)
    screenshot_id = Column(Integer, ForeignKey("screenshots.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("memory_sessions.id"), nullable=False)
    engine = Column(String(80), default="tesseract")
    status = Column(String(80), default="queued")
    language = Column(String(80), default="eng+tam")
    quality_score = Column(Integer, default=0)
    error_message = Column(Text, default="")
    processed_at = Column(DateTime, default=datetime.utcnow)


class ProcessedSession(Base):
    __tablename__ = "processed_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("memory_sessions.id"), unique=True, nullable=False)
    title = Column(String(200), default="Untitled Session")
    summary = Column(Text, default="")
    source_mix = Column(String(200), default="")
    chunk_count = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
