from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.health.constants import (
    VaccinationRoute,
    VaccinationScheduleStatus,
)


def _normalize_optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


class VaccinationScheduleCreate(BaseModel):
    """Information required to schedule a vaccination."""

    flock_id: UUID
    product_id: UUID | None = None
    vaccine_name: str = Field(min_length=2, max_length=150)
    disease_target: str | None = Field(default=None, max_length=200)
    scheduled_date: date
    reminder_date: date | None = None
    target_age_days: int | None = Field(default=None, ge=0, le=5000)
    planned_dose: str | None = Field(default=None, max_length=100)
    route: VaccinationRoute = VaccinationRoute.OTHER
    notes: str | None = None

    @field_validator("vaccine_name")
    @classmethod
    def normalize_vaccine_name(cls, value: str) -> str:
        normalized = value.strip()

        if len(normalized) < 2:
            raise ValueError("Vaccine name must contain at least two characters.")

        return normalized

    @field_validator(
        "disease_target",
        "planned_dose",
        "notes",
    )
    @classmethod
    def normalize_optional_fields(
        cls,
        value: str | None,
    ) -> str | None:
        return _normalize_optional_text(value)

    @model_validator(mode="after")
    def validate_reminder_date(
        self,
    ) -> "VaccinationScheduleCreate":
        if self.reminder_date is not None and self.reminder_date > self.scheduled_date:
            raise ValueError("Reminder date cannot be after the scheduled date.")

        return self


class VaccinationScheduleUpdate(BaseModel):
    """Vaccination fields that may be updated."""

    product_id: UUID | None = None
    vaccine_name: str | None = Field(default=None, min_length=2, max_length=150)
    disease_target: str | None = Field(default=None, max_length=200)
    scheduled_date: date | None = None
    reminder_date: date | None = None
    target_age_days: int | None = Field(default=None, ge=0, le=5000)
    planned_dose: str | None = Field(default=None, max_length=100)
    route: VaccinationRoute | None = None
    notes: str | None = None

    @field_validator("vaccine_name")
    @classmethod
    def normalize_vaccine_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        if len(normalized) < 2:
            raise ValueError("Vaccine name must contain at least two characters.")

        return normalized

    @field_validator(
        "disease_target",
        "planned_dose",
        "notes",
    )
    @classmethod
    def normalize_optional_fields(
        cls,
        value: str | None,
    ) -> str | None:
        return _normalize_optional_text(value)


class VaccinationAdministrationCreate(BaseModel):
    """Information recorded when a vaccination is completed."""

    administration_date: date = Field(default_factory=date.today)
    product_id: UUID | None = None
    birds_vaccinated: int = Field(gt=0, le=10_000_000)
    dose: str | None = Field(default=None, max_length=100)
    route: VaccinationRoute | None = None
    batch_number: str | None = Field(default=None, max_length=100)
    expiry_date: date | None = None
    administered_by_name: str | None = Field(default=None, max_length=150)
    veterinarian_name: str | None = Field(default=None, max_length=150)
    notes: str | None = None

    @field_validator("administration_date")
    @classmethod
    def validate_administration_date(
        cls,
        value: date,
    ) -> date:
        if value > date.today():
            raise ValueError("Administration date cannot be in the future.")

        return value

    @field_validator(
        "dose",
        "batch_number",
        "administered_by_name",
        "veterinarian_name",
        "notes",
    )
    @classmethod
    def normalize_optional_fields(
        cls,
        value: str | None,
    ) -> str | None:
        return _normalize_optional_text(value)

    @model_validator(mode="after")
    def validate_expiry_date(
        self,
    ) -> "VaccinationAdministrationCreate":
        if self.expiry_date is not None and self.expiry_date < self.administration_date:
            raise ValueError("The vaccine was expired on the administration date.")

        return self


class VaccinationCancellationRequest(BaseModel):
    """Reason supplied when cancelling a vaccination."""

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


class VaccinationAdministrationResponse(BaseModel):
    """Completed vaccination administration."""

    id: UUID
    farm_id: UUID
    schedule_id: UUID
    flock_id: UUID
    product_id: UUID | None
    product_code: str | None
    product_name: str | None
    administration_date: date
    birds_vaccinated: int
    dose: str | None
    route: VaccinationRoute
    batch_number: str | None
    expiry_date: date | None
    administered_by_name: str | None
    veterinarian_name: str | None
    notes: str | None
    recorded_by: UUID
    created_at: datetime


class VaccinationScheduleResponse(BaseModel):
    """Vaccination schedule returned by the API."""

    id: UUID
    farm_id: UUID
    flock_id: UUID
    flock_code: str
    flock_name: str
    house_id: UUID
    house_code: str
    house_name: str
    product_id: UUID | None
    product_code: str | None
    vaccine_name: str
    disease_target: str | None
    scheduled_date: date
    reminder_date: date | None
    target_age_days: int | None
    planned_dose: str | None
    route: VaccinationRoute
    status: VaccinationScheduleStatus
    days_until_due: int
    reminder_active: bool
    is_overdue: bool
    notes: str | None
    created_by: UUID
    cancelled_by: UUID | None
    cancelled_at: datetime | None
    cancellation_reason: str | None
    administration: VaccinationAdministrationResponse | None
    created_at: datetime
    updated_at: datetime


class VaccinationScheduleListResponse(BaseModel):
    """Paginated vaccination-schedule listing."""

    items: list[VaccinationScheduleResponse]
    total: int
    offset: int
    limit: int


class VaccinationReminderSummaryResponse(BaseModel):
    """Vaccinations requiring attention."""

    as_of_date: date
    upcoming_days: int
    due_today: int
    upcoming: int
    missed: int
    completed: int
    cancelled: int
    items: list[VaccinationScheduleResponse]
