
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
)
from app.modules.platform.models import PlatformUser


PLATFORM_PASSWORD = "SecurePlatformPassword123!"


def create_platform_user(
    database_session: Session,
    *,
    is_active: bool = True,
    is_super_admin: bool = True,
) -> PlatformUser:
    unique_value = uuid4().hex[:10]
    user = PlatformUser(
        username=f"platform-{unique_value}",
        email=f"platform-{unique_value}@example.com",
        password_hash=hash_password(
            PLATFORM_PASSWORD
        ),
        first_name="Platform",
        last_name="Administrator",
        is_active=is_active,
        is_super_admin=is_super_admin,
        must_change_password=False,
    )
    database_session.add(user)
    database_session.commit()
    return user


def platform_login(
    client: TestClient,
    user: PlatformUser,
) -> dict[str, object]:
    response = client.post(
        "/api/v1/platform/auth/login",
        data={
            "username": user.username,
            "password": PLATFORM_PASSWORD,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_platform_login_returns_separate_token_pair(
    client: TestClient,
    database_session: Session,
) -> None:
    user = create_platform_user(database_session)

    response_body = platform_login(client, user)

    assert response_body["access_token"]
    assert response_body["refresh_token"]
    assert response_body["user"]["id"] == str(user.id)
    assert response_body["user"]["is_super_admin"] is True


def test_platform_refresh_rotates_token(
    client: TestClient,
    database_session: Session,
) -> None:
    user = create_platform_user(database_session)
    login_body = platform_login(client, user)
    old_refresh_token = login_body["refresh_token"]

    response = client.post(
        "/api/v1/platform/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert response.status_code == 200
    assert (
        response.json()["refresh_token"]
        != old_refresh_token
    )

    repeated = client.post(
        "/api/v1/platform/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert repeated.status_code == 401
    assert repeated.json()["error"]["code"] == (
        "platform_refresh_token_revoked"
    )


def test_farm_token_is_rejected_by_platform_api(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get(
        "/api/v1/platform/auth/me"
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == (
        "invalid_platform_principal"
    )


def test_platform_token_is_rejected_by_farm_api(
    client: TestClient,
    auth_context: dict[str, object],
    database_session: Session,
) -> None:
    user = create_platform_user(database_session)
    platform_token = create_access_token(
        str(user.id),
        additional_claims={
            "principal_type": "platform_user",
            "username": user.username,
            "is_super_admin": True,
        },
    )
    farm = auth_context["farm"]

    response = client.get(
        f"/api/v1/farms/{farm.id}",
        headers={
            "Authorization": (
                f"Bearer {platform_token}"
            )
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == (
        "invalid_farm_principal"
    )


def test_inactive_platform_user_cannot_login(
    client: TestClient,
    database_session: Session,
) -> None:
    user = create_platform_user(
        database_session,
        is_active=False,
    )

    response = client.post(
        "/api/v1/platform/auth/login",
        data={
            "username": user.username,
            "password": PLATFORM_PASSWORD,
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == (
        "inactive_platform_account"
    )
