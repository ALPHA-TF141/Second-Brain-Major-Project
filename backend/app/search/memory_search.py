import re
from datetime import datetime, timedelta

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.memory import Memory, MemoryTag, SearchIndex


class MemorySearch:
    STOPWORDS = {
        "a", "an", "and", "are", "as", "at", "be", "by", "did", "do", "does", "for",
        "from", "had", "has", "have", "how", "i", "in", "is", "it", "its", "me", "my",
        "of", "on", "or", "said", "say", "she", "tell", "that", "the", "their", "them",
        "there", "they", "this", "to", "was", "we", "were", "what", "when", "where",
        "which", "who", "why", "will", "with", "you", "your", "about", "any", "can",
    }

    def _tokens(self, text: str) -> list[str]:
        """Meaningful lowercase words from a user question."""
        words = re.findall(r"[a-z0-9][a-z0-9_+.#-]{2,}", (text or "").lower())
        tokens = [w for w in words if w not in self.STOPWORDS]
        # de-duplicate but keep order
        seen, out = set(), []
        for token in tokens:
            if token not in seen:
                seen.add(token)
                out.append(token)
        return out

    def search(
        self,
        db: Session,
        q: str = "",
        source_type: str = "",
        topic: str = "",
        app: str = "",
        session_id: int | None = None,
        date: str = "",
        limit: int = 80,
    ):
        """
        Search memories with smart ranking:
        - Whole-phrase matches rank highest
        - Multi-word questions match on ANY meaningful word and are ranked by how
          many of those words they contain
        - Recent memories get higher priority
        - Specified category (topic/app/source) matches get boosted
        """
        query = db.query(Memory).join(SearchIndex, SearchIndex.memory_id == Memory.id)

        filters = []
        tokens: list[str] = []
        if q:
            tokens = self._tokens(q)
            if len(tokens) <= 1:
                # Single word (or no useful words): literal substring match.
                filters.append(SearchIndex.searchable_text.contains(q if not tokens else tokens[0]))
            else:
                # A natural-language question is NOT a substring of any stored
                # text, so matching it whole returned zero rows and the assistant
                # had nothing to answer from whenever the embedding model was
                # unavailable. Match on any meaningful word instead, then rank by
                # how many words matched.
                filters.append(or_(*[SearchIndex.searchable_text.contains(t) for t in tokens]))
        if source_type:
            filters.append(Memory.source_type == source_type)
        if topic:
            filters.append(Memory.topic_label.contains(topic))
        if app:
            filters.append(Memory.app_source.contains(app))
        if session_id:
            filters.append(Memory.session_id == session_id)
        if date:
            start = datetime.fromisoformat(date)
            filters.append(Memory.created_at >= start)
            filters.append(Memory.created_at < start + timedelta(days=1))

        if filters:
            query = query.filter(and_(*filters))

        # Fetch all matches and re-rank by relevance
        all_results = query.all()
        
        if not q:
            # No query text - sort by date only
            return sorted(all_results, key=lambda m: m.created_at, reverse=True)[:limit]
        
        # Compute relevance score for each result
        scored = []
        q_lower = q.lower()
        index_by_memory = {
            row.memory_id: row for row in
            db.query(SearchIndex).filter(SearchIndex.memory_id.in_([m.id for m in all_results])).all()
        } if all_results else {}

        for memory in all_results:
            score = self._compute_relevance_score(memory, q_lower, source_type, topic, app)

            # How many of the question's words actually appear - the main signal
            # for a multi-word question.
            hits = 0
            if tokens:
                haystack = (index_by_memory.get(memory.id).searchable_text.lower()
                            if index_by_memory.get(memory.id) else f"{memory.title} {memory.content}".lower())
                hits = sum(1 for token in tokens if token in haystack)

            scored.append((hits, score, memory.created_at, memory))

        # Most matched words first, then relevance, then recency
        scored.sort(key=lambda x: (-x[0], -x[1], -x[2].timestamp()))

        return [m for _, _, _, m in scored[:limit]]

    def _compute_relevance_score(self, memory: Memory, query: str, source_type: str, topic: str, app: str) -> float:
        """
        Compute relevance score for a memory (higher is more relevant).
        Factors:
        - Title/content contains query exactly (case-insensitive)
        - Topic/category match
        - Source/app match
        """
        score = 0.0
        
        # Query match scoring
        if query:
            title_lower = memory.title.lower()
            content_lower = memory.content.lower()
            
            # Exact phrase match in title gets highest score
            if query in title_lower:
                score += 100
            # Partial match in title
            elif any(word in title_lower for word in query.split()):
                score += 50
            # Match in content
            elif query in content_lower:
                score += 30
            # Any word from query in content
            elif any(word in content_lower for word in query.split()):
                score += 15
        
        # Filter bonus (if user has applied specific filters)
        if source_type and memory.source_type == source_type:
            score += 20
        if topic and topic.lower() in memory.topic_label.lower():
            score += 20
        if app and app.lower() in memory.app_source.lower():
            score += 20
        
        # Recency bonus (slightly favor newer memories)
        days_old = max(0, (datetime.utcnow() - memory.created_at).days)
        recency_bonus = max(0, 10 - days_old)
        score += recency_bonus
        
        return score

    def tags_for_memories(self, db: Session, memory_ids: list[int]):
        rows = db.query(MemoryTag).filter(MemoryTag.memory_id.in_(memory_ids or [0])).all()
        tags = {}
        for row in rows:
            tags.setdefault(row.memory_id, []).append(row.tag)
        return tags
    
    def find_related_memories(self, db: Session, memory_id: int, limit: int = 10):
        """
        Find related memories by:
        1. Same topic
        2. Same app source
        3. Same category
        Returns ordered by relevance/recency.
        """
        memory = db.query(Memory).filter(Memory.id == memory_id).first()
        if not memory:
            return []
        
        related = db.query(Memory).filter(
            Memory.id != memory_id,
            or_(
                Memory.topic_label == memory.topic_label,
                Memory.app_source == memory.app_source,
                Memory.category == memory.category
            )
        ).order_by(Memory.created_at.desc()).limit(limit).all()
        
        return related
    
    def get_memory_stats(self, db: Session):
        """Get summary statistics about all memories."""
        total = db.query(func.count(Memory.id)).scalar() or 0
        by_category = db.query(
            Memory.category,
            func.count(Memory.id)
        ).group_by(Memory.category).all()
        
        by_source = db.query(
            Memory.source_type,
            func.count(Memory.id)
        ).group_by(Memory.source_type).all()
        
        return {
            "total_memories": total,
            "by_category": {cat: count for cat, count in by_category},
            "by_source": {src: count for src, count in by_source},
        }


memory_search = MemorySearch()
