from datetime import datetime


class HybridRanker:
    def rank(self, semantic_results: list[dict], keyword_memories: list, semantic_weight: float = 0.7):
        ranked = {}

        for item in semantic_results:
            memory_id = item["memory_id"]
            ranked[memory_id] = {
                **item,
                "keyword_score": 0.0,
                "hybrid_score": item["score"] * semantic_weight,
            }

        for index, memory in enumerate(keyword_memories):
            keyword_score = max(0.1, 1.0 - (index * 0.04))
            recency = self._recency_score(memory.created_at)
            if memory.id not in ranked:
                ranked[memory.id] = {
                    "memory_id": memory.id,
                    "score": 0.0,
                    "keyword_score": keyword_score,
                    "hybrid_score": (keyword_score * (1 - semantic_weight)) + (recency * 0.08),
                }
            else:
                ranked[memory.id]["keyword_score"] = keyword_score
                ranked[memory.id]["hybrid_score"] += keyword_score * (1 - semantic_weight) + recency * 0.08

        return sorted(ranked.values(), key=lambda item: item["hybrid_score"], reverse=True)

    def _recency_score(self, created_at):
        if not created_at:
            return 0.0
        days = max(0, (datetime.utcnow() - created_at).days)
        return max(0.0, 1.0 - min(days, 30) / 30)


hybrid_ranker = HybridRanker()
