from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.health.constants import (
    TreatmentStatus,
    VaccinationRoute,
)


def _normalize_optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


class TreatmentRecordCreate(BaseModel):
    """Information required to record flock treatment."""

    flock_id: UUID
    health_incident_id: UUID | None = None
    product_id: UUID | None = None
    product_name: str | None = Field(default=None, max_length=150)
    treatment_date: date = Field(default_factory=date.today)
    end_date: date | None = None
    birds_treated: int = Field(gt=0, le=10_000_000)
    dose: str | None = Field(default=None, max_length=100)
    route: VaccinationRoute = VaccinationRoute.OTHER
    purpose: str | None = Field(default=None, max_length=250)
    prescribed_by: str | None = Field(default=None, max_length=150)
    treatment_cost: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=14,
        decimal_places=2,
    )
    egg_withdrawal_days: int | None = Field(default=None, ge=0, le=365)
    meat_withdrawal_days: int | None = Field(default=None, ge=0, le=365)
    notes: str | None = None

    @field_validator(
        "product_name",
        "dose",
        "purpose",
        "prescribed_by",
        "notes",
    )
    @classmethod
    def normalize_optional_fields(
        cls,
        value: str | None,
    ) -> str | None:
        return _normalize_optional_text(value)

    @model_validator(mode="after")
    def validate_treatment(
        self,
    ) -> "TreatmentRecordCreate":
        if self.product_id is None and self.product_name is None:
            raise ValueError("Provide either a health product or a product name.")

        if self.end_date is not None and self.end_date < self.treatment_date:
            raise ValueError("Treatment end date cannot be before the treatment date.")

        return self


class TreatmentCompletionRequest(BaseModel):
    """Information required to complete treatment."""

    end_date: date = Field(default_factory=date.today)
    notes: str | None = None

    @field_validator("end_date")
    @classmethod
    def validate_end_date(
        cls,
        value: date,
    ) -> date:
        if value > date.today():
            raise ValueError("Treatment completion date cannot be in the future.")

        return value

    @field_validator("notes")
    @classmethod
    def normalize_notes(
        cls,
        value: str | None,
    ) -> str | None:
        return _normalize_optional_text(value)


class TreatmentCancellationRequest(BaseModel):
    """Reason supplied when cancelling treatment."""

    reason: str = Field(min_length=5, max_length=1000)

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        normalized = value.strip()

        if len(normalized) < 5:
            raise ValueError(
                "Cancellation reason must contain at least five characters."
            )

        return normalized


class TreatmentRecordResponse(BaseModel):
    """Complete flock treatment record."""

    id: UUID
    farm_id: UUID
    flock_id: UUID
    flock_code: str
    flock_name: str
    health_incident_id: UUID | None
    incident_code: str | None
    product_id: UUID | None
    product_code: str | None
    product_name: str
    treatment_date: date
    end_date: date | None
    birds_treated: int
    dose: str | None
    route: VaccinationRoute
    purpose: str | None
    prescribed_by: str | None
    treatment_cost: Decimal
    egg_withdrawal_days: int
    meat_withdrawal_days: int
    egg_withdrawal_until: date | None
    meat_withdrawal_until: date | None
    is_egg_withdrawal_active: bool
    is_meat_withdrawal_active: bool
    status: TreatmentStatus
    notes: str | None
    recorded_by: UUID
    completed_by: UUID | None
    completed_at: datetime | None
    is_completed: bool
    created_at: datetime
    updated_at: datetime


class TreatmentRecordListResponse(BaseModel):
    """Paginated treatment-record listing."""

    items: list[TreatmentRecordResponse]
    total: int
    offset: int
    limit: int
