from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.finance.constants import (
    CashFlowDirection,
    ExpenseCategoryKind,
    FinanceDocumentStatus,
    FinancePaymentMethod,
    FinancePaymentStatus,
    SupplierBillStatus,
)

if TYPE_CHECKING:
    from app.modules.farms.models import Farm
    from app.modules.feed.models import FeedPurchase
    from app.modules.sales.models import SalePayment
    from app.modules.suppliers.models import Supplier


MONEY_QUANTUM = Decimal("0.01")


def normalize_finance_money(
    value: Decimal | int | str,
) -> Decimal:
    """Round a financial amount to two decimal places."""
    return Decimal(str(value)).quantize(
        MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


class ExpenseCategory(Base):
    """A farm-defined category used to classify operating expenses."""

    __tablename__ = "finance_expense_categories"
    __table_args__ = (
        UniqueConstraint(
            "farm_id",
            "category_code",
            name="uq_finance_expense_categories_farm_code",
        ),
        CheckConstraint(
            "kind IN ("
            "'FEED', 'VETERINARY', 'LABOUR', 'UTILITIES', "
            "'TRANSPORT', 'EQUIPMENT', 'MAINTENANCE', "
            "'HOUSING', 'ADMINISTRATION', 'BIOSECURITY', "
            "'OTHER'"
            ")",
            name="ck_finance_expense_categories_kind",
        ),
        Index(
            "ix_finance_expense_categories_farm_active",
            "farm_id",
            "is_active",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    farm_id: Mapped[UUID] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_code: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default=ExpenseCategoryKind.OTHER.value,
    )
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    farm: Mapped[Farm] = relationship()
    expenses: Mapped[list[Expense]] = relationship(
        back_populates="category",
    )


class Expense(Base):
    """A posted or voided operating expense."""

    __tablename__ = "finance_expenses"
    __table_args__ = (
        UniqueConstraint(
            "farm_id",
            "expense_number",
            name="uq_finance_expenses_farm_number",
        ),
        CheckConstraint(
            "amount > 0",
            name="ck_finance_expenses_amount_positive",
        ),
        CheckConstraint(
            "status IN ('DRAFT', 'POSTED', 'VOIDED')",
            name="ck_finance_expenses_status",
        ),
        CheckConstraint(
            "payment_method IN ("
            "'CASH', 'MOBILE_MONEY', 'BANK_TRANSFER', "
            "'CHEQUE', 'OTHER'"
            ")",
            name="ck_finance_expenses_payment_method",
        ),
        CheckConstraint(
            "(status <> 'VOIDED') OR "
            "(voided_by IS NOT NULL AND voided_at IS NOT NULL "
            "AND void_reason IS NOT NULL)",
            name="ck_finance_expenses_void_audit",
        ),
        Index(
            "ix_finance_expenses_farm_date",
            "farm_id",
            "expense_date",
        ),
        Index(
            "ix_finance_expenses_farm_status",
            "farm_id",
            "status",
        ),
        Index(
            "ix_finance_expenses_category_date",
            "category_id",
            "expense_date",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    farm_id: Mapped[UUID] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "finance_expense_categories.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    supplier_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
    )
    expense_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    expense_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )
    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    payment_method: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=FinancePaymentMethod.CASH.value,
    )
    reference_number: Mapped[str | None] = mapped_column(
        String(120),
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=FinanceDocumentStatus.POSTED.value,
    )
    source_type: Mapped[str | None] = mapped_column(
        String(60),
    )
    source_id: Mapped[UUID | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(Text)
    recorded_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    voided_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
    )
    voided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    void_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    farm: Mapped[Farm] = relationship()
    category: Mapped[ExpenseCategory] = relationship(
        back_populates="expenses",
    )
    supplier: Mapped[Supplier | None] = relationship()

    @property
    def is_posted(self) -> bool:
        return self.status == FinanceDocumentStatus.POSTED.value

    @property
    def is_voided(self) -> bool:
        return self.status == FinanceDocumentStatus.VOIDED.value


class SupplierBill(Base):
    """A supplier payable, optionally linked to an existing purchase."""

    __tablename__ = "supplier_bills"
    __table_args__ = (
        UniqueConstraint(
            "farm_id",
            "bill_number",
            name="uq_supplier_bills_farm_number",
        ),
        UniqueConstraint(
            "farm_id",
            "supplier_id",
            "supplier_invoice_number",
            name="uq_supplier_bills_supplier_invoice",
        ),
        CheckConstraint(
            "subtotal >= 0 AND tax_amount >= 0 "
            "AND total_amount >= 0 AND amount_paid >= 0 "
            "AND balance_due >= 0",
            name="ck_supplier_bills_amounts_nonnegative",
        ),
        CheckConstraint(
            "amount_paid <= total_amount",
            name="ck_supplier_bills_paid_not_above_total",
        ),
        CheckConstraint(
            "balance_due = total_amount - amount_paid",
            name="ck_supplier_bills_balance_consistent",
        ),
        CheckConstraint(
            "due_date IS NULL OR due_date >= bill_date",
            name="ck_supplier_bills_due_date",
        ),
        CheckConstraint(
            "status IN ('UNPAID', 'PARTIALLY_PAID', 'PAID', 'VOIDED')",
            name="ck_supplier_bills_status",
        ),
        CheckConstraint(
            "(status <> 'VOIDED') OR "
            "(voided_by IS NOT NULL AND voided_at IS NOT NULL "
            "AND void_reason IS NOT NULL)",
            name="ck_supplier_bills_void_audit",
        ),
        Index(
            "ix_supplier_bills_farm_date",
            "farm_id",
            "bill_date",
        ),
        Index(
            "ix_supplier_bills_supplier_date",
            "supplier_id",
            "bill_date",
        ),
        Index(
            "ix_supplier_bills_farm_status",
            "farm_id",
            "status",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    farm_id: Mapped[UUID] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
    )
    supplier_id: Mapped[UUID] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    feed_purchase_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "feed_purchases.id",
            ondelete="RESTRICT",
        ),
    )
    bill_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    supplier_invoice_number: Mapped[str | None] = mapped_column(
        String(100),
    )
    bill_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )
    due_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    balance_due: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=SupplierBillStatus.UNPAID.value,
    )
    source_type: Mapped[str | None] = mapped_column(
        String(60),
    )
    source_id: Mapped[UUID | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(Text)
    recorded_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    voided_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
    )
    voided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    void_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    farm: Mapped[Farm] = relationship()
    supplier: Mapped[Supplier] = relationship()
    feed_purchase: Mapped[FeedPurchase | None] = relationship()
    payments: Mapped[list[SupplierBillPayment]] = relationship(
        back_populates="supplier_bill",
        order_by="SupplierBillPayment.payment_date",
    )

    @property
    def is_paid(self) -> bool:
        return (
            self.status == SupplierBillStatus.PAID.value
            and self.balance_due == Decimal("0.00")
        )

    @property
    def is_voided(self) -> bool:
        return self.status == SupplierBillStatus.VOIDED.value


