"""Database session and engine setup."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True, pool_size=20, max_overflow=40)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session with automatic cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
