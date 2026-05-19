from datetime import datetime

from pydantic import BaseModel


class ActivityCreate(BaseModel):
    title: str
    description: str = ""
    activity_type: str = "general"


class ActivityOut(ActivityCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
