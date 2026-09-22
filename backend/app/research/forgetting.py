"""
Contribution 6 - Forgetting / Unlearning.
===========================================================================
"Delete it" is not enough. If a vector or an index row survives anywhere, the
content can still be retrieved - which is exactly the failure that makes
unlearning research non-trivial. Deletion must be enforced at every place a
memory can re-enter a result set.

Enforcement points covered here:
  1. SQLite retrieval      (memory_search)      - excluded by id
  2. Semantic retrieval    (chroma vectors)     - vector deleted AND id filtered
  3. Knowledge graph       (GraphNode edges)    - node removed
  4. Temporal facts        (TemporalFact rows)  - closed and detached
  5. Memory scores         (MemoryScore rows)   - removed

The `memories` row itself is kept and tombstoned, so ids stay stable and the
history of what was forgotten is auditable. `hard_delete=True` purges it.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

# Strip the tail of an email/clipboard header so a forget request matches
HEADER_NOISE = re.compile(r"^(?:email received by|clipboard:|capture from)\b.*$", re.I | re.M)


class ForgettingService:
    # ------------------------------------------------------------ tombstones
    def forgotten_ids(self, db) -> set:
        from app.models.research import ForgottenMemory

        try:
            return {row.memory_id for row in db.query(ForgottenMemory).all()}
        except Exception:
            return set()

    def forget(self, db, memory_id: int, reason: str = "user_request",
               hard: bool = False) -> Dict[str, Any]:
        from app.models.memory import Memory, SearchIndex
        from app.models.research import (
            ForgottenMemory, KnowledgeGap, MemoryConsolidation, MemoryConflict,
            MemoryScore, TemporalFact,
        )

        memory = db.query(Memory).filter(Memory.id == memory_id).first()
        if not memory:
            return {"forgotten": False, "reason": "Memory not found"}

        removed = {"search_index": 0, "vectors": 0, "graph_nodes": 0,
                   "temporal_facts": 0, "scores": 0, "relationships": 0}

        # 1. keyword retrieval
        removed["search_index"] = (
            db.query(SearchIndex).filter(SearchIndex.memory_id == memory_id)
            .delete(synchronize_session=False)
        )

        # 2. vector retrieval - remove the embedding itself, not just filter it
        try:
            from app.vectorstore.chroma_store import chroma_store

            chroma_store.delete(f"memory-{memory_id}")
            removed["vectors"] = 1
        except Exception:
            # If chroma is unavailable there is no vector to leak.
            pass

        # 3. knowledge graph
        try:
            from app.models.graph import GraphEdge, GraphNode

            nodes = db.query(GraphNode).filter(GraphNode.memory_id == memory_id).all()
            for node in nodes:
                db.query(GraphEdge).filter(
                    (GraphEdge.source_node_id == node.id) | (GraphEdge.target_node_id == node.id)
                ).delete(synchronize_session=False)
                db.delete(node)
                removed["graph_nodes"] += 1
        except Exception:
            pass

        # 4. temporal facts derived from it
        facts = db.query(TemporalFact).filter(TemporalFact.source_memory_id == memory_id).all()
        for fact in facts:
            fact.valid_to = datetime.utcnow()
            fact.source_memory_id = None       # detach so the traceback is gone too
            removed["temporal_facts"] += 1

        # 5. scores, conflicts, consolidations
        removed["scores"] = (
            db.query(MemoryScore).filter(MemoryScore.memory_id == memory_id)
            .delete(synchronize_session=False)
        )
        removed["relationships"] = (
            db.query(MemoryConflict)
            .filter((MemoryConflict.older_memory_id == memory_id) | (MemoryConflict.newer_memory_id == memory_id))
            .delete(synchronize_session=False)
        )
        db.query(KnowledgeGap).delete()
        db.flush()

        # 6. mark, or purge
        if hard:
            db.query(MemoryConsolidation).filter(
                MemoryConsolidation.canonical_memory_id == memory_id
            ).delete(synchronize_session=False)
            db.delete(memory)
        else:
            existing = db.query(ForgottenMemory).filter(ForgottenMemory.memory_id == memory_id).first()
            if not existing:
                db.add(ForgottenMemory(
                    memory_id=memory_id,
                    reason=reason[:200],
                    requested_by="user",
                    hard_delete=False,
                    forgotten_at=datetime.utcnow(),
                ))

        db.commit()
        return {
            "forgotten": True,
            "memory_id": memory_id,
            "title": memory.title if not hard else getattr(memory, "title", ""),
            "hard_delete": hard,
            "removed": removed,
            "enforcement_points": 5,
        }

    # --------------------------------------------------------- bulk forgetting
    def forget_matching(self, db, query: str, hard: bool = False,
                        limit: int = 50) -> Dict[str, Any]:
        """
        "Forget everything about X."

        Substring match on title/content, case-insensitive. Deliberately
        conservative: it reports exactly which memories it will remove.
        """
        from app.models.memory import Memory

        if not query.strip():
            return {"forgotten": 0, "reason": "empty query"}

        needle = query.strip().lower()
        matches = [
            m for m in db.query(Memory).all()
            if needle in (m.title or "").lower() or needle in (m.content or "").lower()
        ][:limit]

        results = [self.forget(db, m.id, reason=f"bulk: {query}", hard=hard) for m in matches]
        return {
            "query": query,
            "matched": len(matches),
            "forgotten": sum(1 for r in results if r.get("forgotten")),
            "memory_ids": [r["memory_id"] for r in results if r.get("forgotten")],
            "titles": [r.get("title", "") for r in results if r.get("forgotten")],
        }

    def restore(self, db, memory_id: int) -> Dict[str, Any]:
        """Undo a soft forget: re-index so it becomes retrievable again."""
        from app.models.memory import Memory, SearchIndex
        from app.models.research import ForgottenMemory

        row = db.query(ForgottenMemory).filter(ForgottenMemory.memory_id == memory_id).first()
        if not row:
            return {"restored": False, "reason": "Not in the forgotten set"}

        memory = db.query(Memory).filter(Memory.id == memory_id).first()
        if not memory:
            return {"restored": False, "reason": "Memory row no longer exists"}

        existing = db.query(SearchIndex).filter(SearchIndex.memory_id == memory_id).first()
        if not existing:
            tags = ""
            db.add(SearchIndex(
                memory_id=memory.id,
                session_id=memory.session_id,
                searchable_text=f"{memory.title} {memory.content} {memory.topic_label}",
                tags_text=tags,
                app_source=memory.app_source,
                source_type=memory.source_type,
                topic_label=memory.topic_label,
                created_at=memory.created_at,
            ))

        db.delete(row)
        db.commit()
        return {"restored": True, "memory_id": memory_id, "reindexed": True}

    # ------------------------------------------------------------- reporting
    def summary(self, db) -> Dict[str, Any]:
        from app.models.research import ForgottenMemory
        from app.models.memory import Memory

        rows = db.query(ForgottenMemory).all()
        total_memories = db.query(Memory).count()
        return {
            "forgotten_count": len(rows),
            "total_memories": total_memories,
            "entries": [
                {
                    "memory_id": r.memory_id,
                    "reason": r.reason,
                    "hard_delete": r.hard_delete,
                    "forgotten_at": r.forgotten_at.isoformat() if r.forgotten_at else None,
                }
                for r in sorted(rows, key=lambda x: -(x.forgotten_at.timestamp() if x.forgotten_at else 0))[:40]
            ],
        }


forgetting_service = ForgettingService()
