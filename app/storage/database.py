"""Database engine and session helpers."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


def create_engine_from_url(database_url: str, *, echo: bool = False) -> Engine:
    """Create a SQLAlchemy engine for the provided URL."""
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, echo=echo, future=True, connect_args=connect_args)


def get_engine() -> Engine:
    """Create a SQLAlchemy engine from application settings."""
    return create_engine_from_url(get_settings().database.url)


def get_session_factory(engine: Engine | None = None) -> sessionmaker[Session]:
    """Return a SQLAlchemy session factory."""
    return sessionmaker(bind=engine or get_engine(), expire_on_commit=False, class_=Session)


@contextmanager
def session_scope(engine: Engine | None = None) -> Iterator[Session]:
    """Provide a transactional session scope."""
    session = get_session_factory(engine)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
