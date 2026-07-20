from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


class FarmSettingsCreate(BaseModel):
    """Optional settings supplied while creating a farm."""

    eggs_per_tray: int = Field(default=30, gt=0, le=100)
    low_production_threshold: Decimal = Field(
        default=Decimal("70.00"),
        ge=0,
        le=100,
        decimal_places=2,
    )
    mortality_alert_threshold: Decimal = Field(
        default=Decimal("1.00"),
        ge=0,
        le=100,
        decimal_places=2,
    )
    vaccination_reminder_days: int = Field(default=3, ge=0, le=365)
    session_timeout_minutes: int = Field(default=60, gt=0, le=1440)
    allow_negative_stock: bool = False
    allow_customer_credit: bool = True
    maximum_discount_percentage: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        le=100,
        decimal_places=2,
    )


class FarmSettingsUpdate(BaseModel):
    """Fields that can be changed in a farm's settings."""

    eggs_per_tray: int | None = Field(default=None, gt=0, le=100)
    low_production_threshold: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        decimal_places=2,
    )
    mortality_alert_threshold: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        decimal_places=2,
    )
    vaccination_reminder_days: int | None = Field(
        default=None,
        ge=0,
        le=365,
    )
    session_timeout_minutes: int | None = Field(
        default=None,
        gt=0,
        le=1440,
    )
    allow_negative_stock: bool | None = None
    allow_customer_credit: bool | None = None
    maximum_discount_percentage: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        decimal_places=2,
    )


class FarmSettingsResponse(BaseModel):
    """Farm-settings response returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    eggs_per_tray: int
    low_production_threshold: Decimal
    mortality_alert_threshold: Decimal
    vaccination_reminder_days: int
    session_timeout_minutes: int
    allow_negative_stock: bool
    allow_customer_credit: bool
    maximum_discount_percentage: Decimal
    created_at: datetime
    updated_at: datetime


class FarmCreate(BaseModel):
    """Information required to register a PoultryPulse farm."""

    farm_code: str = Field(min_length=2, max_length=30)
    name: str = Field(min_length=2, max_length=150)
    owner_name: str | None = Field(default=None, max_length=150)
    telephone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    district: str | None = Field(default=None, max_length=100)
    address: str | None = None
    logo_url: str | None = None
    timezone: str = Field(default="Africa/Kampala", max_length=50)
    currency_code: str = Field(default="UGX", min_length=3, max_length=3)
    settings: FarmSettingsCreate = Field(default_factory=FarmSettingsCreate)

    @field_validator("farm_code")
    @classmethod
    def normalize_farm_code(cls, value: str) -> str:
        normalized_value = value.strip().upper().replace(" ", "-")

        if not normalized_value:
            raise ValueError("Farm code cannot be empty.")

        return normalized_value

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized_value = value.strip()

        if len(normalized_value) < 2:
            raise ValueError("Farm name must contain at least two characters.")

        return normalized_value

    @field_validator("currency_code")
    @classmethod
    def normalize_currency_code(cls, value: str) -> str:
        return value.strip().upper()


class FarmUpdate(BaseModel):
    """Farm fields that can be changed after registration."""

    farm_code: str | None = Field(default=None, min_length=2, max_length=30)
    name: str | None = Field(default=None, min_length=2, max_length=150)
    owner_name: str | None = Field(default=None, max_length=150)
    telephone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    district: str | None = Field(default=None, max_length=100)
    address: str | None = None
    logo_url: str | None = None
    timezone: str | None = Field(default=None, max_length=50)
    currency_code: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
    )
    is_active: bool | None = None

    @field_validator("farm_code")
    @classmethod
    def normalize_farm_code(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized_value = value.strip().upper().replace(" ", "-")

        if not normalized_value:
            raise ValueError("Farm code cannot be empty.")

        return normalized_value

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized_value = value.strip()

        if len(normalized_value) < 2:
            raise ValueError("Farm name must contain at least two characters.")

        return normalized_value

    @field_validator("currency_code")
    @classmethod
    def normalize_currency_code(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return value.strip().upper()


class FarmResponse(BaseModel):
    """Complete farm response returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_code: str
    name: str
    owner_name: str | None
    telephone: str | None
    email: str | None
    district: str | None
    address: str | None
    logo_url: str | None
    timezone: str
    currency_code: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    settings: FarmSettingsResponse | None


class FarmListResponse(BaseModel):
    """Paginated response containing registered farms."""

    items: list[FarmResponse]
    total: int
    offset: int
    limit: int
