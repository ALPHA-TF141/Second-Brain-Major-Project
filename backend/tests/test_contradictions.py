"""
Phase 5 - Contradiction detection.

The required distinctions:
  genuine conflict   same thing, same time anchor, incompatible value
  valid change       same thing, different time anchor (the deadline moved)
  coexistence        different things that merely share wording
  uncertainty        a hedged claim is not treated as a hard conflict
  corroboration      several sources agreeing is not a conflict
Conflicts are stored with provenance and never silently deleted.
Rule-based only (use_neural=False), so results are the same on every machine.
"""
from app.research.contradictions import contradiction_resolver as cr
from app.models.research import MemoryConflict
from tests.research_fixtures import db, dt, make_memory  # noqa: F401


def _conflicts_between(db, a, b):
    return [
        c for c in db.query(MemoryConflict).all()
        if {c.older_memory_id, c.newer_memory_id} == {a.id, b.id}
    ]


def _run(db, memories):
    return cr.resolve(db, memory_ids=[m.id for m in memories], use_neural=False)


# ---------------------------------------------------------------- genuine conflicts

def test_same_meeting_same_day_different_time_is_a_conflict(db):
    """The paper's example: 10 AM vs 2 PM for the same meeting on the same date."""
    a = make_memory(db, "The team meeting is at 10 AM on 20 October 2026.", dt(2026, 10, 1))
    b = make_memory(db, "The team meeting is at 2 PM on 20 October 2026.", dt(2026, 10, 5))
    _run(db, [a, b])
    rows = _conflicts_between(db, a, b)
    assert len(rows) == 1
    assert rows[0].conflict_type == "contradiction"
    assert rows[0].older_memory_id == a.id and rows[0].newer_memory_id == b.id


def test_conflict_keeps_both_values_and_sources(db):
    a = make_memory(db, "The team meeting is at 10 AM on 20 October 2026.", dt(2026, 10, 1), source="mail")
    b = make_memory(db, "The team meeting is at 2 PM on 20 October 2026.", dt(2026, 10, 5), source="screen")
    _run(db, [a, b])
    row = _conflicts_between(db, a, b)[0]
    assert row.older_value == "10am"          # normalised clock time
    assert row.newer_value == "2pm"
    # the losing claim is still in the store
    assert db.query(type(a)).filter(type(a).id == a.id).one().content.startswith("The team meeting")


def test_contradictory_claims_from_different_sources_are_detected(db):
    a = make_memory(db, "Project deadline for the SecondBrain evaluation is 15 October 2026.", dt(2026, 9, 1), source="mail")
    b = make_memory(db, "Project deadline for the SecondBrain evaluation moved to 30 September 2026.", dt(2026, 9, 20), source="screen")
    _run(db, [a, b])
    assert len(_conflicts_between(db, a, b)) == 1


# ---------------------------------------------------------------- valid change over time

def test_moved_deadline_is_a_value_change_not_a_contradiction(db):
    """Different dates on different days: the fact changed over time."""
    a = make_memory(db, "Project deadline for the SecondBrain evaluation is 15 October 2026.", dt(2026, 9, 1))
    b = make_memory(db, "Project deadline for the SecondBrain evaluation moved to 30 September 2026.", dt(2026, 9, 20))
    _run(db, [a, b])
    rows = _conflicts_between(db, a, b)
    assert rows and all(r.conflict_type == "value_change" for r in rows)
    assert rows[0].resolution == "prefer_newer"


def test_same_meeting_on_different_days_is_not_a_contradiction(db):
    """10 AM on 20 Oct and 2 PM on 21 Oct are two different events, not a conflict."""
    a = make_memory(db, "The team meeting is at 10 AM on 20 October 2026.", dt(2026, 10, 1))
    b = make_memory(db, "The team meeting is at 2 PM on 21 October 2026.", dt(2026, 10, 2))
    _run(db, [a, b])
    assert not [r for r in _conflicts_between(db, a, b) if r.conflict_type == "contradiction"]


# ---------------------------------------------------------------- coexistence / unrelated

def test_unrelated_memories_with_similar_wording_are_not_paired(db):
    a = make_memory(db, "Dentist appointment is booked for 3 March 2026 at the clinic.", dt(2026, 2, 1))
    b = make_memory(db, "Gym membership renews automatically on 12 March 2026 for the clinic plan.", dt(2026, 2, 10))
    _run(db, [a, b])
    assert _conflicts_between(db, a, b) == []


