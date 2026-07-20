from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.modules.health.schemas.incidents import (
    HealthIncidentResponse,
)
from app.modules.health.schemas.treatments import (
    TreatmentRecordResponse,
)
from app.modules.health.schemas.vaccinations import (
    VaccinationScheduleResponse,
)


class HealthSummaryResponse(BaseModel):
    """Current farm vaccination and health summary."""

    as_of_date: date
    scheduled_vaccinations: int
    due_vaccinations: int
    missed_vaccinations: int
    completed_vaccinations: int
    open_incidents: int
    incidents_under_treatment: int
    critical_incidents: int
    active_treatments: int
    planned_treatments: int
    active_egg_withdrawals: int
    active_meat_withdrawals: int


class FlockHealthHistoryResponse(BaseModel):
    """Complete health history for one flock."""

    flock_id: UUID
    flock_code: str
    flock_name: str
    vaccination_schedules: list[VaccinationScheduleResponse]
    health_incidents: list[HealthIncidentResponse]
    treatment_records: list[TreatmentRecordResponse]
