from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient


def create_house(
    client: TestClient,
    capacity: int = 1500,
) -> dict[str, object]:
    response = client.post(
        "/api/v1/houses",
        json={
            "house_code": (f"H-{uuid4().hex[:8].upper()}"),
            "name": "Test Layer House",
            "capacity": capacity,
            "location": "Test section",
            "status": "ACTIVE",
        },
    )

    assert response.status_code == 201
    return response.json()


def create_supplier(
    client: TestClient,
    supplier_type: str = "BIRD_SUPPLIER",
) -> dict[str, object]:
    response = client.post(
        "/api/v1/suppliers",
        json={
            "supplier_code": (f"S-{uuid4().hex[:8].upper()}"),
            "name": "Test Bird Supplier",
            "supplier_type": supplier_type,
            "telephone": "+256700000100",
        },
    )

    assert response.status_code == 201
    return response.json()


def build_flock_payload(
    house_id: str,
    supplier_id: str | None,
    *,
    initial_population: int = 1000,
    flock_code: str | None = None,
) -> dict[str, object]:
    return {
        "house_id": house_id,
        "supplier_id": supplier_id,
        "flock_code": (flock_code or f"F-{uuid4().hex[:8].upper()}"),
        "name": "Test Layers Flock",
        "breed": "Lohmann Brown",
        "arrival_date": date.today().isoformat(),
        "hatch_date": None,
        "age_at_arrival_days": 126,
        "initial_population": initial_population,
        "purchase_cost": 25000000,
        "production_stage": "POINT_OF_LAY",
        "notes": "Automated-test flock.",
    }


def create_flock(
    client: TestClient,
    *,
    capacity: int = 1500,
    initial_population: int = 1000,
) -> dict[str, object]:
    house = create_house(client, capacity)
    supplier = create_supplier(client)

    response = client.post(
        "/api/v1/flocks",
        json=build_flock_payload(
            house["id"],
            supplier["id"],
            initial_population=initial_population,
        ),
    )

    assert response.status_code == 201
    return response.json()


def test_create_supplier(
    authenticated_client: TestClient,
) -> None:
    supplier = create_supplier(authenticated_client)

    assert supplier["supplier_type"] == ("BIRD_SUPPLIER")
    assert supplier["is_active"] is True


def test_duplicate_supplier_code_is_rejected(
    authenticated_client: TestClient,
) -> None:
    supplier_code = f"DUP-{uuid4().hex[:8].upper()}"

    payload = {
        "supplier_code": supplier_code,
        "name": "Duplicate Supplier",
        "supplier_type": "BIRD_SUPPLIER",
    }

    first_response = authenticated_client.post(
        "/api/v1/suppliers",
        json=payload,
    )

    second_response = authenticated_client.post(
        "/api/v1/suppliers",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_create_flock_creates_initial_population(
    authenticated_client: TestClient,
) -> None:
    flock = create_flock(authenticated_client)

    assert flock["initial_population"] == 1000
    assert flock["current_population"] == 1000
    assert flock["status"] == "ACTIVE"

    population_response = authenticated_client.get(
        f"/api/v1/flocks/{flock['id']}/population"
    )

    assert population_response.status_code == 200
    assert population_response.json()["current_population"] == 1000


def test_initial_placement_transaction_exists(
    authenticated_client: TestClient,
) -> None:
    flock = create_flock(authenticated_client)

    response = authenticated_client.get(
        (f"/api/v1/flocks/{flock['id']}/population-transactions")
    )

    response_body = response.json()

    assert response.status_code == 200
    assert response_body["total"] == 1
    assert response_body["items"][0]["transaction_type"] == "INITIAL_PLACEMENT"
    assert response_body["items"][0]["signed_quantity"] == 1000


def test_house_capacity_is_enforced(
    authenticated_client: TestClient,
) -> None:
    house = create_house(
        authenticated_client,
        capacity=500,
    )

    supplier = create_supplier(authenticated_client)

    response = authenticated_client.post(
        "/api/v1/flocks",
        json=build_flock_payload(
            house["id"],
            supplier["id"],
            initial_population=600,
        ),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == ("house_capacity_exceeded")


def test_duplicate_flock_code_is_rejected(
    authenticated_client: TestClient,
) -> None:
    house = create_house(
        authenticated_client,
        capacity=2500,
    )

    supplier = create_supplier(authenticated_client)

    flock_code = f"DUP-F-{uuid4().hex[:8].upper()}"

    payload = build_flock_payload(
        house["id"],
        supplier["id"],
        initial_population=500,
        flock_code=flock_code,
    )

    first_response = authenticated_client.post(
        "/api/v1/flocks",
        json=payload,
    )

    second_response = authenticated_client.post(
        "/api/v1/flocks",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_invalid_supplier_type_is_rejected(
    authenticated_client: TestClient,
) -> None:
    house = create_house(authenticated_client)

    supplier = create_supplier(
        authenticated_client,
        supplier_type="FEED_SUPPLIER",
    )

    response = authenticated_client.post(
        "/api/v1/flocks",
        json=build_flock_payload(
            house["id"],
            supplier["id"],
        ),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == ("invalid_bird_supplier")


def test_population_reduction_updates_balance(
    authenticated_client: TestClient,
) -> None:
    flock = create_flock(authenticated_client)

    transaction_response = authenticated_client.post(
        (f"/api/v1/flocks/{flock['id']}/population-transactions"),
        json={
            "transaction_date": (date.today().isoformat()),
            "transaction_type": "TRANSFER_OUT",
            "quantity": 25,
            "description": ("Transferred to another unit."),
        },
    )

    assert transaction_response.status_code == 201
    assert transaction_response.json()["signed_quantity"] == -25

    population_response = authenticated_client.get(
        f"/api/v1/flocks/{flock['id']}/population"
    )

    assert population_response.json()["current_population"] == 975


def test_population_cannot_become_negative(
    authenticated_client: TestClient,
) -> None:
    flock = create_flock(
        authenticated_client,
        initial_population=100,
    )

    response = authenticated_client.post(
        (f"/api/v1/flocks/{flock['id']}/population-transactions"),
        json={
            "transaction_type": "ADJUSTMENT_OUT",
            "quantity": 101,
            "description": "Invalid reduction.",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == ("insufficient_flock_population")


def test_list_flocks(
    authenticated_client: TestClient,
) -> None:
    flock = create_flock(authenticated_client)

    response = authenticated_client.get(
        "/api/v1/flocks",
        params={
            "status": "ACTIVE",
            "search": "Layers",
        },
    )

    returned_ids = {item["id"] for item in response.json()["items"]}

    assert response.status_code == 200
    assert flock["id"] in returned_ids
