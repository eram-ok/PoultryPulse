from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient


def create_house(
    client: TestClient,
) -> dict[str, object]:
    response = client.post(
        "/api/v1/houses",
        json={
            "house_code": (f"EGG-H-{uuid4().hex[:8].upper()}"),
            "name": "Egg Inventory Test House",
            "capacity": 1500,
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
            "supplier_code": (f"EGG-S-{uuid4().hex[:8].upper()}"),
            "name": "Egg Inventory Test Supplier",
            "supplier_type": "BIRD_SUPPLIER",
        },
    )

    assert response.status_code == 201
    return response.json()


def create_laying_flock(
    client: TestClient,
) -> dict[str, object]:
    house = create_house(client)
    supplier = create_supplier(client)

    response = client.post(
        "/api/v1/flocks",
        json={
            "house_id": house["id"],
            "supplier_id": supplier["id"],
            "flock_code": (f"EGG-F-{uuid4().hex[:8].upper()}"),
            "name": "Egg Inventory Layers",
            "breed": "Lohmann Brown",
            "arrival_date": date.today().isoformat(),
            "hatch_date": None,
            "age_at_arrival_days": 126,
            "initial_population": 1000,
            "purchase_cost": 25000000,
            "production_stage": "LAYING",
        },
    )

    assert response.status_code == 201
    return response.json()


def create_confirmed_production(
    client: TestClient,
) -> dict[str, object]:
    flock = create_laying_flock(client)

    create_response = client.post(
        "/api/v1/production-records",
        json={
            "flock_id": flock["id"],
            "production_date": date.today().isoformat(),
            "morning_eggs": 400,
            "afternoon_eggs": 350,
            "evening_eggs": 200,
            "large_eggs": 500,
            "medium_eggs": 300,
            "small_eggs": 100,
            "damaged_eggs": 30,
            "rejected_eggs": 20,
            "notes": "Egg inventory integration test.",
        },
    )

    assert create_response.status_code == 201

    production_id = create_response.json()["id"]

    submit_response = client.post(
        (f"/api/v1/production-records/{production_id}/submit")
    )

    assert submit_response.status_code == 200

    confirm_response = client.post(
        (f"/api/v1/production-records/{production_id}/confirm")
    )

    assert confirm_response.status_code == 200

    return confirm_response.json()


def get_grade_balance(
    client: TestClient,
    egg_grade: str,
) -> dict[str, object]:
    response = client.get("/api/v1/egg-inventory/balances")

    assert response.status_code == 200

    for balance in response.json()["balances"]:
        if balance["egg_grade"] == egg_grade:
            return balance

    raise AssertionError(f"Grade {egg_grade!r} was not returned.")


