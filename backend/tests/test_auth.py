from fastapi.testclient import TestClient


def test_login_returns_token_pair(
    client: TestClient,
    auth_context: dict[str, object],
) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": auth_context["login_identifier"],
            "password": auth_context["password"],
        },
    )

    response_body = response.json()

    assert response.status_code == 200
    assert response_body["token_type"] == "bearer"
    assert response_body["access_token"]
    assert response_body["refresh_token"]
    assert response_body["user"]["username"] == "testadmin"


def test_invalid_password_is_rejected(
    client: TestClient,
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
    assert response.json()["error"]["code"] == ("invalid_credentials")


def test_get_current_user(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["username"] == "testadmin"


def test_refresh_rotates_refresh_token(
    client: TestClient,
    auth_context: dict[str, object],
) -> None:
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": auth_context["login_identifier"],
            "password": auth_context["password"],
        },
    )

    old_refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert refresh_response.status_code == 200
    assert refresh_response.json()["refresh_token"] != old_refresh_token

    repeated_response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert repeated_response.status_code == 401
    assert repeated_response.json()["error"]["code"] == ("refresh_token_revoked")


def test_protected_route_requires_token(
    client: TestClient,
    auth_context: dict[str, object],
) -> None:
    farm = auth_context["farm"]

    response = client.get(f"/api/v1/farms/{farm.id}")

    assert response.status_code == 401


def test_authenticated_user_can_view_farm(
    authenticated_client: TestClient,
    auth_context: dict[str, object],
) -> None:
    farm = auth_context["farm"]

    response = authenticated_client.get(f"/api/v1/farms/{farm.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(farm.id)

def test_inactive_farm_cannot_log_in(
    client: TestClient,
    auth_context: dict[str, object],
    database_session,
) -> None:
    farm = auth_context["farm"]
    farm.is_active = False
    database_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": auth_context["login_identifier"],
            "password": auth_context["password"],
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "inactive_farm"


def test_inactive_farm_access_token_is_rejected(
    client: TestClient,
    auth_context: dict[str, object],
    database_session,
) -> None:
    farm = auth_context["farm"]
    farm.is_active = False
    database_session.commit()

    response = client.get(
        f"/api/v1/farms/{farm.id}",
        headers=auth_context["headers"],
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "inactive_farm"


def test_inactive_farm_refresh_is_rejected(
    client: TestClient,
    auth_context: dict[str, object],
    database_session,
) -> None:
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": auth_context["login_identifier"],
            "password": auth_context["password"],
        },
    )
    refresh_token = login_response.json()["refresh_token"]

    farm = auth_context["farm"]
    farm.is_active = False
    database_session.commit()

    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "inactive_farm"
