from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.health.constants import HealthProductType


def _normalize_required_text(value: str, field_name: str) -> str:
    normalized = value.strip()

    if len(normalized) < 2:
        raise ValueError(f"{field_name} must contain at least two characters.")

    return normalized


def _normalize_optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


class HealthProductCreate(BaseModel):
    """Information required to register a health product."""

    product_code: str = Field(min_length=2, max_length=30)
    name: str = Field(min_length=2, max_length=150)
    product_type: HealthProductType
    manufacturer: str | None = Field(default=None, max_length=150)
    active_ingredient: str | None = Field(default=None, max_length=200)
    description: str | None = None
    default_egg_withdrawal_days: int = Field(default=0, ge=0, le=365)
    default_meat_withdrawal_days: int = Field(default=0, ge=0, le=365)

    @field_validator("product_code")
    @classmethod
    def normalize_product_code(cls, value: str) -> str:
        normalized = value.strip().upper().replace(" ", "-")

        if len(normalized) < 2:
            raise ValueError("Product code must contain at least two characters.")

        return normalized

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return _normalize_required_text(value, "Product name")

    @field_validator(
        "manufacturer",
        "active_ingredient",
        "description",
    )
    @classmethod
    def normalize_optional_fields(
        cls,
        value: str | None,
    ) -> str | None:
        return _normalize_optional_text(value)


class HealthProductUpdate(BaseModel):
    """Health-product fields that may be changed."""

    product_code: str | None = Field(default=None, min_length=2, max_length=30)
    name: str | None = Field(default=None, min_length=2, max_length=150)
    product_type: HealthProductType | None = None
    manufacturer: str | None = Field(default=None, max_length=150)
    active_ingredient: str | None = Field(default=None, max_length=200)
    description: str | None = None
    default_egg_withdrawal_days: int | None = Field(
        default=None,
        ge=0,
        le=365,
    )
    default_meat_withdrawal_days: int | None = Field(
        default=None,
        ge=0,
        le=365,
    )

    @field_validator("product_code")
    @classmethod
    def normalize_product_code(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip().upper().replace(" ", "-")

        if len(normalized) < 2:
            raise ValueError("Product code must contain at least two characters.")

        return normalized

    @field_validator("name")
    @classmethod
    def normalize_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return _normalize_required_text(value, "Product name")

    @field_validator(
        "manufacturer",
        "active_ingredient",
        "description",
    )
    @classmethod
    def normalize_optional_fields(
        cls,
        value: str | None,
    ) -> str | None:
        return _normalize_optional_text(value)


class HealthProductResponse(BaseModel):
    """Health-product information returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    product_code: str
    name: str
    product_type: HealthProductType
    manufacturer: str | None
    active_ingredient: str | None
    description: str | None
    default_egg_withdrawal_days: int
    default_meat_withdrawal_days: int
    is_active: bool
    is_vaccine: bool
    created_at: datetime
    updated_at: datetime


class HealthProductListResponse(BaseModel):
    """Paginated health-product listing."""

    items: list[HealthProductResponse]
    total: int
    offset: int
    limit: int
