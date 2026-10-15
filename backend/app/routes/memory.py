from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.security import decode_token
from app.database.session import get_db
from app.memory.archive import memory_archive
from app.models.memory import Memory, MemoryRelationship, SessionSummary
from app.models.user import User
from app.schemas.memory import (
    MemoryCreate,
    MemoryDeleteResult,
    MemoryOut,
    MemoryUpdate,
    RelationshipOut,
    SessionSummaryOut,
)
from app.services import memory_crud
from app.services.memory_crud import DuplicateMemoryError, MemoryNotFoundError, MemoryValidationError
from app.search.memory_search import memory_search


router = APIRouter()


def attach_tags(db: Session, memories: list[Memory]):
    tags = memory_search.tags_for_memories(db, [memory.id for memory in memories])
    results = []
    for memory in memories:
        item = MemoryOut.model_validate(memory)
        item.tags = tags.get(memory.id, [])
        results.append(item)
    return results


@router.post("/rebuild")
def rebuild_archive(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return memory_archive.rebuild_all(db)


@router.post("/sessions/{session_id}/rebuild")
def rebuild_session(session_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return {"memories": memory_archive.rebuild_session(db, session_id)}


@router.get("/search", response_model=list[MemoryOut])
def search_memories(
    q: str = "",
    source_type: str = "",
    topic: str = "",
    app: str = "",
    session_id: int | None = None,
    date: str = "",
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    memories = memory_search.search(db, q, source_type, topic, app, session_id, date)
    return attach_tags(db, memories)


@router.get("/memories", response_model=list[MemoryOut])
def list_memories(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Live (not forgotten) memories, newest first."""
    try:
        memories = memory_crud.list_memories(db, limit=limit, offset=offset)
    except MemoryValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return attach_tags(db, memories)


@router.post("/memories", response_model=MemoryOut, status_code=201)
def create_memory(payload: MemoryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        memory = memory_crud.create_memory(
            db,
            user_id=user.id,
            content=payload.content,
            title=payload.title,
            topic_label=payload.topic_label,
            category=payload.category,
            tags=payload.tags,
        )
    except MemoryValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except DuplicateMemoryError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return attach_tags(db, [memory])[0]


@router.get("/memories/{memory_id}", response_model=MemoryOut)
def memory_detail(memory_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    try:
        memory = memory_crud.get_memory(db, memory_id)
    except MemoryNotFoundError:
        raise HTTPException(status_code=404, detail="Memory not found")
    return attach_tags(db, [memory])[0]


@router.put("/memories/{memory_id}", response_model=MemoryOut)
def update_memory(memory_id: int, payload: MemoryUpdate, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=422, detail="No fields to update")
    try:
        memory = memory_crud.update_memory(db, memory_id, **changes)
    except MemoryNotFoundError:
        raise HTTPException(status_code=404, detail="Memory not found")
    except MemoryValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except DuplicateMemoryError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return attach_tags(db, [memory])[0]


@router.delete("/memories/{memory_id}", response_model=MemoryDeleteResult)
def delete_memory(
    memory_id: int,
    hard: bool = Query(False, description="Purge the row and its derived data instead of tombstoning it."),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    try:
        outcome = memory_crud.delete_memory(db, memory_id, hard=hard)
    except MemoryNotFoundError:
        raise HTTPException(status_code=404, detail="Memory not found")
    return MemoryDeleteResult(
        forgotten=True,
        memory_id=memory_id,
        hard_delete=hard,
        enforcement_points=outcome.get("enforcement_points"),
        removed=outcome.get("removed", {}),
    )


@router.get("/memories/{memory_id}/relationships", response_model=list[RelationshipOut])
def memory_relationships(memory_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return (
        db.query(MemoryRelationship)
        .filter((MemoryRelationship.source_memory_id == memory_id) | (MemoryRelationship.target_memory_id == memory_id))
        .order_by(MemoryRelationship.strength.desc())
        .limit(20)
        .all()
    )


@router.get("/memories/{memory_id}/related", response_model=list[MemoryOut])
def memory_related(memory_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    """Get related memories based on topic, category, and app similarity."""
    related = memory_search.find_related_memories(db, memory_id, limit=15)
    if not related:
        raise HTTPException(status_code=404, detail="No related memories found")
    return attach_tags(db, related)


@router.get("/stats")
def memory_stats(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    """Get memory system statistics."""
    return memory_search.get_memory_stats(db)


@router.get("/sessions", response_model=list[SessionSummaryOut])
def memory_sessions(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return db.query(SessionSummary).order_by(SessionSummary.started_at.desc()).limit(50).all()


@router.get("/sessions/{session_id}", response_model=SessionSummaryOut)
def memory_session_detail(session_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    summary = db.query(SessionSummary).filter(SessionSummary.session_id == session_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Session summary not found")
    return summary


@router.get("/sessions/{session_id}/memories", response_model=list[MemoryOut])
def memories_for_session(session_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    memories = db.query(Memory).filter(Memory.session_id == session_id).order_by(Memory.created_at.asc()).all()
    return attach_tags(db, memories)


@router.get("/export/session/{session_id}")
def export_session(session_id: int, token: str = "", db: Session = Depends(get_db)):
    if not decode_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")

    summary = db.query(SessionSummary).filter(SessionSummary.session_id == session_id).first()
    memories = db.query(Memory).filter(Memory.session_id == session_id).order_by(Memory.created_at.asc()).all()
    if not summary and not memories:
        raise HTTPException(status_code=404, detail="Session not found")

    title = summary.title if summary else f"Session {session_id}"
    lines = [f"# {title}", ""]
    if summary:
        lines.extend([summary.summary, "", f"Type: {summary.session_type}", f"Apps: {summary.dominant_apps}", f"Topics: {summary.detected_topics}", ""])
    for memory in memories:
        lines.extend([f"## {memory.title}", f"- Time: {memory.created_at}", f"- Source: {memory.source_type} / {memory.app_source}", "", memory.content, ""])
    return Response("\n".join(lines), media_type="text/markdown", headers={"Content-Disposition": f'attachment; filename="session-{session_id}.md"'})
