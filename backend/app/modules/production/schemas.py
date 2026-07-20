from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)

from app.modules.production.constants import (
    ProductionRecordStatus,
)


class DailyEggProductionCreate(BaseModel):
    """Information required to create a daily production draft."""

    flock_id: UUID
    production_date: date = Field(default_factory=date.today)

    morning_eggs: int = Field(default=0, ge=0)
    afternoon_eggs: int = Field(default=0, ge=0)
    evening_eggs: int = Field(default=0, ge=0)

    large_eggs: int = Field(default=0, ge=0)
    medium_eggs: int = Field(default=0, ge=0)
    small_eggs: int = Field(default=0, ge=0)
    damaged_eggs: int = Field(default=0, ge=0)
    rejected_eggs: int = Field(default=0, ge=0)

    notes: str | None = None

    @field_validator("production_date")
    @classmethod
    def validate_production_date(
        cls,
        value: date,
    ) -> date:
        if value > date.today():
            raise ValueError("Production date cannot be in the future.")

        return value

    @model_validator(mode="after")
    def validate_egg_totals(
        self,
    ) -> "DailyEggProductionCreate":
        total_collected = self.morning_eggs + self.afternoon_eggs + self.evening_eggs

        total_graded = (
            self.large_eggs
            + self.medium_eggs
            + self.small_eggs
            + self.damaged_eggs
            + self.rejected_eggs
        )

        if total_graded > total_collected:
            raise ValueError("Total graded eggs cannot exceed total collected eggs.")

        return self


class DailyEggProductionUpdate(BaseModel):
    """Egg-production fields that may be edited in a draft."""

    morning_eggs: int | None = Field(
        default=None,
        ge=0,
    )
    afternoon_eggs: int | None = Field(
        default=None,
        ge=0,
    )
    evening_eggs: int | None = Field(
        default=None,
        ge=0,
    )

    large_eggs: int | None = Field(
        default=None,
        ge=0,
    )
    medium_eggs: int | None = Field(
        default=None,
        ge=0,
    )
    small_eggs: int | None = Field(
        default=None,
        ge=0,
    )
    damaged_eggs: int | None = Field(
        default=None,
        ge=0,
    )
    rejected_eggs: int | None = Field(
        default=None,
        ge=0,
    )

    notes: str | None = None


class ProductionRejectionRequest(BaseModel):
    """Reason supplied when rejecting a production record."""

    reason: str = Field(
        min_length=5,
        max_length=1000,
    )

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        normalized = value.strip()

        if len(normalized) < 5:
            raise ValueError("Rejection reason must contain at least five characters.")

        return normalized


class DailyEggProductionResponse(BaseModel):
    """Complete daily egg-production API response."""

    id: UUID
    farm_id: UUID

    flock_id: UUID
    flock_code: str
    flock_name: str
    house_id: UUID
    house_code: str

    production_date: date
    birds_present: int

    morning_eggs: int
    afternoon_eggs: int
    evening_eggs: int
    total_collected: int

    large_eggs: int
    medium_eggs: int
    small_eggs: int
    damaged_eggs: int
    rejected_eggs: int

    total_graded: int
    saleable_eggs: int
    ungraded_eggs: int
    laying_percentage: Decimal

    status: ProductionRecordStatus
    notes: str | None
    rejection_reason: str | None
    revision_number: int

    recorded_by: UUID
    last_updated_by: UUID

    submitted_by: UUID | None
    submitted_at: datetime | None

    confirmed_by: UUID | None
    confirmed_at: datetime | None

    rejected_by: UUID | None
    rejected_at: datetime | None

    created_at: datetime
    updated_at: datetime


class DailyEggProductionListResponse(BaseModel):
    """Paginated daily egg-production listing."""

    items: list[DailyEggProductionResponse]
    total: int
    offset: int
    limit: int


class ProductionSummaryResponse(BaseModel):
    """Aggregated egg-production summary."""

    date_from: date
    date_to: date
    status: ProductionRecordStatus | None

    record_count: int
    bird_days: int

    morning_eggs: int
    afternoon_eggs: int
    evening_eggs: int
    total_collected: int

    large_eggs: int
    medium_eggs: int
    small_eggs: int
    damaged_eggs: int
    rejected_eggs: int

    saleable_eggs: int
    weighted_laying_percentage: Decimal
