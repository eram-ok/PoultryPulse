from datetime import date, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient


def create_house(
    client: TestClient,
    capacity: int = 1500,
) -> dict[str, object]:
    response = client.post(
        "/api/v1/houses",
        json={
            "house_code": (f"PROD-H-{uuid4().hex[:8].upper()}"),
            "name": "Production Test House",
            "capacity": capacity,
            "location": "Production test section",
            "status": "ACTIVE",
        },
    )

    assert response.status_code == 201
    return response.json()


def create_supplier(
    client: TestClient,
) -> dict[str, object]:
    response = client.post(
        "/api/v1/suppliers",
        json={
            "supplier_code": (f"PROD-S-{uuid4().hex[:8].upper()}"),
            "name": "Production Test Supplier",
            "supplier_type": "BIRD_SUPPLIER",
        },
    )

    assert response.status_code == 201
    return response.json()


def create_laying_flock(
    client: TestClient,
    *,
    population: int = 1000,
) -> dict[str, object]:
    house = create_house(
        client,
        capacity=population + 500,
    )

    supplier = create_supplier(client)

    response = client.post(
        "/api/v1/flocks",
        json={
            "house_id": house["id"],
            "supplier_id": supplier["id"],
            "flock_code": (f"PROD-F-{uuid4().hex[:8].upper()}"),
            "name": "Production Test Layers",
            "breed": "Lohmann Brown",
            "arrival_date": date.today().isoformat(),
            "hatch_date": None,
            "age_at_arrival_days": 126,
            "initial_population": population,
            "purchase_cost": 25000000,
            "production_stage": "LAYING",
            "notes": "Flock used for production tests.",
        },
    )

    assert response.status_code == 201
    return response.json()


def build_production_payload(
    flock_id: str,
) -> dict[str, object]:
    return {
        "flock_id": flock_id,
        "production_date": date.today().isoformat(),
        "morning_eggs": 400,
        "afternoon_eggs": 350,
        "evening_eggs": 200,
        "large_eggs": 500,
        "medium_eggs": 300,
        "small_eggs": 100,
        "damaged_eggs": 30,
        "rejected_eggs": 20,
        "notes": "Daily automated-test production.",
    }


def create_production_record(
    client: TestClient,
) -> dict[str, object]:
    flock = create_laying_flock(client)

    response = client.post(
        "/api/v1/production-records",
        json=build_production_payload(flock["id"]),
    )

    assert response.status_code == 201
    return response.json()


