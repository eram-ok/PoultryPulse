from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class inherited by all PoultryPulse database models."""

    pass


def get_database_session() -> Generator[Session, None, None]:
    """Create and safely close a database session for a request."""

    database_session = SessionLocal()

    try:
        yield database_session
    finally:
        database_session.close()
