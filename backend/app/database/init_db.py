from app.auth.security import hash_password
from app.config import settings
from app.database.session import Base, SessionLocal, engine
from app.models.activity import Activity
from app.models.capture import ActivityLog, AppUsage, ClipboardLog, MemorySession, Screenshot
from app.models.conversation import AIFeedback, AISummary, Conversation, ConversationContext, Message, RetrievedMemory
from app.models.memory import Memory, MemoryRelationship, MemoryTag, SearchIndex, SessionSummary
from app.models.ocr import DetectedTopic, ExtractedText, OCRMetadata, ProcessedSession, SemanticChunk
from app.models.semantic import EmbeddingJob, MemoryCluster, SearchHistory, SemanticRelationship, VectorMemory
from app.models.session import UserSession
from app.models.setting import Setting
from app.models.timeline_event import TimelineEvent
from app.models.user import User


def init_database():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == settings.demo_username).first()
        if not user:
            user = User(
                username=settings.demo_username,
                password_hash=hash_password(settings.demo_password),
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        if not db.query(Setting).filter(Setting.user_id == user.id).first():
            db.add_all(
                [
                    Setting(user_id=user.id, key="theme", value="dark"),
                    Setting(user_id=user.id, key="language", value="en"),
                    Setting(user_id=user.id, key="assistant_name", value="Second Brain"),
                ]
            )

        if not db.query(TimelineEvent).filter(TimelineEvent.user_id == user.id).first():
            db.add(
                TimelineEvent(
                    user_id=user.id,
                    title="Backend initialized",
                    description="SQLite database and demo user are ready.",
                    event_type="system",
                )
            )

        db.commit()
    finally:
        db.close()


__all__ = [
    "Activity",
    "ActivityLog",
    "AIFeedback",
    "AISummary",
    "AppUsage",
    "ClipboardLog",
    "Conversation",
    "ConversationContext",
    "DetectedTopic",
    "EmbeddingJob",
    "ExtractedText",
    "Memory",
    "MemoryCluster",
    "MemoryRelationship",
    "MemorySession",
    "MemoryTag",
    "Message",
    "OCRMetadata",
    "ProcessedSession",
    "RetrievedMemory",
    "SearchIndex",
    "SearchHistory",
    "SemanticRelationship",
    "Screenshot",
    "SemanticChunk",
    "SessionSummary",
    "VectorMemory",
    "UserSession",
    "Setting",
    "TimelineEvent",
    "User",
    "init_database",
]
