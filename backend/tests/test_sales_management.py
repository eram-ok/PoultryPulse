from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.eggs.constants import (
    EggInventoryTransactionType,
)
from app.modules.eggs.models import EggInventoryTransaction
from app.modules.users.models import User


def get_test_user(
    database_session: Session,
) -> User:
    user = database_session.scalar(select(User).order_by(User.created_at.desc()))
    assert user is not None
    return user


def seed_large_egg_inventory(
    database_session: Session,
    *,
    quantity: int,
) -> None:
    user = get_test_user(database_session)

    database_session.add(
        EggInventoryTransaction(
            farm_id=user.farm_id,
            transaction_group_id=uuid4(),
            inventory_date=date.today(),
            egg_grade="LARGE",
            transaction_type=(EggInventoryTransactionType.ADJUSTMENT_IN.value),
            quantity=quantity,
            signed_quantity=quantity,
            source_type="STAGE13_TEST",
            source_id=uuid4(),
            reference="STAGE13-STOCK",
            description="Stage 13 test inventory",
            created_by=user.id,
        )
    )
    database_session.commit()


def current_large_balance(
    database_session: Session,
) -> int:
    user = get_test_user(database_session)
    result = database_session.scalar(
        select(
            func.coalesce(
                func.sum(EggInventoryTransaction.signed_quantity),
                0,
            )
        ).where(
            EggInventoryTransaction.farm_id == user.farm_id,
            EggInventoryTransaction.egg_grade == "LARGE",
        )
    )
    return int(result or 0)


def create_customer(
    client: TestClient,
    *,
    credit_limit: str = "1000000.00",
) -> dict:
    response = client.post(
        "/api/v1/sales/customers",
        json={
            "customer_code": (f"CUS-{uuid4().hex[:8].upper()}"),
            "name": "Stage 13 Customer",
            "phone_number": "+256700000001",
            "credit_limit": credit_limit,
        },
    )
    assert response.status_code == 201
    return response.json()


def create_sale(
    client: TestClient,
    *,
    customer_id: str,
    trays: int = 2,
    price: str = "15000.00",
) -> dict:
    response = client.post(
        "/api/v1/sales/invoices",
        json={
            "customer_id": customer_id,
            "payment_terms": "CREDIT",
            "due_date": (date.today() + timedelta(days=14)).isoformat(),
            "items": [
                {
                    "egg_grade": "LARGE",
                    "unit": "TRAY",
                    "quantity": trays,
                    "unit_price": price,
                }
            ],
        },
    )
    assert response.status_code == 201
    return response.json()


def confirm_sale(
    client: TestClient,
    sale_id: str,
) -> dict:
    response = client.post(
        f"/api/v1/sales/invoices/{sale_id}/confirm",
        json={},
    )
    assert response.status_code == 200
    return response.json()


def test_sales_routes_require_authentication(
    client: TestClient,
) -> None:
    assert client.get("/api/v1/sales/customers").status_code == 401


def test_create_customer(
    authenticated_client: TestClient,
) -> None:
    customer = create_customer(authenticated_client)

    assert customer["status"] == "ACTIVE"
    assert customer["current_balance"] == "0.00"
    assert customer["available_credit"] == "1000000.00"


def test_confirm_sale_reduces_egg_inventory(
    authenticated_client: TestClient,
    database_session: Session,
) -> None:
    seed_large_egg_inventory(
        database_session,
        quantity=300,
    )
    before = current_large_balance(database_session)

    customer = create_customer(authenticated_client)
    draft = create_sale(
        authenticated_client,
        customer_id=customer["id"],
        trays=2,
    )
    confirmed = confirm_sale(
        authenticated_client,
        draft["id"],
    )

    database_session.expire_all()
    after = current_large_balance(database_session)

    assert confirmed["status"] == "CONFIRMED"
    assert confirmed["balance_due"] == "30000.00"
    assert after == before - 60


def test_insufficient_inventory_rejects_confirmation(
    authenticated_client: TestClient,
) -> None:
    customer = create_customer(authenticated_client)
    draft = create_sale(
        authenticated_client,
        customer_id=customer["id"],
        trays=100000,
    )

    response = authenticated_client.post(
        f"/api/v1/sales/invoices/{draft['id']}/confirm",
        json={},
    )
    assert response.status_code == 422


