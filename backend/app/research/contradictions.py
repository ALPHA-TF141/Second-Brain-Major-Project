"""
Contribution 3 - Contradiction Detection and Resolution
===========================================================================
Retrieval-augmented generation assumes retrieved context is mutually consistent.
For a personal memory store that assumption fails constantly: you change your
mind, your circumstances change, you learn something that replaces an earlier
belief. Plain RAG has no mechanism to notice, so it will happily cite both the
old and the new memory as if both were true.

This module detects three kinds of conflict:

  value_change  same (subject, predicate), different object, later timestamp
                -> "learning Python" then "focus on Java"
  negation      one memory asserts, a later one explicitly denies
  staleness     a memory whose temporal validity has closed

and decides what retrieval should do about it. Crucially it can PREFER NEWER
without deleting the older evidence, so "what did I think in January?" still
works - which is exactly the property a forgetting-everything system loses.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Iterable

from app.research.temporal import temporal_knowledge_graph

# Matched with WORD BOUNDARIES. A plain `"not" in text` check is a substring
# match, so "notes", "notification", "another" and "cannot" all registered as
# negations - which produced contradiction reports for notes that merely
# mentioned notes. Every one of those is a false positive on real mail/notes.
NEGATION_PATTERNS = (
    r"\bnot\b", r"\bno longer\b", r"\bstopped\b", r"\bnever\b",
    r"\bquit\b", r"\babandoned\b", r"\bdropped\b", r"\bcancelled\b",
    r"\bcanceled\b", r"\breplaced\b", r"\bsuperseded\b", r"\bobsolete\b",
)


def _has_negation(text: str) -> bool:
    return any(re.search(pattern, text) for pattern in NEGATION_PATTERNS)


class ContradictionResolver:
    def __init__(self):
        self.min_similarity = 0.45

    # ------------------------------------------------------------- detection
    @staticmethod
    def _tokens(text: str) -> set:
        return set(re.findall(r"[a-z][a-z0-9_+.#-]{2,}", (text or "").lower()))

    def _similarity(self, a: str, b: str) -> float:
        ta, tb = self._tokens(a), self._tokens(b)
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / len(ta | tb)

    def detect_for_memory(self, db, memory, all_facts: Optional[List] = None,
                          scope_ids: Optional[Iterable[int]] = None) -> List[Dict[str, Any]]:
        """
        Find memories that conflict with this one.

        Two independent signals are combined:
          (a) temporal  - both memories assert the same predicate with different objects
          (b) lexical   - the texts are about the same thing and one negates the other

        `scope_ids` limits which memories this one may be compared against. Without
        it the comparison set is "the most recent N memories in the database",
        which on a used machine is mostly the user's own notes - and once more than
        N memories are newer than the ones under test, the ones under test are not
        compared at all. The benchmark passes its corpus ids so its conflict set is
        a property of the corpus.
        """
        from app.models.research import TemporalFact

        conflicts: List[Dict[str, Any]] = []
        text = f"{memory.title or ''} {memory.content or ''}".lower()

        # ---- (a) temporal conflicts -------------------------------------
        facts = db.query(TemporalFact).filter(TemporalFact.source_memory_id == memory.id).all()
        for fact in facts:
            if fact.valid_to is not None and fact.superseded_by:
                newer = db.query(TemporalFact).filter(TemporalFact.id == fact.superseded_by).first()
                if newer and newer.source_memory_id and newer.source_memory_id != memory.id:
                    conflicts.append({
                        "subject": fact.subject,
                        "predicate": fact.predicate,
                        "older_memory_id": memory.id,
                        "newer_memory_id": newer.source_memory_id,
                        "older_value": fact.object,
                        "newer_value": newer.object,
                        "conflict_type": "value_change",
                        "severity": 0.8,
                        "detected_by": "temporal",
                    })

        # ---- (b) lexical negation conflicts -----------------------------
        has_negation = _has_negation(text)
        if has_negation:
            from app.models.memory import Memory

            candidate_query = db.query(Memory).filter(Memory.id != memory.id)
            if scope_ids is not None:
                candidate_query = candidate_query.filter(Memory.id.in_(scope_ids))
            candidates = (
                candidate_query.order_by(Memory.created_at.desc()).limit(80).all()
            )
            mine = self._tokens(text)
            for other in candidates:
                other_text = f"{other.title or ''} {other.content or ''}".lower()
                if _has_negation(other_text):
                    continue      # both negative: not a conflict
                similarity = self._similarity(text, other_text)
                if similarity < self.min_similarity:
                    continue
                # same topic, one denies -> conflict
                conflicts.append({
                    "subject": "user",
                    "predicate": "claim",
                    "older_memory_id": None,
                    "newer_memory_id": memory.id,
                    "older_value": other.title or other.content[:60],
                    "newer_value": text[:60],
                    "conflict_type": "negation",
                    "severity": round(min(0.9, similarity + 0.2), 3),
                    "detected_by": "lexical",
                })
                break

        # ---- (c) factual value changes --------------------------------
        conflicts.extend(self._detect_value_changes(db, memory, scope_ids))

        return conflicts

    # ---------------------------------------------------- value changes
    DATE_PATTERN = re.compile(
        r"\b(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{0,4}"
        r"|\d{4}-\d{2}-\d{2}"
        r"|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
        re.IGNORECASE,
    )

    def _signature(self, text: str) -> set:
        """Salient topic words, used to decide whether two texts discuss the same thing."""
        words = re.findall(r"[a-z][a-z0-9_+.#-]{3,}", (text or "").lower())
        # Only GENERIC filler is removed. An earlier version also stripped
        # "deadline" and "project" - which are precisely the topic words that
        # make two memories about the same subject, so the strongest real
        # contradiction in the corpus stopped being detected.
        return {w for w in words if w not in {
            "according", "first", "earlier", "cancelled", "canceled",
            "replaced", "moved", "this", "that", "with", "from", "have",
            "been", "will", "than", "now", "date", "notice",
        }}

    def _detect_value_changes(self, db, memory,
                              scope_ids: Optional[Iterable[int]] = None) -> List[Dict[str, Any]]:
        """
        Same topic, different dated/numeric value, different time -> conflict.

        Rule-based and conservative: it requires (a) a shared topic signature and
        (b) differing extracted values, so unrelated memories that both happen to
        contain a date are not paired.
        """
        from app.models.memory import Memory

        text = f"{memory.title or ''} {memory.content or ''}"
        my_values = {v.lower().strip() for v in self.DATE_PATTERN.findall(text)}
        if not my_values:
            return []

        my_sig = self._signature(text)
        if len(my_sig) < 2:
            return []

        out: List[Dict[str, Any]] = []
        candidate_query = db.query(Memory).filter(Memory.id != memory.id)
        if scope_ids is not None:
            candidate_query = candidate_query.filter(Memory.id.in_(scope_ids))
        candidates = (
            candidate_query.order_by(Memory.created_at.desc()).limit(120).all()
        )

        for other in candidates:
            other_text = f"{other.title or ''} {other.content or ''}"
            other_values = {v.lower().strip() for v in self.DATE_PATTERN.findall(other_text)}
            if not other_values or other_values == my_values:
                continue

            other_sig = self._signature(other_text)
            shared = my_sig & other_sig
            overlap = len(shared) / max(1, min(len(my_sig), len(other_sig)))

            # Precision over recall. A false contradiction told to the user is
            # worse than a missed one, and a loose threshold paired any two
            # memories that happened to contain a date. Requiring BOTH a high
            # overlap AND a few shared salient words keeps the pairings honest.
            if overlap < 0.5 or len(shared) < 3:
                continue

            mine_time = memory.created_at or datetime.min
            other_time = other.created_at or datetime.min
            if mine_time >= other_time:
                older_id, newer_id = other.id, memory.id
                older_val, newer_val = sorted(other_values)[0], sorted(my_values)[0]
            else:
                older_id, newer_id = memory.id, other.id
                older_val, newer_val = sorted(my_values)[0], sorted(other_values)[0]

            out.append({
                "subject": "topic",
                "predicate": "dated_value",
                "older_memory_id": older_id,
                "newer_memory_id": newer_id,
                "older_value": older_val,
                "newer_value": newer_val,
                "conflict_type": "value_change",
                "severity": round(min(0.9, 0.5 + overlap * 0.4), 3),
                "detected_by": "value_change",
                "_shared": sorted(shared)[:4],
            })

        return out

    # ------------------------------------------------------------- resolving
    def resolve(self, db, memory_ids: Optional[List[int]] = None,
                scope_ids: Optional[Iterable[int]] = None) -> Dict[str, Any]:
        """
        Detect and store conflicts; mark which memory retrieval should prefer.

        `memory_ids` selects which memories to examine, `scope_ids` which memories
        they may be compared against (default: the whole database). Keeping them
        separate matters for evaluation - and for the stored rows, a scoped run
        only clears the conflicts that touch its scope, so it cannot wipe the
        user's conflict history.
        """
        from app.models.memory import Memory
        from app.models.research import MemoryConflict

        query = db.query(Memory)
        if memory_ids:
            query = query.filter(Memory.id.in_(memory_ids))
        memories = query.all()

        # Clear previous auto-detections so a re-run does not accumulate
        if scope_ids is not None:
            scope = list(scope_ids)
            db.query(MemoryConflict).filter(
                (MemoryConflict.older_memory_id.in_(scope)) |
                (MemoryConflict.newer_memory_id.in_(scope))
            ).delete(synchronize_session=False)
        else:
            db.query(MemoryConflict).delete()
        db.commit()

        stored = 0
        seen_pairs = set()
        for memory in memories:
            for conflict in self.detect_for_memory(db, memory, scope_ids=scope_ids):
                pair = (
                    conflict.get("older_memory_id"),
                    conflict.get("newer_memory_id"),
                    conflict.get("conflict_type"),
                )
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)

                # Default policy: the newer assertion wins, unless the user
                # explicitly confirms the older one.
                resolution = "prefer_newer"
                older_id = conflict.get("older_memory_id")
                newer_id = conflict.get("newer_memory_id")
                if older_id and newer_id:
                    older = db.query(Memory).filter(Memory.id == older_id).first()
                    newer = db.query(Memory).filter(Memory.id == newer_id).first()
                    if older and newer:
                        older_time = older.created_at or datetime.min
                        newer_time = newer.created_at or datetime.min
                        if older_time > newer_time:
                            # labels swapped relative to time: trust the clock
                            conflict["older_memory_id"], conflict["newer_memory_id"] = newer_id, older_id
                            conflict["older_value"], conflict["newer_value"] = \
                                conflict["newer_value"], conflict["older_value"]

                row = MemoryConflict(
                    subject=conflict["subject"],
                    predicate=conflict["predicate"],
                    older_memory_id=conflict.get("older_memory_id"),
                    newer_memory_id=conflict.get("newer_memory_id"),
                    older_value=str(conflict.get("older_value", ""))[:300],
                    newer_value=str(conflict.get("newer_value", ""))[:300],
                    detected_by=conflict.get("detected_by", "rule"),
                    conflict_type=conflict.get("conflict_type", "value_change"),
                    severity=float(conflict.get("severity", 0.5)),
                    resolution=resolution,
                    resolved=False,
                    detected_at=datetime.utcnow(),
                )
                db.add(row)
                stored += 1

        db.commit()
        return {"conflicts": stored, "memories_examined": len(memories)}

    # --------------------------------------------------- retrieval weighting
    def conflict_penalty(self, db, memory_id: int) -> Tuple[float, str]:
        """
        Returns (multiplier, reason) for retrieval scoring.

        A superseded memory is damped but NOT removed - damping preserves
        "what did I used to think?", removal destroys it.
        """
        from app.models.research import MemoryConflict

        conflicts = db.query(MemoryConflict).filter(
            MemoryConflict.older_memory_id == memory_id,
            MemoryConflict.resolved == False,  # noqa: E712
        ).all()
        if not conflicts:
            return 1.0, ""

        worst = max(c.severity for c in conflicts)
        # 0.3 .. 1.0 : a severe conflict damps the memory to 30%
        multiplier = 1.0 - (0.7 * worst)
        return round(multiplier, 3), f"superseded by memory {conflicts[0].newer_memory_id}"

    def summary(self, db) -> Dict[str, Any]:
        from app.models.research import MemoryConflict

        rows = db.query(MemoryConflict).all()
        by_type: Dict[str, int] = {}
        for row in rows:
            by_type[row.conflict_type] = by_type.get(row.conflict_type, 0) + 1
        return {
            "total": len(rows),
            "by_type": by_type,
            "unresolved": sum(1 for r in rows if not r.resolved),
            "conflicts": [
                {
                    "id": r.id, "predicate": r.predicate, "type": r.conflict_type,
                    "older_value": r.older_value, "newer_value": r.newer_value,
                    "older_memory_id": r.older_memory_id, "newer_memory_id": r.newer_memory_id,
                    "severity": r.severity, "resolution": r.resolution,
                }
                for r in sorted(rows, key=lambda x: -x.severity)[:40]
            ],
        }


contradiction_resolver = ContradictionResolver()
