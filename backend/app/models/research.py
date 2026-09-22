"""
Research-layer models: the tables behind the paper's contributions.
===========================================================================
These are ADDITIVE. Nothing existing changes shape, so the app keeps working
while the research layer lands (Base.metadata.create_all picks these up
automatically on next start).

Design note: every research record is keyed to an existing `Memory.id`. The
research layer observes and annotates memory; it never owns it. That keeps the
capture/ingest pipeline untouched and makes the layer removable.
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.session import Base


class MemoryScore(Base):
    """
    Contribution 1 - Adaptive Memory Scoring.

    One row per memory, recomputed by the scoring agent. The individual
    components are stored, not just the total, so a reviewer can inspect WHY a
    memory ranked where it did and the weights stay tunable.
    """
    __tablename__ = "memory_scores"

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("memories.id"), nullable=False, unique=True, index=True)

    total = Column(Float, default=0.0, index=True)

    # positive contributors
    relevance = Column(Float, default=0.0)          # R - semantic/keyword match to the user's interests
    frequency = Column(Float, default=0.0)          # F - how often this content recurs
    temporal = Column(Float, default=0.0)           # T - recency, with decay
    connectivity = Column(Float, default=0.0)       # G - degree in the knowledge graph
    user_confirmation = Column(Float, default=0.0)  # U - explicit pins/confirmations
    future_utility = Column(Float, default=0.0)     # P - predicted usefulness

    # negative contributors
    redundancy = Column(Float, default=0.0)         # D - duplication penalty
    contradiction = Column(Float, default=0.0)      # C - conflict penalty

    computed_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    weights_version = Column(String(40), default="v1")


class TemporalFact(Base):
    """
    Contribution 2 - Temporal Personal Knowledge Graph.

    A (subject, predicate, object) triple carrying a validity interval. This is
    what makes "I was learning Python" distinguishable from "I am learning Java"
    instead of both being equally true forever.
    """
    __tablename__ = "temporal_facts"
    __table_args__ = (
        Index("ix_temporal_subject_predicate", "subject", "predicate"),
        Index("ix_temporal_validity", "valid_from", "valid_to"),
    )

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(200), nullable=False, index=True)
    predicate = Column(String(120), nullable=False, index=True)
    object = Column(String(300), nullable=False)

    valid_from = Column(DateTime, default=datetime.utcnow, index=True)
    valid_to = Column(DateTime, nullable=True, index=True)   # NULL = still true
    superseded_by = Column(Integer, ForeignKey("temporal_facts.id"), nullable=True)

    confidence = Column(Float, default=0.7)
    source_memory_id = Column(Integer, ForeignKey("memories.id"), nullable=True, index=True)
    extraction_method = Column(String(40), default="rule")   # rule | llm | user
    evidence_text = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class MemoryConflict(Base):
    """
    Contribution 3 - Contradiction-Aware Hybrid RAG.

    A detected conflict between two memories about the same (subject, predicate)
    with incompatible objects. `resolution` records what the retriever should do.
    """
    __tablename__ = "memory_conflicts"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(200), index=True)
    predicate = Column(String(120), index=True)

    older_memory_id = Column(Integer, ForeignKey("memories.id"), nullable=True, index=True)
    newer_memory_id = Column(Integer, ForeignKey("memories.id"), nullable=True, index=True)
    older_value = Column(String(300), default="")
    newer_value = Column(String(300), default="")

    detected_by = Column(String(40), default="rule")    # rule | llm
    conflict_type = Column(String(40), default="value_change")  # value_change | negation | staleness
    severity = Column(Float, default=0.5)

    resolution = Column(String(40), default="prefer_newer")  # prefer_newer | prefer_older | ask_user | keep_both
    resolved = Column(Boolean, default=False)
    detected_at = Column(DateTime, default=datetime.utcnow)


class MemoryConsolidation(Base):
    """
    Contribution 4 - Memory Consolidation.

    Records that a set of memories was merged into one canonical memory, and
    keeps the member ids so provenance is never lost (the paper claims
    provenance preservation explicitly).
    """
    __tablename__ = "memory_consolidations"

    id = Column(Integer, primary_key=True, index=True)
    canonical_memory_id = Column(Integer, ForeignKey("memories.id"), nullable=False, index=True)
    merged_memory_ids = Column(Text, default="")        # comma-separated ids
    merged_count = Column(Integer, default=0)
    similarity_threshold = Column(Float, default=0.90)
    method = Column(String(40), default="semantic")    # semantic | hash | hybrid
    tokens_before = Column(Integer, default=0)
    tokens_after = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class ForgottenMemory(Base):
    """
    Contribution 6 - Forgetting / Unlearning.

    A tombstone. The row stays in `memories` (so ids stay stable and history is
    auditable) but retrieval hard-excludes anything listed here. Un-learning must
    be enforced at RETRIEVAL time - deleting the row would not stop a cached
    vector from being returned, which is the subtle failure mode.
    """
    __tablename__ = "forgotten_memories"

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("memories.id"), nullable=False, unique=True, index=True)
    reason = Column(String(200), default="user_request")
    requested_by = Column(String(80), default="user")
    hard_delete = Column(Boolean, default=False)
    forgotten_at = Column(DateTime, default=datetime.utcnow, index=True)


class KnowledgeGap(Base):
    """
    Contribution 5 - Knowledge-Gap Detection.

    A concept the user has encountered without depth: mentioned repeatedly, but
    weakly connected in the graph and never explained in their own words.
    """
    __tablename__ = "knowledge_gaps"

    id = Column(Integer, primary_key=True, index=True)
    concept = Column(String(200), nullable=False, index=True)
    mentions = Column(Integer, default=0)
    depth_score = Column(Float, default=0.0)         # 0 = shallow exposure, 1 = well understood
    connectivity = Column(Float, default=0.0)
    evidence_count = Column(Integer, default=0)
    gap_score = Column(Float, default=0.0, index=True)
    rationale = Column(Text, default="")
    detected_at = Column(DateTime, default=datetime.utcnow)


class ResearchRun(Base):
    """One execution of the benchmark / evaluation harness, so results are traceable."""
    __tablename__ = "research_runs"

    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String(40), default="benchmark")   # benchmark | scoring | consolidation
    system = Column(String(60), default="")          # which variant was evaluated
    questions = Column(Integer, default=0)
    metrics_json = Column(Text, default="{}")
    duration_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
