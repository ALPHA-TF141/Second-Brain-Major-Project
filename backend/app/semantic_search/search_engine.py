from app.embeddings.embedding_model import embedding_model
from app.models.memory import Memory
from app.models.semantic import SearchHistory, SemanticRelationship, VectorMemory
from app.ranking.hybrid_ranker import hybrid_ranker
from app.retrieval.context_assembler import context_assembler
from app.search.memory_search import memory_search
from app.vectorstore.chroma_store import chroma_store


class SemanticSearchEngine:
    def semantic_search(self, db, query: str, limit: int = 8, source_type: str = "", session_id: int | None = None):
        where = {}
        if source_type:
            where["source_type"] = source_type
        if session_id:
            where["session_id"] = session_id

        query_vector = embedding_model.encode([query])[0]
        raw = chroma_store.query(query_vector, n_results=limit, where=where or None)
        ids = raw.get("ids", [[]])[0]
        distances = raw.get("distances", [[]])[0]

        results = []
        for vector_id, distance in zip(ids, distances):
            memory_id = int(str(vector_id).replace("memory-", ""))
            score = max(0.0, 1.0 - float(distance))
            results.append({"memory_id": memory_id, "score": score})

        db.add(SearchHistory(query=query, search_type="semantic", result_count=len(results)))
        db.commit()
        return self._hydrate(db, results)

    def hybrid_search(self, db, query: str, limit: int = 10, source_type: str = "", session_id: int | None = None):
        semantic_rank = []
        try:
            query_vector = embedding_model.encode([query])[0]
            where = {}
            if source_type:
                where["source_type"] = source_type
            if session_id:
                where["session_id"] = session_id
            raw = chroma_store.query(query_vector, n_results=limit, where=where or None)
            for vector_id, distance in zip(raw.get("ids", [[]])[0], raw.get("distances", [[]])[0]):
                semantic_rank.append({"memory_id": int(str(vector_id).replace("memory-", "")), "score": max(0.0, 1.0 - float(distance))})
        except Exception:
            semantic_rank = []

        keyword_results = memory_search.search(db, q=query, source_type=source_type, session_id=session_id, limit=limit)
        ranked = hybrid_ranker.rank(semantic_rank, keyword_results)
        hydrated = self._hydrate(db, ranked[:limit])
        db.add(SearchHistory(query=query, search_type="hybrid", result_count=len(hydrated)))
        db.commit()
        return hydrated

    def related_memories(self, db, memory_id: int, limit: int = 6):
        memory = db.query(Memory).filter(Memory.id == memory_id).first()
        if not memory:
            return []
        return [item for item in self.hybrid_search(db, memory.content[:500], limit=limit + 1) if item["memory"].id != memory_id][:limit]

    def context(self, db, query: str, limit: int = 6):
        results = self.hybrid_search(db, query, limit=limit)
        memories = [item["memory"] for item in results]
        return context_assembler.assemble(query, memories, max_items=limit)

    def detect_relationships(self, db, limit: int = 4):
        vector_rows = db.query(VectorMemory).all()
        created = 0
        for row in vector_rows:
            related = self.related_memories(db, row.memory_id, limit=limit)
            for item in related:
                target_id = item["memory"].id
                if target_id == row.memory_id:
                    continue
                exists = db.query(SemanticRelationship).filter(
                    SemanticRelationship.source_memory_id == row.memory_id,
                    SemanticRelationship.target_memory_id == target_id,
                ).first()
                if exists:
                    continue
                db.add(
                    SemanticRelationship(
                        source_memory_id=row.memory_id,
                        target_memory_id=target_id,
                        similarity_score=item["score"],
                    )
                )
                created += 1
        db.commit()
        return {"relationships": created}

    def _hydrate(self, db, ranked: list[dict]):
        memory_ids = [item["memory_id"] for item in ranked]
        memories = {memory.id: memory for memory in db.query(Memory).filter(Memory.id.in_(memory_ids or [0])).all()}
        hydrated = []
        for item in ranked:
            memory = memories.get(item["memory_id"])
            if memory:
                hydrated.append({"memory": memory, "score": item.get("hybrid_score", item.get("score", 0.0)), "semantic_score": item.get("score", 0.0)})
        return hydrated


semantic_search_engine = SemanticSearchEngine()
