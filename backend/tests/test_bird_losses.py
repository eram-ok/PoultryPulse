from datetime import date, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient


def create_house(
    client: TestClient,
    *,
    capacity: int = 1500,
) -> dict[str, object]:
    response = client.post(
        "/api/v1/houses",
        json={
            "house_code": (f"LOSS-H-{uuid4().hex[:8].upper()}"),
            "name": "Bird Loss Test House",
            "capacity": capacity,
            "status": "ACTIVE",
        },
    )

    assert response.status_code == 201
    return response.json()


def create_bird_supplier(
    client: TestClient,
) -> dict[str, object]:
    response = client.post(
        "/api/v1/suppliers",
        json={
            "supplier_code": (f"LOSS-S-{uuid4().hex[:8].upper()}"),
            "name": "Bird Loss Test Supplier",
            "supplier_type": "BIRD_SUPPLIER",
        },
    )

    assert response.status_code == 201
    return response.json()


def create_flock(
    client: TestClient,
    *,
    population: int = 1000,
    capacity: int = 1500,
) -> dict[str, object]:
    house = create_house(
        client,
        capacity=capacity,
    )

    supplier = create_bird_supplier(client)

    response = client.post(
        "/api/v1/flocks",
        json={
            "house_id": house["id"],
            "supplier_id": supplier["id"],
            "flock_code": (f"LOSS-F-{uuid4().hex[:8].upper()}"),
            "name": "Bird Loss Test Flock",
            "breed": "Lohmann Brown",
            "arrival_date": date.today().isoformat(),
            "age_at_arrival_days": 126,
            "initial_population": population,
            "purchase_cost": 25000000,
            "production_stage": "LAYING",
        },
    )

    assert response.status_code == 201
    return response.json()


def create_mortality(
    client: TestClient,
    flock_id: str,
    *,
    quantity: int = 5,
) -> dict[str, object]:
    response = client.post(
        "/api/v1/bird-losses",
        json={
            "flock_id": flock_id,
            "loss_date": date.today().isoformat(),
            "loss_type": "MORTALITY",
            "quantity": quantity,
            "reason_category": "DISEASE",
            "cause_details": ("Suspected respiratory infection."),
            "disposal_method": "BURIAL",
            "disposal_details": ("Buried in the designated disposal area."),
            "location": "Main layers house",
            "reference": "MORT-TEST-001",
            "notes": "Automated mortality test.",
        },
    )

    assert response.status_code == 201
    return response.json()