def test_coexisting_facts_are_not_conflicts(db):
    """Knowing two languages is not a contradiction."""
    a = make_memory(db, "I know Python well and use it daily.", dt(2026, 1, 1))
    b = make_memory(db, "I know Java well and use it at work.", dt(2026, 1, 2))
    _run(db, [a, b])
    assert _conflicts_between(db, a, b) == []


# ---------------------------------------------------------------- uncertainty

def test_hedged_claim_is_not_recorded_as_a_hard_conflict(db):
    a = make_memory(db, "The team meeting is at 10 AM on 20 October 2026.", dt(2026, 10, 1))
    b = make_memory(db, "The team meeting might be at 2 PM on 20 October 2026, not sure.", dt(2026, 10, 5))
    _run(db, [a, b])
    assert not [r for r in _conflicts_between(db, a, b) if r.conflict_type == "contradiction"]


# ---------------------------------------------------------------- corroboration

def test_corroborating_sources_do_not_conflict(db):
    a = make_memory(db, "The team meeting is at 10 AM on 20 October 2026.", dt(2026, 10, 1), source="mail")
    b = make_memory(db, "Reminder: the team meeting is at 10 AM on 20 October 2026.", dt(2026, 10, 2), source="screen")
    c = make_memory(db, "Calendar shows the team meeting at 10 AM on 20 October 2026.", dt(2026, 10, 3), source="calendar")
    _run(db, [a, b, c])
    assert db.query(MemoryConflict).count() == 0


def test_dissenting_source_conflicts_with_each_supporter(db):
    a = make_memory(db, "The team meeting is at 10 AM on 20 October 2026.", dt(2026, 10, 1))
    b = make_memory(db, "Reminder: the team meeting is at 10 AM on 20 October 2026.", dt(2026, 10, 2))
    odd = make_memory(db, "The team meeting is at 2 PM on 20 October 2026.", dt(2026, 10, 5))
    _run(db, [a, b, odd])
    assert _conflicts_between(db, a, odd) and _conflicts_between(db, b, odd)
    assert not _conflicts_between(db, a, b)


# ---------------------------------------------------------------- negation direction and penalty

def test_negation_conflict_names_the_older_memory(db):
    """The older claim must be the one that gets damped, regardless of which text has the negation."""
    old = make_memory(db, "I use Java daily for backend work.", dt(2026, 1, 1))
    new = make_memory(db, "I stopped using Java for backend work.", dt(2026, 6, 1))
    _run(db, [old, new])
    rows = [r for r in db.query(MemoryConflict).all() if r.conflict_type == "negation"]
    assert rows, "negation conflict should be detected"
    assert all(r.older_memory_id is not None for r in rows)
    assert all(r.older_memory_id == old.id and r.newer_memory_id == new.id for r in rows)


def test_superseded_memory_is_damped_but_not_removed(db):
    old = make_memory(db, "The team meeting is at 10 AM on 20 October 2026.", dt(2026, 10, 1))
    new = make_memory(db, "The team meeting is at 2 PM on 20 October 2026.", dt(2026, 10, 5))
    _run(db, [old, new])
    mult_old, reason = cr.conflict_penalty(db, old.id)
    mult_new, _ = cr.conflict_penalty(db, new.id)
    assert 0.3 <= mult_old < 1.0
    assert mult_new == 1.0
    assert "superseded" in reason
    assert db.query(type(old)).filter(type(old).id == old.id).count() == 1  # not deleted


# ---------------------------------------------------------------- evidence is never silently erased

def test_rerun_does_not_erase_a_resolved_conflict(db):
    """A user-resolved conflict is evidence; an automatic re-scan must not delete it."""
    a = make_memory(db, "The team meeting is at 10 AM on 20 October 2026.", dt(2026, 10, 1))
    b = make_memory(db, "The team meeting is at 2 PM on 20 October 2026.", dt(2026, 10, 5))
    _run(db, [a, b])
    row = _conflicts_between(db, a, b)[0]
    row.resolved = True
    db.commit()

    cr.resolve(db, use_neural=False)  # unscoped re-run over the whole database
    survivors = [r for r in db.query(MemoryConflict).all() if r.id == row.id]
    assert survivors and survivors[0].resolved is True


def test_rerun_does_not_duplicate_unresolved_conflicts(db):
    a = make_memory(db, "The team meeting is at 10 AM on 20 October 2026.", dt(2026, 10, 1))
    b = make_memory(db, "The team meeting is at 2 PM on 20 October 2026.", dt(2026, 10, 5))
    _run(db, [a, b])
    first = db.query(MemoryConflict).count()
    _run(db, [a, b])
    assert db.query(MemoryConflict).count() == first
