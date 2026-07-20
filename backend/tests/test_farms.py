from uuid import uuid4

from fastapi.testclient import TestClient


def build_farm_payload(
    farm_code: str | None = None,
) -> dict[str, object]:
    """Build a unique valid farm request for an API test."""

    unique_code = farm_code or f"PP-{uuid4().hex[:8].upper()}"

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


def create_test_farm(
    client: TestClient,
    farm_code: str | None = None,
) -> dict[str, object]:
    response = client.post(
        "/api/v1/farms",
        json=build_farm_payload(farm_code),
    )

    assert response.status_code == 201
    return response.json()


def test_create_farm_with_default_settings(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/farms",
        json=build_farm_payload(),
    )

    response_body = response.json()

    assert response.status_code == 201
    assert response_body["name"] == ("PoultryPulse Demonstration Farm")
    assert response_body["currency_code"] == "UGX"
    assert response_body["timezone"] == "Africa/Kampala"
    assert response_body["settings"]["eggs_per_tray"] == 30
    assert response_body["settings"]["allow_customer_credit"] is True


def test_get_farm_by_id(
    client: TestClient,
) -> None:
    created_farm = create_test_farm(client)
    farm_id = created_farm["id"]

    response = client.get(f"/api/v1/farms/{farm_id}")

    assert response.status_code == 200
    assert response.json()["id"] == farm_id


def test_update_farm(
    client: TestClient,
) -> None:
    created_farm = create_test_farm(client)
    farm_id = created_farm["id"]

    response = client.patch(
        f"/api/v1/farms/{farm_id}",
        json={
            "name": "Updated Poultry Farm",
            "district": "Wakiso",
        },
    )

    response_body = response.json()

    assert response.status_code == 200
    assert response_body["name"] == "Updated Poultry Farm"
    assert response_body["district"] == "Wakiso"


def test_update_farm_settings(
    client: TestClient,
) -> None:
    created_farm = create_test_farm(client)
    farm_id = created_farm["id"]

    response = client.patch(
        f"/api/v1/farms/{farm_id}/settings",
        json={
            "eggs_per_tray": 24,
            "low_production_threshold": 75,
            "maximum_discount_percentage": 10,
        },
    )

    response_body = response.json()

    assert response.status_code == 200
    assert response_body["eggs_per_tray"] == 24
    assert float(response_body["low_production_threshold"]) == 75
    assert float(response_body["maximum_discount_percentage"]) == 10


def test_duplicate_farm_code_is_rejected(
    client: TestClient,
) -> None:
    farm_code = f"DUP-{uuid4().hex[:8].upper()}"

    first_response = client.post(
        "/api/v1/farms",
        json=build_farm_payload(farm_code),
    )

    second_response = client.post(
        "/api/v1/farms",
        json=build_farm_payload(farm_code),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["error"]["code"] == ("farm_code_already_exists")


def test_list_farms_contains_created_farm(
    client: TestClient,
) -> None:
    created_farm = create_test_farm(client)

    response = client.get(
        "/api/v1/farms",
        params={
            "offset": 0,
            "limit": 100,
        },
    )

    response_body = response.json()
    returned_ids = {farm["id"] for farm in response_body["items"]}

    assert response.status_code == 200
    assert created_farm["id"] in returned_ids
    assert response_body["limit"] == 100


def test_missing_farm_returns_not_found(
    client: TestClient,
) -> None:
    missing_farm_id = uuid4()

    response = client.get(f"/api/v1/farms/{missing_farm_id}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "farm_not_found"
