from datetime import datetime

from pydantic import BaseModel


class SemanticSearchRequest(BaseModel):
    query: str
    limit: int = 8
    source_type: str = ""
    session_id: int | None = None


class SemanticMemoryResult(BaseModel):
    memory_id: int
    title: str
    content: str
    source_type: str
    app_source: str
    topic_label: str
    session_id: int
    screenshot_id: int | None = None
    score: float
    semantic_score: float = 0.0
    created_at: datetime


class EmbeddingJobOut(BaseModel):
    id: int
    memory_id: int | None = None
    job_type: str
    status: str
    error_message: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None

    model_config = {"from_attributes": True}


class MemoryClusterOut(BaseModel):
    id: int
    label: str
    description: str
    memory_ids: str
    size: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SearchHistoryOut(BaseModel):
    id: int
    query: str
    search_type: str
    result_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
