"""
User-authored memory CRUD.

Capture and ingest pipelines create memories automatically. This module lets
the user create, read, edit and delete a memory directly, with validation and
the same bookkeeping (content hash, tags, keyword index, session link) that the
automatic pipelines maintain, so a manual memory behaves like any other memory.

Deletion is delegated to `ForgettingService`:
  * soft delete (default) tombstones the memory and excludes it from retrieval,
  * hard delete purges the memory row and its tags/relationships/tombstones.
"""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.memory.archive import memory_archive
from app.models.capture import MemorySession
from app.models.memory import Memory, MemoryTag, SearchIndex
from app.models.research import ForgottenMemory

MAX_TITLE_CHARS = 220
MAX_CONTENT_CHARS = 20_000
MAX_TAGS = 20
MAX_TAG_CHARS = 100
MANUAL_SESSION_TYPE = "manual"


class MemoryValidationError(ValueError):
    """Input rejected before anything is written."""


class MemoryNotFoundError(LookupError):
    """No live (non-forgotten) memory has this id."""


class DuplicateMemoryError(Exception):
    """A memory with the same normalised content already exists."""

    def __init__(self, existing_id: int):
        super().__init__(f"Identical memory already exists (id {existing_id})")
        self.existing_id = existing_id


def _clean_text(value: Optional[str], field: str, max_chars: int, required: bool) -> str:
    text = (value or "").strip()
    if required and not text:
        raise MemoryValidationError(f"{field} must not be empty")
    if len(text) > max_chars:
        raise MemoryValidationError(f"{field} must be at most {max_chars} characters")
    return text


def _clean_tags(tags: Optional[Iterable[str]]) -> list[str]:
    cleaned: list[str] = []
    for raw in tags or []:
        tag = (raw or "").strip()
        if not tag:
            continue
        if len(tag) > MAX_TAG_CHARS:
            raise MemoryValidationError(f"each tag must be at most {MAX_TAG_CHARS} characters")
        if tag.lower() not in {t.lower() for t in cleaned}:
            cleaned.append(tag)
    if len(cleaned) > MAX_TAGS:
        raise MemoryValidationError(f"at most {MAX_TAGS} tags are allowed")
    return cleaned


def _content_hash(content: str) -> str:
    return memory_archive._hash(content)


def _live_query(db: Session):
    """Memories the user can still see: not tombstoned by forgetting."""
    forgotten = db.query(ForgottenMemory.memory_id)
    return db.query(Memory).filter(~Memory.id.in_(forgotten))


def _manual_session(db: Session, user_id: int) -> MemorySession:
    session = (
        db.query(MemorySession)
        .filter(MemorySession.user_id == user_id, MemorySession.session_type == MANUAL_SESSION_TYPE)
        .order_by(MemorySession.id.asc())
        .first()
    )
    if session is None:
        session = MemorySession(
            user_id=user_id,
            session_type=MANUAL_SESSION_TYPE,
            dominant_activity="user-authored",
            is_active=True,
            started_at=datetime.utcnow(),
        )
        db.add(session)
        db.flush()
    return session


def _write_index(db: Session, memory: Memory, tags: list[str]) -> None:
    """Replace this memory's tags and keyword-index row."""
    db.query(MemoryTag).filter(MemoryTag.memory_id == memory.id).delete(synchronize_session=False)
    db.query(SearchIndex).filter(SearchIndex.memory_id == memory.id).delete(synchronize_session=False)
    db.flush()
    for tag in tags:
        db.add(MemoryTag(memory_id=memory.id, tag=tag, source="user"))
    db.add(
        SearchIndex(
            memory_id=memory.id,
            session_id=memory.session_id,
            searchable_text=f"{memory.title} {memory.content} {memory.topic_label} {' '.join(tags)}",
            tags_text=", ".join(tags),
            app_source=memory.app_source or "",
            source_type=memory.source_type or "",
            topic_label=memory.topic_label or "",
            created_at=memory.created_at,
        )
    )


def _tags_for(db: Session, memory_id: int) -> list[str]:
    return [row.tag for row in db.query(MemoryTag).filter(MemoryTag.memory_id == memory_id).order_by(MemoryTag.id).all()]


