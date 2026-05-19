from datetime import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    conversation_id: int | None = None
    mode: str = "summary"


class ConversationOut(BaseModel):
    id: int
    title: str
    mode: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RetrievedMemoryOut(BaseModel):
    id: int
    conversation_id: int
    message_id: int | None = None
    memory_id: int
    score: str
    reason: str
    created_at: datetime

    model_config = {"from_attributes": True}
