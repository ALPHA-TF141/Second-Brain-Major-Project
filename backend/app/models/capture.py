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
