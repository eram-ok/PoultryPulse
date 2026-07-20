from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.modules.eggs.constants import EggGrade
from app.modules.sales.constants import (
    EggSaleUnit,
    SaleReturnStatus,
)


def normalize_optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


class SaleReturnItemCreate(BaseModel):
    sale_item_id: UUID
    quantity: int = Field(gt=0, le=1_000_000)
    reason: str | None = None

    @field_validator("reason")
    @classmethod
    def normalize_reason(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_optional_text(value)


class SaleReturnCreate(BaseModel):
    sale_id: UUID
    return_date: date = Field(default_factory=date.today)
    reason: str = Field(min_length=5, max_length=2000)
    notes: str | None = None
    items: list[SaleReturnItemCreate] = Field(
        min_length=1,
        max_length=10,
    )

    @field_validator("return_date")
    @classmethod
    def validate_return_date(
        cls,
        value: date,
    ) -> date:
        if value > date.today():
            raise ValueError("Return date cannot be in the future.")
        return value

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 5:
            raise ValueError("Return reason must contain at least five characters.")
        return normalized

    @field_validator("notes")
    @classmethod
    def normalize_notes(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_optional_text(value)


class SaleReturnReversalRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 5:
            raise ValueError("Reversal reason must contain at least five characters.")
        return normalized


class SaleReturnItemResponse(BaseModel):
    id: UUID
    sale_item_id: UUID
    egg_grade: EggGrade
    unit: EggSaleUnit
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    total_eggs: int
    reason: str | None


class SaleReturnResponse(BaseModel):
    id: UUID
    farm_id: UUID
    sale_id: UUID
    invoice_number: str
    customer_id: UUID
    customer_code: str
    customer_name: str
    return_number: str
    return_date: date
    total_refund: Decimal
    status: SaleReturnStatus
    reason: str
    notes: str | None
    recorded_by: UUID
    reversed_by: UUID | None
    reversed_at: datetime | None
    reversal_reason: str | None
    is_reversed: bool
    items: list[SaleReturnItemResponse]
    created_at: datetime


class SaleReturnListResponse(BaseModel):
    items: list[SaleReturnResponse]
    total: int
    offset: int
    limit: int
