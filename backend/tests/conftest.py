from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import engine, get_database_session
from app.main import app


@pytest.fixture()
def database_session() -> Generator[Session, None, None]:
    """Create a test session that is rolled back after each test."""

    connection = engine.connect()
    outer_transaction = connection.begin()

    session = Session(
        bind=connection,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session
    finally:
        session.close()

        if outer_transaction.is_active:
            outer_transaction.rollback()

        connection.close()


@pytest.fixture()
def client(
    database_session: Session,
) -> Generator[TestClient, None, None]:
    """Create an API test client using the rollback test session."""

    def override_database_session() -> Generator[Session, None, None]:
        yield database_session

    app.dependency_overrides[get_database_session] = override_database_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
