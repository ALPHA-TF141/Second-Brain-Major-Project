from datetime import datetime

from pydantic import BaseModel, Field

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


class MemoryCreate(BaseModel):
    content: str = Field(..., description="The fact, note or event to remember.")
    title: str | None = Field(default=None, max_length=220)
    topic_label: str | None = Field(default=None, max_length=160)
    category: str | None = Field(default=None, max_length=80)
    tags: list[str] = Field(default_factory=list, max_length=20)


class MemoryUpdate(BaseModel):
    """Partial update. Omitted fields are left unchanged."""

    content: str | None = None
    title: str | None = Field(default=None, max_length=220)
    topic_label: str | None = Field(default=None, max_length=160)
    category: str | None = Field(default=None, max_length=80)
    tags: list[str] | None = Field(default=None, max_length=20)


class MemoryDeleteResult(BaseModel):
    forgotten: bool
    memory_id: int
    hard_delete: bool
    enforcement_points: int | None = None
    removed: dict = Field(default_factory=dict)
