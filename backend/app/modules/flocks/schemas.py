from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.modules.flocks.constants import (
    FlockProductionStage,
    FlockStatus,
    PopulationTransactionType,
)


MANUAL_POPULATION_TRANSACTION_TYPES = {
    PopulationTransactionType.TRANSFER_IN,
    PopulationTransactionType.TRANSFER_OUT,
    PopulationTransactionType.ADJUSTMENT_IN,
    PopulationTransactionType.ADJUSTMENT_OUT,
}


class FlockCreate(BaseModel):
    """Information required to register a flock."""

    house_id: UUID
    supplier_id: UUID | None = None
    flock_code: str = Field(
        min_length=2,
        max_length=30,
    )
    name: str = Field(
        min_length=2,
        max_length=120,
    )
    breed: str = Field(
        min_length=2,
        max_length=120,
    )
    arrival_date: date
    hatch_date: date | None = None
    age_at_arrival_days: int | None = Field(
        default=None,
        ge=0,
        le=5000,
    )
    initial_population: int = Field(
        gt=0,
        le=10_000_000,
    )
    purchase_cost: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        decimal_places=2,
    )
    production_stage: FlockProductionStage = FlockProductionStage.GROWING
    notes: str | None = None

    @field_validator("flock_code")
    @classmethod
    def normalize_flock_code(cls, value: str) -> str:
        normalized = value.strip().upper().replace(" ", "-")

        if not normalized:
            raise ValueError("Flock code cannot be empty.")

        return normalized

    @field_validator("name", "breed")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()

        if len(normalized) < 2:
            raise ValueError("The value must contain at least two characters.")

        return normalized

    @model_validator(mode="after")
    def validate_dates(self) -> "FlockCreate":
        if self.arrival_date > date.today():
            raise ValueError("Arrival date cannot be in the future.")

        if self.hatch_date is not None and self.hatch_date > self.arrival_date:
            raise ValueError("Hatch date cannot be after arrival date.")

        if self.hatch_date is not None:
            calculated_age = (self.arrival_date - self.hatch_date).days

            if (
                self.age_at_arrival_days is not None
                and self.age_at_arrival_days != calculated_age
            ):
                raise ValueError(
                    "Age at arrival does not match the hatch and arrival dates."
                )

        return self


class FlockUpdate(BaseModel):
    """Flock fields that may be updated."""

    house_id: UUID | None = None
    supplier_id: UUID | None = None
    flock_code: str | None = Field(
        default=None,
        min_length=2,
        max_length=30,
    )
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=120,
    )
    breed: str | None = Field(
        default=None,
        min_length=2,
        max_length=120,
    )
    purchase_cost: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
    )
    production_stage: FlockProductionStage | None = None
    status: FlockStatus | None = None
    notes: str | None = None

    @field_validator("flock_code")
    @classmethod
    def normalize_flock_code(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip().upper().replace(" ", "-")

        if not normalized:
            raise ValueError("Flock code cannot be empty.")

        return normalized

    @field_validator("name", "breed")
    @classmethod
    def normalize_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        if len(normalized) < 2:
            raise ValueError("The value must contain at least two characters.")

        return normalized


class PopulationTransactionCreate(BaseModel):
    """Manual flock-population movement."""

    transaction_date: date = Field(default_factory=date.today)
    transaction_type: PopulationTransactionType
    quantity: int = Field(
        gt=0,
        le=10_000_000,
    )
    description: str | None = None

    @field_validator("transaction_type")
    @classmethod
    def validate_transaction_type(
        cls,
        value: PopulationTransactionType,
    ) -> PopulationTransactionType:
        if value not in MANUAL_POPULATION_TRANSACTION_TYPES:
            raise ValueError(
                "Only transfer and adjustment transactions may be entered here."
            )

        return value

    @field_validator("transaction_date")
    @classmethod
    def validate_transaction_date(
        cls,
        value: date,
    ) -> date:
        if value > date.today():
            raise ValueError("Transaction date cannot be in the future.")

        return value


class PopulationTransactionResponse(BaseModel):
    """Population transaction returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    flock_id: UUID
    transaction_date: date
    transaction_type: PopulationTransactionType
    quantity: int
    signed_quantity: int
    source_type: str
    source_id: UUID | None
    description: str | None
    created_by: UUID
    reversed_transaction_id: UUID | None
    created_at: datetime


class PopulationTransactionListResponse(BaseModel):
    """Paginated population-transaction listing."""

    items: list[PopulationTransactionResponse]
    total: int
    offset: int
    limit: int


class FlockResponse(BaseModel):
    """Flock information returned by the API."""

    id: UUID
    farm_id: UUID
    house_id: UUID
    house_code: str
    house_name: str
    house_capacity: int
    supplier_id: UUID | None
    supplier_code: str | None
    supplier_name: str | None
    flock_code: str
    name: str
    breed: str
    arrival_date: date
    hatch_date: date | None
    age_at_arrival_days: int | None
    initial_population: int
    current_population: int
    purchase_cost: Decimal
    production_stage: FlockProductionStage
    status: FlockStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime


class FlockListResponse(BaseModel):
    """Paginated flock listing."""

    items: list[FlockResponse]
    total: int
    offset: int
    limit: int


class FlockPopulationSummaryResponse(BaseModel):
    """Current flock and poultry-house population summary."""

    flock_id: UUID
    flock_code: str
    house_id: UUID
    house_code: str
    initial_population: int
    current_population: int
    house_capacity: int
    house_occupancy: int
    available_house_capacity: int
