from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.modules.houses.constants import PoultryHouseStatus


class PoultryHouseCreate(BaseModel):
    """Information required to register a poultry house."""

    house_code: str = Field(
        min_length=2,
        max_length=30,
    )

    name: str = Field(
        min_length=2,
        max_length=100,
    )

    capacity: int = Field(
        gt=0,
        le=10_000_000,
    )

    location: str | None = Field(
        default=None,
        max_length=255,
    )

    description: str | None = None

    status: PoultryHouseStatus = PoultryHouseStatus.ACTIVE

    @field_validator("house_code")
    @classmethod
    def normalize_house_code(cls, value: str) -> str:
        normalized = value.strip().upper().replace(" ", "-")

        if not normalized:
            raise ValueError("House code cannot be empty.")

        return normalized

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()

        if len(normalized) < 2:
            raise ValueError("House name must contain at least two characters.")

        return normalized

    @field_validator("location")
    @classmethod
    def normalize_location(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None


class PoultryHouseUpdate(BaseModel):
    """Poultry-house fields that may be updated."""

    house_code: str | None = Field(
        default=None,
        min_length=2,
        max_length=30,
    )

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    capacity: int | None = Field(
        default=None,
        gt=0,
        le=10_000_000,
    )

    location: str | None = Field(
        default=None,
        max_length=255,
    )

    description: str | None = None

    status: PoultryHouseStatus | None = None

    @field_validator("house_code")
    @classmethod
    def normalize_house_code(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip().upper().replace(" ", "-")

        if not normalized:
            raise ValueError("House code cannot be empty.")

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
            raise ValueError("House name must contain at least two characters.")

        return normalized

    @field_validator("location")
    @classmethod
    def normalize_location(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None


class PoultryHouseResponse(BaseModel):
    """Poultry-house information returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    house_code: str
    name: str
    capacity: int
    location: str | None
    description: str | None
    status: PoultryHouseStatus
    created_at: datetime
    updated_at: datetime


class PoultryHouseListResponse(BaseModel):
    """Paginated poultry-house listing."""

    items: list[PoultryHouseResponse]
    total: int
    offset: int
    limit: int
