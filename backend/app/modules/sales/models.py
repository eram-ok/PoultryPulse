from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.sales.constants import (
    CustomerStatus,
    EggSaleUnit,
    PaymentMethod,
    PaymentStatus,
    SalePaymentTerms,
    SaleReturnStatus,
    SaleStatus,
)

if TYPE_CHECKING:
    from app.modules.farms.models import Farm


MONEY_QUANTUM = Decimal("0.01")


def normalize_money(value: Decimal | int | str) -> Decimal:
    """Round monetary values to two decimal places."""
    return Decimal(str(value)).quantize(
        MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def calculate_line_total(
    quantity: int,
    unit_price: Decimal | int | str,
) -> Decimal:
    """Calculate a sale or return line total."""
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    price = normalize_money(unit_price)

    if price < 0:
        raise ValueError("Unit price cannot be negative.")

    return normalize_money(Decimal(quantity) * price)


class Customer(Base):
    """A farm customer who may purchase eggs on cash or credit."""

    __tablename__ = "sales_customers"
    __table_args__ = (
        UniqueConstraint(
            "farm_id",
            "customer_code",
            name="uq_sales_customers_farm_code",
        ),
        CheckConstraint(
            "credit_limit >= 0",
            name="ck_sales_customers_credit_limit_nonnegative",
        ),
        CheckConstraint(
            "opening_balance >= 0",
            name="ck_sales_customers_opening_balance_nonnegative",
        ),
        CheckConstraint(
            "current_balance >= 0",
            name="ck_sales_customers_current_balance_nonnegative",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE', 'BLOCKED')",
            name="ck_sales_customers_status",
        ),
        Index(
            "ix_sales_customers_farm_status",
            "farm_id",
            "status",
        ),
        Index(
            "ix_sales_customers_farm_name",
            "farm_id",
            "name",
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
    customer_code: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(180),
        nullable=False,
    )
    phone_number: Mapped[str | None] = mapped_column(
        String(40),
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
    )
    address: Mapped[str | None] = mapped_column(
        Text,
    )
    tax_number: Mapped[str | None] = mapped_column(
        String(80),
    )
    contact_person: Mapped[str | None] = mapped_column(
        String(150),
    )
    credit_limit: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=CustomerStatus.ACTIVE.value,
    )
    notes: Mapped[str | None] = mapped_column(Text)
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
    sales: Mapped[list[Sale]] = relationship(
        back_populates="customer",
    )
    payments: Mapped[list[SalePayment]] = relationship(
        back_populates="customer",
    )
    returns: Mapped[list[SaleReturn]] = relationship(
        back_populates="customer",
    )
    ledger_entries: Mapped[list[CustomerLedgerEntry]] = relationship(
        back_populates="customer",
        order_by="CustomerLedgerEntry.entry_date",
    )

    @property
    def is_active(self) -> bool:
        return self.status == CustomerStatus.ACTIVE.value

    @property
    def available_credit(self) -> Decimal:
        remaining = normalize_money(self.credit_limit - self.current_balance)
        return max(Decimal("0.00"), remaining)


class Sale(Base):
    """An egg sale invoice."""

    __tablename__ = "sales"
    __table_args__ = (
        UniqueConstraint(
            "farm_id",
            "invoice_number",
            name="uq_sales_farm_invoice_number",
        ),
        CheckConstraint(
            "subtotal >= 0 AND discount_amount >= 0 "
            "AND tax_amount >= 0 AND total_amount >= 0 "
            "AND amount_paid >= 0 AND balance_due >= 0",
            name="ck_sales_amounts_nonnegative",
        ),
        CheckConstraint(
            "amount_paid <= total_amount",
            name="ck_sales_amount_paid_not_above_total",
        ),
        CheckConstraint(
            "balance_due = total_amount - amount_paid",
            name="ck_sales_balance_consistent",
        ),
        CheckConstraint(
            "due_date IS NULL OR due_date >= sale_date",
            name="ck_sales_due_date",
        ),
        CheckConstraint(
            "status IN ("
            "'DRAFT', 'CONFIRMED', 'PARTIALLY_PAID', 'PAID', "
            "'PARTIALLY_RETURNED', 'RETURNED', 'CANCELLED'"
            ")",
            name="ck_sales_status",
        ),
        CheckConstraint(
            "payment_terms IN ('CASH', 'CREDIT')",
            name="ck_sales_payment_terms",
        ),
        CheckConstraint(
            "(status <> 'CANCELLED') OR "
            "(cancelled_by IS NOT NULL AND cancelled_at IS NOT NULL "
            "AND cancellation_reason IS NOT NULL)",
            name="ck_sales_cancellation_audit",
        ),
        Index(
            "ix_sales_farm_date",
            "farm_id",
            "sale_date",
        ),
        Index(
            "ix_sales_farm_status",
            "farm_id",
            "status",
        ),
        Index(
            "ix_sales_customer_date",
            "customer_id",
            "sale_date",
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
    customer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "sales_customers.id",
            ondelete="RESTRICT",
        ),
    )
    invoice_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    sale_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )
    due_date: Mapped[date | None] = mapped_column(Date)
    payment_terms: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SalePaymentTerms.CASH.value,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=SaleStatus.DRAFT.value,
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    balance_due: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    customer_name_snapshot: Mapped[str | None] = mapped_column(
        String(180),
    )
    customer_phone_snapshot: Mapped[str | None] = mapped_column(
        String(40),
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    confirmed_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    cancelled_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    cancellation_reason: Mapped[str | None] = mapped_column(
        Text,
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

    customer: Mapped[Customer | None] = relationship(
        back_populates="sales",
    )
    items: Mapped[list[SaleItem]] = relationship(
        back_populates="sale",
        cascade="all, delete-orphan",
        order_by="SaleItem.created_at",
    )
    payments: Mapped[list[SalePayment]] = relationship(
        back_populates="sale",
    )
    returns: Mapped[list[SaleReturn]] = relationship(
        back_populates="sale",
    )

    @property
    def is_paid(self) -> bool:
        return self.status == SaleStatus.PAID.value and self.balance_due == Decimal(
            "0.00"
        )

    @property
    def is_cancelled(self) -> bool:
        return self.status == SaleStatus.CANCELLED.value

    @property
    def is_confirmed(self) -> bool:
        return self.status not in {
            SaleStatus.DRAFT.value,
            SaleStatus.CANCELLED.value,
        }

    @property
    def is_credit_sale(self) -> bool:
        return self.payment_terms == SalePaymentTerms.CREDIT.value


class SaleItem(Base):
    """One egg grade and quantity sold on an invoice."""

    __tablename__ = "sale_items"
    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_sale_items_quantity_positive",
        ),
        CheckConstraint(
            "eggs_per_unit > 0",
            name="ck_sale_items_eggs_per_unit_positive",
        ),
        CheckConstraint(
            "unit_price >= 0 AND line_total >= 0",
            name="ck_sale_items_amounts_nonnegative",
        ),
        CheckConstraint(
            "quantity_returned >= 0 AND quantity_returned <= quantity",
            name="ck_sale_items_returned_quantity",
        ),
        CheckConstraint(
            "unit IN ('PIECE', 'TRAY', 'CRATE')",
            name="ck_sale_items_unit",
        ),
        Index(
            "ix_sale_items_sale_grade",
            "sale_id",
            "egg_grade",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    sale_id: Mapped[UUID] = mapped_column(
        ForeignKey("sales.id", ondelete="CASCADE"),
        nullable=False,
    )
    egg_grade: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=EggSaleUnit.TRAY.value,
    )
    eggs_per_unit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    quantity_returned: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    sale: Mapped[Sale] = relationship(
        back_populates="items",
    )
    return_items: Mapped[list[SaleReturnItem]] = relationship(
        back_populates="sale_item",
    )

    @property
    def remaining_returnable_quantity(self) -> int:
        return self.quantity - self.quantity_returned


class SalePayment(Base):
    """A customer payment allocated to a sale or account."""

    __tablename__ = "sale_payments"
    __table_args__ = (
        UniqueConstraint(
            "farm_id",
            "payment_number",
            name="uq_sale_payments_farm_number",
        ),
        CheckConstraint(
            "amount > 0",
            name="ck_sale_payments_amount_positive",
        ),
        CheckConstraint(
            "method IN ('CASH', 'MOBILE_MONEY', 'BANK_TRANSFER', 'CHEQUE', 'OTHER')",
            name="ck_sale_payments_method",
        ),
        CheckConstraint(
            "status IN ('POSTED', 'REVERSED')",
            name="ck_sale_payments_status",
        ),
        CheckConstraint(
            "(status <> 'REVERSED') OR "
            "(reversed_by IS NOT NULL AND reversed_at IS NOT NULL "
            "AND reversal_reason IS NOT NULL)",
            name="ck_sale_payments_reversal_audit",
        ),
        Index(
            "ix_sale_payments_farm_date",
            "farm_id",
            "payment_date",
        ),
        Index(
            "ix_sale_payments_customer_date",
            "customer_id",
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
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "sales_customers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    sale_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("sales.id", ondelete="RESTRICT"),
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
        default=PaymentMethod.CASH.value,
    )
    reference_number: Mapped[str | None] = mapped_column(
        String(120),
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=PaymentStatus.POSTED.value,
    )
    notes: Mapped[str | None] = mapped_column(Text)
    received_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reversed_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
    )
    reversed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    reversal_reason: Mapped[str | None] = mapped_column(
        Text,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    customer: Mapped[Customer] = relationship(
        back_populates="payments",
    )
    sale: Mapped[Sale | None] = relationship(
        back_populates="payments",
    )

    @property
    def is_reversed(self) -> bool:
        return self.status == PaymentStatus.REVERSED.value


class SaleReturn(Base):
    """A posted or reversed return against a confirmed sale."""

    __tablename__ = "sale_returns"
    __table_args__ = (
        UniqueConstraint(
            "farm_id",
            "return_number",
            name="uq_sale_returns_farm_number",
        ),
        CheckConstraint(
            "total_refund >= 0",
            name="ck_sale_returns_refund_nonnegative",
        ),
        CheckConstraint(
            "status IN ('POSTED', 'REVERSED')",
            name="ck_sale_returns_status",
        ),
        CheckConstraint(
            "(status <> 'REVERSED') OR "
            "(reversed_by IS NOT NULL AND reversed_at IS NOT NULL "
            "AND reversal_reason IS NOT NULL)",
            name="ck_sale_returns_reversal_audit",
        ),
        Index(
            "ix_sale_returns_farm_date",
            "farm_id",
            "return_date",
        ),
        Index(
            "ix_sale_returns_sale",
            "sale_id",
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
    sale_id: Mapped[UUID] = mapped_column(
        ForeignKey("sales.id", ondelete="RESTRICT"),
        nullable=False,
    )
    customer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "sales_customers.id",
            ondelete="RESTRICT",
        ),
    )
    return_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    return_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )
    total_refund: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SaleReturnStatus.POSTED.value,
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text)
    recorded_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reversed_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
    )
    reversed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    reversal_reason: Mapped[str | None] = mapped_column(
        Text,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    sale: Mapped[Sale] = relationship(
        back_populates="returns",
    )
    customer: Mapped[Customer | None] = relationship(
        back_populates="returns",
    )
    items: Mapped[list[SaleReturnItem]] = relationship(
        back_populates="sale_return",
        cascade="all, delete-orphan",
    )

    @property
    def is_reversed(self) -> bool:
        return self.status == SaleReturnStatus.REVERSED.value


class SaleReturnItem(Base):
    """One returned line from an original sale item."""

    __tablename__ = "sale_return_items"
    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_sale_return_items_quantity_positive",
        ),
        CheckConstraint(
            "unit_price >= 0 AND line_total >= 0",
            name="ck_sale_return_items_amounts_nonnegative",
        ),
        CheckConstraint(
            "unit IN ('PIECE', 'TRAY', 'CRATE')",
            name="ck_sale_return_items_unit",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    sale_return_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "sale_returns.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    sale_item_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "sale_items.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    egg_grade: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(Text)

    sale_return: Mapped[SaleReturn] = relationship(
        back_populates="items",
    )
    sale_item: Mapped[SaleItem] = relationship(
        back_populates="return_items",
    )


class CustomerLedgerEntry(Base):
    """An immutable customer receivables ledger entry."""

    __tablename__ = "customer_ledger_entries"
    __table_args__ = (
        CheckConstraint(
            "debit_amount >= 0 AND credit_amount >= 0 AND balance_after >= 0",
            name="ck_customer_ledger_amounts_nonnegative",
        ),
        CheckConstraint(
            "NOT (debit_amount > 0 AND credit_amount > 0)",
            name="ck_customer_ledger_single_side",
        ),
        CheckConstraint(
            "entry_type IN ("
            "'OPENING_BALANCE', 'SALE', 'PAYMENT', "
            "'SALE_RETURN', 'ADJUSTMENT', 'REVERSAL'"
            ")",
            name="ck_customer_ledger_entry_type",
        ),
        Index(
            "ix_customer_ledger_customer_date",
            "customer_id",
            "entry_date",
        ),
        Index(
            "ix_customer_ledger_farm_date",
            "farm_id",
            "entry_date",
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
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "sales_customers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    sale_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("sales.id", ondelete="RESTRICT"),
    )
    payment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "sale_payments.id",
            ondelete="RESTRICT",
        ),
    )
    sale_return_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "sale_returns.id",
            ondelete="RESTRICT",
        ),
    )
    entry_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )
    entry_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    debit_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    credit_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    customer: Mapped[Customer] = relationship(
        back_populates="ledger_entries",
    )
