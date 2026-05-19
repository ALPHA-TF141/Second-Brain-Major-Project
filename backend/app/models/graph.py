from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, JSON

from app.database.session import Base


class GraphNode(Base):
    """Represents nodes in the knowledge graph (concepts, memories, sessions, topics)"""
    __tablename__ = "graph_nodes"
    __table_args__ = (
        UniqueConstraint("node_type", "name", name="uq_node_type_name"),
        Index("ix_nodes_type_importance", "node_type", "importance_score"),
        Index("ix_nodes_created", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    node_type = Column(String(80), nullable=False, index=True)  # "concept", "memory", "session", "topic", "technology"
    description = Column(Text, default="")
    
    # Associated content
    memory_id = Column(Integer, ForeignKey("memories.id"), nullable=True, index=True)
    session_id = Column(Integer, ForeignKey("memory_sessions.id"), nullable=True, index=True)
    
    # Metrics
    frequency = Column(Integer, default=1)  # How many times this concept appeared
    importance_score = Column(Float, default=0.0)  # 0-1 importance ranking
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    metadata = Column(JSON, default={})  # Additional metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GraphEdge(Base):
    """Represents relationships/edges in the knowledge graph"""
    __tablename__ = "graph_edges"
    __table_args__ = (
        UniqueConstraint("source_node_id", "target_node_id", "relationship_type", name="uq_edge_relationship"),
        Index("ix_edges_source", "source_node_id"),
        Index("ix_edges_target", "target_node_id"),
        Index("ix_edges_strength", "strength_score"),
    )

    id = Column(Integer, primary_key=True, index=True)
    source_node_id = Column(Integer, ForeignKey("graph_nodes.id"), nullable=False)
    target_node_id = Column(Integer, ForeignKey("graph_nodes.id"), nullable=False)
    
    # Relationship properties
    relationship_type = Column(String(100), nullable=False, index=True)  # "related_to", "depends_on", "follows", "similar_to"
    strength_score = Column(Float, default=0.5)  # 0-1 strength of relationship
    frequency = Column(Integer, default=1)  # How many times this relationship appeared
    
    # Source tracking
    source = Column(String(80), default="auto")  # "auto", "semantic", "temporal", "manual"
    
    # Metadata
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConceptCluster(Base):
    """Groups related concepts together"""
    __tablename__ = "concept_clusters"
    __table_args__ = (Index("ix_clusters_created", "created_at"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, default="")
    
    # Cluster properties
    primary_topic = Column(String(255), default="")
    node_ids = Column(JSON, default=[])  # List of graph_node IDs in this cluster
    size = Column(Integer, default=0)
    cohesion_score = Column(Float, default=0.0)  # How tightly clustered (0-1)
    
    # Metadata
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TopicRelationship(Base):
    """Tracks how topics evolve and relate to each other over time"""
    __tablename__ = "topic_relationships"
    __table_args__ = (
        UniqueConstraint("source_topic", "target_topic", name="uq_topic_relationship"),
        Index("ix_topic_rel_created", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    source_topic = Column(String(255), nullable=False, index=True)
    target_topic = Column(String(255), nullable=False, index=True)
    
    # Relationship metrics
    co_occurrence_count = Column(Integer, default=1)  # Times they appeared together
    learning_progression = Column(String(80), default="")  # "prerequisite", "followup", "related"
    strength = Column(Float, default=0.0)
    
    # Timeline
    first_linked = Column(DateTime, default=datetime.utcnow)
    last_linked = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LearningProgression(Base):
    """Tracks the evolution of learning over time"""
    __tablename__ = "learning_progression"
    __table_args__ = (Index("ix_progression_topic_date", "topic", "date"),)

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(255), nullable=False, index=True)
    
    # Progression metrics
    level = Column(Integer, default=1)  # Learning level (1-5)
    memory_count = Column(Integer, default=0)  # Memories on this topic
    session_count = Column(Integer, default=0)  # Sessions on this topic
    
    # Timeline
    date = Column(DateTime, nullable=False, index=True)  # When this data point was recorded
    duration_hours = Column(Float, default=0.0)
    
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)


class GraphMetadata(Base):
    """Stores graph-wide metadata and statistics"""
    __tablename__ = "graph_metadata"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), nullable=False, unique=True, index=True)
    value = Column(Text, nullable=False)
    
    # Tracking
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
