from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all PoultryPulse SQLAlchemy models."""

    pass


def get_database_session() -> Generator[Session, None, None]:
    """Provide a database session to a FastAPI route."""

    database_session = SessionLocal()

    try:
        yield database_session
    finally:
        database_session.close()
