"""
Research layer: the seven contributions behind the IEEE paper.

Importing this package guarantees every ORM model is registered, because
SQLAlchemy cannot resolve relationships between mappers that were never
imported - which fails confusingly at query time rather than at import time.
"""
from app.database.init_db import init_database  # noqa: F401  (registers all models)


def ensure_models_loaded() -> None:
    """Idempotent: importing init_db is what actually matters."""
    return None


__all__ = ["ensure_models_loaded", "init_database"]
