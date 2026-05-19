from datetime import datetime

from pydantic import BaseModel


class MemoryOut(BaseModel):
    id: int
    session_id: int
    screenshot_id: int | None = None
    title: str
    content: str
    source_type: str
    app_source: str
    topic_label: str
    category: str
    created_at: datetime
    tags: list[str] = []

    model_config = {"from_attributes": True}


class SessionSummaryOut(BaseModel):
    id: int
    session_id: int
    title: str
    summary: str
    session_type: str
    dominant_apps: str
    detected_topics: str
    memory_count: int
    screenshot_count: int
    started_at: datetime | None = None
    ended_at: datetime | None = None

    model_config = {"from_attributes": True}


class RelationshipOut(BaseModel):
    id: int
    source_memory_id: int
    target_memory_id: int
    relationship_type: str
    strength: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TimelineGroup(BaseModel):
    label: str
    memories: list[MemoryOut]
