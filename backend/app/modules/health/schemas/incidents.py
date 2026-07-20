from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.modules.health.constants import (
    HealthIncidentSeverity,
    HealthIncidentStatus,
)


def _normalize_optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


class HealthIncidentCreate(BaseModel):
    """Information required to report a health incident."""

    flock_id: UUID
    incident_code: str = Field(min_length=2, max_length=40)
    incident_date: date = Field(default_factory=date.today)
    severity: HealthIncidentSeverity = HealthIncidentSeverity.MODERATE
    affected_birds: int = Field(gt=0, le=10_000_000)
    symptoms: str = Field(min_length=3, max_length=5000)
    suspected_cause: str | None = None
    diagnosis: str | None = None
    veterinarian_name: str | None = Field(default=None, max_length=150)
    isolation_required: bool = False
    isolation_details: str | None = None
    notes: str | None = None

    @field_validator("incident_code")
    @classmethod
    def normalize_incident_code(cls, value: str) -> str:
        normalized = value.strip().upper().replace(" ", "-")

        if len(normalized) < 2:
            raise ValueError("Incident code must contain at least two characters.")

        return normalized

    @field_validator("incident_date")
    @classmethod
    def validate_incident_date(
        cls,
        value: date,
    ) -> date:
        if value > date.today():
            raise ValueError("Health incident date cannot be in the future.")

        return value

    @field_validator("symptoms")
    @classmethod
    def normalize_symptoms(cls, value: str) -> str:
        normalized = value.strip()

        if len(normalized) < 3:
            raise ValueError("Symptoms must contain at least three characters.")

        return normalized

    @field_validator(
        "suspected_cause",
        "diagnosis",
        "veterinarian_name",
        "isolation_details",
        "notes",
    )
    @classmethod
    def normalize_optional_fields(
        cls,
        value: str | None,
    ) -> str | None:
        return _normalize_optional_text(value)


class HealthIncidentUpdate(BaseModel):
    """Health-incident fields that may be updated."""

    severity: HealthIncidentSeverity | None = None
    affected_birds: int | None = Field(default=None, gt=0, le=10_000_000)
    symptoms: str | None = Field(default=None, min_length=3, max_length=5000)
    suspected_cause: str | None = None
    diagnosis: str | None = None
    veterinarian_name: str | None = Field(default=None, max_length=150)
    isolation_required: bool | None = None
    isolation_details: str | None = None
    notes: str | None = None
    status: HealthIncidentStatus | None = None

    @field_validator("symptoms")
    @classmethod
    def normalize_symptoms(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        if len(normalized) < 3:
            raise ValueError("Symptoms must contain at least three characters.")

        return normalized

    @field_validator(
        "suspected_cause",
        "diagnosis",
        "veterinarian_name",
        "isolation_details",
        "notes",
    )
    @classmethod
    def normalize_optional_fields(
        cls,
        value: str | None,
    ) -> str | None:
        return _normalize_optional_text(value)


class HealthIncidentResolutionRequest(BaseModel):
    """Information required to resolve an incident."""

    resolution_date: date = Field(default_factory=date.today)
    resolution_notes: str = Field(min_length=5, max_length=5000)

    @field_validator("resolution_date")
    @classmethod
    def validate_resolution_date(
        cls,
        value: date,
    ) -> date:
        if value > date.today():
            raise ValueError("Resolution date cannot be in the future.")

        return value

    @field_validator("resolution_notes")
    @classmethod
    def normalize_resolution_notes(cls, value: str) -> str:
        normalized = value.strip()

        if len(normalized) < 5:
            raise ValueError("Resolution notes must contain at least five characters.")

        return normalized


class HealthIncidentResponse(BaseModel):
    """Complete flock health incident."""

    id: UUID
    farm_id: UUID
    flock_id: UUID
    flock_code: str
    flock_name: str
    house_id: UUID
    house_code: str
    incident_code: str
    incident_date: date
    severity: HealthIncidentSeverity
    status: HealthIncidentStatus
    affected_birds: int
    symptoms: str
    suspected_cause: str | None
    diagnosis: str | None
    veterinarian_name: str | None
    isolation_required: bool
    isolation_details: str | None
    notes: str | None
    resolution_date: date | None
    resolution_notes: str | None
    recorded_by: UUID
    resolved_by: UUID | None
    is_resolved: bool
    treatment_count: int
    created_at: datetime
    updated_at: datetime


class HealthIncidentListResponse(BaseModel):
    """Paginated health-incident listing."""

    items: list[HealthIncidentResponse]
    total: int
    offset: int
    limit: int
