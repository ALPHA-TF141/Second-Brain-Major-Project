from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class JSONMemoryCard(BaseModel):
    id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    domain: str = "Technology"  # Technology, Science, Geopolitics, Research, Coding, General
    priority: str = "medium"  # high, medium, low
    quality_score: float = 0.8
    app_source: str = ""
    window_title: str = ""
    topic: str = ""
    summary: str = ""
    key_pointers: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    source_url_or_ref: Optional[str] = None
    raw_ocr_excerpt: Optional[str] = None
    hero_image: Optional[str] = None  # Relative path to persistent hero screenshot in memory_vault/images/...
    hero_image_info_score: float = 0.0
