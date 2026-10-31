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


# Hedged statements are uncertain claims, not assertions. They are not recorded
# as hard conflicts: "might be at 2 PM" does not contradict "is at 10 AM".
# Restriction markers. Two memories that both restrict the same statement
# ("never outside sessions" versus "only inside sessions") are usually saying
# the same thing, and MNLI reads that pair as a contradiction. When both sides
# carry a marker the neural signal alone is not trusted.
POLARITY_PATTERN = re.compile(
    r"\b(?:not|never|no|none|nothing|without|cannot|can't|only|except|excluding)\b",
    re.IGNORECASE,
)


HEDGE_PATTERN = re.compile(
    r"\b(?:might|maybe|possibly|perhaps|probably|not sure|unsure|unconfirmed|tentative(?:ly)?|tbc|to be confirmed|i think|i believe)\b",
    re.IGNORECASE,
)


def _is_hedged(text: str) -> bool:
    return bool(HEDGE_PATTERN.search(text or ""))


# Clock times: "10 AM", "2:30pm", "14:00". Normalised to "10am", "2:30pm", "14:00".
TIME_PATTERN = re.compile(
    r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm))\b|\b([01]?\d|2[0-3]):([0-5]\d)\b",
    re.IGNORECASE,
)


def _clock_times(text: str) -> set:
    found = set()
    for m in TIME_PATTERN.finditer(text or ""):
        if m.group(1):
            found.add(re.sub(r"\s+", "", m.group(1).lower()))
        else:
            found.add(f"{int(m.group(2)):02d}:{m.group(3)}")
    return found


