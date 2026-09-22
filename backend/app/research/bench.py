"""
Contribution 7 - PersonalBrain-Bench, and the evaluation harness.
===========================================================================
The paper's claims are quantitative, so they need a measuring instrument.

PersonalBrain-Bench is a synthetic personal-knowledge corpus with a question set
that specifically probes the phenomena the research layer targets:

    factual      plain recall                          (all systems should do well)
    temporal     "what am I working on NOW?"           (needs validity intervals)
    contradiction two memories disagree                (needs conflict resolution)
    multi_hop    requires linking two memories         (needs the graph)
    forgetting   asks about something forgotten        (needs retrieval exclusion)
    gap          asks about a concept never learned    (needs honest abstention)

Metrics
    hit@k          did the gold memory appear in the top k
    mrr            mean reciprocal rank of the gold memory
    precision@k    fraction of retrieved items that are relevant
    staleness      fraction of results that are superseded or forgotten
    duplicate_rate fraction of results that are near-duplicates of each other
    context_tokens characters fed to the model (token-budget proxy)
    latency_ms     retrieval time

Stale and duplicate rates are the ones that matter for this paper: a baseline can
have decent hit@k while stuffing its context with outdated and repeated material,
which is precisely the failure the research layer addresses.

The corpus is synthetic ON PURPOSE. Using a real personal memory store would make
the experiment unreproducible and would put someone's private data in a paper.
"""
from __future__ import annotations

import json
import math
import re
import time
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# Importing the package registers every ORM mapper. Without this, running the
# benchmark from a bare script fails with a mapper-resolution error that looks
# unrelated to the actual cause.
import app.research  # noqa: F401

STOP = {
    "the", "and", "for", "with", "from", "that", "this", "what", "which", "when",
    "have", "has", "was", "were", "are", "you", "your", "not", "but", "all",
    "can", "will", "am", "is", "are", "my", "me", "i", "on", "in", "to", "of",
    "about", "currently", "now", "still", "any", "do", "does", "did",
}


def _tokens(text: str) -> set:
    return {w for w in re.findall(r"[a-z][a-z0-9_+.#-]{2,}", (text or "").lower()) if w not in STOP}


