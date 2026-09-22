"""
Contribution 1 - Adaptive Memory Scoring (AMS).
===========================================================================
The problem: a personal memory store grows without bound. Storing everything
with equal weight means the retriever cannot tell a throwaway clipboard fragment
from the note that defines your project.

AMS assigns each memory an importance score with explicit, inspectable terms:

    M = w1*R + w2*F + w3*T + w4*G + w5*U + w6*P - w7*D - w8*C

    R relevance         overlap with the user's represented interests
    F frequency         how often this content recurs across memories
    T temporal          recency with exponential decay
    G connectivity      degree of the memory's concepts in the knowledge graph
    U user_confirmation explicit pin / user confirmation
    P future_utility    predicted usefulness (actionable, project-linked, dated)
    D redundancy        duplication penalty
    C contradiction     unresolved-conflict penalty

Every term is stored alongside the total, so the score is auditable rather than
a black box - which is the whole point of a *scoring* contribution.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Iterable

# Weights are deliberately exposed as a versioned dict so an ablation study can
# vary them without touching code. Sum of positive weights = 1.0.
DEFAULT_WEIGHTS: Dict[str, float] = {
    "relevance": 0.30,
    "frequency": 0.08,
    "temporal": 0.22,
    "connectivity": 0.15,
    "user_confirmation": 0.15,
    "future_utility": 0.10,
    "redundancy": 0.18,      # subtracted
    "contradiction": 0.25,   # subtracted
}
WEIGHTS_VERSION = "v1"

ACTIONABLE_PATTERNS = (
    "deadline", "due", "submit", "must", "todo", "to-do", "action", "reminder",
    "meeting", "exam", "interview", "invoice", "payment", "review",
)
PROJECT_PATTERNS = ("project", "thesis", "paper", "ieee", "assignment", "report")

# Terms that indicate durable knowledge rather than a passing fragment
DURABLE_PATTERNS = (
    "definition", "architecture", "algorithm", "concept", "theory", "framework",
    "tutorial", "documentation", "reference", "specification",
)


class AdaptiveMemoryScorer:
    """Computes and persists the per-memory importance score."""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = {**DEFAULT_WEIGHTS, **(weights or {})}
        self.half_life_days = 45.0   # T decays to 0.5 after this long

    # ------------------------------------------------------------ individual
    def _relevance(self, memory, interests: Counter) -> float:
        """Cosine-ish overlap between the memory's terms and the user's interests."""
        text = f"{memory.title or ''} {memory.content or ''}".lower()
        terms = self._terms(text)
        if not terms or not interests:
            return 0.0
        total = sum(interests.values()) or 1
        hits = sum(interests.get(t, 0) for t in terms)
        # normalise by memory length so a long memory is not automatically "relevant"
        return min(1.0, (hits / total) * 6.0)

    def _frequency(self, memory, term_counts: Counter, corpus_size: int) -> float:
        """Recurrence of this memory's distinctive terms across the corpus."""
        terms = self._terms(f"{memory.title or ''} {memory.content or ''}")
        if not terms or corpus_size <= 1:
            return 0.0
        rare = [t for t in set(terms) if 1 < term_counts[t] < corpus_size]
        return min(1.0, len(rare) / max(1, len(set(terms))))

    def _temporal(self, memory, now: Optional[datetime] = None) -> float:
        """Exponential recency decay, which keeps the score comparable over time."""
        now = now or datetime.utcnow()
        created = memory.created_at or now
        age_days = max(0.0, (now - created).total_seconds() / 86400.0)
        return math.pow(0.5, age_days / self.half_life_days)

    def _connectivity(self, memory, degree_by_term: Counter) -> float:
        """How well connected this memory's concepts are in the graph."""
        terms = self._terms(f"{memory.title or ''} {memory.content or ''}")
        if not terms:
            return 0.0
        degree = sum(degree_by_term.get(t, 0) for t in set(terms))
        return min(1.0, degree / (len(set(terms)) * 4.0))

    def _user_confirmation(self, memory, confirmed_ids: set) -> float:
        if memory.id in confirmed_ids:
            return 1.0
        text = f"{memory.title or ''} {memory.content or ''}".lower()
        if any(w in text for w in ("i decided", "i confirmed", "my choice", "final", "approved")):
            return 0.6
        return 0.0

    def _future_utility(self, memory) -> float:
        """Actionable, project-linked or explicitly dated content is worth keeping."""
        text = f"{memory.title or ''} {memory.content or ''}".lower()
        score = 0.0
        if any(p in text for p in ACTIONABLE_PATTERNS):
            score += 0.5
        if any(p in text for p in PROJECT_PATTERNS):
            score += 0.3
        if any(p in text for p in DURABLE_PATTERNS):
            score += 0.3
        if re.search(r"\b\d{4}-\d{2}-\d{2}\b", text):
            score += 0.2
        return min(1.0, score)

    def _redundancy(self, memory, term_counts: Counter, corpus_size: int) -> float:
        """
        Penalise near-duplicate content.

        Uses term commonality as a proxy: a memory made almost entirely of terms
        that appear everywhere adds little new information (high IDF inverse).
        """
        terms = self._terms(f"{memory.title or ''} {memory.content or ''}")
        if not terms or corpus_size <= 1:
            return 0.0
        common = sum(1 for t in set(terms) if term_counts[t] >= max(3, corpus_size * 0.5))
        return min(1.0, common / max(1, len(set(terms))))

    def _contradiction(self, memory, conflicts_by_memory: Counter) -> float:
        """Penalise memories involved in unresolved conflicts."""
        hits = conflicts_by_memory.get(memory.id, 0)
        return min(1.0, hits / 2.0)

    # ---------------------------------------------------------------- utils
    STOP = {
        "the", "and", "for", "with", "from", "that", "this", "have", "has",
        "was", "were", "are", "you", "your", "not", "but", "all", "can", "will",
        "into", "than", "then", "there", "their", "they", "them", "its", "it's",
        "about", "which", "when", "what", "who", "how", "why", "our", "out",
    }

    def _terms(self, text: str) -> List[str]:
        words = re.findall(r"[a-z][a-z0-9_+.#-]{2,}", (text or "").lower())
        return [w for w in words if w not in self.STOP]

    # ------------------------------------------------------------- scoring
    def score_memory(self, memory, context: Dict[str, Any]) -> Dict[str, float]:
        w = self.weights
        components = {
            "relevance": self._relevance(memory, context["interests"]),
            "frequency": self._frequency(memory, context["term_counts"], context["corpus_size"]),
            "temporal": self._temporal(memory, context.get("now")),
            "connectivity": self._connectivity(memory, context["degree_by_term"]),
            "user_confirmation": self._user_confirmation(memory, context["confirmed_ids"]),
            "future_utility": self._future_utility(memory),
            "redundancy": self._redundancy(memory, context["term_counts"], context["corpus_size"]),
            "contradiction": self._contradiction(memory, context["conflicts_by_memory"]),
        }

        total = (
            w["relevance"] * components["relevance"]
            + w["frequency"] * components["frequency"]
            + w["temporal"] * components["temporal"]
            + w["connectivity"] * components["connectivity"]
            + w["user_confirmation"] * components["user_confirmation"]
            + w["future_utility"] * components["future_utility"]
            - w["redundancy"] * components["redundancy"]
            - w["contradiction"] * components["contradiction"]
        )

        components["total"] = round(max(0.0, min(1.5, total)), 6)
        return components

    # ------------------------------------------------------- corpus context
    def build_context(self, db, memories: List,
                      scope_ids: Optional[Iterable[int]] = None) -> Dict[str, Any]:
        """
        One pass over the corpus to compute the shared statistics.

        `scope_ids` limits the graph-degree term to nodes belonging to the set
        being scored. Unscoped, a memory's connectivity would be measured against
        the user's entire knowledge graph, so the same corpus would score
        differently on two machines - which is exactly what makes an evaluation
        table irreproducible.
        """
        from app.models.graph import GraphNode
        from app.models.research import MemoryConflict

        corpus_size = max(1, len(memories))

        term_counts: Counter = Counter()
        for memory in memories:
            for term in set(self._terms(f"{memory.title or ''} {memory.content or ''}")):
                term_counts[term] += 1

        # interests = the most frequent meaningful terms, i.e. what this user
        # actually keeps thinking about
        interests = Counter({t: c for t, c in term_counts.most_common(150)})

        degree_by_term: Counter = Counter()
        try:
            node_query = db.query(GraphNode)
            if scope_ids is not None:
                scope = set(scope_ids)
                if not scope:
                    raise ValueError("empty scope")
                node_query = node_query.filter(GraphNode.memory_id.in_(scope))
            for node in node_query.all():
                for term in set(self._terms(node.name or "")):
                    degree_by_term[term] += 1
        except Exception:
            pass

        conflicts_by_memory: Counter = Counter()
        try:
            for conflict in db.query(MemoryConflict).filter(MemoryConflict.resolved == False).all():  # noqa: E712
                if conflict.older_memory_id:
                    conflicts_by_memory[conflict.older_memory_id] += 1
                if conflict.newer_memory_id:
                    conflicts_by_memory[conflict.newer_memory_id] += 1
        except Exception:
            pass

        confirmed_ids = set()
        try:
            for memory in memories:
                if getattr(memory, "category", "") == "pinned":
                    confirmed_ids.add(memory.id)
        except Exception:
            pass

        return {
            "interests": interests,
            "term_counts": term_counts,
            "degree_by_term": degree_by_term,
            "conflicts_by_memory": conflicts_by_memory,
            "confirmed_ids": confirmed_ids,
            "corpus_size": corpus_size,
            "now": datetime.utcnow(),
        }

    # -------------------------------------------------------------- persist
    def score_corpus(self, db, limit: Optional[int] = None,
                     scope_ids: Optional[Iterable[int]] = None) -> Dict[str, Any]:
        """
        `scope_ids` scores a subset as if it were the whole corpus.

        The components are corpus-relative by construction - term interests,
        frequency and connectivity are normalised over the set being scored - so
        scoring a benchmark corpus inside a database that also holds the user's
        own memories changes the numbers. The evaluation harness passes the corpus
        ids to keep the published figures reproducible between machines.
        """
        from app.models.memory import Memory
        from app.models.research import MemoryScore

        query = db.query(Memory)
        if scope_ids is not None:
            scope = set(scope_ids)
            if not scope:
                return {"scored": 0, "orphans_pruned": 0, "weights_version": WEIGHTS_VERSION,
                        "weights": self.weights, "corpus_size": 0}
            query = query.filter(Memory.id.in_(scope))
        if limit:
            query = query.order_by(Memory.created_at.desc()).limit(limit)
        memories = query.all()

        # Prune orphans first: a memory deleted elsewhere leaves its score row
        # behind, and an orphan inflates counts while never appearing in the
        # joined listing. Cheap to clean, and it keeps the tables consistent.
        # Orphan pruning is a whole-database repair, not a corpus statistic, so
        # it only runs for an unscoped pass - a scoped run must not delete the
        # scores belonging to memories outside its scope.
        pruned = 0
        if scope_ids is None:
            live_ids = {m.id for m in memories}
            for row in db.query(MemoryScore).all():
                if row.memory_id not in live_ids:
                    db.delete(row)
                    pruned += 1
        if pruned:
            db.flush()

        context = self.build_context(db, memories, scope_ids=scope_ids)
        scored = 0
        for memory in memories:
            components = self.score_memory(memory, context)
            row = db.query(MemoryScore).filter(MemoryScore.memory_id == memory.id).first()
            if not row:
                row = MemoryScore(memory_id=memory.id)
                db.add(row)
            row.total = components["total"]
            row.relevance = components["relevance"]
            row.frequency = components["frequency"]
            row.temporal = components["temporal"]
            row.connectivity = components["connectivity"]
            row.user_confirmation = components["user_confirmation"]
            row.future_utility = components["future_utility"]
            row.redundancy = components["redundancy"]
            row.contradiction = components["contradiction"]
            row.weights_version = WEIGHTS_VERSION
            scored += 1

        db.commit()
        return {
            "scored": scored,
            "orphans_pruned": pruned,
            "weights_version": WEIGHTS_VERSION,
            "weights": self.weights,
            "corpus_size": context["corpus_size"],
        }


adaptive_memory_scorer = AdaptiveMemoryScorer()
