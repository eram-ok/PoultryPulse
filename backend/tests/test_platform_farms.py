import json
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.security import (
    create_access_token,
    hash_password,
)
from app.modules.platform.models import (
    PlatformAuditLog,
    PlatformUser,
)
from app.modules.users.models import Role, User


PLATFORM_PASSWORD = "SecurePlatformPassword123!"


def create_platform_headers(
    database_session: Session,
    *,
    is_super_admin: bool = True,
) -> dict[str, str]:
    unique_value = uuid4().hex[:10]
    user = PlatformUser(
        username=f"lifecycle-{unique_value}",
        email=f"lifecycle-{unique_value}@example.com",
        password_hash=hash_password(
            PLATFORM_PASSWORD
        ),
        first_name="Platform",
        last_name="Lifecycle",
        is_active=True,
        is_super_admin=is_super_admin,
        must_change_password=False,
    )
    database_session.add(user)
    database_session.commit()

    token = create_access_token(
        str(user.id),
        additional_claims={
            "principal_type": "platform_user",
            "username": user.username,
            "is_super_admin": user.is_super_admin,
        },
    )
    return {
        "Authorization": f"Bearer {token}",
    }


def build_onboarding_payload(
    *,
    farm_code: str | None = None,
) -> dict[str, object]:
    unique_value = uuid4().hex[:10]
    return {
        "farm_code": (
            farm_code
            or f"LIFE-{unique_value.upper()}"
        ),
        "name": "Lifecycle Demonstration Farm",
        "owner_name": "Lifecycle Owner",
        "telephone": "+256700123456",
        "email": f"farm-{unique_value}@example.com",
        "district": "Mukono",
        "address": "Mukono, Uganda",
        "timezone": "Africa/Kampala",
        "currency_code": "UGX",
        "settings": {
            "eggs_per_tray": 30,
            "low_production_threshold": 70,
            "mortality_alert_threshold": 1,
            "vaccination_reminder_days": 3,
            "session_timeout_minutes": 60,
            "allow_negative_stock": False,
            "allow_customer_credit": True,
            "maximum_discount_percentage": 5,
        },
        "first_administrator": {
            "username": f"admin-{unique_value}",
            "email": f"admin-{unique_value}@example.com",
            "telephone": "+256701123456",
            "first_name": "First",
            "last_name": "Administrator",
        },
    }


def test_platform_super_admin_can_list_farms(
    client: TestClient,
    auth_context: dict[str, object],
    database_session: Session,
) -> None:
    farm = auth_context["farm"]
    headers = create_platform_headers(
        database_session
    )

    response = client.get(
        "/api/v1/platform/farms",
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert any(
        item["id"] == str(farm.id)
        for item in body["items"]
    )
    assert body["recent_login_window_days"] == 30


def test_farm_token_cannot_list_platform_farms(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get(
        "/api/v1/platform/farms"
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == (
        "invalid_platform_principal"
    )


def test_non_super_admin_cannot_manage_farms(
    client: TestClient,
    database_session: Session,
) -> None:
    headers = create_platform_headers(
        database_session,
        is_super_admin=False,
    )

    response = client.get(
        "/api/v1/platform/farms",
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == (
        "platform_super_admin_required"
    )


def test_platform_onboarding_is_atomic_and_returns_invitation_once(
    client: TestClient,
    auth_context: dict[str, object],
    database_session: Session,
) -> None:
    _ = auth_context
    headers = create_platform_headers(
        database_session
    )
    payload = build_onboarding_payload()

    response = client.post(
        "/api/v1/platform/farms",
        headers=headers,
        json=payload,
    )

    assert response.status_code == 201
    assert response.headers["cache-control"] == (
        "no-store, max-age=0"
    )
    body = response.json()
    setup_url = body["setup_url"]
    farm_id = body["farm"]["id"]
    farm_uuid = UUID(farm_id)

    assert setup_url
    assert "temporary_password" not in body
    assert body["farm"]["lifecycle_status"] == "ACTIVE"
    assert body["administrator"]["is_active"] is False
    assert body["administrator"]["is_verified"] is False
    assert body["administrator"][
        "must_change_password"
    ] is True
    assert body["invitation"]["status"] == "PENDING"
    assert body["setup_url_returned_once"] is True

    roles = list(
        database_session.scalars(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.farm_id == farm_uuid)
        ).all()
    )
    assert {
        role.name
        for role in roles
    } == {
        "Administrator",
        "Owner",
        "Manager",
        "Attendant",
        "Sales Officer",
    }

    administrator_role = next(
        role
        for role in roles
        if role.name == "Administrator"
    )
    assert "farms.create" not in {
        permission.code
        for permission in administrator_role.permissions
    }

    administrator = database_session.scalar(
        select(User).where(
            User.farm_id == farm_uuid,
            User.username
            == payload["first_administrator"][
                "username"
            ],
        )
    )
    assert administrator is not None
    assert administrator.is_active is False
    assert administrator.is_verified is False

    detail_response = client.get(
        f"/api/v1/platform/farms/{farm_id}",
        headers=headers,
    )
    assert detail_response.status_code == 200
    assert "setup_url" not in detail_response.json()
    assert "temporary_password" not in (
        detail_response.json()
    )

    audit = database_session.scalar(
        select(PlatformAuditLog).where(
            PlatformAuditLog.action
            == "FARM_CREATE",
            PlatformAuditLog.target_farm_id
            == farm_uuid,
        )
    )
    assert audit is not None
    assert setup_url not in json.dumps(
        audit.metadata_json
    )


def test_duplicate_farm_code_is_rejected(
    client: TestClient,
    auth_context: dict[str, object],
    database_session: Session,
) -> None:
    _ = auth_context
    headers = create_platform_headers(
        database_session
    )
    farm_code = f"DUP-{uuid4().hex[:8].upper()}"
    first = build_onboarding_payload(
        farm_code=farm_code
    )
    second = build_onboarding_payload(
        farm_code=farm_code
    )

    first_response = client.post(
        "/api/v1/platform/farms",
        headers=headers,
        json=first,
    )
    second_response = client.post(
        "/api/v1/platform/farms",
        headers=headers,
        json=second,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_suspension_revokes_sessions_and_blocks_access(
    client: TestClient,
    auth_context: dict[str, object],
    database_session: Session,
) -> None:
    farm = auth_context["farm"]
    platform_headers = create_platform_headers(
        database_session
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": auth_context[
                "login_identifier"
            ],
            "password": auth_context["password"],
        },
    )
    assert login_response.status_code == 200
    farm_access_token = login_response.json()[
        "access_token"
    ]
    farm_refresh_token = login_response.json()[
        "refresh_token"
    ]

    response = client.post(
        f"/api/v1/platform/farms/{farm.id}/suspend",
        headers=platform_headers,
        json={
            "reason": (
                "Subscription payment requires review."
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["lifecycle_status"] == (
        "SUSPENDED"
    )
    assert response.json()["is_active"] is False

    access_response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": (
                f"Bearer {farm_access_token}"
            )
        },
    )
    assert access_response.status_code == 401
    assert access_response.json()["error"]["code"] == (
        "inactive_farm"
    )

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": farm_refresh_token,
        },
    )
    assert refresh_response.status_code == 401
    assert refresh_response.json()["error"]["code"] == (
        "refresh_token_revoked"
    )

    audit_count = database_session.scalar(
        select(func.count(PlatformAuditLog.id)).where(
            PlatformAuditLog.action
            == "FARM_SUSPEND",
            PlatformAuditLog.target_farm_id
            == farm.id,
        )
    )
    assert audit_count == 1