def test_production_requires_authentication(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/production-records")

    assert response.status_code == 401


def test_create_daily_production(
    authenticated_client: TestClient,
) -> None:
    production = create_production_record(authenticated_client)

    assert production["birds_present"] == 1000
    assert production["total_collected"] == 950
    assert production["total_graded"] == 950
    assert production["saleable_eggs"] == 900
    assert production["ungraded_eggs"] == 0
    assert float(production["laying_percentage"]) == 95.0
    assert production["status"] == "DRAFT"


def test_duplicate_flock_date_is_rejected(
    authenticated_client: TestClient,
) -> None:
    flock = create_laying_flock(authenticated_client)

    payload = build_production_payload(flock["id"])

    first_response = authenticated_client.post(
        "/api/v1/production-records",
        json=payload,
    )

    second_response = authenticated_client.post(
        "/api/v1/production-records",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["error"]["code"] == (
        "production_record_already_exists"
    )


def test_incomplete_grading_blocks_submission(
    authenticated_client: TestClient,
) -> None:
    flock = create_laying_flock(authenticated_client)

    payload = build_production_payload(flock["id"])

    payload["rejected_eggs"] = 0

    create_response = authenticated_client.post(
        "/api/v1/production-records",
        json=payload,
    )

    assert create_response.status_code == 201
    assert create_response.json()["ungraded_eggs"] == 20

    production_id = create_response.json()["id"]

    submit_response = authenticated_client.post(
        (f"/api/v1/production-records/{production_id}/submit")
    )

    assert submit_response.status_code == 422
    assert submit_response.json()["error"]["code"] == ("production_grading_incomplete")


def test_update_and_submit_record(
    authenticated_client: TestClient,
) -> None:
    flock = create_laying_flock(authenticated_client)

    payload = build_production_payload(flock["id"])

    payload["rejected_eggs"] = 0

    create_response = authenticated_client.post(
        "/api/v1/production-records",
        json=payload,
    )

    production_id = create_response.json()["id"]

    update_response = authenticated_client.patch(
        (f"/api/v1/production-records/{production_id}"),
        json={
            "rejected_eggs": 20,
            "notes": "Grading completed.",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["ungraded_eggs"] == 0
    assert update_response.json()["revision_number"] == 2

    submit_response = authenticated_client.post(
        (f"/api/v1/production-records/{production_id}/submit")
    )

    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == ("SUBMITTED")
    assert submit_response.json()["submitted_at"]


def test_confirm_submitted_record(
    authenticated_client: TestClient,
) -> None:
    production = create_production_record(authenticated_client)

    production_id = production["id"]

    authenticated_client.post((f"/api/v1/production-records/{production_id}/submit"))

    confirm_response = authenticated_client.post(
        (f"/api/v1/production-records/{production_id}/confirm")
    )

    assert confirm_response.status_code == 200
    assert confirm_response.json()["status"] == ("CONFIRMED")
    assert confirm_response.json()["confirmed_at"]


def test_confirmed_record_is_locked(
    authenticated_client: TestClient,
) -> None:
    production = create_production_record(authenticated_client)

    production_id = production["id"]

    authenticated_client.post((f"/api/v1/production-records/{production_id}/submit"))

    authenticated_client.post((f"/api/v1/production-records/{production_id}/confirm"))

    update_response = authenticated_client.patch(
        (f"/api/v1/production-records/{production_id}"),
        json={
            "morning_eggs": 401,
        },
    )

    assert update_response.status_code == 422
    assert update_response.json()["error"]["code"] == ("production_record_locked")


def test_rejected_record_returns_to_draft_after_edit(
    authenticated_client: TestClient,
) -> None:
    production = create_production_record(authenticated_client)

    production_id = production["id"]

    authenticated_client.post((f"/api/v1/production-records/{production_id}/submit"))

    reject_response = authenticated_client.post(
        (f"/api/v1/production-records/{production_id}/reject"),
        json={"reason": ("The damaged egg count must be checked.")},
    )

    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == ("REJECTED")
    assert reject_response.json()["rejection_reason"]

    update_response = authenticated_client.patch(
        (f"/api/v1/production-records/{production_id}"),
        json={
            "notes": "Damaged eggs were recounted.",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "DRAFT"
    assert update_response.json()["rejection_reason"] is None


def test_population_snapshot_uses_ledger(
    authenticated_client: TestClient,
) -> None:
    flock = create_laying_flock(
        authenticated_client,
        population=1000,
    )

    transaction_response = authenticated_client.post(
        (f"/api/v1/flocks/{flock['id']}/population-transactions"),
        json={
            "transaction_date": date.today().isoformat(),
            "transaction_type": "TRANSFER_OUT",
            "quantity": 10,
            "description": "Birds moved before collection.",
        },
    )

    assert transaction_response.status_code == 201

    payload = build_production_payload(flock["id"])

    create_response = authenticated_client.post(
        "/api/v1/production-records",
        json=payload,
    )

    assert create_response.status_code == 201
    assert create_response.json()["birds_present"] == 990


def test_future_production_date_is_rejected(
    authenticated_client: TestClient,
) -> None:
    flock = create_laying_flock(authenticated_client)

    payload = build_production_payload(flock["id"])

    payload["production_date"] = (date.today() + timedelta(days=1)).isoformat()

    response = authenticated_client.post(
        "/api/v1/production-records",
        json=payload,
    )

    assert response.status_code == 422


def test_confirmed_production_summary(
    authenticated_client: TestClient,
) -> None:
    production = create_production_record(authenticated_client)

    production_id = production["id"]

    authenticated_client.post((f"/api/v1/production-records/{production_id}/submit"))

    authenticated_client.post((f"/api/v1/production-records/{production_id}/confirm"))

    summary_response = authenticated_client.get(
        "/api/v1/production-records/summary",
        params={
            "date_from": date.today().isoformat(),
            "date_to": date.today().isoformat(),
            "status": "CONFIRMED",
        },
    )

    summary = summary_response.json()

    assert summary_response.status_code == 200
    assert summary["record_count"] >= 1
    assert summary["total_collected"] >= 950
    assert summary["saleable_eggs"] >= 900
    assert float(summary["weighted_laying_percentage"]) > 0
