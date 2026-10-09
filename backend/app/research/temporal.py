"""
Contribution 2 - Temporal Personal Knowledge Graph.
===========================================================================
A personal graph that is timeless cannot answer "what am I working on NOW?".
If "learning Python" (January) and "learning Java" (September) are both simply
true, retrieval returns whichever chunk scores higher and the assistant reports
stale facts with full confidence. That is the failure this fixes.

Model: facts are (subject, predicate, object) triples with a validity interval
[valid_from, valid_to). A NULL valid_to means "still true". When a new fact
arrives with the same (subject, predicate) but a different object, the older one
is CLOSED (valid_to set, superseded_by linked) rather than deleted, so history
survives and "what did I used to think?" remains answerable.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Iterable

# Predicates that describe a current state, and therefore supersede.
STATEFUL_PREDICATES = {
    "current_focus", "current_project", "using", "prefers",
    "located_in", "employed_by", "status",
}

# Predicates are normalised into canonical STATE CLASSES before supersession.
#
# Without this, "I am learning Python" and "I am now focusing on Java" were
# stored under different predicates ("learning" vs "focus"), so neither
# superseded the other and the graph happily reported both as current. That is
# exactly the failure temporal modelling is supposed to prevent - and it is the
# kind of near-miss that looks correct until it is measured.
PREDICATE_CANON = {
    "learning": "current_focus",
    "studying": "current_focus",
    "focus": "current_focus",
    "focused_on": "current_focus",
    "working_on": "current_project",
    "building": "current_project",
}

# Pattern -> (predicate, confidence). Deliberately conservative: a wrong fact in
# a personal graph is worse than a missing one.
FACT_PATTERNS: List[Tuple[str, str, float]] = [
    (r"\bi(?:'m| am| was)?\s+(?:currently\s+)?(?:learning|studying)\s+([A-Za-z0-9+#.\- ]{2,40})", "learning", 0.85),
    (r"\bi(?:'m| am)\s+(?:now\s+)?(?:mainly\s+|primarily\s+|mostly\s+)?focus(?:ed|ing)?\s+(?:on|in)\s+([A-Za-z0-9+#.\- ]{2,40})", "focus", 0.85),
    (r"\bi(?:'m| am)\s+working\s+on\s+([A-Za-z0-9+#.\- ]{2,60})", "working_on", 0.80),
    (r"\bi\s+(?:use|prefer)\s+([A-Za-z0-9+#.\- ]{2,40})", "using", 0.70),
    (r"\bmy\s+project\s+is\s+([A-Za-z0-9+#.\- ]{2,60})", "working_on", 0.80),
    (r"\bi\s+(?:live|am based)\s+in\s+([A-Za-z0-9 ,.\-]{2,40})", "located_in", 0.75),
    (r"\bi\s+know\s+([A-Za-z0-9+#.\- ]{2,40})", "knows", 0.70),
    (r"\bi(?:'m| am)\s+not\s+learning\s+([A-Za-z0-9+#.\- ]{2,40})", "learning", 0.80),
]

NEGATION_WORDS = ("not", "no longer", "stopped", "quit", "gave up", "dropped", "switched from")

SUBJECT = "user"


class TemporalKnowledgeGraph:
    def __init__(self):
        self.subject = SUBJECT

    # ----------------------------------------------------------- extraction
    @staticmethod
    def _clean_object(value: str) -> str:
        value = value.strip(" .,;:-")
        # cut trailing clauses that leak in from free text
        value = re.split(r"\b(?:because|since|so|but|and then|which|that)\b", value, maxsplit=1)[0]
        return value.strip(" .,;:-")[:120]

    def _extract_neural_facts(self, text: str) -> List[Dict[str, Any]]:
        """
        Lightweight neural dependency parsing and entity extraction using spaCy.
        Catches natural language variations and syntactic structures that static regex misses.
        """
        try:
            import spacy
            try:
                nlp = spacy.load("en_core_web_sm")
            except Exception:
                return []

            state_map = {
                "learn": "learning", "study": "learning", "focus": "focus",
                "concentrate": "focus", "switch": "focus", "specialize": "focus",
                "work": "working_on", "build": "working_on", "develop": "working_on",
                "create": "working_on", "use": "using", "prefer": "using",
                "adopt": "using", "live": "located_in", "reside": "located_in",
                "relocate": "located_in",
            }

            doc = nlp(text or "")
            facts = []

            for token in doc:
                lemma = token.lemma_.lower()
                if lemma not in state_map:
                    continue

                subjs = [w for w in token.children if "subj" in w.dep_]
                has_first_person = any(w.text.lower() in ("i", "we", "me") for w in subjs)
                if not has_first_person and not any(t.text.lower() in ("i", "my") for t in doc[:5]):
                    continue

                negated = any(
                    w.dep_ == "neg" or w.lower_ in ("not", "never", "stopped", "quit")
                    for w in token.children
                )

                target_obj = None
                dobjs = [w for w in token.children if "obj" in w.dep_ or w.dep_ == "dobj"]
                if dobjs:
                    dobj = dobjs[0]
                    target_obj = " ".join([t.text for t in dobj.subtree if t.dep_ not in ("prep", "punct")])

                if not target_obj:
                    for prep in [w for w in token.children if w.dep_ == "prep"]:
                        pobjs = [w for w in prep.children if "obj" in w.dep_ or w.dep_ == "pobj"]
                        if pobjs:
                            pobj = pobjs[0]
                            target_obj = " ".join([t.text for t in pobj.subtree if t.dep_ not in ("prep", "punct")])
                            break

                if target_obj:
                    clean_obj = self._clean_object(target_obj)
                    if clean_obj and len(clean_obj) > 1:
                        facts.append({
                            "subject": self.subject,
                            "predicate": state_map[lemma],
                            "object": clean_obj,
                            "negated": negated,
                            "confidence": 0.82,
                            "evidence": token.sent.text[:200],
                            "method": "neural_dep",
                        })

            return facts
        except Exception:
            return []

    def extract_facts(self, text: str, use_neural: bool = True) -> List[Dict[str, Any]]:
        """Rule-based + Neural dependency triple extraction."""
        lowered = (text or "").lower()
        facts: List[Dict[str, Any]] = []

        for pattern, predicate, confidence in FACT_PATTERNS:
            for match in re.finditer(pattern, lowered, flags=re.IGNORECASE):
                obj = self._clean_object(match.group(1))
                if not obj:
                    continue

                # "I'm not learning X" should RETRACT, not assert
                context = lowered[max(0, match.start() - 40): match.start()]
                negated = any(neg in context for neg in NEGATION_WORDS) or "not learning" in match.group(0)

                facts.append({
                    "subject": self.subject,
                    "predicate": predicate,
                    "object": obj,
                    "negated": negated,
                    "confidence": confidence,
                    "evidence": match.group(0)[:200],
                    "method": "rule",
                })

        # Add neural dependency-extracted facts for phrases regex missed
        if use_neural:
            neural_facts = self._extract_neural_facts(text)
            facts.extend(neural_facts)

        # de-duplicate triples within one text, merging overlapping phrases
        unique = []
        for fact in facts:
            is_dup = False
            for u in unique:
                if u["predicate"] == fact["predicate"] and u["negated"] == fact["negated"]:
                    o1, o2 = u["object"].lower(), fact["object"].lower()
                    if o1 in o2 or o2 in o1:
                        is_dup = True
                        # If the new object is cleaner/shorter (e.g. 'Python' vs 'python for data analysis'), keep the cleaner one
                        if len(fact["object"]) < len(u["object"]) and len(fact["object"]) >= 3:
                            u["object"] = fact["object"]
                            u["evidence"] = fact["evidence"]
                        break
            if not is_dup:
                unique.append(fact)
        return unique

    # -------------------------------------------------------------- merging
    @staticmethod
    def _open_facts(db, TemporalFact, subject: str, predicate: str, scope) -> List:
        """
        The still-open facts matching this (subject, predicate).

        `scope=None` means the whole database; a set of memory ids limits the
        answer to facts asserted by those memories, which is what keeps an
        evaluation corpus from closing the user's own live facts.
        """
        query = db.query(TemporalFact).filter(
            TemporalFact.subject == subject,
            TemporalFact.predicate == predicate,
            TemporalFact.valid_to.is_(None),
        )
        if scope is not None:
            query = query.filter(TemporalFact.source_memory_id.in_(scope))
        return query.all()

    def record_facts(self, db, facts: List[Dict[str, Any]], source_memory_id: Optional[int] = None,
                     at: Optional[datetime] = None, user_id: Optional[int] = None,
                     scope_ids: Optional[Iterable[int]] = None) -> Dict[str, Any]:
        """
        Insert facts and apply supersession.

        A new stateful fact with the same (subject, predicate) but a different
        object CLOSES the previous one. That is what turns a pile of statements
        into a timeline.

        `scope_ids` limits which existing facts may be superseded. The evaluation
        corpus must not be able to close one of the user's live facts (nor have
        its own closed by one), otherwise the same corpus produces different
        results on two machines.
        """
        from app.models.research import TemporalFact

        at = at or datetime.utcnow()
        created, superseded, retracted = 0, 0, 0
        scope = set(scope_ids) if scope_ids is not None else None

        for fact in facts:
            subject = fact["subject"]
            predicate = PREDICATE_CANON.get(fact["predicate"], fact["predicate"])
            obj = fact["object"]

            if fact.get("negated"):
                # Retraction: close any open fact with this predicate.
                open_rows = self._open_facts(db, TemporalFact, subject, predicate, scope)
                for row in open_rows:
                    row.valid_to = at
                    retracted += 1
                db.flush()
                continue

            open_rows = self._open_facts(db, TemporalFact, subject, predicate, scope)

            same_object = next((r for r in open_rows if r.object.lower() == obj.lower()), None)
            if same_object:
                # Re-assertion: reinforce confidence instead of duplicating.
                same_object.confidence = min(1.0, (same_object.confidence or 0.7) + 0.05)
                continue

            new_row = TemporalFact(
                subject=subject,
                predicate=predicate,
                object=obj,
                valid_from=at,
                valid_to=None,
                confidence=fact.get("confidence", 0.7),
                source_memory_id=source_memory_id,
                extraction_method=fact.get("method", "rule"),
                evidence_text=fact.get("evidence", ""),
            )
            db.add(new_row)
            db.flush()
            created += 1

            if predicate in STATEFUL_PREDICATES:
                for row in open_rows:
                    row.valid_to = at
                    row.superseded_by = new_row.id
                    superseded += 1

        db.commit()
        return {"created": created, "superseded": superseded, "retracted": retracted}

    # ------------------------------------------------------------- querying
    def current_facts(self, db, predicate: Optional[str] = None) -> List[Dict[str, Any]]:
        from app.models.research import TemporalFact

        predicate = PREDICATE_CANON.get(predicate, predicate) if predicate else None
        query = db.query(TemporalFact).filter(
            TemporalFact.subject == self.subject, TemporalFact.valid_to.is_(None))
        if predicate:
            query = query.filter(TemporalFact.predicate == predicate)
        return [
            {
                "id": r.id, "subject": r.subject, "predicate": r.predicate, "object": r.object,
                "valid_from": r.valid_from.isoformat() if r.valid_from else None,
                "valid_to": None, "confidence": r.confidence, "current": True,
            }
            for r in query.order_by(TemporalFact.confidence.desc()).all()
        ]

    def history(self, db, predicate: Optional[str] = None) -> List[Dict[str, Any]]:
        from app.models.research import TemporalFact

        query = db.query(TemporalFact).filter(TemporalFact.subject == self.subject)
        if predicate:
            query = query.filter(TemporalFact.predicate == predicate)
        return [
            {
                "id": r.id, "predicate": r.predicate, "object": r.object,
                "valid_from": r.valid_from.isoformat() if r.valid_from else None,
                "valid_to": r.valid_to.isoformat() if r.valid_to else None,
                "superseded_by": r.superseded_by,
                "confidence": r.confidence,
                "current": r.valid_to is None,
            }
            for r in query.order_by(TemporalFact.valid_from.asc()).all()
        ]

    def current_focus(self, db) -> List[str]:
        """The objects the user is currently focused on (canonicalised)."""
        return [f["object"] for f in self.current_facts(db, "current_focus")]

    # ------------------------------------------------- temporal tie-breaking
    def temporal_weight(self, db, memory_id: int, now: Optional[datetime] = None) -> float:
        """
        How current is the knowledge in this memory?

        1.0 = asserts a fact that is still true
        0.4 = asserts a fact that has since been superseded
        0.7 = contains no temporal fact at all (neutral)
        """
        from app.models.research import TemporalFact

        now = now or datetime.utcnow()
        facts = db.query(TemporalFact).filter(TemporalFact.source_memory_id == memory_id).all()
        if not facts:
            return 0.7

        weights = []
        for fact in facts:
            if fact.valid_to is None:
                weights.append(1.0)
            elif fact.superseded_by:
                weights.append(0.4)      # outdated by a later statement
            else:
                weights.append(0.6)      # closed for some other reason
        return sum(weights) / len(weights)


temporal_knowledge_graph = TemporalKnowledgeGraph()
