from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.database.session import Base


class VoiceSession(Base):
    __tablename__ = "voice_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True, index=True)
    mode = Column(String(80), default="continuous")
    language = Column(String(40), default="mixed")
    status = Column(String(80), default="active")
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    voice_session_id = Column(Integer, ForeignKey("voice_sessions.id"), nullable=False, index=True)
    speaker = Column(String(40), default="user")
    text = Column(Text, nullable=False)
    language = Column(String(40), default="mixed")
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class VoiceCommand(Base):
    __tablename__ = "voice_commands"

    id = Column(Integer, primary_key=True, index=True)
    voice_session_id = Column(Integer, ForeignKey("voice_sessions.id"), nullable=False, index=True)
    command_text = Column(Text, nullable=False)
    intent = Column(String(120), default="ask_memory")
    status = Column(String(80), default="handled")
    result = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class ConversationAudio(Base):
    __tablename__ = "conversation_audio"

    id = Column(Integer, primary_key=True, index=True)
    voice_session_id = Column(Integer, ForeignKey("voice_sessions.id"), nullable=False, index=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id"), nullable=True, index=True)
    file_path = Column(String(500), default="")
    direction = Column(String(40), default="input")
    duration_seconds = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class LanguagePreference(Base):
    __tablename__ = "language_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    preferred_language = Column(String(40), default="mixed")
    reply_language = Column(String(40), default="auto")
    wake_words = Column(Text, default="Second Brain,Hey Brain")
    voice_speed = Column(Float, default=1.0)
    microphone_name = Column(String(200), default="")
    voice_model = Column(String(200), default="default")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