class PersonalBrainBench:
    """
    Synthetic personal corpus + graded question set.

    Times are relative to `now` at build time so the corpus always exercises real
    recency and supersession rather than depending on hard-coded dates.
    """

    def __init__(self):
        self.now = datetime.utcnow()

    # ------------------------------------------------------------- corpus
    def build_corpus(self) -> List[Dict[str, Any]]:
        now = self.now
        def days_ago(n: int) -> datetime:
            return now - timedelta(days=n)

        return [
            # ---- plain facts -------------------------------------------------
            {"key": "ieee", "title": "IEEE conference paper submission",
             "content": "The IEEE conference paper abstract must be submitted to the review "
                        "committee by 25 September 2026. The document uses two-column format.",
             "source_type": "email", "app_source": "vtu24334@veltech.edu.in", "created_at": days_ago(3)},
            {"key": "dataset", "title": "Central Pollution AQI dataset",
             "content": "The Central Pollution Control Board AQI dataset contains hourly readings "
                        "for particulate matter across monitoring stations from 2015 to 2024.",
             "source_type": "web", "app_source": "research", "created_at": days_ago(20)},
            {"key": "randomforest", "title": "Random Forest regressor for AQI",
             "content": "Random Forest regression predicts AQI from temperature humidity and "
                        "particulate features and is compared against XGBoost and linear baselines.",
             "source_type": "code", "app_source": "vscode", "created_at": days_ago(12)},

            # ---- TEMPORAL: superseded pair -----------------------------------
            {"key": "python_old", "title": "Learning Python",
             "content": "I am learning Python for data analysis and scripting.",
             "source_type": "note", "app_source": "notes", "created_at": days_ago(240)},
            {"key": "java_new", "title": "Focus on Java",
             "content": "I am now mainly focusing on Java for backend development with Spring Boot.",
             "source_type": "note", "app_source": "notes", "created_at": days_ago(4)},

            # ---- CONTRADICTION: project deadline changed ---------------------
            {"key": "deadline_old", "title": "Project deadline was October",
             "content": "The project evaluation deadline is 15 October 2026 according to the first notice.",
             "source_type": "email", "app_source": "college", "created_at": days_ago(60)},
            {"key": "deadline_new", "title": "Project deadline moved",
             "content": "The project evaluation deadline is now 30 September 2026. The earlier "
                        "October date was cancelled and replaced.",
             "source_type": "email", "app_source": "college", "created_at": days_ago(2)},

            # ---- MULTI-HOP ---------------------------------------------------
            {"key": "airnet", "title": "Air pollution neural network experiment",
             "content": "The air pollution project compares a neural network against the Random "
                        "Forest regressor on the pollution dataset.",
             "source_type": "code", "app_source": "vscode", "created_at": days_ago(8)},

            # ---- FORGETTING target -------------------------------------------
            {"key": "old_password", "title": "Temporary portal credential",
             "content": "The temporary lab portal credential was shared in a message and should "
                        "not be kept after the session.",
             "source_type": "clipboard", "app_source": "clipboard", "created_at": days_ago(30)},

            # ---- KNOWLEDGE GAP -----------------------------------------------
            {"key": "gap1", "title": "Multithreading",
             "content": "Multithreading appeared in the reading list.",
             "source_type": "screen", "app_source": "chrome", "created_at": days_ago(40)},
            {"key": "gap2", "title": "Multithreading notes",
             "content": "Multithreading multithreading multithreading is on the syllabus list.",
             "source_type": "screen", "app_source": "chrome", "created_at": days_ago(18)},
            {"key": "gap3", "title": "Syllabus topics",
             "content": "Topics remaining: multithreading, JDBC, exception handling.",
             "source_type": "screen", "app_source": "chrome", "created_at": days_ago(6)},

            # ---- DUPLICATES (for consolidation) ------------------------------
            {"key": "dup_a", "title": "FastAPI routing notes",
             "content": "FastAPI routing uses decorators to map HTTP methods and paths to "
                        "Python functions and supports dependency injection.",
             "source_type": "web", "app_source": "browser", "created_at": days_ago(15)},
            {"key": "dup_b", "title": "FastAPI routing notes",
             "content": "FastAPI routing uses decorators to map HTTP methods and paths to "
                        "Python functions and supports dependency injection.",
             "source_type": "web", "app_source": "browser", "created_at": days_ago(14)},
            {"key": "dup_c", "title": "FastAPI routing",
             "content": "FastAPI routing maps HTTP methods and paths to Python functions using "
                        "decorators, and supports dependency injection.",
             "source_type": "web", "app_source": "browser", "created_at": days_ago(13)},
        ]

    # ---------------------------------------------------------- questions
    def build_questions(self) -> List[Dict[str, Any]]:
        return [
            {"id": "q1", "type": "factual",
             "question": "When is the IEEE conference paper submission deadline?",
             "gold_keys": ["ieee"], "forbidden_keys": []},
            {"id": "q2", "type": "factual",
             "question": "What does the pollution dataset contain?",
             "gold_keys": ["dataset"], "forbidden_keys": []},
            {"id": "q3", "type": "factual",
             "question": "Which model is compared against Random Forest for AQI?",
             "gold_keys": ["randomforest", "airnet"], "forbidden_keys": []},

            {"id": "q4", "type": "temporal",
             "question": "What programming language am I currently focusing on?",
             "gold_keys": ["java_new"], "forbidden_keys": ["python_old"]},
            {"id": "q5", "type": "temporal",
             "question": "What am I learning right now?",
             "gold_keys": ["java_new"], "forbidden_keys": ["python_old"]},

            {"id": "q6", "type": "contradiction",
             "question": "When is the project evaluation deadline?",
             "gold_keys": ["deadline_new"], "forbidden_keys": ["deadline_old"]},
            {"id": "q7", "type": "contradiction",
             "question": "What is the current project deadline?",
             "gold_keys": ["deadline_new"], "forbidden_keys": ["deadline_old"]},

            {"id": "q8", "type": "multi_hop",
             "question": "How does the air pollution project compare models on the dataset?",
             "gold_keys": ["airnet", "randomforest", "dataset"], "forbidden_keys": []},

            {"id": "q9", "type": "forgetting",
             "question": "What was the temporary lab portal credential?",
             "gold_keys": [], "forbidden_keys": ["old_password"]},

            {"id": "q10", "type": "gap",
             "question": "What do I know about multithreading in depth?",
             "gold_keys": [], "forbidden_keys": []},

            # surfaces the duplicate cluster: a naive retriever fills its context
            # with three near-identical FastAPI notes
            {"id": "q11", "type": "duplicate",
             "question": "How does FastAPI routing work?",
             "gold_keys": ["dup_a"], "forbidden_keys": []},
        ]

    def relevance_key(self, key: str) -> str:
        return key


