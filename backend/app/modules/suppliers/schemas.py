from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from app.modules.suppliers.constants import SupplierType


class SupplierCreate(BaseModel):
    """Information required to register a supplier."""

    supplier_code: str = Field(
        min_length=2,
        max_length=30,
    )
    name: str = Field(
        min_length=2,
        max_length=150,
    )
    supplier_type: SupplierType = SupplierType.GENERAL_SUPPLIER
    telephone: str | None = Field(
        default=None,
        max_length=30,
    )
    email: EmailStr | None = None
    address: str | None = None
    notes: str | None = None

    @field_validator("supplier_code")
    @classmethod
    def normalize_supplier_code(cls, value: str) -> str:
        normalized = value.strip().upper().replace(" ", "-")

        if not normalized:
            raise ValueError("Supplier code cannot be empty.")

        return normalized

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()

        if len(normalized) < 2:
            raise ValueError("Supplier name must contain at least two characters.")

        return normalized

    @field_validator("telephone")
    @classmethod
    def normalize_telephone(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None


class SupplierUpdate(BaseModel):
    """Supplier fields that may be updated."""

    supplier_code: str | None = Field(
        default=None,
        min_length=2,
        max_length=30,
    )
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    supplier_type: SupplierType | None = None
    telephone: str | None = Field(
        default=None,
        max_length=30,
    )
    email: EmailStr | None = None
    address: str | None = None
    notes: str | None = None

    @field_validator("supplier_code")
    @classmethod
    def normalize_supplier_code(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip().upper().replace(" ", "-")

        if not normalized:
            raise ValueError("Supplier code cannot be empty.")

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
            raise ValueError("Supplier name must contain at least two characters.")

        return normalized


class SupplierResponse(BaseModel):
    """Supplier information returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    supplier_code: str
    name: str
    supplier_type: SupplierType
    telephone: str | None
    email: str | None
    address: str | None
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SupplierListResponse(BaseModel):
    """Paginated supplier listing."""

    items: list[SupplierResponse]
    total: int
    offset: int
    limit: int
