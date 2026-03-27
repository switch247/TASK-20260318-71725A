from collections.abc import Generator
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import get_settings

# Lazily-created engine/session so tests can set env vars before initialization
settings = get_settings()

engine: Optional[object] = None
SessionLocal: Optional[sessionmaker] = None


def _ensure_engine() -> None:
    global engine, SessionLocal
    if SessionLocal is None or engine is None:
        settings = get_settings()
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# Public alias for tests / other modules to ensure engine is initialized
def ensure_engine() -> None:
    _ensure_engine()


def get_db_session() -> Generator[Session, None, None]:
    _ensure_engine()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