class ContradictionResolver:
    def __init__(self):
        self.min_similarity = 0.45

    # ------------------------------------------------------------- detection
    @staticmethod
    def _tokens(text: str) -> set:
        """
        Lowercase word set. Surrounding punctuation is stripped first: the raw
        pattern kept the sentence-final full stop, so "RAM." and "RAM" were
        different tokens and a near-identical pair failed the similarity gate.
        Interior punctuation that carries meaning (v2.0, c++) is preserved.
        """
        words = re.findall(r"[a-z][a-z0-9_+.#-]{2,}", (text or "").lower())
        return {w.strip(".,;:!?-_#") for w in words if len(w.strip(".,;:!?-_#")) >= 2}

    def _similarity(self, a: str, b: str) -> float:
        ta, tb = self._tokens(a), self._tokens(b)
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / len(ta | tb)

    def _detect_neural_conflicts(
        self, db, memory, scope_ids: Optional[Iterable[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Neural Natural Language Inference (NLI) conflict detection.
        Uses a lightweight ONNX Cross-Encoder to detect semantic contradictions
        and moved values that rule-based patterns miss.
        """
        try:
            from app.models.memory import Memory
            from app.research.neural_nli import neural_nli

            if not neural_nli.is_available():
                return []

            text = f"{memory.title or ''} {memory.content or ''}".strip()
            if not text:
                return []

            my_tokens = self._tokens(text)
            if not my_tokens:
                return []

            candidate_query = db.query(Memory).filter(Memory.id != memory.id)
            if scope_ids is not None:
                candidate_query = candidate_query.filter(Memory.id.in_(scope_ids))
            candidates = candidate_query.order_by(Memory.created_at.desc()).limit(80).all()

            conflicts = []
            for other in candidates:
                other_text = f"{other.title or ''} {other.content or ''}".strip()
                other_tokens = self._tokens(other_text)

                # Fast-path screen: must share at least 2 salient tokens
                shared = my_tokens & other_tokens
                if len(shared) < 2 and (len(shared) / max(1, len(my_tokens | other_tokens))) < 0.15:
                    continue

                # Both premise orders must agree, and two one-sided
                # restriction markers cancel the signal.
                if bool(POLARITY_PATTERN.search(text)) and bool(POLARITY_PATTERN.search(other_text)):
                    continue

                is_conflict, severity, _ = neural_nli.classify_conflict(
                    text, other_text, threshold=0.55, both_orders=True
                )
                if is_conflict:
                    mine_time = memory.created_at or datetime.min
                    other_time = other.created_at or datetime.min
                    if mine_time >= other_time:
                        older_id, newer_id = other.id, memory.id
                        older_val, newer_val = other_text[:120], text[:120]
                    else:
                        older_id, newer_id = memory.id, other.id
                        older_val, newer_val = text[:120], other_text[:120]

                    conflicts.append({
                        "subject": "statement",
                        "predicate": "claim",
                        "older_memory_id": older_id,
                        "newer_memory_id": newer_id,
                        "older_value": older_val,
                        "newer_value": newer_val,
                        "conflict_type": "contradiction",
                        "severity": round(severity, 3),
                        "detected_by": "neural_nli",
                    })

            return conflicts
        except Exception:
            return []

    def detect_for_memory(self, db, memory, all_facts: Optional[List] = None,
                          scope_ids: Optional[Iterable[int]] = None,
                          use_neural: bool = True) -> List[Dict[str, Any]]:
        """
        Find memories that conflict with this one.

        Three signals are combined:
          (a) temporal  - both memories assert the same predicate with different objects
          (b) lexical   - the texts are about the same thing and one negates the other
          (c) neural    - lightweight ONNX cross-encoder NLI semantic contradiction
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
                if _is_hedged(text) or _is_hedged(other_text):
                    continue      # uncertain claim: not a hard conflict
                # same topic, one denies -> conflict. Name the older side by
                # time: the retrieval penalty damps the OLDER memory.
                other_time = other.created_at or datetime.min
                mine_time = memory.created_at or datetime.min
                if other_time <= mine_time:
                    older_m, newer_m = other, memory
                else:
                    older_m, newer_m = memory, other
                conflicts.append({
                    "subject": "user",
                    "predicate": "claim",
                    "older_memory_id": older_m.id,
                    "newer_memory_id": newer_m.id,
                    "older_value": (older_m.title or older_m.content or "")[:60],
                    "newer_value": (newer_m.title or newer_m.content or "")[:60],
                    "conflict_type": "negation",
                    "severity": round(min(0.9, similarity + 0.2), 3),
                    "detected_by": "lexical",
                })
                break

        # ---- (c) factual value changes --------------------------------
        conflicts.extend(self._detect_value_changes(db, memory, scope_ids))
        conflicts.extend(self._detect_slot_changes(db, memory, scope_ids))

        # ---- (d) neural NLI contradictions ----------------------------
        if use_neural:
            conflicts.extend(self._detect_neural_conflicts(db, memory, scope_ids))

        return conflicts

    # ------------------------------------------- generalised value slots
    # The dated-value rule below only fires when both memories carry a
    # calendar date. Supersession in a personal memory store is usually not
    # dated: "40 GPU-hours per epoch" becomes "12 GPU-hours", "8,000
    # screenshots" becomes "5,400", a repository moves from GitLab to GitHub.
    # This detector extracts typed value slots and compares them instead.
    # A number plus the word that names what it counts: "8,000 labelled
    # screenshots" anchors on "labelled", "2,400 rupees" on "rupees". The
    # anchor, not the unit spelling, decides whether two numbers occupy the
    # same slot, so "10 AM" and "2 PM" never pair while "12 synthetic
    # memories" and "15 synthetic memories" do.
    NUMBER_PATTERN = re.compile(r"\b(\d[\d,]*(?:\.\d+)?)\b")
    SLOT_SKIPWORDS = {
        "the", "a", "an", "of", "and", "or", "to", "in", "on", "at", "for",
        "is", "was", "were", "be", "been", "per", "by", "with", "from",
    }

    MONTH_OR_DAY = {
        "jan", "january", "feb", "february", "mar", "march", "apr", "april",
        "may", "jun", "june", "jul", "july", "aug", "august", "sep", "sept",
        "september", "oct", "october", "nov", "november", "dec", "december",
        "mon", "tue", "tues", "wed", "thu", "thur", "thurs", "fri", "sat", "sun",
    }

    # A change of circumstances is normally announced. Requiring the cue in
    # exactly one memory keeps the rule from pairing two statements that both
    # describe a stable state.
    CHANGE_CUE = re.compile(
        r"\b(?:now|switched|switch(?:ed)? to|moved|migrated|changed|instead|"
        r"any ?more|no longer|after the|upgraded|replaced|extended)\b",
        re.IGNORECASE,
    )

    def _quantities(self, text: str) -> set:
        """(value, slot anchor) pairs for every number in the text."""
        out = set()
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#._-]*|\d[\d,]*(?:\.\d+)?", text or "")
        for index, token in enumerate(tokens):
            if not token[0].isdigit():
                continue
            try:
                value = float(token.replace(",", ""))
            except ValueError:
                continue
            anchor = ""
            for follow in tokens[index + 1:index + 4]:
                low = follow.lower().strip(".,;:!?-#")
                if follow[0].isdigit() or low in self.SLOT_SKIPWORDS or len(low) < 2:
                    continue
                # Dates belong to the calendar rule, so a month or weekday is
                # never a numeric slot anchor.
                if low in self.MONTH_OR_DAY:
                    continue
                anchor = low
                break
            if anchor:
                out.add((value, anchor))
        return out

    ENTITY_STOPWORDS = {
        "the", "a", "an", "and", "but", "after", "before", "every", "each",
        "this", "that", "these", "those", "then", "now", "again", "also",
        "i", "my", "me", "we", "our", "you", "your", "it", "its",
    }

    def _entities(self, text: str) -> set:
        """Capitalised tokens that are not sentence-initial, dates or stopwords."""
        found = set()
        for sentence in re.split(r"[.!?\n]", text or ""):
            words = re.findall(r"[A-Za-z][A-Za-z0-9+#._-]{2,}", sentence or "")
            for word in words[1:]:
                low = word.lower()
                if word[0].isupper() and low not in self.MONTH_OR_DAY \
                        and low not in self.ENTITY_STOPWORDS:
                    found.add(low)
        return found

    def _detect_slot_changes(self, db, memory,
                             scope_ids: Optional[Iterable[int]] = None) -> List[Dict[str, Any]]:
        """Same topic, different typed value slot (quantity or named entity)."""
        from app.models.memory import Memory

        text = f"{memory.title or ''} {memory.content or ''}".strip()
        my_sig = self._signature(text)
        my_qty = self._quantities(text)
        my_ent = self._entities(text)
        my_cue = bool(self.CHANGE_CUE.search(text))
        if len(my_sig) < 2 or (not my_qty and not my_ent):
            return []
        if _is_hedged(text):
            return []

        candidate_query = db.query(Memory).filter(Memory.id != memory.id)
        if scope_ids is not None:
            candidate_query = candidate_query.filter(Memory.id.in_(scope_ids))
        candidates = candidate_query.order_by(Memory.created_at.desc()).limit(120).all()

        out: List[Dict[str, Any]] = []
        for other in candidates:
            other_text = f"{other.title or ''} {other.content or ''}".strip()
            other_sig = self._signature(other_text)
            shared = my_sig & other_sig
            if not shared:
                continue
            overlap = len(shared) / max(1, min(len(my_sig), len(other_sig)))
            if _is_hedged(other_text):
                continue

            other_qty = self._quantities(other_text)
            other_ent = self._entities(other_text)
            other_cue = bool(self.CHANGE_CUE.search(other_text))

            kind, mine_val, other_val = None, "", ""
            # (a) quantity slot: same unit, different number
            anchors = {a for _, a in my_qty} & {a for _, a in other_qty}
            if shared and anchors and overlap >= 0.15:
                mine_vals = {v for v, a in my_qty if a in anchors}
                other_vals = {v for v, a in other_qty if a in anchors}
                if mine_vals and other_vals and mine_vals != other_vals:
                    kind = "quantity"
                    mine_val = "%g" % sorted(mine_vals)[0]
                    other_val = "%g" % sorted(other_vals)[0]

            # (b) entity slot: both name a different entity and one side
            #     announces a change of circumstances
            if kind is None and my_cue != other_cue and overlap >= 0.10:
                only_mine, only_other = my_ent - other_ent, other_ent - my_ent
                if only_mine and only_other:
                    kind = "entity"
                    mine_val = sorted(only_mine)[0]
                    other_val = sorted(only_other)[0]

            if kind is None:
                continue

            mine_time = memory.created_at or datetime.min
            other_time = other.created_at or datetime.min
            if mine_time >= other_time:
                older_id, newer_id = other.id, memory.id
                older_val, newer_val = other_val, mine_val
            else:
                older_id, newer_id = memory.id, other.id
                older_val, newer_val = mine_val, other_val

            out.append({
                "subject": "topic",
                "predicate": kind,
                "older_memory_id": older_id,
                "newer_memory_id": newer_id,
                "older_value": older_val,
                "newer_value": newer_val,
                "conflict_type": "value_change",
                "severity": round(min(0.9, 0.5 + overlap * 0.4), 3),
                "detected_by": "value_slot",
                "_shared": sorted(shared)[:4],
            })
        return out

    # ---------------------------------------------------- value changes
    DATE_PATTERN = re.compile(
        r"\b(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{0,4}"
        r"|\d{4}-\d{2}-\d{2}"
        r"|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
        re.IGNORECASE,
    )

    def _signature(self, text: str) -> set:
        """Salient topic words, used to decide whether two texts discuss the same thing."""
        words = [w.strip(".,;:!?-_#")
                 for w in re.findall(r"[a-z][a-z0-9_+.#-]{3,}", (text or "").lower())]
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

        my_hedged = _is_hedged(text)
        my_times = _clock_times(text)
        for other in candidates:
            other_text = f"{other.title or ''} {other.content or ''}"
            other_values = {v.lower().strip() for v in self.DATE_PATTERN.findall(other_text)}
            if not other_values:
                continue

            other_sig = self._signature(other_text)
            shared = my_sig & other_sig
            overlap = len(shared) / max(1, min(len(my_sig), len(other_sig)))

            # Precision over recall. A false contradiction told to the user is
            # worse than a missed one, and a loose threshold paired any two
            # memories that happened to contain a date. Requiring BOTH a high
            # overlap AND a few shared salient words keeps the pairings honest.
            if overlap < 0.5 or len(shared) < 2:
                continue

            # Uncertain claims are not hard conflicts.
            if my_hedged or _is_hedged(other_text):
                continue

            if other_values == my_values:
                # Same anchor date. A different single clock time for the same
                # topic is a genuine contradiction ("10 AM" vs "2 PM" on 20 Oct).
                other_times = _clock_times(other_text)
                if len(my_times) == 1 and len(other_times) == 1 and my_times != other_times:
                    mine_time = memory.created_at or datetime.min
                    other_time = other.created_at or datetime.min
                    if mine_time >= other_time:
                        older_id, newer_id = other.id, memory.id
                        older_val, newer_val = sorted(other_times)[0], sorted(my_times)[0]
                    else:
                        older_id, newer_id = memory.id, other.id
                        older_val, newer_val = sorted(my_times)[0], sorted(other_times)[0]
                    out.append({
                        "subject": "topic",
                        "predicate": "clock_time",
                        "older_memory_id": older_id,
                        "newer_memory_id": newer_id,
                        "older_value": older_val,
                        "newer_value": newer_val,
                        "conflict_type": "contradiction",
                        "severity": round(min(0.9, 0.6 + overlap * 0.3), 3),
                        "detected_by": "value_change",
                        "_shared": sorted(shared)[:4],
                    })
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
                scope_ids: Optional[Iterable[int]] = None,
                use_neural: bool = True) -> Dict[str, Any]:
        """
        Detect and store conflicts; mark which memory retrieval should prefer.

        `memory_ids` selects which memories to examine, `scope_ids` which memories
        they may be compared against (default: the whole database). Keeping them
        separate matters for evaluation - and for the stored rows, a scoped run
        only clears the conflicts that touch its scope, so it cannot wipe the
        user's conflict history.
        `use_neural` controls whether the lightweight ONNX NLI classifier is used.
        """
        from app.models.memory import Memory
        from app.models.research import MemoryConflict

        query = db.query(Memory)
        if memory_ids:
            query = query.filter(Memory.id.in_(memory_ids))
        memories = query.all()

        # Clear previous UNRESOLVED auto-detections so a re-run does not
        # accumulate. Resolved conflicts are evidence a user reviewed; they are
        # never deleted by a re-scan.
        unresolved = MemoryConflict.resolved == False  # noqa: E712
        if scope_ids is not None:
            scope = list(scope_ids)
            db.query(MemoryConflict).filter(
                unresolved,
                (MemoryConflict.older_memory_id.in_(scope)) |
                (MemoryConflict.newer_memory_id.in_(scope))
            ).delete(synchronize_session=False)
        else:
            db.query(MemoryConflict).filter(unresolved).delete(synchronize_session=False)
        db.commit()

        stored = 0
        seen_pairs = set()
        for memory in memories:
            for conflict in self.detect_for_memory(db, memory, scope_ids=scope_ids, use_neural=use_neural):
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

                # Do not re-store a pair that already has a row (for example one
                # the user resolved): the evidence is kept once, not duplicated.
                already = db.query(MemoryConflict).filter(
                    MemoryConflict.older_memory_id == conflict.get("older_memory_id"),
                    MemoryConflict.newer_memory_id == conflict.get("newer_memory_id"),
                    MemoryConflict.conflict_type == conflict.get("conflict_type", "value_change"),
                ).first()
                if already is not None:
                    continue

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
