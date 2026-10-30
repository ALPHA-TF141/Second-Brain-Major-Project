"""
Adaptive Memory Retrieval - the paper's proposed pipeline, and its baselines.
===========================================================================
Four retrievers share one interface so the evaluation harness can compare them
on identical questions. The switchable design is not decoration: the paper's
central claim is that the research layer improves answers, and a claim like that
is only meaningful against named baselines.

  vanilla   dense/vector only.            The standard RAG baseline.
  hybrid    vector + keyword, fused.      The app's original pipeline.
  graph     hybrid + knowledge-graph boost.  Graph-RAG style baseline.
  adaptive  hybrid + graph + the research layer:
              forgetting exclusion      (hard, at retrieval time)
              temporal validity         (superseded memories damped)
              contradiction penalty     (older side of a conflict damped)
              consolidation dedupe      (near-duplicates collapsed)
              adaptive importance score (multi-factor ranking)

Ordering matters and is deliberate: exclusions first (cheap, absolute), then
damping, then re-ranking, then dedupe. Doing dedupe first would waste the
context budget on items that damping later removes.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List, Optional, Tuple

from app.research.graph_builder import graph_builder

# adaptive_graph = adaptive + query-conditioned graph expansion. It exists as a
# SEPARATE mode so the graph's contribution can be measured instead of assumed:
# "adaptive" keeps the paper's original definition (research layer on hybrid).
MODES = ("vanilla", "hybrid", "graph", "adaptive", "adaptive_graph")


class AdaptiveMemoryRetrieval:
    def __init__(self):
        self.last_trace: Dict[str, Any] = {}

    # ================================================================ helpers
    @staticmethod
    def _candidate_semantic(db, question: str, limit: int,
                            allowed_ids: Optional[set] = None) -> List[Tuple[int, float]]:
        """Dense retrieval. Returns [] if no embedding model is installed."""
        try:
            from app.embeddings.embedding_model import embedding_model
            from app.vectorstore.chroma_store import chroma_store

            vector = embedding_model.encode([question])[0]
            # A scoped call over-fetches and filters below, because the vector
            # store is queried globally: asking for `limit` neighbours of the
            # whole collection returns the user's memories, not the corpus's.
            n_results = limit if allowed_ids is None else max(limit * 4, 64)
            raw = chroma_store.query(vector, n_results=n_results)
            out = []
            for vector_id, distance in zip(raw.get("ids", [[]])[0], raw.get("distances", [[]])[0]):
                try:
                    memory_id = int(str(vector_id).replace("memory-", ""))
                except ValueError:
                    continue
                if allowed_ids is not None and memory_id not in allowed_ids:
                    continue
                out.append((memory_id, max(0.0, 1.0 - float(distance))))
            return out
        except Exception:
            return []

    @staticmethod
    def _candidate_bm25(db, question: str, limit: int,
                        allowed_ids: Optional[set] = None,
                        k1: float = 1.5, b: float = 0.75) -> List[Tuple[int, float]]:
        """
        Okapi BM25 - the stronger lexical baseline the paper was missing.

        TF-IDF cosine and BM25 differ in exactly the regime this corpus lives in
        (short documents, rare terms): BM25 saturates term frequency and
        normalises by document length, so a long memory cannot win by repeating
        a word. Reviewers ask for it by name, and it costs nothing to add because
        it is pure arithmetic - no model, no network, deterministic.
        """
        import math
        import re
        from collections import Counter

        from app.models.memory import Memory

        def vec(text: str) -> Counter:
            return Counter(re.findall(r"[a-z][a-z0-9_+.#-]{2,}", (text or "").lower()))

        query = db.query(Memory)
        if allowed_ids is not None:
            if not allowed_ids:
                return []
            query = query.filter(Memory.id.in_(allowed_ids))
        memories = query.all()
        if not memories:
            return []

        query_terms = vec(question)
        if not query_terms:
            return []

        doc_vecs = [(m, vec(f"{m.title or ''} {m.content or ''}")) for m in memories]
        total_docs = max(1, len(doc_vecs))
        avg_length = sum(sum(dv.values()) for _m, dv in doc_vecs) / total_docs or 1.0

        df = Counter()
        for _m, dv in doc_vecs:
            for term in dv:
                df[term] += 1

        def idf(term: str) -> float:
            n = df.get(term, 0)
            return math.log(1.0 + (total_docs - n + 0.5) / (n + 0.5))

        scored = []
        for memory, dv in doc_vecs:
            length = sum(dv.values()) or 1
            score = 0.0
            for term, q_count in query_terms.items():
                tf = dv.get(term, 0)
                if not tf:
                    continue
                denominator = tf + k1 * (1.0 - b + b * length / avg_length)
                score += idf(term) * (tf * (k1 + 1.0) / denominator) * q_count
            if score > 0:
                scored.append((memory.id, score))

        scored.sort(key=lambda t: -t[1])
        # normalise to [0,1] so the hybrid ranker sees the same scale as TF-IDF
        ceiling = scored[0][1] if scored else 1.0
        return [(mid, value / ceiling) for mid, value in scored[:limit]]

    @staticmethod
    def _candidate_tfidf(db, question: str, limit: int,
                         allowed_ids: Optional[set] = None) -> List[Tuple[int, float]]:
        """
        TF-IDF cosine retrieval - the dense baseline, available without any model.

        Why this exists: with no neural embedder installed, a vector-only
        baseline retrieves nothing and the comparison becomes meaningless (a
        baseline that scores 0.000 makes ANY method look good). TF-IDF gives a
        genuine lexical-dense baseline that is fully reproducible offline.

        When a neural embedder IS configured, `_candidate_semantic` is preferred
        and this becomes the fallback.
        """
        import math
        import re
        from collections import Counter

        from app.models.memory import Memory

        def vec(text: str) -> Counter:
            return Counter(re.findall(r"[a-z][a-z0-9_+.#-]{2,}", (text or "").lower()))

        query = db.query(Memory)
        if allowed_ids is not None:
            if not allowed_ids:
                return []
            query = query.filter(Memory.id.in_(allowed_ids))
        memories = query.all()
        if not memories:
            return []

        query_vec = vec(question)
        if not query_vec:
            return []

        doc_vecs = [(m, vec(f"{m.title or ''} {m.content or ''}")) for m in memories]

        # document frequency for IDF
        df = Counter()
        for _m, dv in doc_vecs:
            for term in dv:
                df[term] += 1
        total_docs = max(1, len(doc_vecs))

        def idf(term: str) -> float:
            return math.log((1 + total_docs) / (1 + df.get(term, 0))) + 1.0

        query_weights = {t: c * idf(t) for t, c in query_vec.items()}
        query_norm = math.sqrt(sum(w * w for w in query_weights.values())) or 1.0

        scored = []
        for memory, dv in doc_vecs:
            doc_weights = {t: c * idf(t) for t, c in dv.items()}
            doc_norm = math.sqrt(sum(w * w for w in doc_weights.values())) or 1.0
            dot = sum(query_weights.get(t, 0.0) * doc_weights.get(t, 0.0) for t in query_weights)
            if dot > 0:
                scored.append((memory.id, dot / (query_norm * doc_norm)))

        scored.sort(key=lambda t: -t[1])
        return scored[:limit]

    @staticmethod
    def _candidate_keyword(db, question: str, limit: int,
                           allowed_ids: Optional[set] = None) -> List[int]:
        from app.search.memory_search import memory_search

        try:
            # The scope goes INTO the query. Filtering a global top-N afterwards
            # starves the scope: unrelated memories take the top slots, and the
            # corpus candidates left over depend on what the user happened to
            # capture that day.
            hits = [m.id for m in memory_search.search(
                db, q=question, limit=limit,
                memory_ids=sorted(allowed_ids) if allowed_ids is not None else None)]
        except Exception:
            return []
        if allowed_ids is not None:
            hits = [i for i in hits if i in allowed_ids]
        return hits

    @staticmethod
    def _graph_neighbours(db, memory_ids: List[int]) -> Dict[int, float]:
        """Graph boost: memories whose nodes are well connected rank higher."""
        from app.models.graph import GraphEdge, GraphNode
        from app.models.memory import Memory

        boost: Dict[int, float] = {}
        try:
            rows = db.query(Memory).filter(Memory.id.in_(memory_ids)).all()
            node_by_memory: Dict[int, List] = {}
            for node in db.query(GraphNode).all():
                if node.memory_id:
                    node_by_memory.setdefault(node.memory_id, []).append(node)

            degree = {}
            for edge in db.query(GraphEdge).all():
                degree[edge.source_node_id] = degree.get(edge.source_node_id, 0) + 1
                degree[edge.target_node_id] = degree.get(edge.target_node_id, 0) + 1

            max_degree = max(degree.values()) if degree else 1
            for memory in rows:
                nodes = node_by_memory.get(memory.id, [])
                if not nodes:
                    boost[memory.id] = 0.0
                    continue
                best = max(degree.get(n.id, 0) for n in nodes)
                boost[memory.id] = min(1.0, best / max(1, max_degree))
        except Exception:
            pass
        return boost

    # ================================================================== modes
    def retrieve(self, db, question: str, limit: int = 8, mode: str = "adaptive",
                 allowed_ids: Optional[Iterable[int]] = None,
                 dense_backend: Optional[str] = None,
                 ablation: Optional[Dict[str, bool]] = None) -> List[Dict[str, Any]]:
        """
        `allowed_ids` restricts the candidate pool to a set of memories.

        Why it exists: the evaluation harness must not be moved by whatever else
        happens to be in the user's database. Without a scope, a top-k slot can be
        taken by an unrelated memory the user captured, which makes hit@k/MRR a
        property of their inbox rather than of the retriever - the benchmark then
        stops being reproducible between machines. The benchmark passes the
        corpus ids, so every mode is measured on the same evidence.
        """
        from app.models.memory import Memory
        from app.ranking.hybrid_ranker import hybrid_ranker

        if mode not in MODES:
            mode = "adaptive"

        scope = set(allowed_ids) if allowed_ids is not None else None

        trace: Dict[str, Any] = {"mode": mode, "question": question, "stages": {}}
        # Pool size is configurable because it decides whether graph expansion
        # can do anything at all: when the pool is larger than the corpus every
        # memory is already a candidate, so "the graph found something lexical
        # retrieval missed" is untestable by construction.
        pool = int(os.getenv("RETRIEVAL_POOL", "0") or 0) or max(limit * 4, 24)

        # ---- candidate generation ----------------------------------------
        # `dense_backend="tfidf"` pins the offline dense retriever and never even
        # loads the neural model. The benchmark asks for that: it is deterministic,
        # needs no network, and it is the configuration the published numbers were
        # produced with, so the table means the same thing on every machine.
        bm25 = dense_backend == "bm25"
        semantic = ([] if dense_backend in ("tfidf", "bm25")
                    else self._candidate_semantic(db, question, pool, scope))
        keyword_ids = self._candidate_keyword(db, question, pool, scope)
        trace["stages"]["semantic_candidates"] = len(semantic)
        trace["stages"]["keyword_candidates"] = len(keyword_ids)
        if scope is not None:
            trace["stages"]["scoped_to"] = len(scope)

        # Dense candidates: neural if an embedder is configured, otherwise
        # TF-IDF. Either way every mode has a real dense signal, so no baseline
        # degenerates to zero and flatters the proposed method.
        if bm25:
            dense = self._candidate_bm25(db, question, pool, scope)
        elif semantic:
            dense = semantic
        else:
            dense = self._candidate_tfidf(db, question, pool, scope)
        trace["stages"]["dense_backend"] = (
            "bm25" if bm25 else ("neural" if semantic else "tfidf"))
        trace["stages"]["dense_pinned"] = dense_backend or "auto"
        trace["stages"]["dense_candidates"] = len(dense)

        # ================================================== VANILLA =======
        if mode == "vanilla":
            candidates = dense[:limit]
            rows = {m.id: m for m in db.query(Memory).filter(Memory.id.in_([c[0] for c in candidates])).all()}
            self.last_trace = trace
            return [
                self._shape(rows[mid], score, {"rank_source": "vector"})
                for mid, score in candidates if mid in rows
            ]

        # =================================================== HYBRID =======
        try:
            keyword_memories = db.query(Memory).filter(Memory.id.in_(keyword_ids)).all()
        except Exception:
            keyword_memories = []
        # hybrid_ranker returns dicts carrying `memory_id`, not ORM objects, so
        # hydrate them back into Memory rows before the research layer sees them.
        ranked = hybrid_ranker.rank(
            [{"memory_id": mid, "score": score} for mid, score in dense],
            keyword_memories,
        )
        ranked_ids = [item["memory_id"] for item in ranked]
        if not ranked_ids:
            ranked_ids = keyword_ids
        rows = db.query(Memory).filter(Memory.id.in_(ranked_ids)).all()
        by_id = {m.id: m for m in rows}
        ordered = [by_id[i] for i in ranked_ids if i in by_id]

        # If there is no embedding model, semantic results are empty and the
        # ranker only saw keyword hits - which is the honest "hybrid without
        # vectors" behaviour rather than a silent failure.
        trace["stages"]["fused_pool"] = len(ordered)

        # ==================================================== GRAPH =======
        # Query-conditioned expansion, not a degree-only sort.
        #
        # The previous implementation ranked memories by how many edges their
        # nodes had, which promotes hub memories whether or not they relate to
        # the QUESTION - it is a popularity prior, not a retrieval signal. This
        # version seeds from concepts the query actually names, walks one
        # predicate hop, and fuses the result with the lexical prior. A memory
        # the lexical retriever missed entirely can still be pulled in (that is
        # what multi-hop questions need).
        if mode in ("graph", "adaptive_graph"):
            ids = [m.id for m in ordered]
            graph_scores = graph_builder.expand_scores(db, question, ids, hops=1)
            alpha = float(os.getenv("GRAPH_ALPHA", "0.3"))
            fused: Dict[int, float] = {}
            rows_by_id = {m.id: m for m in ordered}
            for index, memory in enumerate(ordered):
                prior = 1.0 / (1.0 + index)
                fused[memory.id] = (1.0 - alpha) * prior + alpha * graph_scores.get(memory.id, 0.0)

            missing = [mid for mid in graph_scores if mid not in fused]
            if missing:
                extra = db.query(Memory).filter(Memory.id.in_(missing)).all()
                if scope is not None:
                    extra = [m for m in extra if m.id in scope]
                for memory in extra:
                    fused[memory.id] = alpha * graph_scores[memory.id]
                    rows_by_id[memory.id] = memory

            ordered = [rows_by_id[mid] for mid in sorted(fused, key=lambda k: -fused[k])
                       if mid in rows_by_id]
            trace["stages"]["graph_alpha"] = alpha
            trace["stages"]["graph_seeded_memories"] = len(graph_scores)
            trace["stages"]["graph_promoted"] = len(missing)

        # ================================================= ADAPTIVE =======
        # adaptive_graph runs the same research layer as adaptive, on top of a
        # graph-expanded ranking. Keeping them separate is what makes the
        # question "does the graph add anything?" answerable.
        if mode in ("adaptive", "adaptive_graph"):
            ordered = self._apply_research_layer(db, ordered, trace, ablation)

        trace["stages"]["returned"] = min(len(ordered), limit)
        self.last_trace = trace
        return [self._shape(m, 0.0, {"rank_source": mode}) for m in ordered[:limit]]

    # ------------------------------------------------- research layer
    def _apply_research_layer(self, db, ordered: List, trace: Dict[str, Any],
                              ablation: Optional[Dict[str, bool]] = None) -> List:
        # Ablation support (paper E1): when `ablation` is given, ONLY the named
        # mechanisms run; absent keys are disabled. None = every mechanism on,
        # which is the shipped behaviour.
        from app.models.research import ForgottenMemory, MemoryScore
        from app.research.consolidation import memory_consolidator
        from app.research.contradictions import contradiction_resolver
        from app.research.temporal import temporal_knowledge_graph

        flags = {"forgetting": True, "temporal": True, "contradiction": True,
                 "consolidation": True, "importance": True}
        if ablation is not None:
            flags = {key: bool(ablation.get(key, False)) for key in flags}
            trace["stages"]["ablation"] = dict(flags)

        # 1. EXCLUDE forgotten memories. Absolute - nothing can re-admit them.
        if flags["forgetting"]:
            try:
                forgotten = {row.memory_id for row in db.query(ForgottenMemory).all()}
            except Exception:
                forgotten = set()
            before = len(ordered)
            ordered = [m for m in ordered if m.id not in forgotten]
            trace["stages"]["excluded_forgotten"] = before - len(ordered)

        # 2. DAMP superseded memories (temporal) and conflicted ones
        scores = {}
        try:
            scores = {row.memory_id: row.total for row in db.query(MemoryScore).all()}
        except Exception:
            pass

        adjusted = []
        damped_temporal = 0
        damped_conflict = 0
        for index, memory in enumerate(ordered):
            multiplier = 1.0

            if flags["temporal"]:
                temporal_weight = temporal_knowledge_graph.temporal_weight(db, memory.id)
                if temporal_weight < 0.7:
                    multiplier *= temporal_weight
                    damped_temporal += 1

            if flags["contradiction"]:
                conflict_mult, _reason = contradiction_resolver.conflict_penalty(db, memory.id)
                if conflict_mult < 1.0:
                    multiplier *= conflict_mult
                    damped_conflict += 1

            # Rank-preserving: the fused retrieval order is the prior, damping
            # adjusts it, and importance is only a light tie-breaker. Sorting on
            # importance alone was actively HARMFUL in testing - it promoted
            # high-importance-but-less-relevant memories above the gold one.
            prior = 1.0 / (1.0 + index)
            importance = scores.get(memory.id, 0.5)
            importance_factor = (0.85 + 0.15 * importance) if flags["importance"] else 1.0
            final = prior * multiplier * importance_factor
            adjusted.append((memory, final, multiplier, importance))

        adjusted.sort(key=lambda t: -t[1])
        ordered = [m for m, _final, _mult, _imp in adjusted]
        trace["stages"]["damped_temporal"] = damped_temporal
        trace["stages"]["damped_conflict"] = damped_conflict

        # 3. COLLAPSE near-duplicates so the context budget is not wasted
        if flags["consolidation"]:
            ids = [m.id for m in ordered]
            kept_ids = memory_consolidator.retrieval_dedup(db, ids)
            trace["stages"]["deduped"] = len(ids) - len(kept_ids)
            by_id = {m.id: m for m in ordered}
            ordered = [by_id[i] for i in kept_ids if i in by_id]

        return ordered

    @staticmethod
    def _shape(memory, score: float, extra: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "memory_id": memory.id,
            "title": memory.title,
            "content": (memory.content or "")[:1100],
            "source_type": memory.source_type,
            "app_source": memory.app_source,
            "session_id": memory.session_id,
            "screenshot_id": memory.screenshot_id,
            "timestamp": memory.created_at,
            "score": score,
            **extra,
        }


adaptive_retrieval = AdaptiveMemoryRetrieval()
