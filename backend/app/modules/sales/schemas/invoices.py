from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)

from app.modules.eggs.constants import EggGrade
from app.modules.sales.constants import (
    EggSaleUnit,
    SalePaymentTerms,
    SaleStatus,
)


DEFAULT_EGGS_PER_UNIT = {
    EggSaleUnit.PIECE: 1,
    EggSaleUnit.TRAY: 30,
    EggSaleUnit.CRATE: 360,
}


def normalize_optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


class SaleItemCreate(BaseModel):
    egg_grade: EggGrade
    unit: EggSaleUnit = EggSaleUnit.TRAY
    eggs_per_unit: int | None = Field(default=None, ge=1, le=10000)
    quantity: int = Field(gt=0, le=1_000_000)
    unit_price: Decimal = Field(
        ge=0,
        max_digits=14,
        decimal_places=2,
    )
    notes: str | None = None

    @field_validator("notes")
    @classmethod
    def normalize_notes(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_optional_text(value)

    @model_validator(mode="after")
    def set_default_eggs_per_unit(
        self,
    ) -> "SaleItemCreate":
        if self.eggs_per_unit is None:
            self.eggs_per_unit = DEFAULT_EGGS_PER_UNIT[self.unit]
        return self


class SaleCreate(BaseModel):
    customer_id: UUID
    sale_date: date = Field(default_factory=date.today)
    due_date: date | None = None
    payment_terms: SalePaymentTerms = SalePaymentTerms.CASH
    discount_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=14,
        decimal_places=2,
    )
    tax_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=14,
        decimal_places=2,
    )
    notes: str | None = None
    items: list[SaleItemCreate] = Field(
        min_length=1,
        max_length=10,
    )

    @field_validator("sale_date")
    @classmethod
    def validate_sale_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Sale date cannot be in the future.")
        return value

    @field_validator("notes")
    @classmethod
    def normalize_notes(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_optional_text(value)

    @model_validator(mode="after")
    def validate_sale(self) -> "SaleCreate":
        if self.due_date is not None and self.due_date < self.sale_date:
            raise ValueError("Due date cannot be before the sale date.")

        if self.payment_terms == SalePaymentTerms.CREDIT and self.due_date is None:
            raise ValueError("Credit sales require a due date.")

        grades = [item.egg_grade for item in self.items]
        if len(grades) != len(set(grades)):
            raise ValueError("Each egg grade may appear only once per invoice.")

        return self


class SaleUpdate(BaseModel):
    due_date: date | None = None
    payment_terms: SalePaymentTerms | None = None
    discount_amount: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=14,
        decimal_places=2,
    )
    tax_amount: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=14,
        decimal_places=2,
    )
    notes: str | None = None
    items: list[SaleItemCreate] | None = Field(
        default=None,
        min_length=1,
        max_length=10,
    )

    @field_validator("notes")
    @classmethod
    def normalize_notes(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_optional_text(value)

    @model_validator(mode="after")
    def validate_items(self) -> "SaleUpdate":
        if self.items is not None:
            grades = [item.egg_grade for item in self.items]
            if len(grades) != len(set(grades)):
                raise ValueError("Each egg grade may appear only once per invoice.")
        return self


class SaleConfirmationRequest(BaseModel):
    notes: str | None = None

    @field_validator("notes")
    @classmethod
    def normalize_notes(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_optional_text(value)


class SaleCancellationRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 5:
            raise ValueError(
                "Cancellation reason must contain at least five characters."
            )
        return normalized


class SaleItemResponse(BaseModel):
    id: UUID
    egg_grade: EggGrade
    unit: EggSaleUnit
    eggs_per_unit: int
    quantity: int
    quantity_returned: int
    remaining_returnable_quantity: int
    unit_price: Decimal
    line_total: Decimal
    total_eggs: int
    notes: str | None
    created_at: datetime


class SaleResponse(BaseModel):
    id: UUID
    farm_id: UUID
    customer_id: UUID
    customer_code: str
    customer_name: str
    invoice_number: str
    sale_date: date
    due_date: date | None
    payment_terms: SalePaymentTerms
    status: SaleStatus
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    is_paid: bool
    is_cancelled: bool
    is_confirmed: bool
    notes: str | None
    created_by: UUID
    confirmed_by: UUID | None
    confirmed_at: datetime | None
    cancelled_by: UUID | None
    cancelled_at: datetime | None
    cancellation_reason: str | None
    items: list[SaleItemResponse]
    created_at: datetime
    updated_at: datetime


class SaleListResponse(BaseModel):
    items: list[SaleResponse]
    total: int
    offset: int
    limit: int
