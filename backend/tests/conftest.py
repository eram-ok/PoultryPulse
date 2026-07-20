from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import engine, get_database_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.farms.models import Farm, FarmSettings
from app.modules.users.models import Permission, Role, User


REQUIRED_TEST_PERMISSIONS = [
    ("farms.view", "farms", "View farm information"),
    ("farms.create", "farms", "Create farms"),
    ("farms.update", "farms", "Update farm information"),
    (
        "farms.settings.update",
        "farms",
        "Update farm settings",
    ),
    ("users.view", "users", "View users"),
    ("users.create", "users", "Create users"),
    ("users.update", "users", "Update users"),
    ("users.deactivate", "users", "Deactivate users"),
    ("roles.view", "roles", "View roles"),
    ("roles.assign", "roles", "Assign roles"),
    ("houses.view", "houses", "View poultry houses"),
    ("houses.create", "houses", "Create poultry houses"),
    ("houses.update", "houses", "Update poultry houses"),
    ("suppliers.view", "suppliers", "View suppliers"),
    ("suppliers.create", "suppliers", "Create suppliers"),
    ("suppliers.update", "suppliers", "Update suppliers"),
    ("flocks.view", "flocks", "View flocks"),
    ("flocks.create", "flocks", "Create flocks"),
    ("flocks.update", "flocks", "Update flocks"),
    (
        "flocks.population.adjust",
        "flocks",
        "Adjust flock population",
    ),
    (
        "production.view",
        "production",
        "View production",
    ),
    (
        "production.create",
        "production",
        "Create production",
    ),
    (
        "production.submit",
        "production",
        "Submit production",
    ),
    (
        "production.confirm",
        "production",
        "Confirm production",
    ),
    (
        "production.adjust",
        "production",
        "Adjust production",
    ),
]


@pytest.fixture()
def database_session() -> Generator[Session, None, None]:
    """Create a database session rolled back after each test."""

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
    """Create an API client using the rollback session."""

    def override_database_session() -> Generator[
        Session,
        None,
        None,
    ]:
        yield database_session

    app.dependency_overrides[get_database_session] = override_database_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def auth_context(
    database_session: Session,
) -> dict[str, object]:
    """Create an authenticated administrator for API tests."""

    unique_value = uuid4().hex[:10].upper()

    farm = Farm(
        farm_code=f"TEST-{unique_value}",
        name="PoultryPulse Test Farm",
        owner_name="Test Owner",
        timezone="Africa/Kampala",
        currency_code="UGX",
    )

    farm.settings = FarmSettings()
    database_session.add(farm)
    database_session.flush()

    permissions: list[Permission] = []

    for code, module, name in REQUIRED_TEST_PERMISSIONS:
        permission = database_session.scalar(
            select(Permission).where(Permission.code == code)
        )

        if permission is None:
            permission = Permission(
                code=code,
                module=module,
                name=name,
            )
            database_session.add(permission)
            database_session.flush()

        permissions.append(permission)

    role = Role(
        farm_id=farm.id,
        name="Test Administrator",
        description="Administrator used by automated tests.",
        is_system_role=True,
        is_active=True,
    )

    role.permissions = permissions

    plain_password = "SecureTestPassword123!"

    user = User(
        farm_id=farm.id,
        username="testadmin",
        email=f"test-{uuid4().hex[:8]}@example.com",
        password_hash=hash_password(plain_password),
        first_name="Test",
        last_name="Administrator",
        is_active=True,
        is_verified=True,
        must_change_password=False,
    )

    user.roles.append(role)

    database_session.add_all([role, user])
    database_session.commit()

    access_token = create_access_token(
        str(user.id),
        additional_claims={
            "farm_id": str(farm.id),
            "username": user.username,
        },
    )

    return {
        "farm": farm,
        "user": user,
        "role": role,
        "password": plain_password,
        "login_identifier": (f"{farm.farm_code}:{user.username}"),
        "access_token": access_token,
        "headers": {"Authorization": f"Bearer {access_token}"},
    }


@pytest.fixture()
def authenticated_client(
    client: TestClient,
    auth_context: dict[str, object],
) -> TestClient:
    """Return a client with a valid bearer token."""

    client.headers.update(auth_context["headers"])
    return client
