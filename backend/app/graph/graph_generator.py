"""Knowledge graph generation pipeline"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session as DBSession

from app.graph.neo4j_client import Neo4jClient
from app.entities.entity_extractor import EntityExtractor, Entity
from app.relationships.relationship_detector import RelationshipDetector, DetectedRelationship
from app.models.graph import GraphNode, GraphEdge, ConceptCluster, LearningProgression
from app.models.memory import Memory, MemorySession, SemanticChunk

logger = logging.getLogger(__name__)


class GraphGenerator:
    """Generate and maintain knowledge graph from memories"""

    def __init__(self, db: DBSession, neo4j_client: Neo4jClient):
        """Initialize graph generator"""
        self.db = db
        self.neo4j = neo4j_client
        self.entity_extractor = EntityExtractor()
        self.relationship_detector = RelationshipDetector()

    def generate_graph_from_memories(self, limit: int = 1000) -> Dict[str, int]:
        """Generate knowledge graph from all memories"""
        stats = {
            "nodes_created": 0,
            "edges_created": 0,
            "clusters_created": 0,
            "errors": 0
        }

        try:
            # Get memories with semantic chunks
            memories = self.db.query(Memory).order_by(
                Memory.created_at.desc()
            ).limit(limit).all()

            logger.info(f"Generating graph from {len(memories)} memories")

            for i, memory in enumerate(memories):
                try:
                    # Extract entities from memory
                    entities = self.entity_extractor.extract_entities(
                        memory.content,
                        source=memory.source_type
                    )

                    # Create nodes for each entity
                    node_ids = []
                    for entity in entities:
                        node = self._create_or_update_node(
                            entity.name,
                            entity.type,
                            memory_id=memory.id,
                            frequency=1
                        )
                        if node:
                            node_ids.append(node.id)
                            stats["nodes_created"] += 1

                    # Create relationships between entities
                    entity_names = [e.name for e in entities]
                    relationships = self.relationship_detector.detect_relationships(
                        entity_names,
                        context=memory.content
                    )

                    for rel in relationships:
                        edge = self._create_or_update_edge(
                            rel.source,
                            rel.target,
                            rel.relationship_type,
                            rel.strength
                        )
                        if edge:
                            stats["edges_created"] += 1

                    # Add memory node to graph
                    memory_node = self._create_memory_node(memory, entity_names)
                    if memory_node:
                        stats["nodes_created"] += 1

                    if (i + 1) % 100 == 0:
                        logger.info(f"Processed {i + 1}/{len(memories)} memories")

                except Exception as e:
                    logger.error(f"Error processing memory {memory.id}: {e}")
                    stats["errors"] += 1
                    continue

            # Create clusters
            clusters = self._create_concept_clusters()
            stats["clusters_created"] = len(clusters)

            logger.info(f"Graph generation complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error in graph generation: {e}")
            raise

    def update_graph_from_session(self, session_id: int) -> Dict[str, int]:
        """Update graph with memories from a session"""
        stats = {
            "nodes_created": 0,
            "edges_created": 0,
            "errors": 0
        }

        try:
            # Get memories from session
            memories = self.db.query(Memory).filter(
                Memory.session_id == session_id
            ).all()

            logger.info(f"Updating graph from session {session_id} with {len(memories)} memories")

            for memory in memories:
                try:
                    entities = self.entity_extractor.extract_entities(
                        memory.content,
                        source=memory.source_type
                    )

                    # Create or update nodes
                    for entity in entities:
                        node = self._create_or_update_node(
                            entity.name,
                            entity.type,
                            memory_id=memory.id
                        )
                        if node:
                            stats["nodes_created"] += 1

                    # Create relationships
                    entity_names = [e.name for e in entities]
                    relationships = self.relationship_detector.detect_relationships(
                        entity_names,
                        context=memory.content
                    )

                    for rel in relationships:
                        edge = self._create_or_update_edge(
                            rel.source,
                            rel.target,
                            rel.relationship_type,
                            rel.strength
                        )
                        if edge:
                            stats["edges_created"] += 1

                except Exception as e:
                    logger.error(f"Error processing memory: {e}")
                    stats["errors"] += 1

            return stats

        except Exception as e:
            logger.error(f"Error updating graph from session: {e}")
            raise

    def _create_or_update_node(
        self,
        name: str,
        node_type: str,
        memory_id: Optional[int] = None,
        frequency: int = 1
    ) -> Optional[GraphNode]:
        """Create or update a graph node"""
        try:
            # Check if node exists
            node = self.db.query(GraphNode).filter(
                GraphNode.name == name,
                GraphNode.node_type == node_type
            ).first()

            if node:
                # Update existing node
                node.frequency += frequency
                node.last_seen = datetime.utcnow()
            else:
                # Create new node
                node = GraphNode(
                    name=name,
                    node_type=node_type,
                    description="",
                    memory_id=memory_id,
                    frequency=1,
                    importance_score=self._calculate_importance(node_type)
                )
                self.db.add(node)

            self.db.commit()

            # Also add to Neo4j
            self.neo4j.get_or_create_node(
                name=name,
                node_type=node_type,
                properties={"db_id": node.id}
            )

            return node

        except Exception as e:
            logger.error(f"Error creating node: {e}")
            self.db.rollback()
            return None

    def _create_or_update_edge(
        self,
        source_name: str,
        target_name: str,
        relationship_type: str,
        strength: float
    ) -> Optional[GraphEdge]:
        """Create or update a graph edge"""
        try:
            # Get source and target nodes
            source_node = self.db.query(GraphNode).filter(
                GraphNode.name == source_name
            ).first()
            target_node = self.db.query(GraphNode).filter(
                GraphNode.name == target_name
            ).first()

            if not source_node or not target_node:
                return None

            # Check if edge exists
            edge = self.db.query(GraphEdge).filter(
                GraphEdge.source_node_id == source_node.id,
                GraphEdge.target_node_id == target_node.id,
                GraphEdge.relationship_type == relationship_type
            ).first()

            if edge:
                # Update existing edge
                edge.frequency += 1
                edge.strength_score = min((edge.strength_score + strength) / 2, 1.0)
            else:
                # Create new edge
                edge = GraphEdge(
                    source_node_id=source_node.id,
                    target_node_id=target_node.id,
                    relationship_type=relationship_type,
                    strength_score=strength,
                    frequency=1,
                    source="auto"
                )
                self.db.add(edge)

            self.db.commit()

            # Also add to Neo4j
            self.neo4j.create_relationship(
                source_name=source_name,
                source_type=source_node.node_type,
                target_name=target_name,
                target_type=target_node.node_type,
                relationship_type=relationship_type,
                strength=strength
            )

            return edge

        except Exception as e:
            logger.error(f"Error creating edge: {e}")
            self.db.rollback()
            return None

    def _create_memory_node(self, memory: Memory, related_entities: List[str]) -> Optional[GraphNode]:
        """Create a memory node and link it to entities"""
        try:
            # Create memory node
            node = self.db.query(GraphNode).filter(
                GraphNode.memory_id == memory.id,
                GraphNode.node_type == "memory"
            ).first()

            if node:
                return node

            node = GraphNode(
                name=f"Memory: {memory.title}",
                node_type="memory",
                description=memory.content[:500],
                memory_id=memory.id,
                frequency=1,
                importance_score=0.5
            )
            self.db.add(node)
            self.db.commit()

            # Link memory to related entities
            for entity_name in related_entities:
                entity_node = self.db.query(GraphNode).filter(
                    GraphNode.name == entity_name
                ).first()

                if entity_node:
                    edge = GraphEdge(
                        source_node_id=node.id,
                        target_node_id=entity_node.id,
                        relationship_type="mentions",
                        strength_score=0.8,
                        frequency=1
                    )
                    self.db.add(edge)

            self.db.commit()
            return node

        except Exception as e:
            logger.error(f"Error creating memory node: {e}")
            self.db.rollback()
            return None

    def _create_concept_clusters(self) -> List[ConceptCluster]:
        """Create clusters of related concepts"""
        try:
            clusters = []

            # Get all concept nodes
            concepts = self.db.query(GraphNode).filter(
                GraphNode.node_type.in_(["concept", "technology", "framework"])
            ).all()

            # Group by category (simple clustering)
            category_map = {}
            for concept in concepts:
                # Determine cluster by node type
                cluster_name = f"{concept.node_type.title()}s"

                if cluster_name not in category_map:
                    category_map[cluster_name] = []

                category_map[cluster_name].append(concept.id)

            # Create cluster records
            for cluster_name, node_ids in category_map.items():
                cluster = ConceptCluster(
                    name=cluster_name,
                    description=f"Cluster of {cluster_name.lower()}",
                    primary_topic=cluster_name,
                    node_ids=node_ids,
                    size=len(node_ids),
                    cohesion_score=0.7
                )
                self.db.add(cluster)
                clusters.append(cluster)

            self.db.commit()
            logger.info(f"Created {len(clusters)} clusters")
            return clusters

        except Exception as e:
            logger.error(f"Error creating clusters: {e}")
            self.db.rollback()
            return []

    def _calculate_importance(self, node_type: str) -> float:
        """Calculate initial importance score based on node type"""
        weights = {
            "framework": 0.8,
            "technology": 0.7,
            "language": 0.75,
            "concept": 0.6,
            "topic": 0.65,
            "memory": 0.4,
            "session": 0.3,
        }
        return weights.get(node_type, 0.5)

    def recalculate_importance_scores(self):
        """Recalculate importance scores for all nodes based on metrics"""
        try:
            nodes = self.db.query(GraphNode).all()

            for node in nodes:
                # Count incoming edges (popularity)
                incoming = self.db.query(GraphEdge).filter(
                    GraphEdge.target_node_id == node.id
                ).count()

                # Count outgoing edges (influence)
                outgoing = self.db.query(GraphEdge).filter(
                    GraphEdge.source_node_id == node.id
                ).count()

                # Calculate based on frequency and edges
                base_score = self._calculate_importance(node.node_type)
                frequency_score = min(node.frequency / 100, 1.0)
                connectivity_score = min((incoming + outgoing) / 20, 1.0)

                node.importance_score = (base_score + frequency_score + connectivity_score) / 3

            self.db.commit()
            logger.info("Importance scores recalculated")

        except Exception as e:
            logger.error(f"Error recalculating importance: {e}")
            self.db.rollback()

    def get_graph_stats(self) -> Dict:
        """Get statistics about the current graph"""
        try:
            total_nodes = self.db.query(GraphNode).count()
            total_edges = self.db.query(GraphEdge).count()
            total_clusters = self.db.query(ConceptCluster).count()

            node_types = self.db.query(
                GraphNode.node_type,
                GraphNode.id
            ).group_by(GraphNode.node_type).all()

            type_counts = {node_type: count for node_type, count in node_types}

            return {
                "total_nodes": total_nodes,
                "total_edges": total_edges,
                "total_clusters": total_clusters,
                "node_types": type_counts,
                "timestamp": datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Error getting graph stats: {e}")
            return {}
