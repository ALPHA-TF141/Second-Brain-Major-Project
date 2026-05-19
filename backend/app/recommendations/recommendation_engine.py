"""Recommendation engine for knowledge graph"""

import logging
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
from sqlalchemy.orm import Session as DBSession

from app.models.graph import GraphNode, GraphEdge
from app.models.memory import Memory

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generate recommendations based on knowledge graph"""

    def __init__(self, db: DBSession):
        """Initialize recommendation engine"""
        self.db = db

    def recommend_related_topics(
        self,
        topic: str,
        limit: int = 5
    ) -> List[Dict]:
        """Recommend related topics for a given topic"""
        try:
            # Find the node for this topic
            node = self.db.query(GraphNode).filter(
                GraphNode.name.ilike(f"%{topic}%")
            ).first()

            if not node:
                return []

            # Get connected nodes
            edges = self.db.query(GraphEdge).filter(
                GraphEdge.source_node_id == node.id
            ).order_by(GraphEdge.strength_score.desc()).limit(limit).all()

            recommendations = []
            for edge in edges:
                target = self.db.query(GraphNode).filter(
                    GraphNode.id == edge.target_node_id
                ).first()

                if target:
                    recommendations.append({
                        "name": target.name,
                        "type": target.node_type,
                        "strength": edge.strength_score,
                        "reasoning": f"Related via {edge.relationship_type}"
                    })

            return recommendations

        except Exception as e:
            logger.error(f"Error recommending related topics: {e}")
            return []

    def recommend_next_learning_topics(
        self,
        learned_topics: List[str],
        limit: int = 5
    ) -> List[Dict]:
        """Recommend next topics to learn based on learned topics"""
        try:
            recommendations = defaultdict(float)

            # Find nodes for learned topics
            learned_nodes = []
            for topic in learned_topics:
                node = self.db.query(GraphNode).filter(
                    GraphNode.name.ilike(f"%{topic}%")
                ).first()
                if node:
                    learned_nodes.append(node)

            if not learned_nodes:
                return []

            # Find topics that follow from learned topics
            for node in learned_nodes:
                # Get outgoing edges (dependencies)
                edges = self.db.query(GraphEdge).filter(
                    GraphEdge.source_node_id == node.id,
                    GraphEdge.relationship_type.in_(["depends_on", "follows"])
                ).all()

                for edge in edges:
                    target = self.db.query(GraphNode).filter(
                        GraphNode.id == edge.target_node_id
                    ).first()

                    if target and target.name not in learned_topics:
                        # Score based on relationship strength and frequency
                        score = edge.strength_score * target.importance_score
                        recommendations[target.name] += score

            # Sort by score
            sorted_recs = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)

            result = []
            for topic_name, score in sorted_recs[:limit]:
                node = self.db.query(GraphNode).filter(
                    GraphNode.name == topic_name
                ).first()

                if node:
                    result.append({
                        "name": node.name,
                        "type": node.node_type,
                        "score": score,
                        "importance": node.importance_score,
                        "reasoning": "Natural learning progression"
                    })

            return result

        except Exception as e:
            logger.error(f"Error recommending next topics: {e}")
            return []

    def recommend_forgotten_concepts(
        self,
        days_threshold: int = 30,
        limit: int = 5
    ) -> List[Dict]:
        """Recommend concepts that haven't been revisited recently"""
        try:
            from datetime import datetime, timedelta

            cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)

            # Find nodes not seen recently but important
            old_nodes = self.db.query(GraphNode).filter(
                GraphNode.last_seen < cutoff_date,
                GraphNode.importance_score > 0.5
            ).order_by(
                GraphNode.importance_score.desc()
            ).limit(limit).all()

            recommendations = []
            for node in old_nodes:
                recommendations.append({
                    "name": node.name,
                    "type": node.node_type,
                    "importance": node.importance_score,
                    "days_since_seen": (datetime.utcnow() - node.last_seen).days,
                    "reasoning": f"Important concept not revisited in {(datetime.utcnow() - node.last_seen).days} days"
                })

            return recommendations

        except Exception as e:
            logger.error(f"Error recommending forgotten concepts: {e}")
            return []

    def recommend_related_memories(
        self,
        memory_id: int,
        limit: int = 5
    ) -> List[Dict]:
        """Recommend memories related to a given memory"""
        try:
            # Get the memory
            memory = self.db.query(Memory).filter(Memory.id == memory_id).first()
            if not memory:
                return []

            # Get its node
            memory_node = self.db.query(GraphNode).filter(
                GraphNode.memory_id == memory_id
            ).first()

            if not memory_node:
                return []

            # Find related memory nodes through concept connections
            related_memories = defaultdict(float)

            # Get concepts mentioned in this memory
            edges = self.db.query(GraphEdge).filter(
                GraphEdge.source_node_id == memory_node.id
            ).all()

            for edge in edges:
                concept_node = self.db.query(GraphNode).filter(
                    GraphNode.id == edge.target_node_id
                ).first()

                if concept_node:
                    # Find other memories mentioning this concept
                    related_edges = self.db.query(GraphEdge).filter(
                        GraphEdge.source_node_id == concept_node.id,
                        GraphEdge.relationship_type == "mentions"
                    ).all()

                    for rel_edge in related_edges:
                        other_memory_node = self.db.query(GraphNode).filter(
                            GraphNode.id == rel_edge.target_node_id,
                            GraphNode.id != memory_node.id
                        ).first()

                        if other_memory_node and other_memory_node.memory_id:
                            # Score based on concept strength and memory importance
                            score = edge.strength_score * other_memory_node.importance_score
                            related_memories[other_memory_node.memory_id] += score

            # Get memory details
            sorted_memories = sorted(related_memories.items(), key=lambda x: x[1], reverse=True)

            result = []
            for other_memory_id, score in sorted_memories[:limit]:
                other_memory = self.db.query(Memory).filter(
                    Memory.id == other_memory_id
                ).first()

                if other_memory:
                    result.append({
                        "id": other_memory.id,
                        "title": other_memory.title,
                        "score": score,
                        "created_at": other_memory.created_at.isoformat(),
                        "reasoning": "Shares related concepts"
                    })

            return result

        except Exception as e:
            logger.error(f"Error recommending related memories: {e}")
            return []

    def get_learning_gaps(self, limit: int = 5) -> List[Dict]:
        """Identify learning gaps (topics connected to learned topics but not explored)"""
        try:
            # Find all concepts
            all_nodes = self.db.query(GraphNode).all()

            # Find frequently mentioned concepts
            frequent_nodes = [n for n in all_nodes if n.frequency > 2]

            gaps = []

            for node in frequent_nodes:
                # Find connected nodes with low frequency
                edges = self.db.query(GraphEdge).filter(
                    GraphEdge.source_node_id == node.id,
                    GraphEdge.relationship_type.in_(["depends_on", "follows", "related_to"])
                ).all()

                for edge in edges:
                    target = self.db.query(GraphNode).filter(
                        GraphNode.id == edge.target_node_id
                    ).first()

                    # Recommend if target is less explored but important
                    if target and target.frequency < 2 and target.importance_score > 0.6:
                        gaps.append({
                            "name": target.name,
                            "type": target.node_type,
                            "prerequisite": node.name,
                            "importance": target.importance_score,
                            "gap_score": edge.strength_score * target.importance_score,
                            "reasoning": f"Related to '{node.name}' but under-explored"
                        })

            # Sort by gap score
            gaps.sort(key=lambda x: x["gap_score"], reverse=True)
            return gaps[:limit]

        except Exception as e:
            logger.error(f"Error identifying learning gaps: {e}")
            return []

    def get_learning_path(self, start_topic: str, end_topic: str) -> Dict:
        """Find learning path from one topic to another"""
        try:
            # Find start and end nodes
            start_node = self.db.query(GraphNode).filter(
                GraphNode.name.ilike(f"%{start_topic}%")
            ).first()

            end_node = self.db.query(GraphNode).filter(
                GraphNode.name.ilike(f"%{end_topic}%")
            ).first()

            if not start_node or not end_node:
                return {"path": [], "found": False}

            # Use BFS to find shortest path
            path = self._find_learning_path_bfs(start_node.id, end_node.id)

            if path:
                path_nodes = []
                for node_id in path:
                    node = self.db.query(GraphNode).filter(
                        GraphNode.id == node_id
                    ).first()
                    if node:
                        path_nodes.append({
                            "name": node.name,
                            "type": node.node_type
                        })

                return {
                    "path": path_nodes,
                    "found": True,
                    "steps": len(path_nodes)
                }

            return {"path": [], "found": False}

        except Exception as e:
            logger.error(f"Error finding learning path: {e}")
            return {"path": [], "found": False}

    def _find_learning_path_bfs(self, start_id: int, end_id: int, max_depth: int = 10) -> List[int]:
        """BFS to find path between two nodes"""
        from collections import deque

        queue = deque([(start_id, [start_id])])
        visited = {start_id}

        while queue:
            node_id, path = queue.popleft()

            if node_id == end_id:
                return path

            if len(path) > max_depth:
                continue

            # Find connected nodes
            edges = self.db.query(GraphEdge).filter(
                GraphEdge.source_node_id == node_id
            ).all()

            for edge in edges:
                if edge.target_node_id not in visited:
                    visited.add(edge.target_node_id)
                    queue.append((
                        edge.target_node_id,
                        path + [edge.target_node_id]
                    ))

        return []
