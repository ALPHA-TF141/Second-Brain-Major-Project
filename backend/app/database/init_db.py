from app.auth.security import hash_password
from app.config import settings
from app.database.session import Base, SessionLocal, engine
from app.models.activity import Activity
from app.models.capture import ActivityLog, AppUsage, ClipboardLog, MemorySession, Screenshot
from app.models.conversation import AIFeedback, AISummary, Conversation, ConversationContext, Message, RetrievedMemory
from app.models.graph import ConceptCluster, GraphEdge, GraphMetadata, GraphNode, LearningProgression, TopicRelationship
from app.models.memory import Memory, MemoryRelationship, MemoryTag, SearchIndex, SessionSummary
from app.models.ocr import DetectedTopic, ExtractedText, OCRMetadata, ProcessedSession, SemanticChunk
from app.models.semantic import EmbeddingJob, MemoryCluster, SearchHistory, SemanticRelationship, VectorMemory
from app.models.research import (
    ForgottenMemory,
    KnowledgeGap,
    MemoryConflict,
    MemoryConsolidation,
    MemoryScore,
    ResearchRun,
    TemporalFact,
)
from app.models.session import UserSession
from app.models.setting import Setting
from app.models.timeline_event import TimelineEvent
from app.models.connector import ConnectorCredential
from app.models.user import User
from app.models.voice import ConversationAudio, LanguagePreference, Transcript, VoiceCommand, VoiceSession


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

        # Seed & ensure all app connectors are permanently stored in SQLite DB and live
        default_connectors = [
            {
                "service_key": "gmail_imap",
                "service_name": "Gmail Autonomous Sync",
                "account_identifier": "immanuellourdu@gmail.com",
                "category": "mail",
                "status": "connected",
                "is_live": True,
                "config_metadata": '{"folders": ["INBOX"], "interval_minutes": 10, "provider": "IMAP / SSL"}',
            },
            {
                "service_key": "calendar_ical",
                "service_name": "Google Calendar Feed",
                "account_identifier": "College & Research Schedule",
                "category": "calendar",
                "status": "connected",
                "is_live": True,
                "config_metadata": '{"sync_mode": "iCal live", "auto_refresh": true}',
            },
            {
                "service_key": "ollama_local",
                "service_name": "Local Qwen 2.5 on RTX 3050",
                "account_identifier": "http://localhost:11434 (qwen2.5:3b)",
                "category": "ai",
                "status": "connected",
                "is_live": True,
                "config_metadata": '{"model": "qwen2.5:3b", "latency_ms": 180, "hardware": "NVIDIA RTX 3050"}',
            },
            {
                "service_key": "github_vault",
                "service_name": "GitHub Vault Autonomous Sync",
                "account_identifier": "ALPHA-TF141/Second-Brain",
                "category": "code",
                "status": "connected",
                "is_live": True,
                "config_metadata": '{"auto_sync_interval": "60s", "storage_bloat": "0.0 MB"}',
            },
            {
                "service_key": "deep_research_web",
                "service_name": "Deep Research Synthesizer",
                "account_identifier": "Autonomous Multi-Hop Engine",
                "category": "search",
                "status": "connected",
                "is_live": True,
                "config_metadata": '{"sources": ["Knowledge Graph", "ArXiv", "Master Wiki", "Web Search"]}',
            },
            {
                "service_key": "notion_vault",
                "service_name": "Obsidian & Neo4j Graph Vault",
                "account_identifier": "memory_vault/wiki + Neo4j",
                "category": "knowledge",
                "status": "connected",
                "is_live": True,
                "config_metadata": '{"format": "Bidirectional Markdown", "status": "Synced"}',
            },
        ]

        for conn_data in default_connectors:
            existing = db.query(ConnectorCredential).filter(
                ConnectorCredential.user_id == user.id,
                ConnectorCredential.service_key == conn_data["service_key"]
            ).first()
            if not existing:
                db.add(ConnectorCredential(
                    user_id=user.id,
                    service_key=conn_data["service_key"],
                    service_name=conn_data["service_name"],
                    account_identifier=conn_data["account_identifier"],
                    category=conn_data["category"],
                    status=conn_data["status"],
                    is_live=conn_data["is_live"],
                    config_metadata=conn_data["config_metadata"],
                ))
            else:
                existing.is_live = True
                existing.status = "connected"

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
    "ConversationAudio",
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
    "Transcript",
    "User",
    "LanguagePreference",
    "VoiceCommand",
    "VoiceSession",
    "init_database",
]
