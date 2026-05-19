from datetime import datetime

from pydantic import BaseModel


class VoiceSessionStart(BaseModel):
    mode: str = "continuous"
    language: str = "mixed"
    conversation_id: int | None = None


class VoiceSessionOut(BaseModel):
    id: int
    conversation_id: int | None = None
    mode: str
    language: str
    status: str
    started_at: datetime
    ended_at: datetime | None = None

    model_config = {"from_attributes": True}


class TranscriptOut(BaseModel):
    id: int
    voice_session_id: int
    speaker: str
    text: str
    language: str
    confidence: float
    created_at: datetime

    model_config = {"from_attributes": True}


class LanguagePreferenceUpdate(BaseModel):
    preferred_language: str = "mixed"
    reply_language: str = "auto"
    wake_words: str = "Second Brain,Hey Brain"
    voice_speed: float = 1.0
    microphone_name: str = ""
    voice_model: str = "default"


class LanguagePreferenceOut(LanguagePreferenceUpdate):
    id: int
    user_id: int
    updated_at: datetime

    model_config = {"from_attributes": True}
