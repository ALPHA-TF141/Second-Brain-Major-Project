from datetime import datetime

from pydantic import BaseModel


class SettingUpdate(BaseModel):
    key: str
    value: str


class SettingOut(BaseModel):
    key: str
    value: str
    updated_at: datetime

    model_config = {"from_attributes": True}
