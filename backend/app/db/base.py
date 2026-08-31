"""SQLAlchemy base + engine/session plumbing.

Engine construction is lazy — importing `app.db.base` must not require a live
DATABASE_URL (tests build their own in-memory engines against `Base`).
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Declarative base shared by every SIGNAL model."""


_engine = None
_session_factory: sessionmaker[Session] | None = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: one session per request, always closed."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()
