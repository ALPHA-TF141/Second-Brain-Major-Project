from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint

from app.database.session import Base


class Memory(Base):
    __tablename__ = "memories"
    __table_args__ = (
        UniqueConstraint("content_hash", name="uq_memory_content_hash"),
        Index("ix_memories_created_source", "created_at", "source_type"),
    )

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("memory_sessions.id"), nullable=False, index=True)
    screenshot_id = Column(Integer, ForeignKey("screenshots.id"), nullable=True, index=True)
    semantic_chunk_id = Column(Integer, ForeignKey("semantic_chunks.id"), nullable=True, index=True)
    title = Column(String(220), default="Memory")
    content = Column(Text, nullable=False)
    content_hash = Column(String(80), nullable=False, index=True)
    source_type = Column(String(80), default="screen", index=True)
    app_source = Column(String(160), default="", index=True)
    topic_label = Column(String(160), default="General", index=True)
    category = Column(String(80), default="learning", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MemoryTag(Base):
    __tablename__ = "memory_tags"
    __table_args__ = (UniqueConstraint("memory_id", "tag", name="uq_memory_tag"),)

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("memories.id"), nullable=False, index=True)
    tag = Column(String(100), nullable=False, index=True)
    source = Column(String(80), default="auto")
    created_at = Column(DateTime, default=datetime.utcnow)


class SessionSummary(Base):
    __tablename__ = "session_summaries"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("memory_sessions.id"), unique=True, nullable=False, index=True)
    title = Column(String(220), default="Untitled Session")
    summary = Column(Text, default="")
    session_type = Column(String(80), default="learning")
    dominant_apps = Column(Text, default="")
    detected_topics = Column(Text, default="")
    memory_count = Column(Integer, default=0)
    screenshot_count = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=True, index=True)
    ended_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MemoryRelationship(Base):
    __tablename__ = "memory_relationships"

    id = Column(Integer, primary_key=True, index=True)
    source_memory_id = Column(Integer, ForeignKey("memories.id"), nullable=False, index=True)
    target_memory_id = Column(Integer, ForeignKey("memories.id"), nullable=False, index=True)
    relationship_type = Column(String(80), default="related_topic")
    strength = Column(Integer, default=50)
    created_at = Column(DateTime, default=datetime.utcnow)


class SearchIndex(Base):
    __tablename__ = "search_index"
    __table_args__ = (UniqueConstraint("memory_id", name="uq_search_memory"),)

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("memories.id"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("memory_sessions.id"), nullable=False, index=True)
    searchable_text = Column(Text, nullable=False)
    tags_text = Column(Text, default="")
    app_source = Column(String(160), default="", index=True)
    source_type = Column(String(80), default="screen", index=True)
    topic_label = Column(String(160), default="", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
