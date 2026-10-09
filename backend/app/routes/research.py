"""
Research layer API - every contribution, exposed for demonstration.
===========================================================================
  GET  /api/research/overview            one payload with the whole layer's state
  POST /api/research/score               recompute Adaptive Memory Scoring
  GET  /api/research/scores              ranked memories with score components
  GET  /api/research/temporal            current facts + full history
  POST /api/research/temporal/ingest     extract facts from text and record them
  POST /api/research/conflicts/detect    run contradiction detection
  GET  /api/research/conflicts           detected conflicts and their resolution
  POST /api/research/consolidate         merge near-duplicate memories
  GET  /api/research/gaps                knowledge-gap detection
  POST /api/research/forget              unlearn a memory (or everything matching)
  POST /api/research/forget/{id}/restore undo a soft forget
  GET  /api/research/forgotten           the tombstone list
  POST /api/research/benchmark           run PersonalBrain-Bench across all 4 modes
  GET  /api/research/runs                historical benchmark runs
  POST /api/research/answer              ask a question through a chosen mode
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User

router = APIRouter(prefix="/api/research", tags=["research"])


class IngestTextPayload(BaseModel):
    text: str
    memory_id: Optional[int] = None


class ForgetPayload(BaseModel):
    memory_id: Optional[int] = None
    query: Optional[str] = ""
    hard: Optional[bool] = False
    reason: Optional[str] = "user_request"


class AnswerPayload(BaseModel):
    question: str
    mode: Optional[str] = "adaptive"
    limit: Optional[int] = 5


class BenchmarkPayload(BaseModel):
    k: Optional[int] = 5


# ------------------------------------------------------------------ overview
@router.get("/overview")
def overview(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    """Everything in one call, for the demo dashboard."""
    from app.models.memory import Memory
    from app.models.research import (
        ForgottenMemory, KnowledgeGap, MemoryConflict, MemoryConsolidation, MemoryScore, TemporalFact,
    )

    def _count(model):
        try:
            return db.query(model).count()
        except Exception:
            return 0

    return {
        "memories_total": _count(Memory),
        "scored": _count(MemoryScore),
        "temporal_facts": _count(TemporalFact),
        "open_facts": (
            db.query(TemporalFact).filter(TemporalFact.valid_to.is_(None)).count()
            if _count(TemporalFact) else 0
        ),
        "superseded_facts": (
            db.query(TemporalFact).filter(TemporalFact.superseded_by.isnot(None)).count()
            if _count(TemporalFact) else 0
        ),
        "conflicts": _count(MemoryConflict),
        "consolidations": _count(MemoryConsolidation),
        "gaps": _count(KnowledgeGap),
        "forgotten": _count(ForgottenMemory),
        "modes": ["vanilla", "hybrid", "graph", "adaptive"],
    }


# ---------------------------------------------------------------------1 AMS
@router.post("/score")
def run_scoring(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    from app.research.scoring import adaptive_memory_scorer

    return adaptive_memory_scorer.score_corpus(db)


@router.get("/scores")
def list_scores(limit: int = Query(default=25, ge=1, le=200),
                db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    from app.models.memory import Memory
    from app.models.research import MemoryScore

    rows = (
        db.query(MemoryScore, Memory)
        .join(Memory, Memory.id == MemoryScore.memory_id)
        .order_by(MemoryScore.total.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "memory_id": memory.id,
            "title": memory.title,
            "source_type": memory.source_type,
            "total": round(score.total, 4),
            "components": {
                "relevance": round(score.relevance, 4),
                "frequency": round(score.frequency, 4),
                "temporal": round(score.temporal, 4),
                "connectivity": round(score.connectivity, 4),
                "user_confirmation": round(score.user_confirmation, 4),
                "future_utility": round(score.future_utility, 4),
                "redundancy": round(score.redundancy, 4),
                "contradiction": round(score.contradiction, 4),
            },
        }
        for score, memory in rows
    ]


# ----------------------------------------------------------------2 TEMPORAL
@router.get("/temporal")
def temporal(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    from app.research.temporal import temporal_knowledge_graph

    return {
        "current": temporal_knowledge_graph.current_facts(db),
        "history": temporal_knowledge_graph.history(db),
    }


@router.post("/temporal/ingest")
def temporal_ingest(payload: IngestTextPayload, db: Session = Depends(get_db),
                    _user: User = Depends(get_current_user)):
    from app.research.temporal import temporal_knowledge_graph

    facts = temporal_knowledge_graph.extract_facts(payload.text)
    if not facts:
        return {"extracted": 0, "recorded": {"created": 0, "superseded": 0, "retracted": 0},
                "note": "No personal state was expressed in that text."}
    result = temporal_knowledge_graph.record_facts(db, facts, source_memory_id=payload.memory_id)
    return {"extracted": len(facts), "facts": facts, "recorded": result}


# ------------------------------------------------------------3 CONTRADICTION
@router.post("/conflicts/detect")
def detect_conflicts(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    from app.research.contradictions import contradiction_resolver

    return contradiction_resolver.resolve(db)


@router.get("/conflicts")
def list_conflicts(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    from app.research.contradictions import contradiction_resolver

    return contradiction_resolver.summary(db)


# -----------------------------------------------------------4 CONSOLIDATION
@router.post("/consolidate")
def consolidate(threshold: float = Query(default=0.90, ge=0.5, le=1.0),
                dry_run: bool = Query(default=False),
                db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    from app.research.consolidation import memory_consolidator

    return memory_consolidator.consolidate(db, threshold=threshold, dry_run=dry_run)


# -------------------------------------------------------------------5 GAPS
@router.get("/gaps")
def gaps(recompute: bool = Query(default=True), limit: int = Query(default=25, ge=1, le=100),
         db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    from app.research.gaps import knowledge_gap_detector

    if recompute:
        return knowledge_gap_detector.detect(db, limit=limit)
    return {"items": knowledge_gap_detector.stored(db, limit=limit)}


# --------------------------------------------------------------6 FORGETTING
@router.post("/forget")
def forget(payload: ForgetPayload, db: Session = Depends(get_db),
           _user: User = Depends(get_current_user)):
    from app.research.forgetting import forgetting_service

    if payload.memory_id:
        result = forgetting_service.forget(
            db, payload.memory_id, reason=payload.reason or "user_request", hard=bool(payload.hard))
        if not result.get("forgotten"):
            raise HTTPException(status_code=404, detail=result.get("reason", "Memory not found"))
        return result

    if not (payload.query or "").strip():
        raise HTTPException(status_code=400, detail="Provide memory_id or query.")

    return forgetting_service.forget_matching(
        db, payload.query, hard=bool(payload.hard))


@router.post("/forget/{memory_id}/restore")
def restore(memory_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    from app.research.forgetting import forgetting_service

    result = forgetting_service.restore(db, memory_id)
    if not result.get("restored"):
        raise HTTPException(status_code=404, detail=result.get("reason", "Not restored"))
    return result


@router.get("/forgotten")
def forgotten(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    from app.research.forgetting import forgetting_service

    return forgetting_service.summary(db)


# ---------------------------------------------------------------7 BENCHMARK
@router.post("/benchmark")
def run_benchmark(payload: BenchmarkPayload, db: Session = Depends(get_db),
                  _user: User = Depends(get_current_user)):
    """Run PersonalBrain-Bench over all four modes and return the comparison."""
    from app.research.bench import benchmark_runner

    k = payload.k or 5
    result = benchmark_runner.run_all(db, k=k)

    # the paper's headline table, ready to paste
    summary = {
        mode: {
            "hit_at_k": metrics["hit_at_k"],
            "mrr": metrics["mrr"],
            "stale_top1_rate": metrics["stale_top1_rate"],
            "forgotten_leak_rate": metrics["forgotten_leak_rate"],
            "duplicate_rate": metrics["duplicate_rate"],
            "avg_context_chars": metrics["avg_context_chars"],
            "latency_ms": metrics["latency_ms"],
        }
        for mode, metrics in result["results"].items()
    }
    return {"corpus": result["corpus"], "k": k, "summary": summary,
            "comparison": result["comparison"], "detail": result["results"]}


@router.post("/benchmark/multi-user")
def run_multi_user_benchmark(payload: BenchmarkPayload, db: Session = Depends(get_db),
                             _user: User = Depends(get_current_user)):
    """Run PersonalBrain-Bench v2 across multiple personas with statistical significance."""
    from app.research.multi_user_bench import multi_user_benchmark

    k = payload.k or 5
    return multi_user_benchmark.run_benchmark(db, k=k)


@router.get("/runs")
def runs(limit: int = Query(default=20, ge=1, le=100),
         db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    from app.models.research import ResearchRun

    rows = db.query(ResearchRun).order_by(ResearchRun.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id, "kind": r.kind, "system": r.system, "questions": r.questions,
            "metrics": json.loads(r.metrics_json or "{}"),
            "duration_ms": r.duration_ms,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


# ------------------------------------------------------------------- ANSWER
@router.post("/answer")
def answer(payload: AnswerPayload, db: Session = Depends(get_db),
           _user: User = Depends(get_current_user)):
    """
    Retrieve through a chosen mode and show exactly what changed.

    Returns the retrieved context AND the pipeline trace, so the difference
    between modes is inspectable rather than asserted.
    """
    from app.research.pipeline import adaptive_retrieval

    mode = payload.mode if payload.mode in ("vanilla", "hybrid", "graph", "adaptive") else "adaptive"
    results = adaptive_retrieval.retrieve(db, payload.question, limit=payload.limit or 5, mode=mode)
    return {
        "question": payload.question,
        "mode": mode,
        "trace": adaptive_retrieval.last_trace,
        "count": len(results),
        "context": [
            {"memory_id": r["memory_id"], "title": r["title"],
             "content": (r["content"] or "")[:400]}
            for r in results
        ],
    }
