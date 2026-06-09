"""FastAPI dependency helpers."""

from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.storage.database import session_scope


def get_db_session() -> Iterator[Session]:
    """Yield a database session for request handlers."""
    with session_scope() as session:
        yield session
