from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)

from app.modules.bird_losses.constants import (
    BirdDisposalMethod,
    BirdLossReason,
    BirdLossRecordStatus,
    BirdLossType,
)


class BirdLossCreate(BaseModel):
    """Information required to record mortality or culling."""

    flock_id: UUID
    loss_date: date = Field(default_factory=date.today)
    loss_type: BirdLossType
    quantity: int = Field(
        gt=0,
        le=10_000_000,
    )
    reason_category: BirdLossReason = BirdLossReason.UNKNOWN
    cause_details: str | None = None
    disposal_method: BirdDisposalMethod = BirdDisposalMethod.NOT_RECORDED
    disposal_details: str | None = None
    location: str | None = Field(
        default=None,
        max_length=150,
    )
    reference: str | None = Field(
        default=None,
        max_length=100,
    )
    notes: str | None = None

    @field_validator("loss_date")
    @classmethod
    def validate_loss_date(
        cls,
        value: date,
    ) -> date:
        if value > date.today():
            raise ValueError("Bird-loss date cannot be in the future.")

        return value

    @field_validator(
        "cause_details",
        "disposal_details",
        "location",
        "reference",
        "notes",
    )
    @classmethod
    def normalize_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None


class BirdLossReversalCreate(BaseModel):
    """Information required to reverse a loss record."""

    reversal_date: date = Field(default_factory=date.today)
    reason: str = Field(
        min_length=5,
        max_length=1000,
    )

    @field_validator("reversal_date")
    @classmethod
    def validate_reversal_date(
        cls,
        value: date,
    ) -> date:
        if value > date.today():
            raise ValueError("Reversal date cannot be in the future.")

        return value

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        normalized = value.strip()

        if len(normalized) < 5:
            raise ValueError("Reversal reason must contain at least five characters.")

        return normalized


class BirdLossResponse(BaseModel):
    """Complete mortality or culling record."""

    id: UUID
    farm_id: UUID

    flock_id: UUID
    flock_code: str
    flock_name: str

    house_id: UUID
    house_code: str
    house_name: str

    loss_date: date
    loss_type: BirdLossType
    quantity: int

    reason_category: BirdLossReason
    cause_details: str | None

    disposal_method: BirdDisposalMethod
    disposal_details: str | None

    location: str | None
    reference: str | None
    notes: str | None

    population_before: int
    population_after: int
    current_population: int
    loss_percentage: Decimal

    daily_mortality_quantity: int
    daily_mortality_percentage: Decimal
    mortality_threshold_percentage: Decimal
    mortality_alert: bool

    status: BirdLossRecordStatus
    is_reversed: bool

    population_transaction_id: UUID
    reversal_population_transaction_id: UUID | None

    recorded_by: UUID
    reversed_by: UUID | None
    reversed_at: datetime | None
    reversal_reason: str | None

    created_at: datetime
    updated_at: datetime


class BirdLossListResponse(BaseModel):
    """Paginated mortality and culling listing."""

    items: list[BirdLossResponse]
    total: int
    offset: int
    limit: int


class BirdLossSummaryResponse(BaseModel):
    """Aggregated mortality and culling statistics."""

    date_from: date
    date_to: date
    flock_id: UUID | None

    active_record_count: int
    reversed_record_count: int

    mortality_quantity: int
    culling_quantity: int
    total_loss_quantity: int

    average_incident_loss_percentage: Decimal
    maximum_incident_loss_percentage: Decimal

    mortality_threshold_percentage: Decimal
    high_mortality_incidents: int

    current_flock_population: int | None
