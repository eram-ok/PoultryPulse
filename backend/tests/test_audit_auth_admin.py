from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.modules.audit.constants import (
    AuditAction,
    AuditOutcome,
)
from app.modules.audit.models import AuditLog
from app.modules.farms.models import Farm
from app.modules.users.models import Role, User


def latest_audit(
    database_session: Session,
    *,
    action: AuditAction,
    module: str,
) -> AuditLog:
    item = database_session.scalar(
        select(AuditLog)
        .where(
            AuditLog.action == action.value,
            AuditLog.module == module,
        )
        .order_by(
            AuditLog.occurred_at.desc(),
            AuditLog.id.desc(),
        )
    )
    assert item is not None
    return item


def test_successful_login_is_audited(
    client: TestClient,
    database_session: Session,
    auth_context: dict[str, object],
) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": auth_context["login_identifier"],
            "password": auth_context["password"],
        },
        headers={
            "X-Request-ID": "login-audit-request",
        },
    )

    assert response.status_code == 200

    item = latest_audit(
        database_session,
        action=AuditAction.LOGIN,
        module="auth",
    )
    assert item.outcome == AuditOutcome.SUCCESS.value
    assert item.actor_user_id == auth_context["user"].id
    assert item.request_id == "login-audit-request"
    assert item.ip_address is not None


def test_failed_login_is_audited_without_password(
    client: TestClient,
    database_session: Session,
    auth_context: dict[str, object],
) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": auth_context["login_identifier"],
            "password": "IncorrectPassword123!",
        },
    )

    assert response.status_code == 401

    item = latest_audit(
        database_session,
        action=AuditAction.LOGIN_FAILED,
        module="auth",
    )
    assert item.outcome == AuditOutcome.FAILURE.value
    assert item.actor_user_id == auth_context["user"].id
    assert item.error_code == "invalid_credentials"

    serialized = str(
        {
            "before": item.before_values,
            "after": item.after_values,
            "metadata": item.metadata_json,
        }
    )
    assert "IncorrectPassword123!" not in serialized
    assert "password" not in (item.metadata_json or {})


def test_token_refresh_and_logout_are_audited(
    client: TestClient,
    database_session: Session,
    auth_context: dict[str, object],
) -> None:
    login = client.post(
        "/api/v1/auth/login",
        data={
            "username": auth_context["login_identifier"],
            "password": auth_context["password"],
        },
    )
    refresh_token = login.json()["refresh_token"]

    refreshed = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refreshed.status_code == 200

    refresh_audit = latest_audit(
        database_session,
        action=AuditAction.TOKEN_REFRESH,
        module="auth",
    )
    assert refresh_audit.outcome == (AuditOutcome.SUCCESS.value)

    new_refresh_token = refreshed.json()["refresh_token"]
    logout = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": new_refresh_token},
    )
    assert logout.status_code == 204

    logout_audit = latest_audit(
        database_session,
        action=AuditAction.LOGOUT,
        module="auth",
    )
    assert logout_audit.actor_user_id == (auth_context["user"].id)


def test_password_change_is_audited(
    authenticated_client: TestClient,
    database_session: Session,
    auth_context: dict[str, object],
) -> None:
    response = authenticated_client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": auth_context["password"],
            "new_password": ("AnotherSecurePassword456!"),
        },
    )
    assert response.status_code == 204

    item = latest_audit(
        database_session,
        action=AuditAction.PASSWORD_CHANGE,
        module="auth",
    )
    assert item.actor_user_id == auth_context["user"].id
    assert item.metadata_json == {"existing_sessions_revoked": True}


def test_user_creation_and_update_are_audited(
    authenticated_client: TestClient,
    database_session: Session,
    auth_context: dict[str, object],
) -> None:
    role = auth_context["role"]
    username = f"user-{uuid4().hex[:8]}"

    created = authenticated_client.post(
        "/api/v1/users",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "telephone": None,
            "password": "SecureCreatedPassword123!",
            "first_name": "Created",
            "last_name": "User",
            "must_change_password": True,
            "role_ids": [str(role.id)],
        },
    )
    assert created.status_code == 201
    user_id = created.json()["id"]

    created_audit = latest_audit(
        database_session,
        action=AuditAction.CREATE,
        module="users",
    )
    assert created_audit.resource_id == user_id
    assert created_audit.after_values["username"] == username
    assert "password_hash" not in (created_audit.after_values or {})

    updated = authenticated_client.patch(
        f"/api/v1/users/{user_id}",
        json={
            "first_name": "Updated",
            "telephone": "+256700123456",
        },
    )
    assert updated.status_code == 200

    updated_audit = latest_audit(
        database_session,
        action=AuditAction.UPDATE,
        module="users",
    )
    assert updated_audit.resource_id == user_id
    assert updated_audit.changes["first_name"] == {
        "before": "Created",
        "after": "Updated",
    }


def test_role_assignment_is_audited(
    authenticated_client: TestClient,
    database_session: Session,
    auth_context: dict[str, object],
) -> None:
    farm = auth_context["farm"]
    target = User(
        farm_id=farm.id,
        username=f"target-{uuid4().hex[:8]}",
        email=f"target-{uuid4().hex[:8]}@example.com",
        password_hash=hash_password("SecureTargetPassword123!"),
        first_name="Target",
        last_name="User",
        is_active=True,
        is_verified=True,
    )
    target.roles.append(auth_context["role"])

    extra_role = Role(
        farm_id=farm.id,
        name=f"Extra Role {uuid4().hex[:6]}",
        description="Role used for audit testing.",
        is_active=True,
    )

    database_session.add_all([target, extra_role])
    database_session.commit()

    response = authenticated_client.post(
        f"/api/v1/users/{target.id}/roles/{extra_role.id}"
    )
    assert response.status_code == 200

    item = latest_audit(
        database_session,
        action=AuditAction.ASSIGN,
        module="roles",
    )
    assert item.resource_id == str(target.id)
    assert item.metadata_json["role_id"] == str(extra_role.id)


def test_farm_and_settings_updates_are_audited(
    authenticated_client: TestClient,
    database_session: Session,
    auth_context: dict[str, object],
) -> None:
    farm: Farm = auth_context["farm"]

    updated = authenticated_client.patch(
        f"/api/v1/farms/{farm.id}",
        json={
            "name": "Audited Farm Name",
            "district": "Wakiso",
        },
    )
    assert updated.status_code == 200

    farm_audit = latest_audit(
        database_session,
        action=AuditAction.UPDATE,
        module="farms",
    )
    assert farm_audit.resource_type == "Farm"
    assert farm_audit.changes["name"] == {
        "before": "PoultryPulse Test Farm",
        "after": "Audited Farm Name",
    }

    settings = authenticated_client.patch(
        f"/api/v1/farms/{farm.id}/settings",
        json={
            "eggs_per_tray": 24,
            "low_production_threshold": 75,
        },
    )
    assert settings.status_code == 200

    settings_audit = latest_audit(
        database_session,
        action=AuditAction.UPDATE,
        module="farms",
    )
    assert settings_audit.resource_type == ("FarmSettings")
    assert settings_audit.changes["eggs_per_tray"] == {
        "before": 30,
        "after": 24,
    }
