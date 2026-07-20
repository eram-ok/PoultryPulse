from datetime import date
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient


def create_feed_supplier(
    client: TestClient,
    supplier_type: str = "FEED_SUPPLIER",
) -> dict[str, object]:
    response = client.post(
        "/api/v1/suppliers",
        json={
            "supplier_code": (f"FEED-S-{uuid4().hex[:8].upper()}"),
            "name": "Feed Test Supplier",
            "supplier_type": supplier_type,
        },
    )

    assert response.status_code == 201
    return response.json()


def create_feed_item(
    client: TestClient,
    *,
    reorder_level_kg: str = "200.000",
) -> dict[str, object]:
    response = client.post(
        "/api/v1/feed/items",
        json={
            "feed_code": (f"FEED-I-{uuid4().hex[:8].upper()}"),
            "name": "Premium Layers Mash",
            "category": "LAYERS_MASH",
            "brand": "PoultryPlus",
            "manufacturer": "Test Feed Company",
            "reorder_level_kg": reorder_level_kg,
        },
    )

    assert response.status_code == 201
    return response.json()


def create_feed_purchase(
    client: TestClient,
    feed_item_id: str,
    *,
    quantity_kg: str = "1000.000",
) -> dict[str, object]:
    supplier = create_feed_supplier(client)

    response = client.post(
        "/api/v1/feed/purchases",
        json={
            "feed_item_id": feed_item_id,
            "supplier_id": supplier["id"],
            "purchase_date": date.today().isoformat(),
            "invoice_number": (f"INV-{uuid4().hex[:8].upper()}"),
            "quantity_kg": quantity_kg,
            "unit_cost": "2000.00",
            "notes": "Automated feed purchase.",
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
            "supplier_code": (f"BIRD-S-{uuid4().hex[:8].upper()}"),
            "name": "Bird Test Supplier",
            "supplier_type": "BIRD_SUPPLIER",
        },
    )

    assert response.status_code == 201
    return response.json()


def create_flock(
    client: TestClient,
) -> dict[str, object]:
    house_response = client.post(
        "/api/v1/houses",
        json={
            "house_code": (f"FEED-H-{uuid4().hex[:8].upper()}"),
            "name": "Feed Test House",
            "capacity": 1500,
            "status": "ACTIVE",
        },
    )

    assert house_response.status_code == 201

    supplier = create_bird_supplier(client)

    response = client.post(
        "/api/v1/flocks",
        json={
            "house_id": house_response.json()["id"],
            "supplier_id": supplier["id"],
            "flock_code": (f"FEED-F-{uuid4().hex[:8].upper()}"),
            "name": "Feed Test Layers",
            "breed": "Lohmann Brown",
            "arrival_date": date.today().isoformat(),
            "age_at_arrival_days": 126,
            "initial_population": 1000,
            "purchase_cost": 25000000,
            "production_stage": "LAYING",
        },
    )

    assert response.status_code == 201
    return response.json()


def get_feed_balance(
    client: TestClient,
    feed_item_id: str,
) -> dict[str, object]:
    response = client.get("/api/v1/feed/inventory/balances")

    assert response.status_code == 200

    for item in response.json()["balances"]:
        if item["feed_item_id"] == feed_item_id:
            return item

    raise AssertionError("Feed balance item was not returned.")