def test_payment_and_reversal(
    authenticated_client: TestClient,
    database_session: Session,
) -> None:
    seed_large_egg_inventory(
        database_session,
        quantity=300,
    )
    customer = create_customer(authenticated_client)
    sale = confirm_sale(
        authenticated_client,
        create_sale(
            authenticated_client,
            customer_id=customer["id"],
        )["id"],
    )

    payment_response = authenticated_client.post(
        "/api/v1/sales/payments",
        json={
            "sale_id": sale["id"],
            "amount": "10000.00",
            "method": "MOBILE_MONEY",
            "reference_number": "MOMO-001",
        },
    )
    assert payment_response.status_code == 201
    payment = payment_response.json()
    assert payment["status"] == "POSTED"

    sale_after_payment = authenticated_client.get(
        f"/api/v1/sales/invoices/{sale['id']}"
    ).json()
    assert sale_after_payment["balance_due"] == "20000.00"
    assert sale_after_payment["status"] == "PARTIALLY_PAID"

    reversal = authenticated_client.post(
        (f"/api/v1/sales/payments/{payment['id']}/reverse"),
        json={"reason": "Payment entered twice."},
    )
    assert reversal.status_code == 200
    assert reversal.json()["status"] == "REVERSED"

    sale_after_reversal = authenticated_client.get(
        f"/api/v1/sales/invoices/{sale['id']}"
    ).json()
    assert sale_after_reversal["balance_due"] == "30000.00"


def test_sale_return_and_reversal_restore_inventory(
    authenticated_client: TestClient,
    database_session: Session,
) -> None:
    seed_large_egg_inventory(
        database_session,
        quantity=300,
    )
    customer = create_customer(authenticated_client)
    sale = confirm_sale(
        authenticated_client,
        create_sale(
            authenticated_client,
            customer_id=customer["id"],
            trays=2,
        )["id"],
    )

    balance_after_sale = current_large_balance(database_session)
    item_id = sale["items"][0]["id"]

    return_response = authenticated_client.post(
        "/api/v1/sales/returns",
        json={
            "sale_id": sale["id"],
            "reason": "Customer returned one tray.",
            "items": [
                {
                    "sale_item_id": item_id,
                    "quantity": 1,
                }
            ],
        },
    )
    assert return_response.status_code == 201
    sale_return = return_response.json()

    database_session.expire_all()
    assert current_large_balance(database_session) == balance_after_sale + 30

    sale_after_return = authenticated_client.get(
        f"/api/v1/sales/invoices/{sale['id']}"
    ).json()
    assert sale_after_return["status"] == "PARTIALLY_RETURNED"
    assert sale_after_return["balance_due"] == "15000.00"

    reversal = authenticated_client.post(
        (f"/api/v1/sales/returns/{sale_return['id']}/reverse"),
        json={"reason": "Return entered incorrectly."},
    )
    assert reversal.status_code == 200
    assert reversal.json()["status"] == "REVERSED"

    database_session.expire_all()
    assert current_large_balance(database_session) == balance_after_sale


def test_customer_statement_and_summary(
    authenticated_client: TestClient,
    database_session: Session,
) -> None:
    seed_large_egg_inventory(
        database_session,
        quantity=100,
    )
    customer = create_customer(authenticated_client)
    sale = confirm_sale(
        authenticated_client,
        create_sale(
            authenticated_client,
            customer_id=customer["id"],
            trays=1,
        )["id"],
    )

    statement = authenticated_client.get(
        (f"/api/v1/sales/customers/{customer['id']}/statement")
    )
    assert statement.status_code == 200
    assert len(statement.json()["entries"]) == 1
    assert statement.json()["closing_balance"] == "15000.00"

    summary = authenticated_client.get("/api/v1/sales/summary")
    assert summary.status_code == 200
    assert "inventory_by_grade" in summary.json()
    assert Decimal(summary.json()["outstanding_receivables"]) >= Decimal(
        sale["balance_due"]
    )
