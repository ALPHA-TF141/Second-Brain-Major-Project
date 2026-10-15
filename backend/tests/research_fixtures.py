"""Shared fixture: an isolated in-memory database per test (no shared state)."""
from datetime import datetime
from hashlib import sha1

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.database.init_db  # noqa: F401  registers every ORM model
from app.database.session import Base
from app.models.memory import Memory


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def make_memory(db, content, when, title=None, source="screen"):
    """Insert a memory with an explicit creation time (the 'fact date')."""
    memory = Memory(
        session_id=1,
        title=title or content[:60],
        content=content,
        content_hash=sha1(f"{content}|{when.isoformat()}".encode()).hexdigest(),
        source_type=source,
        created_at=when,
    )
    db.add(memory)
    db.commit()
    return memory


def dt(y, m, d, hh=9):
    return datetime(y, m, d, hh, 0, 0)