class SupplierBillPayment(Base):
    """A payment allocated to one supplier bill."""

    __tablename__ = "supplier_bill_payments"
    __table_args__ = (
        UniqueConstraint(
            "farm_id",
            "payment_number",
            name="uq_supplier_bill_payments_farm_number",
        ),
        CheckConstraint(
            "amount > 0",
            name="ck_supplier_bill_payments_amount_positive",
        ),
        CheckConstraint(
            "method IN ('CASH', 'MOBILE_MONEY', 'BANK_TRANSFER', 'CHEQUE', 'OTHER')",
            name="ck_supplier_bill_payments_method",
        ),
        CheckConstraint(
            "status IN ('POSTED', 'REVERSED')",
            name="ck_supplier_bill_payments_status",
        ),
        CheckConstraint(
            "(status <> 'REVERSED') OR "
            "(reversed_by IS NOT NULL AND reversed_at IS NOT NULL "
            "AND reversal_reason IS NOT NULL)",
            name="ck_supplier_bill_payments_reversal_audit",
        ),
        Index(
            "ix_supplier_bill_payments_farm_date",
            "farm_id",
            "payment_date",
        ),
        Index(
            "ix_supplier_bill_payments_supplier_date",
            "supplier_id",
            "payment_date",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    farm_id: Mapped[UUID] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
    )
    supplier_id: Mapped[UUID] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    supplier_bill_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "supplier_bills.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    payment_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    payment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    method: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=FinancePaymentMethod.CASH.value,
    )
    reference_number: Mapped[str | None] = mapped_column(
        String(120),
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=FinancePaymentStatus.POSTED.value,
    )
    notes: Mapped[str | None] = mapped_column(Text)
    paid_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reversed_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
    )
    reversed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    reversal_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    supplier: Mapped[Supplier] = relationship()
    supplier_bill: Mapped[SupplierBill] = relationship(
        back_populates="payments",
    )

    @property
    def is_reversed(self) -> bool:
        return self.status == FinancePaymentStatus.REVERSED.value


class CashLedgerEntry(Base):
    """An immutable farm cash-flow ledger entry."""

    __tablename__ = "cash_ledger_entries"
    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="ck_cash_ledger_entries_amount_positive",
        ),
        CheckConstraint(
            "direction IN ('INFLOW', 'OUTFLOW')",
            name="ck_cash_ledger_entries_direction",
        ),
        CheckConstraint(
            "entry_type IN ("
            "'OPENING_BALANCE', 'SALES_RECEIPT', "
            "'EXPENSE_PAYMENT', 'SUPPLIER_BILL_PAYMENT', "
            "'OTHER_INCOME', 'ADJUSTMENT', 'REVERSAL'"
            ")",
            name="ck_cash_ledger_entries_type",
        ),
        Index(
            "ix_cash_ledger_entries_farm_date",
            "farm_id",
            "entry_date",
        ),
        Index(
            "ix_cash_ledger_entries_farm_type",
            "farm_id",
            "entry_type",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    farm_id: Mapped[UUID] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
    )
    entry_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )
    entry_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )
    direction: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    expense_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "finance_expenses.id",
            ondelete="RESTRICT",
        ),
    )
    supplier_bill_payment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "supplier_bill_payments.id",
            ondelete="RESTRICT",
        ),
    )
    sale_payment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "sale_payments.id",
            ondelete="RESTRICT",
        ),
    )
    source_type: Mapped[str | None] = mapped_column(
        String(60),
    )
    source_id: Mapped[UUID | None] = mapped_column()
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    farm: Mapped[Farm] = relationship()
    expense: Mapped[Expense | None] = relationship()
    supplier_bill_payment: Mapped[SupplierBillPayment | None] = relationship()
    sale_payment: Mapped[SalePayment | None] = relationship()

    @property
    def signed_amount(self) -> Decimal:
        if self.direction == CashFlowDirection.INFLOW.value:
            return self.amount
        return -self.amount
