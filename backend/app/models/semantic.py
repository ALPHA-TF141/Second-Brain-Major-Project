from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint

from app.database.session import Base


class VectorMemory(Base):
    __tablename__ = "vector_memories"
    __table_args__ = (UniqueConstraint("memory_id", name="uq_vector_memory"),)

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("memories.id"), nullable=False, index=True)
    collection_name = Column(String(120), default="second_brain_memories")
    vector_id = Column(String(160), nullable=False, index=True)
    embedding_model = Column(String(160), default="all-MiniLM-L6-v2")
    dimensions = Column(Integer, default=384)
    indexed_at = Column(DateTime, default=datetime.utcnow)


class EmbeddingJob(Base):
    __tablename__ = "embedding_jobs"

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("memories.id"), nullable=True, index=True)
    job_type = Column(String(80), default="index_memory")
    status = Column(String(80), default="queued", index=True)
    error_message = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)


class SemanticRelationship(Base):
    __tablename__ = "semantic_relationships"

    id = Column(Integer, primary_key=True, index=True)
    source_memory_id = Column(Integer, ForeignKey("memories.id"), nullable=False, index=True)
    target_memory_id = Column(Integer, ForeignKey("memories.id"), nullable=False, index=True)
    similarity_score = Column(Float, default=0.0)
    relationship_type = Column(String(80), default="semantic_similarity")
    created_at = Column(DateTime, default=datetime.utcnow)


class MemoryCluster(Base):
    __tablename__ = "memory_clusters"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String(180), nullable=False, index=True)
    description = Column(Text, default="")
    memory_ids = Column(Text, default="")
    size = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    search_type = Column(String(80), default="hybrid")
    result_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
