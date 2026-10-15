"""
Phase 3 - Temporal personal knowledge graph.

Facts are (subject, predicate, object) with a validity interval
[valid_from, valid_to); valid_to NULL means still true. Supersession closes the
old fact instead of deleting it, so history survives.
"""
from app.research.temporal import temporal_knowledge_graph as tkg
from tests.research_fixtures import db, dt, make_memory  # noqa: F401  (fixture import)


def _record(db, text, memory):
    facts = tkg.extract_facts(text, use_neural=False)
    return tkg.record_facts(db, facts, source_memory_id=memory.id, at=memory.created_at)


def test_extracts_learning_fact_with_canonical_predicate():
    facts = tkg.extract_facts("I am learning Python for data analysis.", use_neural=False)
    # Extraction keeps the surface predicate; canonicalisation to the state class happens on record.
    assert any(f["predicate"] == "learning" and f["object"].startswith("python") for f in facts)


def test_new_focus_supersedes_old_focus_and_keeps_history(db):
    old = make_memory(db, "I am learning Python.", dt(2026, 1, 10))
    new = make_memory(db, "I am now focusing on Java.", dt(2026, 9, 1))
    _record(db, old.content, old)
    result = _record(db, new.content, new)
    assert result["superseded"] == 1

    current = [f["object"] for f in tkg.current_facts(db, "current_focus")]
    assert current == ["java"]

    hist = tkg.history(db, "current_focus")
    assert len(hist) == 2                      # nothing deleted
    closed = next(h for h in hist if h["object"] == "python")
    assert closed["current"] is False
    assert closed["valid_to"] == dt(2026, 9, 1).isoformat()   # closed at the new fact's date
    assert closed["superseded_by"] is not None


def test_point_in_time_query_returns_fact_valid_at_that_time(db):
    """Roadmap check: graph queries return the right relationship for a requested time."""
    old = make_memory(db, "I am learning Python.", dt(2026, 1, 10))
    new = make_memory(db, "I am now focusing on Java.", dt(2026, 9, 1))
    _record(db, old.content, old)
    _record(db, new.content, new)

    before = [f["object"] for f in tkg.facts_as_of(db, dt(2026, 3, 1), "current_focus")]
    after = [f["object"] for f in tkg.facts_as_of(db, dt(2026, 10, 1), "current_focus")]
    boundary = [f["object"] for f in tkg.facts_as_of(db, dt(2026, 9, 1), "current_focus")]

    assert before == ["python"]
    assert after == ["java"]
    assert boundary == ["java"]     # half-open interval: valid_to is exclusive


def test_point_in_time_before_any_fact_is_empty(db):
    m = make_memory(db, "I am learning Python.", dt(2026, 1, 10))
    _record(db, m.content, m)
    assert tkg.facts_as_of(db, dt(2025, 6, 1), "current_focus") == []


def test_valid_from_uses_fact_date_not_ingest_time(db):
    m = make_memory(db, "I am learning Rust.", dt(2024, 4, 2))
    _record(db, m.content, m)
    (fact,) = tkg.history(db, "current_focus")
    assert fact["valid_from"] == dt(2024, 4, 2).isoformat()


def test_fact_keeps_source_memory_reference(db):
    from app.models.research import TemporalFact

    m = make_memory(db, "I am learning Go.", dt(2026, 2, 2))
    _record(db, m.content, m)
    row = db.query(TemporalFact).filter(TemporalFact.object == "go").one()
    assert row.source_memory_id == m.id
    assert "learning" in row.evidence_text.lower()


def test_coexisting_facts_do_not_supersede_each_other(db):
    """'knows' is not a stateful predicate: knowing Python does not end knowing Java."""
    a = make_memory(db, "I know Python.", dt(2026, 1, 1))
    b = make_memory(db, "I know Java.", dt(2026, 2, 1))
    _record(db, a.content, a)
    result = _record(db, b.content, b)
    assert result["superseded"] == 0
    objects = {f["object"] for f in tkg.current_facts(db, "knows")}
    assert objects == {"python", "java"}


def test_negated_statement_retracts_open_fact(db):
    a = make_memory(db, "I am learning Rust.", dt(2026, 1, 1))
    b = make_memory(db, "I am not learning Rust anymore.", dt(2026, 3, 1))
    _record(db, a.content, a)
    result = _record(db, b.content, b)
    assert result["retracted"] >= 1
    assert tkg.current_facts(db, "current_focus") == []
    closed = tkg.history(db, "current_focus")[0]
    assert closed["valid_to"] == dt(2026, 3, 1).isoformat()


def test_reasserting_same_fact_reinforces_not_duplicates(db):
    a = make_memory(db, "I am learning Go.", dt(2026, 1, 1))
    b = make_memory(db, "Still learning Go this week, I am learning Go.", dt(2026, 1, 8))
    _record(db, a.content, a)
    _record(db, b.content, b)
    assert len(tkg.history(db, "current_focus")) == 1


def test_scope_prevents_corpus_from_closing_live_facts(db):
    """An evaluation corpus must not close the user's own open facts."""
    live = make_memory(db, "I am learning Python.", dt(2026, 1, 1))
    _record(db, live.content, live)
    corpus = make_memory(db, "I am now focusing on Java.", dt(2026, 9, 1))
    facts = tkg.extract_facts(corpus.content, use_neural=False)
    tkg.record_facts(db, facts, source_memory_id=corpus.id, at=corpus.created_at, scope_ids=[corpus.id])
    assert {f["object"] for f in tkg.current_facts(db, "current_focus")} == {"python", "java"}
