from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from app.modules.sales.constants import (
    CustomerLedgerEntryType,
    CustomerStatus,
)


def normalize_optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


class CustomerCreate(BaseModel):
    customer_code: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=180)
    phone_number: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = None
    address: str | None = None
    tax_number: str | None = Field(default=None, max_length=80)
    contact_person: str | None = Field(default=None, max_length=150)
    credit_limit: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=14,
        decimal_places=2,
    )
    opening_balance: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=14,
        decimal_places=2,
    )
    notes: str | None = None

    @field_validator("customer_code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        normalized = value.strip().upper().replace(" ", "-")
        if len(normalized) < 2:
            raise ValueError("Customer code must contain at least two characters.")
        return normalized

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("Customer name must contain at least two characters.")
        return normalized

    @field_validator(
        "phone_number",
        "address",
        "tax_number",
        "contact_person",
        "notes",
    )
    @classmethod
    def normalize_optional_fields(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_optional_text(value)


class CustomerUpdate(BaseModel):
    customer_code: str | None = Field(
        default=None,
        min_length=2,
        max_length=40,
    )
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=180,
    )
    phone_number: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = None
    address: str | None = None
    tax_number: str | None = Field(default=None, max_length=80)
    contact_person: str | None = Field(default=None, max_length=150)
    credit_limit: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=14,
        decimal_places=2,
    )
    status: CustomerStatus | None = None
    notes: str | None = None

    @field_validator("customer_code")
    @classmethod
    def normalize_code(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper().replace(" ", "-")
        if len(normalized) < 2:
            raise ValueError("Customer code must contain at least two characters.")
        return normalized

    @field_validator("name")
    @classmethod
    def normalize_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("Customer name must contain at least two characters.")
        return normalized

    @field_validator(
        "phone_number",
        "address",
        "tax_number",
        "contact_person",
        "notes",
    )
    @classmethod
    def normalize_optional_fields(
        cls,
        value: str | None,
    ) -> str | None:
        return normalize_optional_text(value)


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    customer_code: str
    name: str
    phone_number: str | None
    email: str | None
    address: str | None
    tax_number: str | None
    contact_person: str | None
    credit_limit: Decimal
    opening_balance: Decimal
    current_balance: Decimal
    available_credit: Decimal
    status: CustomerStatus
    is_active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class CustomerListResponse(BaseModel):
    items: list[CustomerResponse]
    total: int
    offset: int
    limit: int


class LedgerEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    customer_id: UUID
    sale_id: UUID | None
    payment_id: UUID | None
    sale_return_id: UUID | None
    entry_date: date
    entry_type: CustomerLedgerEntryType
    description: str
    debit_amount: Decimal
    credit_amount: Decimal
    balance_after: Decimal
    created_by: UUID
    created_at: datetime


class CustomerStatementResponse(BaseModel):
    customer: CustomerResponse
    date_from: date | None
    date_to: date | None
    opening_balance: Decimal
    closing_balance: Decimal
    entries: list[LedgerEntryResponse]
