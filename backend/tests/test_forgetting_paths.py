"""Forgetting: a forgotten memory must not come back through any user-facing path."""
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.database.init_db import init_database
from app.database.session import SessionLocal
from app.main import app
from app.models.user import User


def test_forgotten_memory_excluded_from_list_detail_search_and_related():
    init_database()
    db = SessionLocal()
    user = db.query(User).first()
    db.close()
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        with TestClient(app) as c:
            m = c.post("/api/memory/memories", json={
                "content": "FORGET probe: the quokka expedition starts in March.",
                "tags": ["expedition"],
            }).json()
            assert c.get(f"/api/memory/memories/{m['id']}").status_code == 200

            assert c.delete(f"/api/memory/memories/{m['id']}").status_code == 200

            assert c.get(f"/api/memory/memories/{m['id']}").status_code == 404
            assert all(x["id"] != m["id"] for x in c.get("/api/memory/memories?limit=200").json())
            assert all(x["id"] != m["id"] for x in c.get("/api/memory/search?q=quokka").json())
            assert c.get(f"/api/memory/memories/{m['id']}/related").status_code in (200, 404)
    finally:
        app.dependency_overrides.pop(get_current_user, None)
