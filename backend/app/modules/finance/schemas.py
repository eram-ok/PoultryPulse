from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.finance.constants import (
    CashFlowDirection,
    CashLedgerEntryType,
    ExpenseCategoryKind,
    FinanceDocumentStatus,
    FinancePaymentMethod,
    FinancePaymentStatus,
    SupplierBillStatus,
)


def clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


class ExpenseCategoryCreate(BaseModel):
    category_code: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=150)
    kind: ExpenseCategoryKind = ExpenseCategoryKind.OTHER
    description: str | None = None

    @field_validator("category_code")
    @classmethod
    def code(cls, value: str) -> str:
        return value.strip().upper().replace(" ", "_")

    @field_validator("name")
    @classmethod
    def name_value(cls, value: str) -> str:
        return value.strip()

    @field_validator("description")
    @classmethod
    def description_value(cls, value: str | None) -> str | None:
        return clean(value)


class ExpenseCategoryUpdate(BaseModel):
    category_code: str | None = Field(default=None, min_length=2, max_length=40)
    name: str | None = Field(default=None, min_length=2, max_length=150)
    kind: ExpenseCategoryKind | None = None
    description: str | None = None
    is_active: bool | None = None

    @field_validator("category_code")
    @classmethod
    def code(cls, value: str | None) -> str | None:
        return value.strip().upper().replace(" ", "_") if value else None

    @field_validator("name", "description")
    @classmethod
    def text(cls, value: str | None) -> str | None:
        return clean(value)


class ExpenseCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    farm_id: UUID
    category_code: str
    name: str
    kind: ExpenseCategoryKind
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ExpenseCategoryListResponse(BaseModel):
    items: list[ExpenseCategoryResponse]
    total: int
    offset: int
    limit: int


class ExpenseCreate(BaseModel):
    category_id: UUID
    supplier_id: UUID | None = None
    expense_date: date = Field(default_factory=date.today)
    description: str = Field(min_length=3, max_length=255)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    payment_method: FinancePaymentMethod = FinancePaymentMethod.CASH
    reference_number: str | None = Field(default=None, max_length=120)
    notes: str | None = None

    @field_validator("expense_date")
    @classmethod
    def valid_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Expense date cannot be in the future.")
        return value

    @field_validator("description")
    @classmethod
    def description_value(cls, value: str) -> str:
        return value.strip()

    @field_validator("reference_number", "notes")
    @classmethod
    def optional_text(cls, value: str | None) -> str | None:
        return clean(value)


class VoidRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)

    @field_validator("reason")
    @classmethod
    def reason_value(cls, value: str) -> str:
        return value.strip()


class ExpenseResponse(BaseModel):
    id: UUID
    farm_id: UUID
    category_id: UUID
    category_code: str
    category_name: str
    supplier_id: UUID | None
    supplier_name: str | None
    expense_number: str
    expense_date: date
    description: str
    amount: Decimal
    payment_method: FinancePaymentMethod
    reference_number: str | None
    status: FinanceDocumentStatus
    notes: str | None
    recorded_by: UUID
    voided_by: UUID | None
    voided_at: datetime | None
    void_reason: str | None
    is_posted: bool
    is_voided: bool
    created_at: datetime
    updated_at: datetime


class ExpenseListResponse(BaseModel):
    items: list[ExpenseResponse]
    total: int
    offset: int
    limit: int


class SupplierBillCreate(BaseModel):
    supplier_id: UUID
    feed_purchase_id: UUID | None = None
    supplier_invoice_number: str | None = Field(default=None, max_length=100)
    bill_date: date = Field(default_factory=date.today)
    due_date: date | None = None
    description: str = Field(min_length=3, max_length=255)
    subtotal: Decimal | None = Field(
        default=None, ge=0, max_digits=14, decimal_places=2
    )
    tax_amount: Decimal = Field(
        default=Decimal("0.00"), ge=0, max_digits=14, decimal_places=2
    )
    notes: str | None = None

    @field_validator("bill_date")
    @classmethod
    def valid_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Bill date cannot be in the future.")
        return value

    @field_validator("description")
    @classmethod
    def description_value(cls, value: str) -> str:
        return value.strip()

    @field_validator("supplier_invoice_number", "notes")
    @classmethod
    def optional_text(cls, value: str | None) -> str | None:
        return clean(value)

    @model_validator(mode="after")
    def validate_bill(self) -> "SupplierBillCreate":
        if self.due_date is not None and self.due_date < self.bill_date:
            raise ValueError("Due date cannot be before the bill date.")
        if self.feed_purchase_id is None and self.subtotal is None:
            raise ValueError("Subtotal is required when no feed purchase is linked.")
        return self


