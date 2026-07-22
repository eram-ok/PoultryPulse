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
    (
        "eggs.view",
        "eggs",
        "View egg inventory",
    ),
    (
        "eggs.adjust",
        "eggs",
        "Adjust egg inventory",
    ),
    (
        "eggs.issue",
        "eggs",
        "Issue eggs",
    ),
    (
        "eggs.reverse",
        "eggs",
        "Reverse egg inventory transactions",
    ),
    (
        "feed.view",
        "feed",
        "View feed inventory and usage",
    ),
    (
        "feed.items.manage",
        "feed",
        "Manage feed items",
    ),
    (
        "feed.purchases.create",
        "feed",
        "Record feed purchases",
    ),
    (
        "feed.usage.record",
        "feed",
        "Record flock feed usage",
    ),
    (
        "feed.adjust",
        "feed",
        "Adjust feed inventory",
    ),
    (
        "feed.reverse",
        "feed",
        "Reverse feed inventory transactions",
    ),
    (
        "bird_losses.view",
        "bird_losses",
        "View mortality and culling records",
    ),
    (
        "bird_losses.record",
        "bird_losses",
        "Record mortality and culling",
    ),
    (
        "bird_losses.reverse",
        "bird_losses",
        "Reverse mortality and culling records",
    ),
    (
        "health.view",
        "health",
        "View vaccination and health records",
    ),
    (
        "health.products.manage",
        "health",
        "Manage veterinary health products",
    ),
    (
        "health.vaccinations.schedule",
        "health",
        "Schedule flock vaccinations",
    ),
    (
        "health.vaccinations.complete",
        "health",
        "Complete scheduled vaccinations",
    ),
    (
        "health.incidents.manage",
        "health",
        "Manage flock health incidents",
    ),
    (
        "health.treatments.manage",
        "health",
        "Manage flock treatment records",
    ),
    (
        "health.resolve",
        "health",
        "Resolve health incidents and treatments",
    ),
    (
        "sales.view",
        "sales",
        "View Sales",
    ),
    (
        "customers.manage",
        "sales",
        "Manage Customers",
    ),
    (
        "sales.create",
        "sales",
        "Create Sales",
    ),
    (
        "sales.confirm",
        "sales",
        "Confirm Sales",
    ),
    (
        "sales.cancel",
        "sales",
        "Cancel Sales",
    ),
    (
        "payments.record",
        "sales",
        "Record Payments",
    ),
    (
        "payments.reverse",
        "sales",
        "Reverse Payments",
    ),
    (
        "sales.returns",
        "sales",
        "Manage Sale Returns",
    ),
    (
        "finance.view",
        "finance",
        "View Finance",
    ),
    (
        "expense_categories.manage",
        "finance",
        "Manage Expense Categories",
    ),
    (
        "expenses.record",
        "finance",
        "Record Expenses",
    ),
    (
        "expenses.void",
        "finance",
        "Void Expenses",
    ),
    (
        "supplier_bills.manage",
        "finance",
        "Manage Supplier Bills",
    ),
    (
        "supplier_payments.record",
        "finance",
        "Record Supplier Payments",
    ),
    (
        "supplier_payments.reverse",
        "finance",
        "Reverse Supplier Payments",
    ),
    (
        "cash_ledger.adjust",
        "finance",
        "Adjust Cash Ledger",
    ),
    (
        "finance.reports",
        "finance",
        "View Finance Reports",
    ),
    (
        "dashboard.view",
        "reports",
        "View Dashboard",
    ),
    (
        "reports.view",
        "reports",
        "View Analytics Reports",
    ),
    (
        "alerts.view",
        "alerts",
        "View Operational Alerts",
    ),
    (
        "alerts.manage",
        "alerts",
        "Manage Persistent Alerts",
    ),
    (
        "alerts.assign",
        "alerts",
        "Assign Alerts to Users",
    ),
    (
        "alerts.acknowledge",
        "alerts",
        "Acknowledge Alerts",
    ),
    (
        "alerts.resolve",
        "alerts",
        "Resolve and Reopen Alerts",
    ),
    (
        "alerts.refresh",
        "alerts",
        "Refresh Operational Alerts",
    ),
    (
        "notifications.manage",
        "alerts",
        "Manage Notification Preferences",
    ),
    (
        "notifications.send",
        "alerts",
        "Send and Retry Notifications",
    ),
    (
        "notifications.view_deliveries",
        "alerts",
        "View Notification Delivery History",
    ),
    (
        "audit.view",
        "audit",
        "View Audit Trail",
    ),
    (
        "audit.export",
        "audit",
        "Export Audit Trail",
    ),
    (
        "audit.manage",
        "audit",
        "Manage Audit Settings",
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

    test_client = TestClient(app)

    try:
        yield test_client
    finally:
        test_client.close()
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
