from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.session import Base


class MemorySession(Base):
    __tablename__ = "memory_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_type = Column(String(80), default="study")
    dominant_activity = Column(String(160), default="")
    is_active = Column(Boolean, default=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    screenshots = relationship("Screenshot", back_populates="session")
    activity_logs = relationship("ActivityLog", back_populates="session")
    app_usage = relationship("AppUsage", back_populates="session")
    clipboard_logs = relationship("ClipboardLog", back_populates="session")


class Screenshot(Base):
    __tablename__ = "screenshots"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("memory_sessions.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    image_hash = Column(String(80), index=True, nullable=False)
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    captured_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("MemorySession", back_populates="screenshots")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("memory_sessions.id"), nullable=False)
    activity_type = Column(String(80), default="general")
    title = Column(String(200), nullable=False)
    details = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("MemorySession", back_populates="activity_logs")


class AppUsage(Base):
    __tablename__ = "app_usage"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("memory_sessions.id"), nullable=False)
    app_name = Column(String(160), default="")
    window_title = Column(String(500), default="")
    is_browser = Column(Boolean, default=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0)

    session = relationship("MemorySession", back_populates="app_usage")


class ClipboardLog(Base):
    __tablename__ = "clipboard_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("memory_sessions.id"), nullable=False)
    text_preview = Column(Text, default="")
    text_hash = Column(String(80), index=True, nullable=False)
    copied_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("MemorySession", back_populates="clipboard_logs")
