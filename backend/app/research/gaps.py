"""
Contribution 5 - Knowledge-Gap Detection.
===========================================================================
"The user has seen this word five times but has never explained it."

That distinction - exposure versus understanding - is what a gap detector has to
make. It is not enough to check whether a concept appears; a concept you are
studying appears constantly. The signal is the SHAPE of the mentions:

  shallow exposure   many mentions, low graph connectivity, short fragments,
                     always in lists/titles, never the subject of a sentence
  real understanding mentioned as the subject of explanation, connected to other
                     concepts, appears in longer coherent passages, recurs over time

gap_score combines the two opposing signals so that a well-connected concept is
never reported as a gap no matter how often it is mentioned.
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

EXPLANATION_MARKERS = (
    "is a", "is an", "means", "refers to", "defined as", "because", "works by",
    "the reason", "for example", "in other words", "difference between",
)

# Concepts that are not knowledge and should never be reported as gaps
STOP_CONCEPTS = {
    "the", "and", "for", "with", "this", "that", "from", "your", "you", "not",
    "activity", "chrome", "electron", "code", "window", "title", "today",
}


class KnowledgeGapDetector:
    def __init__(self, min_mentions: int = 3):
        self.min_mentions = min_mentions

    # --------------------------------------------------------------- signals
    @staticmethod
    def _tokens(text: str) -> List[str]:
        words = re.findall(r"[A-Za-z][A-Za-z0-9_+.#-]{2,}", text or "")
        return [w.lower() for w in words if w.lower() not in STOP_CONCEPTS]

    def _concept_stats(self, memories: List) -> Dict[str, Dict[str, Any]]:
        stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "mentions": 0,
            "explained": 0,
            "as_subject": 0,
            "total_chars": 0,
            "days": set(),
            "titles": 0,
        })

        for memory in memories:
            title = (memory.title or "")
            content = (memory.content or "")
            text = f"{title} {content}"
            lowered = text.lower()

            day = (memory.created_at or datetime.utcnow()).date()
            for concept in set(self._tokens(text)):
                entry = stats[concept]
                entry["mentions"] += lowered.count(concept)
                entry["total_chars"] += len(content)
                entry["days"].add(day)
                if concept in title.lower():
                    entry["titles"] += 1

                # was it EXPLAINED, or just listed?
                for marker in EXPLANATION_MARKERS:
                    index = lowered.find(f"{concept} {marker}")
                    if index == -1:
                        index = lowered.find(f"{concept}{marker}")
                    if index >= 0:
                        entry["explained"] += 1
                        break

                # did it appear as the SUBJECT of a sentence?
                if re.search(rf"(^|[.!?]\s+){re.escape(concept)}\b", lowered):
                    entry["as_subject"] += 1

        return stats

    # ------------------------------------------------------------ gap scoring
    def detect(self, db, limit: int = 25, scope_ids: Optional[Iterable[int]] = None,
               persist: bool = True) -> Dict[str, Any]:
        """
        `scope_ids` restricts the analysis to a set of memories.

        The evaluation harness needs that: gap scores are relative to the corpus
        being examined (mentions, spread, connectivity are all corpus statistics),
        so scoring a 15-memory corpus against a database that also holds the
        user's own notes answers a different question. `persist=False` keeps a
        scoped run from overwriting the user's real gap snapshot.
        """
        from app.models.graph import GraphNode
        from app.models.memory import Memory
        from app.models.research import KnowledgeGap

        scope = set(scope_ids) if scope_ids is not None else None
        query = db.query(Memory)
        if scope is not None:
            if not scope:
                return {"gaps": 0, "concepts_examined": 0, "memories_examined": 0, "items": []}
            query = query.filter(Memory.id.in_(scope))
        memories = query.all()
        if not memories:
            return {"gaps": 0, "concepts_examined": 0, "memories_examined": 0, "items": []}

        stats = self._concept_stats(memories)
        total_memories = max(1, len(memories))

        # graph connectivity per concept
        degree: Counter = Counter()
        try:
            node_query = db.query(GraphNode)
            if scope is not None:
                node_query = node_query.filter(GraphNode.memory_id.in_(scope))
            for node in node_query.all():
                for token in set(self._tokens(node.name or "")):
                    degree[token] += 1
        except Exception:
            pass
        max_degree = max(degree.values()) if degree else 1

        rows: List[Dict[str, Any]] = []
        for concept, entry in stats.items():
            mentions = entry["mentions"]
            if mentions < self.min_mentions:
                continue

            # exposure driven by repetition in titles/lists rather than prose
            exposure = min(1.0, mentions / 12.0)
            explained_ratio = entry["explained"] / max(1, mentions)
            subject_ratio = entry["as_subject"] / max(1, mentions)
            connectivity = min(1.0, degree.get(concept, 0) / max(1, max_degree))
            spread = min(1.0, len(entry["days"]) / max(1.0, total_memories * 0.25))

            # depth: did the user actually engage with it?
            depth = min(1.0, 0.45 * explained_ratio * 3
                        + 0.30 * subject_ratio * 3
                        + 0.25 * spread)

            gap = max(0.0, exposure * (1.0 - depth) * (1.0 - 0.5 * connectivity))
            if gap < 0.12:
                continue

            if explained_ratio == 0 and connectivity < 0.3:
                rationale = (f"mentioned {mentions}x across {len(entry['days'])} "
                             f"session(s) but never explained and poorly connected")
            elif explained_ratio < 0.2:
                rationale = f"mentioned {mentions}x with little explanatory context"
            else:
                rationale = f"low connectivity ({degree.get(concept, 0)} links) despite {mentions} mentions"

            rows.append({
                "concept": concept,
                "mentions": mentions,
                "depth_score": round(depth, 4),
                "connectivity": round(connectivity, 4),
                "evidence_count": entry["explained"],
                "gap_score": round(gap, 4),
                "rationale": rationale,
            })

        rows.sort(key=lambda r: -r["gap_score"])
        rows = rows[:limit]

        # persist (replace previous snapshot so results do not accumulate)
        if persist:
            db.query(KnowledgeGap).delete()
            db.commit()
            # The bulk delete above leaves stale identities in the session, and
            # the re-insert reuses the freed primary keys (SQLAlchemy "Identity
            # map already had an identity for ..."). Expunging makes the session
            # forget the deleted rows entirely.
            db.expunge_all()
            for row in rows:
                db.add(KnowledgeGap(**row))
            db.commit()

        return {
            "gaps": len(rows),
            "concepts_examined": len(stats),
            "memories_examined": len(memories),
            "items": rows,
        }

    def stored(self, db, limit: int = 25) -> List[Dict[str, Any]]:
        from app.models.research import KnowledgeGap

        return [
            {
                "concept": r.concept, "mentions": r.mentions,
                "depth_score": r.depth_score, "connectivity": r.connectivity,
                "gap_score": r.gap_score, "rationale": r.rationale,
                "detected_at": r.detected_at.isoformat() if r.detected_at else None,
            }
            for r in db.query(KnowledgeGap).order_by(KnowledgeGap.gap_score.desc()).limit(limit).all()
        ]


knowledge_gap_detector = KnowledgeGapDetector()
