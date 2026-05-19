"""Concept clustering algorithm"""

import logging
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
from sqlalchemy.orm import Session as DBSession

from app.models.graph import GraphNode, GraphEdge, ConceptCluster

logger = logging.getLogger(__name__)


class ConceptClusterer:
    """Cluster related concepts using graph-based algorithms"""

    def __init__(self, db: DBSession):
        """Initialize concept clusterer"""
        self.db = db

    def cluster_by_similarity(self, threshold: float = 0.6) -> List[ConceptCluster]:
        """Cluster concepts based on edge similarity"""
        try:
            nodes = self.db.query(GraphNode).all()
            visited = set()
            clusters = []

            for node in nodes:
                if node.id in visited:
                    continue

                # BFS to find connected components
                cluster_nodes = self._bfs_cluster(node, threshold)
                visited.update([n.id for n in cluster_nodes])

                if len(cluster_nodes) > 1:
                    cluster = self._create_cluster(cluster_nodes)
                    clusters.append(cluster)

            logger.info(f"Created {len(clusters)} similarity-based clusters")
            return clusters

        except Exception as e:
            logger.error(f"Error clustering by similarity: {e}")
            return []

    def _bfs_cluster(self, start_node: GraphNode, threshold: float) -> List[GraphNode]:
        """BFS to find cluster around a node"""
        cluster = []
        visited = set()
        queue = [start_node]

        while queue:
            node = queue.pop(0)
            if node.id in visited:
                continue

            visited.add(node.id)
            cluster.append(node)

            # Find connected nodes with strong edges
            neighbors = self.db.query(GraphNode).join(
                GraphEdge,
                (GraphEdge.target_node_id == GraphNode.id)
            ).filter(
                GraphEdge.source_node_id == node.id,
                GraphEdge.strength_score >= threshold
            ).all()

            for neighbor in neighbors:
                if neighbor.id not in visited:
                    queue.append(neighbor)

        return cluster

    def _create_cluster(self, nodes: List[GraphNode]) -> ConceptCluster:
        """Create a cluster from nodes"""
        node_ids = [n.id for n in nodes]
        primary_topic = self._find_primary_topic(nodes)
        cohesion = self._calculate_cohesion(nodes)

        cluster = ConceptCluster(
            name=f"Cluster: {primary_topic}",
            description=f"Cluster containing {len(nodes)} related concepts",
            primary_topic=primary_topic,
            node_ids=node_ids,
            size=len(nodes),
            cohesion_score=cohesion
        )

        self.db.add(cluster)
        return cluster

    def _find_primary_topic(self, nodes: List[GraphNode]) -> str:
        """Find the primary topic for a cluster"""
        # Use node with highest importance as primary
        if nodes:
            primary = max(nodes, key=lambda n: n.importance_score)
            return primary.name
        return "Unknown"

    def _calculate_cohesion(self, nodes: List[GraphNode]) -> float:
        """Calculate cluster cohesion (0-1)"""
        if len(nodes) < 2:
            return 1.0

        # Calculate average edge strength within cluster
        total_strength = 0
        edge_count = 0

        node_ids = {n.id for n in nodes}

        for node in nodes:
            edges = self.db.query(GraphEdge).filter(
                GraphEdge.source_node_id == node.id,
                GraphEdge.target_node_id.in_(node_ids)
            ).all()

            for edge in edges:
                total_strength += edge.strength_score
                edge_count += 1

        if edge_count == 0:
            return 0.5  # Default for disconnected cluster

        return min(total_strength / edge_count, 1.0)

    def cluster_by_type(self) -> List[ConceptCluster]:
        """Cluster concepts by their type"""
        try:
            type_groups = defaultdict(list)

            # Group nodes by type
            nodes = self.db.query(GraphNode).all()
            for node in nodes:
                type_groups[node.node_type].append(node.id)

            # Create clusters
            clusters = []
            for node_type, node_ids in type_groups.items():
                if len(node_ids) > 1:
                    cluster = ConceptCluster(
                        name=f"{node_type.title()}s",
                        description=f"All {node_type} nodes",
                        primary_topic=node_type,
                        node_ids=node_ids,
                        size=len(node_ids),
                        cohesion_score=0.8
                    )
                    clusters.append(cluster)

            return clusters

        except Exception as e:
            logger.error(f"Error clustering by type: {e}")
            return []

    def cluster_by_topic(self) -> List[ConceptCluster]:
        """Cluster concepts by inferred topic"""
        try:
            topic_groups = defaultdict(list)

            # Infer topics and group
            nodes = self.db.query(GraphNode).all()
            for node in nodes:
                topic = self._infer_topic(node)
                topic_groups[topic].append(node.id)

            # Create clusters
            clusters = []
            for topic, node_ids in topic_groups.items():
                if len(node_ids) > 1:
                    cluster = ConceptCluster(
                        name=f"Topic: {topic}",
                        description=f"Concepts related to {topic}",
                        primary_topic=topic,
                        node_ids=node_ids,
                        size=len(node_ids),
                        cohesion_score=0.75
                    )
                    clusters.append(cluster)

            return clusters

        except Exception as e:
            logger.error(f"Error clustering by topic: {e}")
            return []

    def _infer_topic(self, node: GraphNode) -> str:
        """Infer topic for a node"""
        # Topic assignment based on node type and name patterns
        name_lower = node.name.lower()

        if node.node_type in ["language", "framework", "technology"]:
            # Get connected framework/technology nodes
            edges = self.db.query(GraphEdge).filter(
                GraphEdge.source_node_id == node.id
            ).limit(1).all()

            if edges:
                target = self.db.query(GraphNode).filter(
                    GraphNode.id == edges[0].target_node_id
                ).first()
                if target:
                    return target.name.split()[0].title()

        if "python" in name_lower:
            return "Python Ecosystem"
        elif "javascript" in name_lower or "react" in name_lower or "node" in name_lower:
            return "Web Development"
        elif "machine" in name_lower or "deep" in name_lower or "neural" in name_lower:
            return "Machine Learning"
        elif "data" in name_lower or "database" in name_lower:
            return "Data"
        else:
            return "General"

    def hierarchical_clustering(self, distance_threshold: float = 0.5) -> Dict[str, List[int]]:
        """Perform hierarchical clustering"""
        try:
            nodes = self.db.query(GraphNode).all()

            if not nodes:
                return {}

            # Start with each node in its own cluster
            clusters = {str(n.id): [n.id] for n in nodes}

            # Iteratively merge similar clusters
            changed = True
            while changed:
                changed = False
                cluster_keys = list(clusters.keys())

                for i, key1 in enumerate(cluster_keys):
                    for key2 in cluster_keys[i + 1:]:
                        similarity = self._calculate_cluster_similarity(
                            clusters[key1],
                            clusters[key2]
                        )

                        if similarity > distance_threshold:
                            # Merge clusters
                            clusters[key1].extend(clusters[key2])
                            del clusters[key2]
                            changed = True
                            break

                    if changed:
                        break

            logger.info(f"Hierarchical clustering created {len(clusters)} clusters")
            return clusters

        except Exception as e:
            logger.error(f"Error in hierarchical clustering: {e}")
            return {}

    def _calculate_cluster_similarity(self, cluster1: List[int], cluster2: List[int]) -> float:
        """Calculate similarity between two clusters"""
        try:
            # Count edges between clusters
            edges_between = self.db.query(GraphEdge).filter(
                GraphEdge.source_node_id.in_(cluster1),
                GraphEdge.target_node_id.in_(cluster2)
            ).count()

            edges_between += self.db.query(GraphEdge).filter(
                GraphEdge.source_node_id.in_(cluster2),
                GraphEdge.target_node_id.in_(cluster1)
            ).count()

            # Calculate average strength if edges exist
            if edges_between > 0:
                edges = self.db.query(GraphEdge).filter(
                    (GraphEdge.source_node_id.in_(cluster1)) &
                    (GraphEdge.target_node_id.in_(cluster2)) |
                    ((GraphEdge.source_node_id.in_(cluster2)) &
                     (GraphEdge.target_node_id.in_(cluster1)))
                ).all()

                avg_strength = sum(e.strength_score for e in edges) / len(edges)
                return avg_strength

            return 0.0

        except Exception as e:
            logger.error(f"Error calculating cluster similarity: {e}")
            return 0.0