def _commit(db: Session) -> None:
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise


def create_memory(
    db: Session,
    user_id: int,
    content: str,
    title: Optional[str] = None,
    topic_label: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[Iterable[str]] = None,
) -> Memory:
    content = _clean_text(content, "content", MAX_CONTENT_CHARS, required=True)
    title = _clean_text(title, "title", MAX_TITLE_CHARS, required=False) or content[:80]
    topic = _clean_text(topic_label, "topic_label", 160, required=False) or "General"
    category_value = _clean_text(category, "category", 80, required=False) or "note"
    tag_list = _clean_tags(tags)

    content_hash = _content_hash(content)
    existing = db.query(Memory).filter(Memory.content_hash == content_hash).first()
    if existing is not None:
        raise DuplicateMemoryError(existing.id)

    session = _manual_session(db, user_id)
    memory = Memory(
        session_id=session.id,
        title=title,
        content=content,
        content_hash=content_hash,
        source_type="manual",
        app_source="Second Brain",
        topic_label=topic,
        category=category_value,
        created_at=datetime.utcnow(),
    )
    db.add(memory)
    db.flush()
    _write_index(db, memory, tag_list)
    _commit(db)
    db.refresh(memory)
    return memory


def get_memory(db: Session, memory_id: int) -> Memory:
    memory = _live_query(db).filter(Memory.id == memory_id).first()
    if memory is None:
        raise MemoryNotFoundError(f"Memory {memory_id} not found")
    return memory


def list_memories(db: Session, limit: int = 50, offset: int = 0) -> list[Memory]:
    if limit < 1 or limit > 200:
        raise MemoryValidationError("limit must be between 1 and 200")
    if offset < 0:
        raise MemoryValidationError("offset must be >= 0")
    return (
        _live_query(db)
        .order_by(Memory.created_at.desc(), Memory.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


_UNSET = object()


def update_memory(
    db: Session,
    memory_id: int,
    content=_UNSET,
    title=_UNSET,
    topic_label=_UNSET,
    category=_UNSET,
    tags=_UNSET,
) -> Memory:
    memory = get_memory(db, memory_id)

    if content is not _UNSET:
        new_content = _clean_text(content, "content", MAX_CONTENT_CHARS, required=True)
        new_hash = _content_hash(new_content)
        clash = db.query(Memory).filter(Memory.content_hash == new_hash, Memory.id != memory.id).first()
        if clash is not None:
            raise DuplicateMemoryError(clash.id)
        # A title that was only derived from the old content (the default when
        # none was supplied) must follow the edit, or it keeps stale words that
        # keep matching search. A title the user chose is never touched here.
        if (memory.title or "") == (memory.content or "")[:80]:
            memory.title = new_content[:80]
        memory.content = new_content
        memory.content_hash = new_hash
    if title is not _UNSET:
        memory.title = _clean_text(title, "title", MAX_TITLE_CHARS, required=True)
    if topic_label is not _UNSET:
        memory.topic_label = _clean_text(topic_label, "topic_label", 160, required=False) or "General"
    if category is not _UNSET:
        memory.category = _clean_text(category, "category", 80, required=False) or "note"

    tag_list = _clean_tags(tags) if tags is not _UNSET else _tags_for(db, memory.id)
    try:
        db.flush()
        _write_index(db, memory, tag_list)
        _commit(db)
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(memory)
    return memory


def delete_memory(db: Session, memory_id: int, hard: bool = False) -> dict:
    """Delete (soft by default). Returns the forgetting service's audit summary."""
    from app.research.forgetting import forgetting_service

    get_memory(db, memory_id)  # 404 semantics for unknown or already-forgotten ids
    outcome = forgetting_service.forget(db, memory_id, reason="user_delete", hard=hard)
    if not outcome.get("forgotten"):
        raise MemoryNotFoundError(f"Memory {memory_id} not found")
    return outcome


def tags_for(db: Session, memory: Memory) -> list[str]:
    return _tags_for(db, memory.id)
