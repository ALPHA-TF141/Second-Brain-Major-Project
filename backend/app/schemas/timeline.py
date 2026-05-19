from datetime import datetime

from pydantic import BaseModel


class TimelineEventCreate(BaseModel):
    title: str
    description: str = ""
    event_type: str = "system"


class TimelineEventOut(TimelineEventCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