def test_feed_routes_require_authentication(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/feed/items")

    assert response.status_code == 401


def test_create_feed_item(
    authenticated_client: TestClient,
) -> None:
    item = create_feed_item(authenticated_client)

    assert item["category"] == "LAYERS_MASH"
    assert item["is_active"] is True
    assert Decimal(str(item["reorder_level_kg"])) == Decimal("200.000")


def test_duplicate_feed_code_is_rejected(
    authenticated_client: TestClient,
) -> None:
    feed_code = f"DUP-FEED-{uuid4().hex[:8].upper()}"

    payload = {
        "feed_code": feed_code,
        "name": "Duplicate Feed",
        "category": "LAYERS_MASH",
        "reorder_level_kg": "100.000",
    }

    first_response = authenticated_client.post(
        "/api/v1/feed/items",
        json=payload,
    )

    second_response = authenticated_client.post(
        "/api/v1/feed/items",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_purchase_increases_feed_stock(
    authenticated_client: TestClient,
) -> None:
    item = create_feed_item(authenticated_client)

    purchase = create_feed_purchase(
        authenticated_client,
        item["id"],
        quantity_kg="1000.000",
    )

    assert purchase["status"] == "RECEIVED"
    assert Decimal(str(purchase["total_cost"])) == Decimal("2000000.00")

    balance = get_feed_balance(
        authenticated_client,
        item["id"],
    )

    assert Decimal(str(balance["balance_kg"])) == Decimal("1000.000")


def test_invalid_feed_supplier_is_rejected(
    authenticated_client: TestClient,
) -> None:
    item = create_feed_item(authenticated_client)

    supplier = create_feed_supplier(
        authenticated_client,
        supplier_type="BIRD_SUPPLIER",
    )

    response = authenticated_client.post(
        "/api/v1/feed/purchases",
        json={
            "feed_item_id": item["id"],
            "supplier_id": supplier["id"],
            "purchase_date": date.today().isoformat(),
            "invoice_number": "INVALID-SUPPLIER",
            "quantity_kg": "100.000",
            "unit_cost": "2000.00",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == ("invalid_feed_supplier")


def test_feed_usage_reduces_stock(
    authenticated_client: TestClient,
) -> None:
    item = create_feed_item(authenticated_client)

    create_feed_purchase(
        authenticated_client,
        item["id"],
        quantity_kg="1000.000",
    )

    flock = create_flock(authenticated_client)

    usage_response = authenticated_client.post(
        "/api/v1/feed/usages",
        json={
            "flock_id": flock["id"],
            "feed_item_id": item["id"],
            "usage_date": date.today().isoformat(),
            "feeding_period": "MORNING",
            "quantity_kg": "55.000",
            "notes": "Morning feed allocation.",
        },
    )

    usage = usage_response.json()

    assert usage_response.status_code == 201
    assert usage["birds_present"] == 1000
    assert Decimal(str(usage["grams_per_bird"])) == Decimal("55.000")

    balance = get_feed_balance(
        authenticated_client,
        item["id"],
    )

    assert Decimal(str(balance["balance_kg"])) == Decimal("945.000")


def test_feed_usage_uses_current_population(
    authenticated_client: TestClient,
) -> None:
    item = create_feed_item(authenticated_client)

    create_feed_purchase(
        authenticated_client,
        item["id"],
        quantity_kg="500.000",
    )

    flock = create_flock(authenticated_client)

    population_response = authenticated_client.post(
        (f"/api/v1/flocks/{flock['id']}/population-transactions"),
        json={
            "transaction_date": date.today().isoformat(),
            "transaction_type": "TRANSFER_OUT",
            "quantity": 10,
            "description": "Ten birds transferred.",
        },
    )

    assert population_response.status_code == 201

    usage_response = authenticated_client.post(
        "/api/v1/feed/usages",
        json={
            "flock_id": flock["id"],
            "feed_item_id": item["id"],
            "feeding_period": "MORNING",
            "quantity_kg": "55.000",
        },
    )

    assert usage_response.status_code == 201
    assert usage_response.json()["birds_present"] == 990

    assert Decimal(str(usage_response.json()["grams_per_bird"])) == Decimal("55.556")


def test_negative_feed_stock_is_prevented(
    authenticated_client: TestClient,
) -> None:
    item = create_feed_item(authenticated_client)

    response = authenticated_client.post(
        "/api/v1/feed/inventory/wastage",
        json={
            "feed_item_id": item["id"],
            "quantity_kg": "10.000",
            "reference": "WASTE-001",
            "description": ("Testing insufficient feed stock."),
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == ("insufficient_feed_stock")


def test_wastage_reduces_feed_stock(
    authenticated_client: TestClient,
) -> None:
    item = create_feed_item(authenticated_client)

    create_feed_purchase(
        authenticated_client,
        item["id"],
        quantity_kg="100.000",
    )

    response = authenticated_client.post(
        "/api/v1/feed/inventory/wastage",
        json={
            "feed_item_id": item["id"],
            "quantity_kg": "2.500",
            "reference": "WASTE-002",
            "description": ("Feed damaged by water leakage."),
        },
    )

    assert response.status_code == 201
    assert Decimal(str(response.json()["signed_quantity_kg"])) == Decimal("-2.500")

    balance = get_feed_balance(
        authenticated_client,
        item["id"],
    )

    assert Decimal(str(balance["balance_kg"])) == Decimal("97.500")


def test_low_stock_alert(
    authenticated_client: TestClient,
) -> None:
    item = create_feed_item(
        authenticated_client,
        reorder_level_kg="200.000",
    )

    create_feed_purchase(
        authenticated_client,
        item["id"],
        quantity_kg="150.000",
    )

    balance = get_feed_balance(
        authenticated_client,
        item["id"],
    )

    assert balance["is_low_stock"] is True
    assert balance["is_out_of_stock"] is False


def test_manual_adjustment_can_be_reversed(
    authenticated_client: TestClient,
) -> None:
    item = create_feed_item(authenticated_client)

    adjustment_response = authenticated_client.post(
        "/api/v1/feed/inventory/adjustments",
        json={
            "feed_item_id": item["id"],
            "transaction_type": "ADJUSTMENT_IN",
            "quantity_kg": "75.000",
            "reference": "COUNT-001",
            "description": ("Opening feed inventory count."),
        },
    )

    assert adjustment_response.status_code == 201

    transaction_id = adjustment_response.json()["id"]

    reversal_response = authenticated_client.post(
        (f"/api/v1/feed/inventory/transactions/{transaction_id}/reverse"),
        json={"reason": ("The opening balance was entered twice.")},
    )

    assert reversal_response.status_code == 201
    assert reversal_response.json()["is_reversal"] is True

    assert Decimal(str(reversal_response.json()["signed_quantity_kg"])) == Decimal(
        "-75.000"
    )

    balance = get_feed_balance(
        authenticated_client,
        item["id"],
    )

    assert Decimal(str(balance["balance_kg"])) == Decimal("0.000")


def test_feed_transaction_cannot_be_reversed_twice(
    authenticated_client: TestClient,
) -> None:
    item = create_feed_item(authenticated_client)

    adjustment_response = authenticated_client.post(
        "/api/v1/feed/inventory/adjustments",
        json={
            "feed_item_id": item["id"],
            "transaction_type": "ADJUSTMENT_IN",
            "quantity_kg": "20.000",
            "description": "Temporary feed adjustment.",
        },
    )

    transaction_id = adjustment_response.json()["id"]

    payload = {"reason": "Incorrect feed inventory entry."}

    first_response = authenticated_client.post(
        (f"/api/v1/feed/inventory/transactions/{transaction_id}/reverse"),
        json=payload,
    )

    second_response = authenticated_client.post(
        (f"/api/v1/feed/inventory/transactions/{transaction_id}/reverse"),
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["error"]["code"] == (
        "feed_transaction_already_reversed"
    )


def test_purchase_transaction_is_source_controlled(
    authenticated_client: TestClient,
) -> None:
    item = create_feed_item(authenticated_client)

    purchase = create_feed_purchase(
        authenticated_client,
        item["id"],
        quantity_kg="100.000",
    )

    list_response = authenticated_client.get(
        "/api/v1/feed/inventory/transactions",
        params={
            "feed_item_id": item["id"],
            "transaction_type": "PURCHASE_IN",
        },
    )

    transaction = next(
        record
        for record in list_response.json()["items"]
        if record["source_id"] == purchase["id"]
    )

    reversal_response = authenticated_client.post(
        (f"/api/v1/feed/inventory/transactions/{transaction['id']}/reverse"),
        json={"reason": ("Attempting direct purchase reversal.")},
    )

    assert reversal_response.status_code == 422
    assert reversal_response.json()["error"]["code"] == (
        "feed_transaction_source_controlled"
    )


def test_purchase_can_be_voided(
    authenticated_client: TestClient,
) -> None:
    item = create_feed_item(authenticated_client)

    purchase = create_feed_purchase(
        authenticated_client,
        item["id"],
        quantity_kg="100.000",
    )

    response = authenticated_client.post(
        (f"/api/v1/feed/purchases/{purchase['id']}/void"),
        json={"reason": ("The supplier invoice was cancelled.")},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "VOIDED"

    balance = get_feed_balance(
        authenticated_client,
        item["id"],
    )

    assert Decimal(str(balance["balance_kg"])) == Decimal("0.000")
