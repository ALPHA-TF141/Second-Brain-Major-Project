"""
Test isolation.

The app reads DATABASE_URL when `app.config` is first imported, and several
research modules reset derived state on the database they point at. Point the
whole test session at a throw-away SQLite file BEFORE any app module is
imported, so the test suite can never read or modify the user's real database
(backend/data/second_brain.db).
"""
import os
import tempfile
from pathlib import Path

import pytest

_TMP_DIR = Path(tempfile.mkdtemp(prefix="secondbrain-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP_DIR / 'test.db').as_posix()}"
os.environ.setdefault("MAIL_SYNC_ENABLED", "false")
os.environ.setdefault("WAKE_WORD_ENABLED", "false")
os.environ.setdefault("VOICE_ANNOUNCE_ENABLED", "false")


@pytest.fixture(scope="session")
def database_url() -> str:
    return os.environ["DATABASE_URL"]
