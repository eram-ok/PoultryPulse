from decimal import Decimal
from uuid import uuid4


from app.modules.finance.constants import (
    CashFlowDirection,
    ExpenseCategoryKind,
    FinanceDocumentStatus,
    FinancePaymentStatus,
    SupplierBillStatus,
)
from app.modules.finance.models import (
    CashLedgerEntry,
    Expense,
    ExpenseCategory,
    SupplierBill,
    SupplierBillPayment,
    normalize_finance_money,
)


def test_finance_money_rounding() -> None:
    assert normalize_finance_money("1250.555") == Decimal("1250.56")


def test_expense_category_defaults() -> None:
    category = ExpenseCategory(
        farm_id=uuid4(),
        category_code="FEED",
        name="Feed Costs",
        kind=ExpenseCategoryKind.FEED.value,
        is_active=True,
    )

    assert category.is_active is True
    assert category.kind == "FEED"


def test_expense_status_properties() -> None:
    expense = Expense(
        farm_id=uuid4(),
        category_id=uuid4(),
        expense_number="EXP-001",
        description="Electricity",
        amount=Decimal("80000.00"),
        payment_method="MOBILE_MONEY",
        status=FinanceDocumentStatus.POSTED.value,
        recorded_by=uuid4(),
    )

    assert expense.is_posted is True
    assert expense.is_voided is False


def test_voided_expense_property() -> None:
    expense = Expense(
        farm_id=uuid4(),
        category_id=uuid4(),
        expense_number="EXP-002",
        description="Incorrect expense",
        amount=Decimal("1000.00"),
        payment_method="CASH",
        status=FinanceDocumentStatus.VOIDED.value,
        recorded_by=uuid4(),
    )

    assert expense.is_voided is True


def test_unpaid_supplier_bill() -> None:
    bill = SupplierBill(
        farm_id=uuid4(),
        supplier_id=uuid4(),
        bill_number="BILL-001",
        description="Layers mash",
        subtotal=Decimal("500000.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("500000.00"),
        amount_paid=Decimal("0.00"),
        balance_due=Decimal("500000.00"),
        status=SupplierBillStatus.UNPAID.value,
        recorded_by=uuid4(),
    )

    assert bill.is_paid is False
    assert bill.is_voided is False


def test_paid_supplier_bill_property() -> None:
    bill = SupplierBill(
        farm_id=uuid4(),
        supplier_id=uuid4(),
        bill_number="BILL-002",
        description="Veterinary products",
        subtotal=Decimal("120000.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("120000.00"),
        amount_paid=Decimal("120000.00"),
        balance_due=Decimal("0.00"),
        status=SupplierBillStatus.PAID.value,
        recorded_by=uuid4(),
    )

    assert bill.is_paid is True


def test_voided_supplier_bill_property() -> None:
    bill = SupplierBill(
        farm_id=uuid4(),
        supplier_id=uuid4(),
        bill_number="BILL-003",
        description="Invalid supplier bill",
        subtotal=Decimal("1000.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("1000.00"),
        amount_paid=Decimal("0.00"),
        balance_due=Decimal("1000.00"),
        status=SupplierBillStatus.VOIDED.value,
        recorded_by=uuid4(),
    )

    assert bill.is_voided is True


def test_supplier_payment_reversed_property() -> None:
    payment = SupplierBillPayment(
        farm_id=uuid4(),
        supplier_id=uuid4(),
        supplier_bill_id=uuid4(),
        payment_number="SPAY-001",
        amount=Decimal("50000.00"),
        method="BANK_TRANSFER",
        status=FinancePaymentStatus.REVERSED.value,
        paid_by=uuid4(),
    )

    assert payment.is_reversed is True


def test_cash_inflow_signed_amount() -> None:
    entry = CashLedgerEntry(
        farm_id=uuid4(),
        entry_type="SALES_RECEIPT",
        direction=CashFlowDirection.INFLOW.value,
        amount=Decimal("200000.00"),
        balance_after=Decimal("300000.00"),
        description="Egg sale receipt",
        created_by=uuid4(),
    )

    assert entry.signed_amount == Decimal("200000.00")


def test_cash_outflow_signed_amount() -> None:
    entry = CashLedgerEntry(
        farm_id=uuid4(),
        entry_type="EXPENSE_PAYMENT",
        direction=CashFlowDirection.OUTFLOW.value,
        amount=Decimal("75000.00"),
        balance_after=Decimal("225000.00"),
        description="Electricity payment",
        created_by=uuid4(),
    )

    assert entry.signed_amount == Decimal("-75000.00")
