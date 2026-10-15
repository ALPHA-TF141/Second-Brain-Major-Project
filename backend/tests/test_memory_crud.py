"""
Memory CRUD: validation, persistence across restart, error responses, and
isolation (an operation never changes unrelated memories).
"""
import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.database.init_db import init_database
from app.database.session import SessionLocal
from app.main import app
from app.models.memory import Memory, MemoryTag, SearchIndex
from app.models.user import User


@pytest.fixture(scope="module")
def user_id():
    init_database()
    db = SessionLocal()
    try:
        return db.query(User).first().id
    finally:
        db.close()


@pytest.fixture()
def client(user_id):
    def _user():
        db = SessionLocal()
        try:
            return db.query(User).filter(User.id == user_id).first()
        finally:
            db.close()

    app.dependency_overrides[get_current_user] = _user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_current_user, None)


def _create(client, content, **extra):
    body = {"content": content, **extra}
    res = client.post("/api/memory/memories", json=body)
    assert res.status_code == 201, res.text
    return res.json()


def test_create_returns_memory_with_tags(client):
    m = _create(client, "CRUD check: the Phase-2 deadline is 1 November 2026.", title="Deadline", tags=["deadline", "Project"])
    assert m["id"] > 0
    assert m["title"] == "Deadline"
    assert m["source_type"] == "manual"
    assert set(m["tags"]) == {"deadline", "Project"}


@pytest.mark.parametrize("content", ["", "   ", "\n\t"])
def test_rejects_empty_content(client, content):
    res = client.post("/api/memory/memories", json={"content": content})
    assert res.status_code == 422


def test_rejects_missing_content_field(client):
    res = client.post("/api/memory/memories", json={"title": "no content"})
    assert res.status_code == 422


def test_rejects_oversized_content(client):
    res = client.post("/api/memory/memories", json={"content": "x" * 20_001})
    assert res.status_code == 422


def test_rejects_too_many_tags(client):
    res = client.post("/api/memory/memories", json={"content": "many tags", "tags": [f"t{i}" for i in range(21)]})
    assert res.status_code == 422


def test_duplicate_content_is_conflict_not_silent_overwrite(client):
    text = "CRUD duplicate probe: the lab report is due Friday."
    first = _create(client, text)
    res = client.post("/api/memory/memories", json={"content": text.upper()})  # same after normalisation
    assert res.status_code == 409
    assert str(first["id"]) in res.json()["detail"]


def test_get_by_id_and_nonexistent_id(client):
    m = _create(client, "CRUD get probe: the seminar room is B-204.")
    assert client.get(f"/api/memory/memories/{m['id']}").json()["content"] == m["content"]
    assert client.get("/api/memory/memories/999999").status_code == 404


def test_list_is_paginated_and_validated(client):
    _create(client, "CRUD list probe one.")
    assert client.get("/api/memory/memories?limit=1").status_code == 200
    assert len(client.get("/api/memory/memories?limit=1").json()) == 1
    assert client.get("/api/memory/memories?limit=0").status_code == 422
    assert client.get("/api/memory/memories?limit=500").status_code == 422
    assert client.get("/api/memory/memories?offset=-1").status_code == 422


def test_update_changes_only_requested_fields(client):
    a = _create(client, "CRUD update target: project lead is Asha.", tags=["team"])
    b = _create(client, "CRUD update bystander: the room is C-101.", tags=["room"])

    res = client.put(f"/api/memory/memories/{a['id']}", json={"title": "Lead"})
    assert res.status_code == 200
    updated = res.json()
    assert updated["title"] == "Lead"
    assert updated["content"] == a["content"]
    assert updated["tags"] == ["team"]  # untouched when `tags` is omitted

    assert client.get(f"/api/memory/memories/{b['id']}").json() == b  # bystander unchanged


def test_update_content_refreshes_search_index(client):
    m = _create(client, "CRUD index probe: alpha quartz protocol.")
    res = client.put(f"/api/memory/memories/{m['id']}", json={"content": "CRUD index probe: beta zircon protocol."})
    assert res.status_code == 200

    hits = client.get("/api/memory/search?q=zircon").json()
    assert any(h["id"] == m["id"] for h in hits)
    stale = client.get("/api/memory/search?q=quartz").json()
    assert not any(h["id"] == m["id"] for h in stale)


def test_update_validation_and_errors(client):
    m = _create(client, "CRUD validation target.")
    assert client.put(f"/api/memory/memories/{m['id']}", json={"content": "   "}).status_code == 422
    assert client.put(f"/api/memory/memories/{m['id']}", json={}).status_code == 422
    assert client.put("/api/memory/memories/999999", json={"title": "x"}).status_code == 404


def test_update_to_existing_content_is_conflict(client):
    _create(client, "CRUD clash source text.")
    target = _create(client, "CRUD clash target text.")
    res = client.put(f"/api/memory/memories/{target['id']}", json={"content": "crud clash source text."})
    assert res.status_code == 409


def test_soft_delete_hides_memory_and_keeps_others(client):
    victim = _create(client, "CRUD soft delete victim: the passport renewal is pending.", tags=["personal"])
    keeper = _create(client, "CRUD soft delete keeper: the library book is due.")

    res = client.delete(f"/api/memory/memories/{victim['id']}")
    assert res.status_code == 200
    body = res.json()
    assert body["forgotten"] is True and body["hard_delete"] is False

    assert client.get(f"/api/memory/memories/{victim['id']}").status_code == 404
    listed = {m["id"] for m in client.get("/api/memory/memories?limit=200").json()}
    assert victim["id"] not in listed
    assert keeper["id"] in listed
    assert not any(h["id"] == victim["id"] for h in client.get("/api/memory/search?q=passport").json())


def test_hard_delete_purges_tags_and_index(client):
    victim = _create(client, "CRUD hard delete victim: zebra ledger entry.", tags=["ledger-tag"])
    vid = victim["id"]
    res = client.delete(f"/api/memory/memories/{vid}?hard=true")
    assert res.status_code == 200
    assert res.json()["hard_delete"] is True

    db = SessionLocal()
    try:
        assert db.query(Memory).filter(Memory.id == vid).first() is None
        assert db.query(MemoryTag).filter(MemoryTag.memory_id == vid).count() == 0
        assert db.query(SearchIndex).filter(SearchIndex.memory_id == vid).count() == 0
    finally:
        db.close()


def test_delete_unknown_or_already_deleted_is_404(client):
    m = _create(client, "CRUD double delete probe.")
    assert client.delete(f"/api/memory/memories/{m['id']}").status_code == 200
    assert client.delete(f"/api/memory/memories/{m['id']}").status_code == 404
    assert client.delete("/api/memory/memories/999999").status_code == 404


def test_requires_authentication():
    app.dependency_overrides.pop(get_current_user, None)
    with TestClient(app) as c:
        assert c.get("/api/memory/memories").status_code == 401
        assert c.post("/api/memory/memories", json={"content": "x"}).status_code == 401


def test_memories_survive_restart(client, user_id):
    """Data written through the API is still there after the engine is discarded."""
    m = _create(client, "CRUD persistence probe: the server restart keeps this.")
    from app.database.session import engine

    engine.dispose()  # simulate closing every connection, as on backend shutdown
    with TestClient(app) as fresh:
        app.dependency_overrides[get_current_user] = lambda: SessionLocal().query(User).filter(User.id == user_id).first()
        res = fresh.get(f"/api/memory/memories/{m['id']}")
    assert res.status_code == 200
    assert res.json()["content"] == m["content"]
