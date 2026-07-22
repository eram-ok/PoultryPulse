from uuid import uuid4

from fastapi.testclient import TestClient


def build_farm_payload(
    farm_code: str | None = None,
) -> dict[str, object]:
    unique_code = farm_code or (
        f"PP-{uuid4().hex[:8].upper()}"
    )

    return {
        "farm_code": unique_code,
        "name": "PoultryPulse Demonstration Farm",
        "owner_name": "Demonstration Owner",
        "telephone": "+256700000000",
        "email": f"{uuid4().hex[:8]}@example.com",
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
    }


def test_tenant_cannot_create_another_farm(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.post(
        "/api/v1/farms",
        json=build_farm_payload(),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == (
        "platform_farm_registration_required"
    )


def test_get_own_farm(
    authenticated_client: TestClient,
    auth_context: dict[str, object],
) -> None:
    farm = auth_context["farm"]

    response = authenticated_client.get(
        f"/api/v1/farms/{farm.id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(farm.id)
    assert response.json()["lifecycle_status"] == "ACTIVE"


def test_update_own_farm(
    authenticated_client: TestClient,
    auth_context: dict[str, object],
) -> None:
    farm = auth_context["farm"]

    response = authenticated_client.patch(
        f"/api/v1/farms/{farm.id}",
        json={
            "name": "Updated Test Farm",
            "district": "Wakiso",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Test Farm"
    assert response.json()["district"] == "Wakiso"


def test_tenant_cannot_change_farm_lifecycle(
    authenticated_client: TestClient,
    auth_context: dict[str, object],
) -> None:
    farm = auth_context["farm"]

    response = authenticated_client.patch(
        f"/api/v1/farms/{farm.id}",
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 422


def test_update_farm_settings(
    authenticated_client: TestClient,
    auth_context: dict[str, object],
) -> None:
    farm = auth_context["farm"]

    response = authenticated_client.patch(
        f"/api/v1/farms/{farm.id}/settings",
        json={
            "eggs_per_tray": 24,
            "low_production_threshold": 75,
        },
    )

    assert response.status_code == 200
    assert response.json()["eggs_per_tray"] == 24


def test_list_farms_returns_current_farm(
    authenticated_client: TestClient,
    auth_context: dict[str, object],
) -> None:
    farm = auth_context["farm"]

    response = authenticated_client.get(
        "/api/v1/farms"
    )
    response_body = response.json()

    assert response.status_code == 200
    assert response_body["total"] == 1
    assert response_body["items"][0]["id"] == str(
        farm.id
    )


def test_other_farm_is_hidden(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get(
        f"/api/v1/farms/{uuid4()}"
    )

    assert response.status_code == 404