# ===========================================================================
class BenchmarkRunner:
    """Runs every mode over the question set and reports the paper's metrics."""

    def __init__(self):
        self.bench = PersonalBrainBench()

    # ------------------------------------------------------------ ingest
    def load_corpus(self, db, reset: bool = True) -> Dict[str, Any]:
        """
        Materialise the synthetic corpus into the real tables.

        It goes through the real models (Memory + SearchIndex + MemoryScore + the
        research layer), not a mock - otherwise the benchmark would measure a
        different system than the one shipped.
        """
        import hashlib

        from app.models.capture import MemorySession
        from app.models.memory import Memory, SearchIndex
        from app.models.research import ForgottenMemory
        from app.models.user import User

        from app.research.contradictions import contradiction_resolver
        from app.research.scoring import adaptive_memory_scorer
        from app.research.temporal import temporal_knowledge_graph

        user = db.query(User).order_by(User.id.asc()).first()
        if not user:
            return {"error": "No user in the database"}

        if reset:
            # Reproducibility requirement: the benchmark must produce the SAME
            # numbers on every run. Research state derived from earlier runs -
            # temporal facts, conflicts, consolidations, gaps, tombstones - was
            # leaking into subsequent runs and moving the results.

            # Clear derived research state. User memories themselves are NOT
            # touched; only the derived layer is rebuilt from the corpus.
            from app.models.research import (
                ForgottenMemory, KnowledgeGap, MemoryConflict,
                MemoryConsolidation, MemoryScore, TemporalFact,
            )
            for model in (TemporalFact, MemoryConflict, MemoryConsolidation,
                          KnowledgeGap, ForgottenMemory):
                db.query(model).delete(synchronize_session=False)
            db.commit()

            ids = [m.id for m in db.query(Memory).filter(Memory.app_source.like("bench:%")).all()]
            if ids:
                from app.models.memory import MemoryTag
                from app.models.research import MemoryConflict, MemoryScore
                db.query(SearchIndex).filter(SearchIndex.memory_id.in_(ids)).delete(synchronize_session=False)
                db.query(MemoryTag).filter(MemoryTag.memory_id.in_(ids)).delete(synchronize_session=False)
                db.query(MemoryScore).filter(MemoryScore.memory_id.in_(ids)).delete(synchronize_session=False)
                db.query(MemoryConflict).delete()
                db.query(Memory).filter(Memory.id.in_(ids)).delete(synchronize_session=False)
                db.commit()

        session = MemorySession(user_id=user.id, session_type="benchmark",
                                dominant_activity="PersonalBrain-Bench", is_active=True,
                                started_at=self.bench.now)
        db.add(session)
        db.commit()
        db.refresh(session)

        key_to_id: Dict[str, int] = {}
        for item in self.bench.build_corpus():
            content = item["content"]
            memory = Memory(
                session_id=session.id,
                title=item["title"],
                content=content,
                content_hash=hashlib.sha1(f"{item['key']}{content}".encode()).hexdigest(),
                source_type=item["source_type"],
                app_source=f"bench:{item['key']}",
                topic_label=item["title"][:80],
                category="benchmark",
                created_at=item["created_at"],
            )
            db.add(memory)
            db.flush()
            db.add(SearchIndex(
                memory_id=memory.id, session_id=session.id,
                searchable_text=f"{item['title']} {content}",
                tags_text="", app_source=f"bench:{item['key']}",
                source_type=item["source_type"], topic_label=item["title"][:80],
                created_at=item["created_at"],
            ))
            key_to_id[item["key"]] = memory.id
        db.commit()

        # research layer over the corpus
        adaptive_memory_scorer.score_corpus(db)

        # temporal facts, in chronological order so supersession behaves correctly
        corpus = {c["key"]: c for c in self.bench.build_corpus()}
        for key in sorted(corpus, key=lambda k: corpus[k]["created_at"]):
            item = corpus[key]
            facts = temporal_knowledge_graph.extract_facts(item["content"])
            if facts:
                temporal_knowledge_graph.record_facts(
                    db, facts, source_memory_id=key_to_id[key], at=item["created_at"])

        conflict_result = contradiction_resolver.resolve(db)
        db.commit()

        # The forgetting evaluation is meaningless unless something has actually
        # been forgotten, so the corpus includes a target and we unlearn it here
        # through the real service (which enforces exclusion at every retrieval
        # surface, not just by deleting a row).
        forgotten = 0
        if "old_password" in key_to_id:
            from app.research.forgetting import forgetting_service

            outcome = forgetting_service.forget(
                db, key_to_id["old_password"], reason="benchmark: sensitive scratch note")
            forgotten = 1 if outcome.get("forgotten") else 0

        return {
            "memories": len(key_to_id),
            "key_to_id": key_to_id,
            "conflicts": conflict_result["conflicts"],
            "forgotten": forgotten,
            "session_id": session.id,
        }

    # -------------------------------------------------------------- evaluate
    def evaluate(self, db, mode: str = "adaptive", k: int = 5,
                 key_to_id: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        from app.models.memory import Memory
        from app.models.research import ForgottenMemory
        from app.research.consolidation import memory_consolidator
        from app.research.pipeline import adaptive_retrieval

        if key_to_id is None:
            key_to_id = {}
            for memory in db.query(Memory).filter(Memory.app_source.like("bench:%")).all():
                key_to_id[memory.app_source.replace("bench:", "")] = memory.id

        id_to_key = {v: k for k, v in key_to_id.items()}
        forgotten = {row.memory_id for row in db.query(ForgottenMemory).all()}

        # a superseded memory id (for the staleness metric)
        superseded_ids = set()
        try:
            from app.models.research import TemporalFact
            for fact in db.query(TemporalFact).filter(TemporalFact.superseded_by.isnot(None)).all():
                if fact.source_memory_id:
                    superseded_ids.add(fact.source_memory_id)
        except Exception:
            pass

        per_question = []
        start = time.time()
        total_tokens = 0
        duplicate_pairs = 0
        total_results = 0
        stale_top1 = 0

        for question in self.bench.build_questions():
            results = adaptive_retrieval.retrieve(db, question["question"], limit=k, mode=mode)
            result_ids = [r["memory_id"] for r in results]
            result_keys = [id_to_key.get(i, "?") for i in result_ids]

            gold = set(question["gold_keys"])
            forbidden = set(question["forbidden_keys"])
            hits = [1 for key in result_keys if key in gold]

            rank = 0
            for index, key in enumerate(result_keys, start=1):
                if key in gold:
                    rank = index
                    break

            stale = sum(1 for key in result_keys if key in forbidden)
            forgotten_leak = sum(1 for i in result_ids if i in forgotten)

            # stale@1 is the metric that actually matters: it measures whether the
            # FIRST result - the one an LLM leads with - contradicts current
            # knowledge. A stale item at rank 4 barely matters if rank 1 is right.
            top1_is_stale = 1 if (result_keys and result_keys[0] in forbidden) else 0
            stale_top1 += top1_is_stale

            tokens = sum(len((r.get("content") or "")) for r in results)
            total_tokens += tokens
            total_results += len(results)

            # duplicate rate for THIS query, measured the same way for every mode
            if len(result_ids) > 1:
                texts = [(r.get("title") or "") + " " + (r.get("content") or "") for r in results]
                for i in range(len(texts)):
                    for j in range(i + 1, len(texts)):
                        if memory_consolidator.similarity(texts[i], texts[j]) >= 0.90:
                            duplicate_pairs += 1

            per_question.append({
                "id": question["id"], "type": question["type"],
                "question": question["question"],
                "answerable": bool(gold),
                "hit": bool(hits),
                "top1_is_stale": bool(top1_is_stale),
                "rank": rank,
                "reciprocal_rank": (1.0 / rank) if rank else 0.0,
                "precision": round(len(hits) / max(1, len(result_keys)), 3),
                "stale_results": stale,
                "forgotten_leak": forgotten_leak,
                "context_chars": tokens,
                "retrieved": result_keys,
            })

        elapsed_ms = int((time.time() - start) * 1000)
        questions = len(per_question)

        def _for(qtype: str) -> List[Dict[str, Any]]:
            return [q for q in per_question if q["type"] == qtype]

        # hit@k and MRR are computed over ANSWERABLE questions only. The
        # forgetting and gap questions have no gold memory by construction, so
        # including them would drag every system's score down equally and hide
        # real differences.
        answerable = [q for q in per_question if q.get("answerable")]

        return {
            "mode": mode,
            "k": k,
            "questions": questions,
            "answerable_questions": len(answerable),
            "hit_at_k": round(sum(1 for q in answerable if q["hit"]) / max(1, len(answerable)), 4),
            "mrr": round(sum(q["reciprocal_rank"] for q in answerable) / max(1, len(answerable)), 4),
            "stale_top1_rate": round(stale_top1 / max(1, questions), 4),
            "precision_at_k": round(sum(q["precision"] for q in answerable) / max(1, len(answerable)), 4),
            "staleness_rate": round(sum(q["stale_results"] for q in per_question) / max(1, total_results), 4),
            "forgotten_leak_rate": round(sum(q["forgotten_leak"] for q in per_question) / max(1, total_results), 4),
            "duplicate_rate": round(duplicate_pairs / max(1, total_results), 4),
            "avg_context_chars": round(total_tokens / max(1, questions), 1),
            "latency_ms": elapsed_ms,
            "per_type": {
                qtype: {
                    "n": len(_for(qtype)),
                    "hit_at_k": round(sum(1 for q in _for(qtype) if q["hit"]) / max(1, len(_for(qtype))), 4),
                    "mrr": round(sum(q["reciprocal_rank"] for q in _for(qtype)) / max(1, len(_for(qtype))), 4),
                    "stale_results": sum(q["stale_results"] for q in _for(qtype)),
                }
                for qtype in ("factual", "temporal", "contradiction", "multi_hop",
                              "forgetting", "gap", "duplicate")
            },
            "per_question": per_question,
        }

    # ----------------------------------------------------------- full run
    def run_all(self, db, k: int = 5) -> Dict[str, Any]:
        from app.models.research import ResearchRun

        ingest = self.load_corpus(db, reset=True)
        key_to_id = ingest["key_to_id"]

        results = {}
        for mode in ("vanilla", "hybrid", "graph", "adaptive"):
            outcome = self.evaluate(db, mode=mode, k=k, key_to_id=key_to_id)
            results[mode] = outcome
            db.add(ResearchRun(
                kind="benchmark", system=mode, questions=outcome["questions"],
                metrics_json=json.dumps({
                    "hit_at_k": outcome["hit_at_k"], "mrr": outcome["mrr"],
                    "staleness_rate": outcome["staleness_rate"],
                    "duplicate_rate": outcome["duplicate_rate"],
                    "avg_context_chars": outcome["avg_context_chars"],
                }),
                duration_ms=outcome["latency_ms"],
            ))
        db.commit()

        return {
            "corpus": {"memories": ingest["memories"], "conflicts": ingest["conflicts"]},
            "k": k,
            "results": results,
            "comparison": self._comparison(results),
        }

    @staticmethod
    def _comparison(results: Dict[str, Any]) -> Dict[str, Any]:
        """Delta of the proposed method against each baseline."""
        if "adaptive" not in results:
            return {}
        proposed = results["adaptive"]
        out = {}
        for mode in ("vanilla", "hybrid", "graph"):
            base = results.get(mode)
            if not base:
                continue
            out[f"adaptive_vs_{mode}"] = {
                "hit_at_k_delta": round(proposed["hit_at_k"] - base["hit_at_k"], 4),
                "mrr_delta": round(proposed["mrr"] - base["mrr"], 4),
                "staleness_reduction": round(base["staleness_rate"] - proposed["staleness_rate"], 4),
                "duplicate_reduction": round(base["duplicate_rate"] - proposed["duplicate_rate"], 4),
                "context_reduction_pct": round(
                    100.0 * (base["avg_context_chars"] - proposed["avg_context_chars"])
                    / max(1.0, base["avg_context_chars"]), 1),
            }
        return out


benchmark_runner = BenchmarkRunner()
