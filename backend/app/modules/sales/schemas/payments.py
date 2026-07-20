from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.modules.sales.constants import (
    PaymentMethod,
    PaymentStatus,
)


def normalize_optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


class PaymentCreate(BaseModel):
    sale_id: UUID
    payment_date: date = Field(default_factory=date.today)
    amount: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=2,
    )
    method: PaymentMethod = PaymentMethod.CASH
    reference_number: str | None = Field(
        default=None,
        max_length=120,
    )
    notes: str | None = None

    @field_validator("payment_date")
    @classmethod
    def validate_payment_date(
        cls,
        value: date,
    ) -> date:
        if value > date.today():
            raise ValueError("Payment date cannot be in the future.")
        return value

    @field_validator("reference_number", "notes")
    @classmethod
    def normalize_optional_fields(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_optional_text(value)


class PaymentReversalRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 5:
            raise ValueError("Reversal reason must contain at least five characters.")
        return normalized


class PaymentResponse(BaseModel):
    id: UUID
    farm_id: UUID
    customer_id: UUID
    customer_code: str
    customer_name: str
    sale_id: UUID
    invoice_number: str
    payment_number: str
    payment_date: date
    amount: Decimal
    method: PaymentMethod
    reference_number: str | None
    status: PaymentStatus
    notes: str | None
    received_by: UUID
    reversed_by: UUID | None
    reversed_at: datetime | None
    reversal_reason: str | None
    is_reversed: bool
    created_at: datetime


class PaymentListResponse(BaseModel):
    items: list[PaymentResponse]
    total: int
    offset: int
    limit: int
