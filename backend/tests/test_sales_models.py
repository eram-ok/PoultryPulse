from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.sales.constants import (
    CustomerStatus,
    PaymentStatus,
    SalePaymentTerms,
    SaleReturnStatus,
    SaleStatus,
)
from app.modules.sales.models import (
    Customer,
    Sale,
    SaleItem,
    SalePayment,
    SaleReturn,
    calculate_line_total,
    normalize_money,
)


def test_normalize_money_rounds_to_two_places() -> None:
    assert normalize_money("1250.555") == Decimal("1250.56")


def test_calculate_line_total() -> None:
    assert calculate_line_total(
        4,
        Decimal("12500.00"),
    ) == Decimal("50000.00")


def test_line_total_rejects_zero_quantity() -> None:
    with pytest.raises(ValueError):
        calculate_line_total(
            0,
            Decimal("1000.00"),
        )


def test_line_total_rejects_negative_price() -> None:
    with pytest.raises(ValueError):
        calculate_line_total(
            2,
            Decimal("-1.00"),
        )


def test_customer_available_credit() -> None:
    customer = Customer(
        farm_id=uuid4(),
        customer_code="CUS-001",
        name="Test Customer",
        credit_limit=Decimal("500000.00"),
        opening_balance=Decimal("0.00"),
        current_balance=Decimal("125000.00"),
        status=CustomerStatus.ACTIVE.value,
    )

    assert customer.is_active is True
    assert customer.available_credit == Decimal("375000.00")


def test_customer_credit_never_goes_negative() -> None:
    customer = Customer(
        farm_id=uuid4(),
        customer_code="CUS-002",
        name="Over Limit Customer",
        credit_limit=Decimal("100000.00"),
        opening_balance=Decimal("0.00"),
        current_balance=Decimal("150000.00"),
        status=CustomerStatus.ACTIVE.value,
    )

    assert customer.available_credit == Decimal("0.00")


def test_sale_properties() -> None:
    sale = Sale(
        farm_id=uuid4(),
        invoice_number="INV-001",
        sale_date=date.today(),
        payment_terms=SalePaymentTerms.CREDIT.value,
        status=SaleStatus.PARTIALLY_PAID.value,
        subtotal=Decimal("300000.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("300000.00"),
        amount_paid=Decimal("100000.00"),
        balance_due=Decimal("200000.00"),
        created_by=uuid4(),
    )

    assert sale.is_credit_sale is True
    assert sale.is_confirmed is True
    assert sale.is_paid is False
    assert sale.is_cancelled is False


def test_paid_sale_property() -> None:
    sale = Sale(
        farm_id=uuid4(),
        invoice_number="INV-002",
        sale_date=date.today(),
        payment_terms=SalePaymentTerms.CASH.value,
        status=SaleStatus.PAID.value,
        subtotal=Decimal("60000.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("60000.00"),
        amount_paid=Decimal("60000.00"),
        balance_due=Decimal("0.00"),
        created_by=uuid4(),
    )

    assert sale.is_paid is True


def test_sale_item_remaining_returnable_quantity() -> None:
    item = SaleItem(
        sale_id=uuid4(),
        egg_grade="GRADE_A",
        unit="TRAY",
        eggs_per_unit=30,
        quantity=10,
        quantity_returned=3,
        unit_price=Decimal("15000.00"),
        line_total=Decimal("150000.00"),
    )

    assert item.remaining_returnable_quantity == 7


def test_payment_reversed_property() -> None:
    payment = SalePayment(
        farm_id=uuid4(),
        customer_id=uuid4(),
        payment_number="PAY-001",
        amount=Decimal("50000.00"),
        method="CASH",
        status=PaymentStatus.REVERSED.value,
        received_by=uuid4(),
    )

    assert payment.is_reversed is True


def test_sale_return_reversed_property() -> None:
    sale_return = SaleReturn(
        farm_id=uuid4(),
        sale_id=uuid4(),
        return_number="RET-001",
        total_refund=Decimal("20000.00"),
        status=SaleReturnStatus.REVERSED.value,
        reason="Test return",
        recorded_by=uuid4(),
    )

    assert sale_return.is_reversed is True