def test_reactivation_preserves_farm_and_restores_login(
    client: TestClient,
    auth_context: dict[str, object],
    database_session: Session,
) -> None:
    farm = auth_context["farm"]
    headers = create_platform_headers(
        database_session
    )

    suspended = client.post(
        f"/api/v1/platform/farms/{farm.id}/suspend",
        headers=headers,
        json={
            "reason": "Temporary compliance review."
        },
    )
    assert suspended.status_code == 200

    activated = client.post(
        f"/api/v1/platform/farms/{farm.id}/activate",
        headers=headers,
        json={
            "reason": "Compliance review completed."
        },
    )
    assert activated.status_code == 200
    assert activated.json()["lifecycle_status"] == (
        "ACTIVE"
    )
    assert activated.json()["is_active"] is True

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": auth_context[
                "login_identifier"
            ],
            "password": auth_context["password"],
        },
    )
    assert login_response.status_code == 200


def test_deactivation_requires_a_meaningful_reason(
    client: TestClient,
    auth_context: dict[str, object],
    database_session: Session,
) -> None:
    farm = auth_context["farm"]
    headers = create_platform_headers(
        database_session
    )

    missing = client.post(
        f"/api/v1/platform/farms/{farm.id}/deactivate",
        headers=headers,
        json={},
    )
    too_short = client.post(
        f"/api/v1/platform/farms/{farm.id}/deactivate",
        headers=headers,
        json={"reason": "no"},
    )

    assert missing.status_code == 422
    assert too_short.status_code == 422

    valid = client.post(
        f"/api/v1/platform/farms/{farm.id}/deactivate",
        headers=headers,
        json={
            "reason": (
                "Customer requested permanent account closure."
            )
        },
    )
    assert valid.status_code == 200
    assert valid.json()["lifecycle_status"] == (
        "DEACTIVATED"
    )
    assert valid.json()["deactivated_at"] is not None


def test_platform_list_supports_search_and_status_filter(
    client: TestClient,
    auth_context: dict[str, object],
    database_session: Session,
) -> None:
    farm = auth_context["farm"]
    headers = create_platform_headers(
        database_session
    )
    suspended = client.post(
        f"/api/v1/platform/farms/{farm.id}/suspend",
        headers=headers,
        json={"reason": "Testing status filtering."},
    )
    assert suspended.status_code == 200

    response = client.get(
        "/api/v1/platform/farms",
        headers=headers,
        params={
            "search": farm.farm_code,
            "status": "SUSPENDED",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == str(farm.id)


def test_platform_can_update_farm_profile(
    client: TestClient,
    auth_context: dict[str, object],
    database_session: Session,
) -> None:
    farm = auth_context["farm"]
    headers = create_platform_headers(
        database_session
    )

    response = client.patch(
        f"/api/v1/platform/farms/{farm.id}",
        headers=headers,
        json={
            "name": "Platform Updated Farm",
            "district": "Wakiso",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == (
        "Platform Updated Farm"
    )
    assert response.json()["district"] == "Wakiso"
