from datetime import datetime, timedelta

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.memory import Memory, MemoryTag, SearchIndex


class MemorySearch:
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
        - Exact text matches get higher priority
        - Recent memories get higher priority
        - Specified category (topic/app/source) matches get boosted
        - Relevance is computed and results are re-ranked
        """
        query = db.query(Memory).join(SearchIndex, SearchIndex.memory_id == Memory.id)

        filters = []
        if q:
            filters.append(SearchIndex.searchable_text.contains(q))
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
        for memory in all_results:
            score = self._compute_relevance_score(memory, q_lower, source_type, topic, app)
            scored.append((score, memory.created_at, memory))
        
        # Sort by score (desc) then by date (desc)
        scored.sort(key=lambda x: (-x[0], -x[1].timestamp()))
        
        return [m for _, _, m in scored[:limit]]

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
