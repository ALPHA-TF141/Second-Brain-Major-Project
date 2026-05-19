from datetime import datetime

from pydantic import BaseModel


class SessionCreate(BaseModel):
    device_name: str = "desktop"


class SessionOut(BaseModel):
    id: int
    device_name: str
    is_active: bool
    created_at: datetime
    ended_at: datetime | None = None

    model_config = {"from_attributes": True}