class SupplierBillResponse(BaseModel):
    id: UUID
    farm_id: UUID
    supplier_id: UUID
    supplier_code: str
    supplier_name: str
    feed_purchase_id: UUID | None
    bill_number: str
    supplier_invoice_number: str | None
    bill_date: date
    due_date: date | None
    description: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    status: SupplierBillStatus
    notes: str | None
    recorded_by: UUID
    voided_by: UUID | None
    voided_at: datetime | None
    void_reason: str | None
    is_paid: bool
    is_voided: bool
    created_at: datetime
    updated_at: datetime


class SupplierBillListResponse(BaseModel):
    items: list[SupplierBillResponse]
    total: int
    offset: int
    limit: int


class SupplierPaymentCreate(BaseModel):
    supplier_bill_id: UUID
    payment_date: date = Field(default_factory=date.today)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    method: FinancePaymentMethod = FinancePaymentMethod.CASH
    reference_number: str | None = Field(default=None, max_length=120)
    notes: str | None = None

    @field_validator("payment_date")
    @classmethod
    def valid_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Payment date cannot be in the future.")
        return value

    @field_validator("reference_number", "notes")
    @classmethod
    def optional_text(cls, value: str | None) -> str | None:
        return clean(value)


class SupplierPaymentResponse(BaseModel):
    id: UUID
    farm_id: UUID
    supplier_id: UUID
    supplier_code: str
    supplier_name: str
    supplier_bill_id: UUID
    bill_number: str
    payment_number: str
    payment_date: date
    amount: Decimal
    method: FinancePaymentMethod
    reference_number: str | None
    status: FinancePaymentStatus
    notes: str | None
    paid_by: UUID
    reversed_by: UUID | None
    reversed_at: datetime | None
    reversal_reason: str | None
    is_reversed: bool
    created_at: datetime


class SupplierPaymentListResponse(BaseModel):
    items: list[SupplierPaymentResponse]
    total: int
    offset: int
    limit: int


class CashAdjustmentCreate(BaseModel):
    entry_date: date = Field(default_factory=date.today)
    direction: CashFlowDirection
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    description: str = Field(min_length=5, max_length=255)

    @field_validator("entry_date")
    @classmethod
    def valid_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Adjustment date cannot be in the future.")
        return value

    @field_validator("description")
    @classmethod
    def description_value(cls, value: str) -> str:
        return value.strip()


class CashLedgerEntryResponse(BaseModel):
    id: UUID
    farm_id: UUID
    entry_date: date
    entry_type: CashLedgerEntryType
    direction: CashFlowDirection
    amount: Decimal
    signed_amount: Decimal
    balance_after: Decimal
    description: str
    expense_id: UUID | None
    supplier_bill_payment_id: UUID | None
    sale_payment_id: UUID | None
    source_type: str | None
    source_id: UUID | None
    created_by: UUID
    created_at: datetime


class CashLedgerListResponse(BaseModel):
    items: list[CashLedgerEntryResponse]
    total: int
    offset: int
    limit: int
    current_balance: Decimal


class SalesReceiptSyncResponse(BaseModel):
    receipts_created: int
    reversals_created: int
    current_balance: Decimal


class SupplierStatementResponse(BaseModel):
    supplier_id: UUID
    supplier_code: str
    supplier_name: str
    date_from: date | None
    date_to: date | None
    total_billed: Decimal
    total_paid: Decimal
    outstanding_balance: Decimal
    bills: list[SupplierBillResponse]
    payments: list[SupplierPaymentResponse]


class CashFlowReportResponse(BaseModel):
    date_from: date | None
    date_to: date | None
    total_inflows: Decimal
    total_outflows: Decimal
    net_cash_flow: Decimal
    current_balance: Decimal
    inflows_by_type: dict[str, Decimal]
    outflows_by_type: dict[str, Decimal]


class ProfitabilityReportResponse(BaseModel):
    date_from: date | None
    date_to: date | None
    sales_revenue: Decimal
    operating_expenses: Decimal
    supplier_bill_costs: Decimal
    total_costs: Decimal
    gross_profit: Decimal
    profit_margin_percent: Decimal
    expenses_by_category: dict[str, Decimal]


class FinanceSummaryResponse(BaseModel):
    as_of_date: date
    current_cash_balance: Decimal
    outstanding_supplier_payables: Decimal
    posted_expenses: Decimal
    sales_receipts: Decimal
    net_cash_flow: Decimal