def test_inventory_requires_authentication(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/egg-inventory/balances")

    assert response.status_code == 401


def test_confirmation_posts_production_stock(
    authenticated_client: TestClient,
) -> None:
    create_confirmed_production(authenticated_client)

    large = get_grade_balance(
        authenticated_client,
        "LARGE",
    )

    medium = get_grade_balance(
        authenticated_client,
        "MEDIUM",
    )

    small = get_grade_balance(
        authenticated_client,
        "SMALL",
    )

    damaged = get_grade_balance(
        authenticated_client,
        "DAMAGED",
    )

    rejected = get_grade_balance(
        authenticated_client,
        "REJECTED",
    )

    assert large["balance_eggs"] == 500
    assert medium["balance_eggs"] == 300
    assert small["balance_eggs"] == 100
    assert damaged["balance_eggs"] == 30
    assert rejected["balance_eggs"] == 20


def test_tray_conversion(
    authenticated_client: TestClient,
) -> None:
    create_confirmed_production(authenticated_client)

    large = get_grade_balance(
        authenticated_client,
        "LARGE",
    )

    assert large["balance_eggs"] == 500
    assert large["trays"] == 16
    assert large["loose_eggs"] == 20
    assert large["eggs_per_tray"] == 30


def test_production_posting_is_grouped(
    authenticated_client: TestClient,
) -> None:
    production = create_confirmed_production(authenticated_client)

    response = authenticated_client.get(
        "/api/v1/egg-inventory/transactions",
        params={
            "source_type": "DAILY_EGG_PRODUCTION",
        },
    )

    matching = [
        transaction
        for transaction in response.json()["items"]
        if transaction["source_id"] == production["id"]
    ]

    group_ids = {transaction["transaction_group_id"] for transaction in matching}

    assert response.status_code == 200
    assert len(matching) == 5
    assert len(group_ids) == 1


def test_manual_adjustment_increases_stock(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.post(
        "/api/v1/egg-inventory/adjustments",
        json={
            "inventory_date": date.today().isoformat(),
            "egg_grade": "LARGE",
            "transaction_type": "ADJUSTMENT_IN",
            "quantity": 60,
            "reference": "COUNT-001",
            "description": ("Opening physical inventory count."),
        },
    )

    assert response.status_code == 201
    assert response.json()["signed_quantity"] == 60

    large = get_grade_balance(
        authenticated_client,
        "LARGE",
    )

    assert large["balance_eggs"] == 60
    assert large["trays"] == 2
    assert large["loose_eggs"] == 0


def test_issue_reduces_stock(
    authenticated_client: TestClient,
) -> None:
    create_confirmed_production(authenticated_client)

    response = authenticated_client.post(
        "/api/v1/egg-inventory/issues",
        json={
            "inventory_date": date.today().isoformat(),
            "egg_grade": "LARGE",
            "transaction_type": "INTERNAL_USE_OUT",
            "quantity": 20,
            "reference": "KITCHEN-001",
            "description": ("Eggs issued for farm kitchen use."),
        },
    )

    assert response.status_code == 201
    assert response.json()["signed_quantity"] == -20

    large = get_grade_balance(
        authenticated_client,
        "LARGE",
    )

    assert large["balance_eggs"] == 480


def test_negative_stock_is_prevented(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.post(
        "/api/v1/egg-inventory/issues",
        json={
            "inventory_date": date.today().isoformat(),
            "egg_grade": "MEDIUM",
            "transaction_type": "DONATION_OUT",
            "quantity": 100,
            "reference": "DONATION-001",
            "description": ("Donation exceeding available stock."),
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == ("insufficient_egg_stock")


def test_manual_adjustment_can_be_reversed(
    authenticated_client: TestClient,
) -> None:
    adjustment_response = authenticated_client.post(
        "/api/v1/egg-inventory/adjustments",
        json={
            "egg_grade": "SMALL",
            "transaction_type": "ADJUSTMENT_IN",
            "quantity": 90,
            "reference": "COUNT-002",
            "description": ("Physical stock count adjustment."),
        },
    )

    assert adjustment_response.status_code == 201

    transaction_id = adjustment_response.json()["id"]

    reversal_response = authenticated_client.post(
        (f"/api/v1/egg-inventory/transactions/{transaction_id}/reverse"),
        json={
            "inventory_date": date.today().isoformat(),
            "reason": ("The physical count was entered twice."),
        },
    )

    assert reversal_response.status_code == 201
    assert reversal_response.json()["transaction_type"] == "REVERSAL"
    assert reversal_response.json()["signed_quantity"] == -90

    small = get_grade_balance(
        authenticated_client,
        "SMALL",
    )

    assert small["balance_eggs"] == 0


def test_transaction_cannot_be_reversed_twice(
    authenticated_client: TestClient,
) -> None:
    adjustment_response = authenticated_client.post(
        "/api/v1/egg-inventory/adjustments",
        json={
            "egg_grade": "MEDIUM",
            "transaction_type": "ADJUSTMENT_IN",
            "quantity": 50,
            "description": ("Temporary stock adjustment."),
        },
    )

    transaction_id = adjustment_response.json()["id"]

    reversal_payload = {
        "inventory_date": date.today().isoformat(),
        "reason": "Incorrect adjustment entry.",
    }

    first_reversal = authenticated_client.post(
        (f"/api/v1/egg-inventory/transactions/{transaction_id}/reverse"),
        json=reversal_payload,
    )

    second_reversal = authenticated_client.post(
        (f"/api/v1/egg-inventory/transactions/{transaction_id}/reverse"),
        json=reversal_payload,
    )

    assert first_reversal.status_code == 201
    assert second_reversal.status_code == 409
    assert second_reversal.json()["error"]["code"] == (
        "egg_transaction_already_reversed"
    )


def test_production_transaction_is_source_controlled(
    authenticated_client: TestClient,
) -> None:
    create_confirmed_production(authenticated_client)

    list_response = authenticated_client.get(
        "/api/v1/egg-inventory/transactions",
        params={
            "transaction_type": "PRODUCTION_IN",
            "egg_grade": "LARGE",
        },
    )

    transaction_id = list_response.json()["items"][0]["id"]

    reversal_response = authenticated_client.post(
        (f"/api/v1/egg-inventory/transactions/{transaction_id}/reverse"),
        json={"reason": ("Attempting direct production reversal.")},
    )

    assert reversal_response.status_code == 422
    assert reversal_response.json()["error"]["code"] == (
        "egg_transaction_source_controlled"
    )
