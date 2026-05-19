from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.clustering.clusterer import memory_clusterer
from app.database.session import get_db
from app.models.semantic import EmbeddingJob, MemoryCluster, SearchHistory, VectorMemory
from app.models.user import User
from app.schemas.semantic import EmbeddingJobOut, MemoryClusterOut, SearchHistoryOut, SemanticMemoryResult, SemanticSearchRequest
from app.semantic_search.search_engine import semantic_search_engine
from app.workers.embedding_worker import embedding_worker


router = APIRouter()


def serialize_results(results: list[dict]):
    serialized = []
    for item in results:
        memory = item["memory"]
        serialized.append(
            SemanticMemoryResult(
                memory_id=memory.id,
                title=memory.title,
                content=memory.content,
                source_type=memory.source_type,
                app_source=memory.app_source,
                topic_label=memory.topic_label,
                session_id=memory.session_id,
                screenshot_id=memory.screenshot_id,
                score=round(float(item["score"]), 4),
                semantic_score=round(float(item.get("semantic_score", 0.0)), 4),
                created_at=memory.created_at,
            )
        )
    return serialized


@router.get("/status")
def semantic_status(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    status = embedding_worker.status()
    status["indexed_memories"] = db.query(VectorMemory).count()
    status["jobs"] = db.query(EmbeddingJob).count()
    return status


@router.post("/index")
async def index_unindexed(_user: User = Depends(get_current_user)):
    return await embedding_worker.enqueue_unindexed()


@router.post("/reindex")
async def reindex_all(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    db.query(VectorMemory).delete()
    db.commit()
    return await embedding_worker.enqueue_unindexed()


@router.post("/search", response_model=list[SemanticMemoryResult])
def semantic_search(payload: SemanticSearchRequest, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return serialize_results(semantic_search_engine.semantic_search(db, payload.query, payload.limit, payload.source_type, payload.session_id))


@router.post("/hybrid-search", response_model=list[SemanticMemoryResult])
def hybrid_search(payload: SemanticSearchRequest, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return serialize_results(semantic_search_engine.hybrid_search(db, payload.query, payload.limit, payload.source_type, payload.session_id))


@router.get("/related/{memory_id}", response_model=list[SemanticMemoryResult])
def related_memories(memory_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return serialize_results(semantic_search_engine.related_memories(db, memory_id))


@router.post("/context")
def assemble_context(payload: SemanticSearchRequest, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return semantic_search_engine.context(db, payload.query, payload.limit)


@router.post("/relationships/detect")
def detect_relationships(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return semantic_search_engine.detect_relationships(db)


@router.post("/clusters/rebuild")
def rebuild_clusters(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return memory_clusterer.rebuild_clusters(db)


@router.get("/clusters", response_model=list[MemoryClusterOut])
def list_clusters(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return db.query(MemoryCluster).order_by(MemoryCluster.size.desc()).limit(50).all()


@router.get("/jobs", response_model=list[EmbeddingJobOut])
def list_jobs(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return db.query(EmbeddingJob).order_by(EmbeddingJob.created_at.desc()).limit(50).all()


@router.get("/history", response_model=list[SearchHistoryOut])
def search_history(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return db.query(SearchHistory).order_by(SearchHistory.created_at.desc()).limit(30).all()
