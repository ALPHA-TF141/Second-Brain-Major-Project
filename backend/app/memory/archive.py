from hashlib import sha1

from sqlalchemy.orm import Session

from app.models.capture import AppUsage, ClipboardLog, MemorySession, Screenshot
from app.models.memory import Memory, MemoryRelationship, MemoryTag, SearchIndex, SessionSummary
from app.models.ocr import DetectedTopic, SemanticChunk
from app.summarization.session_summarizer import SessionSummarizer
from app.tagging.tagger import MemoryTagger


class MemoryArchive:
    def __init__(self):
        self.tagger = MemoryTagger()
        self.summarizer = SessionSummarizer()

    def rebuild_all(self, db: Session):
        session_ids = [row.id for row in db.query(MemorySession.id).all()]
        total = 0
        for session_id in session_ids:
            total += self.rebuild_session(db, session_id)
        return {"sessions": len(session_ids), "memories": total}

    def rebuild_session(self, db: Session, session_id: int):
        chunks = db.query(SemanticChunk).filter(SemanticChunk.session_id == session_id).order_by(SemanticChunk.created_at.asc()).all()
        created = 0
        for chunk in chunks:
            if self._upsert_memory_from_chunk(db, chunk):
                created += 1

        self._upsert_clipboard_memories(db, session_id)
        self._rebuild_summary(db, session_id)
        self._rebuild_relationships(db, session_id)
        db.commit()
        return created

    def _upsert_memory_from_chunk(self, db: Session, chunk: SemanticChunk):
        content_hash = self._hash(chunk.content)
        existing = db.query(Memory).filter(Memory.content_hash == content_hash).first()
        if existing:
            return False

        category = self.tagger.category(chunk.content, chunk.source_type, chunk.app_source)
        memory = Memory(
            session_id=chunk.session_id,
            screenshot_id=chunk.screenshot_id,
            semantic_chunk_id=chunk.id,
            title=chunk.topic_label[:220],
            content=chunk.content,
            content_hash=content_hash,
            source_type=chunk.source_type,
            app_source=chunk.app_source,
            topic_label=chunk.topic_label,
            category=category,
            created_at=chunk.created_at,
        )
        db.add(memory)
        db.flush()
        self._add_tags_and_index(db, memory)
        return True

    def _upsert_clipboard_memories(self, db: Session, session_id: int):
        clips = db.query(ClipboardLog).filter(ClipboardLog.session_id == session_id).all()
        for clip in clips:
            if not clip.text_preview.strip():
                continue
            content = f"Clipboard: {clip.text_preview.strip()}"
            content_hash = self._hash(content)
            if db.query(Memory).filter(Memory.content_hash == content_hash).first():
                continue
            memory = Memory(
                session_id=session_id,
                title="Clipboard Capture",
                content=content,
                content_hash=content_hash,
                source_type="clipboard",
                app_source="clipboard",
                topic_label="Clipboard",
                category="research",
                created_at=clip.copied_at,
            )
            db.add(memory)
            db.flush()
            self._add_tags_and_index(db, memory)

    def _add_tags_and_index(self, db: Session, memory: Memory):
        tags = self.tagger.tag(memory.content, memory.topic_label, memory.source_type, memory.app_source)
        for tag in tags:
            db.add(MemoryTag(memory_id=memory.id, tag=tag))

        db.add(
            SearchIndex(
                memory_id=memory.id,
                session_id=memory.session_id,
                searchable_text=f"{memory.title} {memory.content} {memory.topic_label} {' '.join(tags)}",
                tags_text=", ".join(tags),
                app_source=memory.app_source,
                source_type=memory.source_type,
                topic_label=memory.topic_label,
                created_at=memory.created_at,
            )
        )

    def _rebuild_summary(self, db: Session, session_id: int):
        session = db.query(MemorySession).filter(MemorySession.id == session_id).first()
        if not session:
            return

        memories = db.query(Memory).filter(Memory.session_id == session_id).order_by(Memory.created_at.asc()).all()
        app_rows = db.query(AppUsage.app_name).filter(AppUsage.session_id == session_id).all()
        topic_rows = db.query(DetectedTopic.topic_label).filter(DetectedTopic.session_id == session_id).all()
        app_names = [name for name, _count in self._most_common([row[0] for row in app_rows])]
        topics = [name for name, _count in self._most_common([row[0] for row in topic_rows] + [memory.topic_label for memory in memories])]

        result = self.summarizer.summarize(session, memories, app_names, topics)
        summary = db.query(SessionSummary).filter(SessionSummary.session_id == session_id).first()
        if not summary:
            summary = SessionSummary(session_id=session_id)
            db.add(summary)

        summary.title = result["title"]
        summary.summary = result["summary"]
        summary.session_type = result["session_type"]
        summary.dominant_apps = ", ".join(app_names[:5])
        summary.detected_topics = ", ".join(topics[:8])
        summary.memory_count = len(memories)
        summary.screenshot_count = db.query(Screenshot).filter(Screenshot.session_id == session_id).count()
        summary.started_at = session.started_at
        summary.ended_at = session.ended_at

    def _rebuild_relationships(self, db: Session, session_id: int):
        """
        Build relationships within a session and also across related sessions.
        Relationships are based on:
        1. Same topic
        2. Same category 
        3. Same app/source
        4. Temporal proximity (adjacent in time)
        """
        memories = db.query(Memory).filter(Memory.session_id == session_id).order_by(Memory.created_at.asc()).all()
        
        # Clear existing relationships for this session's memories
        existing = db.query(MemoryRelationship).filter(
            MemoryRelationship.source_memory_id.in_([memory.id for memory in memories] or [0])
        )
        existing.delete(synchronize_session=False)

        # Build within-session relationships
        for index, memory in enumerate(memories):
            # Nearby memories in same session
            for other in memories[index + 1 : index + 4]:
                if memory.topic_label == other.topic_label:
                    db.add(MemoryRelationship(
                        source_memory_id=memory.id,
                        target_memory_id=other.id,
                        relationship_type="same_topic",
                        strength=85
                    ))
                elif memory.category == other.category:
                    db.add(MemoryRelationship(
                        source_memory_id=memory.id,
                        target_memory_id=other.id,
                        relationship_type="same_category",
                        strength=65
                    ))
                elif memory.app_source == other.app_source:
                    db.add(MemoryRelationship(
                        source_memory_id=memory.id,
                        target_memory_id=other.id,
                        relationship_type="same_app",
                        strength=55
                    ))
        
        # Build cross-session relationships (find recent memories with same topic/category)
        for memory in memories:
            # Find related memories from nearby sessions (last 24 hours)
            related = db.query(Memory).filter(
                Memory.id != memory.id,
                Memory.session_id != session_id,
                Memory.created_at >= (memory.created_at - __import__('datetime').timedelta(hours=24)),
                Memory.created_at <= (memory.created_at + __import__('datetime').timedelta(hours=24)),
            ).all()
            
            for other in related:
                strength = 0
                relationship_type = None
                
                if memory.topic_label == other.topic_label:
                    strength = 75
                    relationship_type = "same_topic_cross_session"
                elif memory.category == other.category:
                    strength = 50
                    relationship_type = "same_category_cross_session"
                
                if relationship_type and not db.query(MemoryRelationship).filter(
                    MemoryRelationship.source_memory_id == memory.id,
                    MemoryRelationship.target_memory_id == other.id
                ).first():
                    db.add(MemoryRelationship(
                        source_memory_id=memory.id,
                        target_memory_id=other.id,
                        relationship_type=relationship_type,
                        strength=strength
                    ))

    def _hash(self, content: str):
        return sha1(content.strip().lower().encode("utf-8", errors="ignore")).hexdigest()

    def _most_common(self, values: list[str]):
        values = [value for value in values if value]
        return Counter(values).most_common()


from collections import Counter

memory_archive = MemoryArchive()
