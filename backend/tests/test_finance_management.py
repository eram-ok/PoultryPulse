from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.suppliers.constants import SupplierType
from app.modules.suppliers.models import Supplier
from app.modules.users.models import User


def get_test_user(db: Session) -> User:
    user = db.scalar(select(User).order_by(User.created_at.desc()))
    assert user is not None
    return user


def supplier(db: Session) -> Supplier:
    user = get_test_user(db)
    item = Supplier(
        farm_id=user.farm_id,
        supplier_code=f"SUP-{uuid4().hex[:8].upper()}",
        name="Stage 14 Supplier",
        supplier_type=SupplierType.GENERAL_SUPPLIER.value,
        telephone="+256700000010",
        is_active=True,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def category(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/finance/expense-categories",
        json={
            "category_code": f"CAT_{uuid4().hex[:8].upper()}",
            "name": "Stage 14 Cost",
            "kind": "OTHER",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_finance_requires_authentication(client: TestClient):
    assert client.get("/api/v1/finance/summary").status_code == 401


def test_expense_and_void(authenticated_client: TestClient):
    cat = category(authenticated_client)
    response = authenticated_client.post(
        "/api/v1/finance/expenses",
        json={
            "category_id": cat["id"],
            "description": "Electricity expense",
            "amount": "75000.00",
            "payment_method": "MOBILE_MONEY",
        },
    )
    assert response.status_code == 201
    expense = response.json()
    assert expense["status"] == "POSTED"
    ledger = authenticated_client.get("/api/v1/finance/cash-ledger").json()
    assert any(
        i["expense_id"] == expense["id"] and i["direction"] == "OUTFLOW"
        for i in ledger["items"]
    )
    voided = authenticated_client.post(
        f"/api/v1/finance/expenses/{expense['id']}/void",
        json={"reason": "Expense entered twice."},
    )
    assert voided.status_code == 200 and voided.json()["status"] == "VOIDED"


def test_supplier_bill_payment_reversal(
    authenticated_client: TestClient, database_session: Session
):
    sup = supplier(database_session)
    bill_response = authenticated_client.post(
        "/api/v1/finance/supplier-bills",
        json={
            "supplier_id": str(sup.id),
            "supplier_invoice_number": f"INV-{uuid4().hex[:8]}",
            "bill_date": date.today().isoformat(),
            "due_date": (date.today() + timedelta(days=14)).isoformat(),
            "description": "General farm supplies",
            "subtotal": "300000.00",
        },
    )
    assert bill_response.status_code == 201
    bill = bill_response.json()
    assert bill["status"] == "UNPAID"
    payment_response = authenticated_client.post(
        "/api/v1/finance/supplier-payments",
        json={
            "supplier_bill_id": bill["id"],
            "amount": "100000.00",
            "method": "BANK_TRANSFER",
        },
    )
    assert payment_response.status_code == 201
    payment = payment_response.json()
    updated = authenticated_client.get(
        f"/api/v1/finance/supplier-bills/{bill['id']}"
    ).json()
    assert (
        updated["status"] == "PARTIALLY_PAID" and updated["balance_due"] == "200000.00"
    )
    reversal = authenticated_client.post(
        f"/api/v1/finance/supplier-payments/{payment['id']}/reverse",
        json={"reason": "Wrong bank transaction."},
    )
    assert reversal.status_code == 200 and reversal.json()["status"] == "REVERSED"


def test_adjustment_reports_and_statement(
    authenticated_client: TestClient, database_session: Session
):
    sup = supplier(database_session)
    adjustment = authenticated_client.post(
        "/api/v1/finance/cash-ledger/adjustments",
        json={
            "direction": "INFLOW",
            "amount": "250000.00",
            "description": "Opening cash adjustment",
        },
    )
    assert adjustment.status_code == 201
    bill = authenticated_client.post(
        "/api/v1/finance/supplier-bills",
        json={
            "supplier_id": str(sup.id),
            "supplier_invoice_number": f"STAT-{uuid4().hex[:8]}",
            "description": "Statement test bill",
            "subtotal": "125000.00",
        },
    )
    assert bill.status_code == 201
    statement = authenticated_client.get(
        f"/api/v1/finance/suppliers/{sup.id}/statement"
    )
    assert (
        statement.status_code == 200 and statement.json()["total_billed"] == "125000.00"
    )
    cash = authenticated_client.get("/api/v1/finance/reports/cash-flow")
    assert cash.status_code == 200 and Decimal(cash.json()["total_inflows"]) >= Decimal(
        "250000.00"
    )
    profitability = authenticated_client.get("/api/v1/finance/reports/profitability")
    assert profitability.status_code == 200 and "gross_profit" in profitability.json()
    summary = authenticated_client.get("/api/v1/finance/summary")
    assert summary.status_code == 200 and "current_cash_balance" in summary.json()
