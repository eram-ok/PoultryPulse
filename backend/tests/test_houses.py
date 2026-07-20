from uuid import uuid4

from fastapi.testclient import TestClient


def build_house_payload(
    house_code: str | None = None,
) -> dict[str, object]:
    """Build a valid poultry-house request."""

    unique_code = house_code or (f"HOUSE-{uuid4().hex[:8].upper()}")

    return {
        "house_code": unique_code,
        "name": "Main Layers House",
        "capacity": 1500,
        "location": "Northern section",
        "description": ("Main poultry house for laying birds."),
        "status": "ACTIVE",
    }


def create_test_house(
    authenticated_client: TestClient,
    house_code: str | None = None,
) -> dict[str, object]:
    response = authenticated_client.post(
        "/api/v1/houses",
        json=build_house_payload(house_code),
    )

    assert response.status_code == 201
    return response.json()


def test_house_creation_requires_authentication(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/houses",
        json=build_house_payload(),
    )

    assert response.status_code == 401


def test_create_poultry_house(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.post(
        "/api/v1/houses",
        json={
            "house_code": "layer house 1",
            "name": "Layer House One",
            "capacity": 1000,
            "location": "Eastern section",
            "status": "ACTIVE",
        },
    )

    response_body = response.json()

    assert response.status_code == 201
    assert response_body["house_code"] == "LAYER-HOUSE-1"
    assert response_body["capacity"] == 1000
    assert response_body["status"] == "ACTIVE"


def test_get_poultry_house(
    authenticated_client: TestClient,
) -> None:
    created_house = create_test_house(authenticated_client)

    response = authenticated_client.get(f"/api/v1/houses/{created_house['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created_house["id"]


def test_list_poultry_houses(
    authenticated_client: TestClient,
) -> None:
    created_house = create_test_house(authenticated_client)

    response = authenticated_client.get(
        "/api/v1/houses",
        params={
            "offset": 0,
            "limit": 20,
        },
    )

    response_body = response.json()

    returned_ids = {house["id"] for house in response_body["items"]}

    assert response.status_code == 200
    assert created_house["id"] in returned_ids
    assert response_body["total"] >= 1


def test_filter_houses_by_status(
    authenticated_client: TestClient,
) -> None:
    create_test_house(authenticated_client)

    response = authenticated_client.get(
        "/api/v1/houses",
        params={
            "status": "ACTIVE",
        },
    )

    assert response.status_code == 200

    for house in response.json()["items"]:
        assert house["status"] == "ACTIVE"


def test_search_poultry_houses(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.post(
        "/api/v1/houses",
        json={
            "house_code": (f"SEARCH-{uuid4().hex[:8].upper()}"),
            "name": "Special Brooding Building",
            "capacity": 800,
            "location": "Western section",
            "status": "ACTIVE",
        },
    )

    assert response.status_code == 201

    search_response = authenticated_client.get(
        "/api/v1/houses",
        params={
            "search": "Brooding",
        },
    )

    returned_names = {house["name"] for house in search_response.json()["items"]}

    assert search_response.status_code == 200
    assert "Special Brooding Building" in returned_names


def test_update_poultry_house(
    authenticated_client: TestClient,
) -> None:
    created_house = create_test_house(authenticated_client)

    response = authenticated_client.patch(
        f"/api/v1/houses/{created_house['id']}",
        json={
            "name": "Updated Layers House",
            "capacity": 2000,
            "status": "UNDER_MAINTENANCE",
        },
    )

    response_body = response.json()

    assert response.status_code == 200
    assert response_body["name"] == "Updated Layers House"
    assert response_body["capacity"] == 2000
    assert response_body["status"] == "UNDER_MAINTENANCE"


def test_duplicate_house_code_is_rejected(
    authenticated_client: TestClient,
) -> None:
    house_code = f"DUP-{uuid4().hex[:8].upper()}"

    first_response = authenticated_client.post(
        "/api/v1/houses",
        json=build_house_payload(house_code),
    )

    second_response = authenticated_client.post(
        "/api/v1/houses",
        json=build_house_payload(house_code),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["error"]["code"] == ("house_code_already_exists")


def test_invalid_capacity_is_rejected(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.post(
        "/api/v1/houses",
        json={
            "house_code": "INVALID-CAPACITY",
            "name": "Invalid House",
            "capacity": 0,
            "status": "ACTIVE",
        },
    )

    assert response.status_code == 422


def test_deactivate_and_activate_house(
    authenticated_client: TestClient,
) -> None:
    created_house = create_test_house(authenticated_client)

    deactivate_response = authenticated_client.post(
        (f"/api/v1/houses/{created_house['id']}/deactivate")
    )

    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["status"] == "INACTIVE"

    activate_response = authenticated_client.post(
        (f"/api/v1/houses/{created_house['id']}/activate")
    )

    assert activate_response.status_code == 200
    assert activate_response.json()["status"] == "ACTIVE"


def test_missing_house_returns_not_found(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get(f"/api/v1/houses/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == ("poultry_house_not_found")
