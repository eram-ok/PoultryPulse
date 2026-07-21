from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.audit.constants import (
    AuditAction,
    AuditOutcome,
    AuditSeverity,
)
from app.modules.audit.context import (
    AuditRequestContext,
    reset_audit_context,
    set_audit_context,
)
from app.modules.audit.sanitizer import (
    calculate_changes,
    sanitize_mapping,
)
from app.modules.audit.service import AuditService
from app.modules.users.models import User


def get_authenticated_user(context: object) -> User:
    """Extract the authenticated user from the project test context."""

    if isinstance(context, User):
        return context

    if isinstance(context, dict):
        for key in (
            "user",
            "current_user",
            "test_user",
        ):
            candidate = context.get(key)
            if isinstance(candidate, User):
                return candidate

    for attribute in (
        "user",
        "current_user",
        "test_user",
    ):
        candidate = getattr(context, attribute, None)
        if isinstance(candidate, User):
            return candidate

    if isinstance(context, (tuple, list)):
        for candidate in context:
            if isinstance(candidate, User):
                return candidate

    raise AssertionError("Could not extract a User from auth_context.")


def test_sensitive_values_are_redacted() -> None:
    sanitized = sanitize_mapping(
        {
            "username": "admin",
            "password": "do-not-store",
            "refresh_token": "token-value",
            "nested": {
                "api_key": "secret",
                "safe": "visible",
            },
        }
    )

    assert sanitized is not None
    assert sanitized["username"] == "admin"
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["refresh_token"] == "[REDACTED]"
    assert sanitized["nested"]["api_key"] == "[REDACTED]"
    assert sanitized["nested"]["safe"] == "visible"


def test_change_calculation() -> None:
    changes = calculate_changes(
        {"name": "Old", "active": True},
        {"name": "New", "active": True},
    )

    assert changes == {
        "name": {
            "before": "Old",
            "after": "New",
        }
    }


def test_audit_service_uses_request_context(
    database_session: Session,
    auth_context: object,
) -> None:
    test_user = get_authenticated_user(auth_context)
    token = set_audit_context(
        AuditRequestContext(
            request_id="test-request-1",
            request_method="PATCH",
            request_path="/api/v1/farms/example",
            ip_address="127.0.0.1",
            user_agent="pytest",
            actor_user_id=test_user.id,
            actor_farm_id=test_user.farm_id,
            actor_username=test_user.username,
        )
    )

    try:
        item = AuditService(database_session).record(
            module="farms",
            action=AuditAction.UPDATE,
            description="Updated farm settings.",
            resource_type="FarmSettings",
            resource_id=uuid4(),
            before_values={"timezone": "UTC"},
            after_values={"timezone": "Africa/Kampala"},
            commit=True,
        )
    finally:
        reset_audit_context(token)

    assert item.farm_id == test_user.farm_id
    assert item.actor_user_id == test_user.id
    assert item.actor_username == test_user.username
    assert item.request_id == "test-request-1"
    assert item.changes == {
        "timezone": {
            "before": "UTC",
            "after": "Africa/Kampala",
        }
    }


def test_audit_routes_require_authentication(
    client: TestClient,
) -> None:
    assert client.get("/api/v1/audit").status_code == 401


def test_audit_list_summary_and_export(
    authenticated_client: TestClient,
    database_session: Session,
    auth_context: object,
) -> None:
    test_user = get_authenticated_user(auth_context)
    AuditService(database_session).record(
        farm_id=test_user.farm_id,
        actor_user_id=test_user.id,
        actor_username=test_user.username,
        module="users",
        action=AuditAction.CREATE,
        outcome=AuditOutcome.SUCCESS,
        severity=AuditSeverity.INFO,
        description="Created a test user.",
        resource_type="User",
        resource_id=uuid4(),
        commit=True,
    )

    listing = authenticated_client.get("/api/v1/audit")
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1

    summary = authenticated_client.get("/api/v1/audit/summary")
    assert summary.status_code == 200
    assert summary.json()["total"] >= 1

    export = authenticated_client.get("/api/v1/audit/export.csv")
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("text/csv")
    assert "Created a test user." in export.text


def test_request_id_header_is_returned(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get(
        "/api/v1/audit/summary",
        headers={"X-Request-ID": "fixed-request-id"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "fixed-request-id"