def test_bird_loss_requires_authentication(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/bird-losses")

    assert response.status_code == 401


def test_mortality_reduces_population(
    authenticated_client: TestClient,
) -> None:
    flock = create_flock(authenticated_client)

    record = create_mortality(
        authenticated_client,
        flock["id"],
        quantity=5,
    )

    assert record["population_before"] == 1000
    assert record["population_after"] == 995
    assert record["current_population"] == 995
    assert record["loss_type"] == "MORTALITY"
    assert record["status"] == "ACTIVE"

    population_response = authenticated_client.get(
        f"/api/v1/flocks/{flock['id']}/population"
    )

    assert population_response.status_code == 200
    assert population_response.json()["current_population"] == 995


def test_mortality_creates_population_transaction(
    authenticated_client: TestClient,
) -> None:
    flock = create_flock(authenticated_client)

    record = create_mortality(
        authenticated_client,
        flock["id"],
    )

    response = authenticated_client.get(
        (f"/api/v1/flocks/{flock['id']}/population-transactions")
    )

    matching = [
        item
        for item in response.json()["items"]
        if item["id"] == record["population_transaction_id"]
    ]

    assert response.status_code == 200
    assert len(matching) == 1
    assert matching[0]["transaction_type"] == "MORTALITY"
    assert matching[0]["signed_quantity"] == -5
    assert matching[0]["source_type"] == "BIRD_LOSS_RECORD"


def test_culling_reduces_population(
    authenticated_client: TestClient,
) -> None:
    flock = create_flock(authenticated_client)

    response = authenticated_client.post(
        "/api/v1/bird-losses",
        json={
            "flock_id": flock["id"],
            "loss_type": "CULLING",
            "quantity": 10,
            "reason_category": "LOW_PRODUCTION",
            "cause_details": ("Birds consistently below production target."),
            "disposal_method": "SOLD_FOR_SLAUGHTER",
            "reference": "CULL-TEST-001",
        },
    )

    assert response.status_code == 201
    assert response.json()["loss_type"] == "CULLING"
    assert response.json()["population_after"] == 990


def test_loss_cannot_exceed_current_population(
    authenticated_client: TestClient,
) -> None:
    flock = create_flock(
        authenticated_client,
        population=100,
    )

    response = authenticated_client.post(
        "/api/v1/bird-losses",
        json={
            "flock_id": flock["id"],
            "loss_type": "MORTALITY",
            "quantity": 101,
            "reason_category": "UNKNOWN",
            "disposal_method": "BURIAL",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] in {
        "bird_loss_exceeds_historical_population",
        "bird_loss_exceeds_current_population",
    }


def test_future_loss_date_is_rejected(
    authenticated_client: TestClient,
) -> None:
    flock = create_flock(authenticated_client)

    response = authenticated_client.post(
        "/api/v1/bird-losses",
        json={
            "flock_id": flock["id"],
            "loss_date": (date.today() + timedelta(days=1)).isoformat(),
            "loss_type": "MORTALITY",
            "quantity": 5,
            "reason_category": "DISEASE",
            "disposal_method": "BURIAL",
        },
    )

    assert response.status_code == 422


def test_mortality_reversal_restores_population(
    authenticated_client: TestClient,
) -> None:
    flock = create_flock(authenticated_client)

    record = create_mortality(
        authenticated_client,
        flock["id"],
        quantity=5,
    )

    response = authenticated_client.post(
        (f"/api/v1/bird-losses/{record['id']}/reverse"),
        json={
            "reversal_date": date.today().isoformat(),
            "reason": ("The mortality count was entered twice."),
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "REVERSED"
    assert response.json()["is_reversed"] is True
    assert response.json()["current_population"] == 1000
    assert response.json()["reversal_population_transaction_id"] is not None


def test_record_cannot_be_reversed_twice(
    authenticated_client: TestClient,
) -> None:
    flock = create_flock(authenticated_client)

    record = create_mortality(
        authenticated_client,
        flock["id"],
    )

    payload = {"reason": "Duplicate mortality entry."}

    first_response = authenticated_client.post(
        (f"/api/v1/bird-losses/{record['id']}/reverse"),
        json=payload,
    )

    second_response = authenticated_client.post(
        (f"/api/v1/bird-losses/{record['id']}/reverse"),
        json=payload,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert second_response.json()["error"]["code"] == (
        "bird_loss_record_already_reversed"
    )


def test_full_loss_marks_flock_depleted(
    authenticated_client: TestClient,
) -> None:
    flock = create_flock(
        authenticated_client,
        population=5,
    )

    record = create_mortality(
        authenticated_client,
        flock["id"],
        quantity=5,
    )

    assert record["current_population"] == 0

    flock_response = authenticated_client.get(f"/api/v1/flocks/{flock['id']}")

    assert flock_response.status_code == 200
    assert flock_response.json()["status"] == ("DEPLETED")


def test_reversal_reactivates_depleted_flock(
    authenticated_client: TestClient,
) -> None:
    flock = create_flock(
        authenticated_client,
        population=5,
    )

    record = create_mortality(
        authenticated_client,
        flock["id"],
        quantity=5,
    )

    reversal_response = authenticated_client.post(
        (f"/api/v1/bird-losses/{record['id']}/reverse"),
        json={
            "reason": ("The complete flock loss was entered against the wrong flock.")
        },
    )

    assert reversal_response.status_code == 200
    assert reversal_response.json()["current_population"] == 5

    flock_response = authenticated_client.get(f"/api/v1/flocks/{flock['id']}")

    assert flock_response.json()["status"] == "ACTIVE"


def test_list_bird_losses(
    authenticated_client: TestClient,
) -> None:
    flock = create_flock(authenticated_client)

    record = create_mortality(
        authenticated_client,
        flock["id"],
    )

    response = authenticated_client.get(
        "/api/v1/bird-losses",
        params={
            "flock_id": flock["id"],
            "loss_type": "MORTALITY",
            "status": "ACTIVE",
        },
    )

    returned_ids = {item["id"] for item in response.json()["items"]}

    assert response.status_code == 200
    assert record["id"] in returned_ids


def test_bird_loss_summary(
    authenticated_client: TestClient,
) -> None:
    flock = create_flock(authenticated_client)

    create_mortality(
        authenticated_client,
        flock["id"],
        quantity=5,
    )

    culling_response = authenticated_client.post(
        "/api/v1/bird-losses",
        json={
            "flock_id": flock["id"],
            "loss_type": "CULLING",
            "quantity": 10,
            "reason_category": "LOW_PRODUCTION",
            "disposal_method": "SOLD_FOR_SLAUGHTER",
        },
    )

    assert culling_response.status_code == 201

    response = authenticated_client.get(
        "/api/v1/bird-losses/summary",
        params={
            "date_from": date.today().isoformat(),
            "date_to": date.today().isoformat(),
            "flock_id": flock["id"],
        },
    )

    summary = response.json()

    assert response.status_code == 200
    assert summary["mortality_quantity"] == 5
    assert summary["culling_quantity"] == 10
    assert summary["total_loss_quantity"] == 15
    assert summary["active_record_count"] == 2
    assert summary["current_flock_population"] == 985


def test_daily_mortality_metrics_are_returned(
    authenticated_client: TestClient,
) -> None:
    flock = create_flock(
        authenticated_client,
        population=1000,
    )

    first = create_mortality(
        authenticated_client,
        flock["id"],
        quantity=5,
    )

    second = create_mortality(
        authenticated_client,
        flock["id"],
        quantity=5,
    )

    assert first["daily_mortality_quantity"] == 5
    assert second["daily_mortality_quantity"] == 10
    assert float(second["daily_mortality_percentage"]) > 0
