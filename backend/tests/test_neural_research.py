"""
Unit and Integration Tests for Neural Research Upgrades:
- Neural NLI Cross-Encoder Contradiction Detection
- Neural Dependency Temporal Fact Extraction
- Multi-User Benchmark Pipeline Integrity
"""
import pytest
from app.database.init_db import init_database
from app.database.session import SessionLocal
from app.research.neural_nli import neural_nli
from app.research.temporal import temporal_knowledge_graph
from app.research.contradictions import contradiction_resolver
from app.research.bench import benchmark_runner


def test_neural_nli_availability():
    """Ensure ONNX NLI model initializes and reports ready."""
    assert neural_nli.is_available() is True


def test_neural_nli_contradiction():
    """Ensure NLI Cross-Encoder detects semantic contradictions accurately."""
    premise = "The project evaluation deadline is 15 October 2026."
    hypothesis = "The project evaluation deadline is now 30 September 2026."
    is_conflict, severity, label = neural_nli.classify_conflict(premise, hypothesis)
    assert is_conflict is True
    assert severity >= 0.70
    assert label == "contradiction"


def test_neural_nli_entailment():
    """Ensure NLI Cross-Encoder does not falsely flag consistent statements."""
    premise = "We are releasing version 2.0 next Tuesday."
    hypothesis = "Version 2.0 will be released next Tuesday."
    is_conflict, severity, label = neural_nli.classify_conflict(premise, hypothesis)
    assert is_conflict is False
    assert label == "consistent"


def test_neural_temporal_fact_extraction():
    """Ensure neural dependency parsing extracts non-regex state transitions."""
    text = "I switched over to Spring Boot for microservices architecture."
    facts = temporal_knowledge_graph.extract_facts(text, use_neural=True)
    assert len(facts) > 0
    # Predicate canonicalized to focus/current_focus
    predicates = [f["predicate"] for f in facts]
    assert any(p in ("focus", "current_focus") for p in predicates)
    objects = [f["object"].lower() for f in facts]
    assert any("spring boot" in obj for obj in objects)


def test_deterministic_v1_benchmark():
    """Ensure original PersonalBrain-Bench v1 remains 100% green and reproducible."""
    init_database()
    db = SessionLocal()
    try:
        results = benchmark_runner.run_all(db, k=5)
        adaptive = results["results"]["adaptive"]
        assert adaptive["hit_at_k"] == 1.0
        assert adaptive["mrr"] == 1.0
        assert adaptive["stale_top1_rate"] == 0.0
        assert adaptive["forgotten_leak_rate"] == 0.0
    finally:
        db.close()
