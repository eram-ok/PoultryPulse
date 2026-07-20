from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_database_session
from app.modules.auth.dependencies import require_permissions
from app.modules.health.constants import (
    HealthIncidentSeverity,
    HealthIncidentStatus,
    HealthProductType,
    TreatmentStatus,
    VaccinationScheduleStatus,
)
from app.modules.health.models import (
    HealthIncident,
    TreatmentRecord,
    VaccinationAdministration,
    VaccinationSchedule,
)
from app.modules.health.schemas import (
    FlockHealthHistoryResponse,
    HealthIncidentCreate,
    HealthIncidentListResponse,
    HealthIncidentResolutionRequest,
    HealthIncidentResponse,
    HealthIncidentUpdate,
    HealthProductCreate,
    HealthProductListResponse,
    HealthProductResponse,
    HealthProductUpdate,
    HealthSummaryResponse,
    TreatmentCancellationRequest,
    TreatmentCompletionRequest,
    TreatmentRecordCreate,
    TreatmentRecordListResponse,
    TreatmentRecordResponse,
    VaccinationAdministrationCreate,
    VaccinationAdministrationResponse,
    VaccinationCancellationRequest,
    VaccinationReminderSummaryResponse,
    VaccinationScheduleCreate,
    VaccinationScheduleListResponse,
    VaccinationScheduleResponse,
    VaccinationScheduleUpdate,
)
from app.modules.health.service import HealthService
from app.modules.users.models import User


router = APIRouter(
    prefix="/health",
    tags=["Vaccination and Health"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


def build_administration_response(
    administration: VaccinationAdministration,
) -> VaccinationAdministrationResponse:
    return VaccinationAdministrationResponse(
        id=administration.id,
        farm_id=administration.farm_id,
        schedule_id=administration.schedule_id,
        flock_id=administration.flock_id,
        product_id=administration.product_id,
        product_code=(
            administration.product.product_code
            if administration.product is not None
            else None
        ),
        product_name=(
            administration.product.name if administration.product is not None else None
        ),
        administration_date=(administration.administration_date),
        birds_vaccinated=(administration.birds_vaccinated),
        dose=administration.dose,
        route=administration.route,
        batch_number=administration.batch_number,
        expiry_date=administration.expiry_date,
        administered_by_name=(administration.administered_by_name),
        veterinarian_name=(administration.veterinarian_name),
        notes=administration.notes,
        recorded_by=administration.recorded_by,
        created_at=administration.created_at,
    )


def build_schedule_response(
    schedule: VaccinationSchedule,
) -> VaccinationScheduleResponse:
    pending_statuses = {
        VaccinationScheduleStatus.SCHEDULED.value,
        VaccinationScheduleStatus.DUE.value,
        VaccinationScheduleStatus.MISSED.value,
    }
    reminder_active = schedule.status in pending_statuses and (
        schedule.reminder_date is None or schedule.reminder_date <= date.today()
    )

    return VaccinationScheduleResponse(
        id=schedule.id,
        farm_id=schedule.farm_id,
        flock_id=schedule.flock_id,
        flock_code=schedule.flock.flock_code,
        flock_name=schedule.flock.name,
        house_id=schedule.flock.house_id,
        house_code=schedule.flock.house.house_code,
        house_name=schedule.flock.house.name,
        product_id=schedule.product_id,
        product_code=(
            schedule.product.product_code if schedule.product is not None else None
        ),
        vaccine_name=schedule.vaccine_name,
        disease_target=schedule.disease_target,
        scheduled_date=schedule.scheduled_date,
        reminder_date=schedule.reminder_date,
        target_age_days=schedule.target_age_days,
        planned_dose=schedule.planned_dose,
        route=schedule.route,
        status=schedule.status,
        days_until_due=(schedule.scheduled_date - date.today()).days,
        reminder_active=reminder_active,
        is_overdue=schedule.is_overdue,
        notes=schedule.notes,
        created_by=schedule.created_by,
        cancelled_by=schedule.cancelled_by,
        cancelled_at=schedule.cancelled_at,
        cancellation_reason=(schedule.cancellation_reason),
        administration=(
            build_administration_response(schedule.administration)
            if schedule.administration is not None
            else None
        ),
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


def build_incident_response(
    incident: HealthIncident,
) -> HealthIncidentResponse:
    return HealthIncidentResponse(
        id=incident.id,
        farm_id=incident.farm_id,
        flock_id=incident.flock_id,
        flock_code=incident.flock.flock_code,
        flock_name=incident.flock.name,
        house_id=incident.flock.house_id,
        house_code=incident.flock.house.house_code,
        incident_code=incident.incident_code,
        incident_date=incident.incident_date,
        severity=incident.severity,
        status=incident.status,
        affected_birds=incident.affected_birds,
        symptoms=incident.symptoms,
        suspected_cause=incident.suspected_cause,
        diagnosis=incident.diagnosis,
        veterinarian_name=incident.veterinarian_name,
        isolation_required=incident.isolation_required,
        isolation_details=incident.isolation_details,
        notes=incident.notes,
        resolution_date=incident.resolution_date,
        resolution_notes=incident.resolution_notes,
        recorded_by=incident.recorded_by,
        resolved_by=incident.resolved_by,
        is_resolved=incident.is_resolved,
        treatment_count=len(incident.treatments),
        created_at=incident.created_at,
        updated_at=incident.updated_at,
    )


def build_treatment_response(
    treatment: TreatmentRecord,
) -> TreatmentRecordResponse:
    return TreatmentRecordResponse(
        id=treatment.id,
        farm_id=treatment.farm_id,
        flock_id=treatment.flock_id,
        flock_code=treatment.flock.flock_code,
        flock_name=treatment.flock.name,
        health_incident_id=(treatment.health_incident_id),
        incident_code=(
            treatment.health_incident.incident_code
            if treatment.health_incident is not None
            else None
        ),
        product_id=treatment.product_id,
        product_code=(
            treatment.product.product_code if treatment.product is not None else None
        ),
        product_name=treatment.product_name,
        treatment_date=treatment.treatment_date,
        end_date=treatment.end_date,
        birds_treated=treatment.birds_treated,
        dose=treatment.dose,
        route=treatment.route,
        purpose=treatment.purpose,
        prescribed_by=treatment.prescribed_by,
        treatment_cost=treatment.treatment_cost,
        egg_withdrawal_days=(treatment.egg_withdrawal_days),
        meat_withdrawal_days=(treatment.meat_withdrawal_days),
        egg_withdrawal_until=(treatment.egg_withdrawal_until),
        meat_withdrawal_until=(treatment.meat_withdrawal_until),
        is_egg_withdrawal_active=(treatment.is_egg_withdrawal_active),
        is_meat_withdrawal_active=(treatment.is_meat_withdrawal_active),
        status=treatment.status,
        notes=treatment.notes,
        recorded_by=treatment.recorded_by,
        completed_by=treatment.completed_by,
        completed_at=treatment.completed_at,
        is_completed=treatment.is_completed,
        created_at=treatment.created_at,
        updated_at=treatment.updated_at,
    )


@router.post(
    "/products",
    response_model=HealthProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_health_product(
    payload: HealthProductCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.products.manage")),
    ],
) -> HealthProductResponse:
    product = HealthService(database_session).create_product(
        current_user.farm_id,
        payload,
    )
    return HealthProductResponse.model_validate(product)


@router.get(
    "/products",
    response_model=HealthProductListResponse,
)
def list_health_products(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.view")),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    product_type: HealthProductType | None = None,
    is_active: bool | None = None,
    search: Annotated[
        str | None,
        Query(min_length=1, max_length=100),
    ] = None,
) -> HealthProductListResponse:
    products, total = HealthService(database_session).list_products(
        current_user.farm_id,
        offset=offset,
        limit=limit,
        product_type=(product_type.value if product_type is not None else None),
        is_active=is_active,
        search=search,
    )
    return HealthProductListResponse(
        items=[HealthProductResponse.model_validate(item) for item in products],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/products/{product_id}",
    response_model=HealthProductResponse,
)
def get_health_product(
    product_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.view")),
    ],
) -> HealthProductResponse:
    product = HealthService(database_session).get_product(
        current_user.farm_id,
        product_id,
    )
    return HealthProductResponse.model_validate(product)


@router.patch(
    "/products/{product_id}",
    response_model=HealthProductResponse,
)
def update_health_product(
    product_id: UUID,
    payload: HealthProductUpdate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.products.manage")),
    ],
) -> HealthProductResponse:
    product = HealthService(database_session).update_product(
        current_user.farm_id,
        product_id,
        payload,
    )
    return HealthProductResponse.model_validate(product)


@router.post(
    "/products/{product_id}/activate",
    response_model=HealthProductResponse,
)
def activate_health_product(
    product_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.products.manage")),
    ],
) -> HealthProductResponse:
    product = HealthService(database_session).set_product_active_status(
        current_user.farm_id,
        product_id,
        is_active=True,
    )
    return HealthProductResponse.model_validate(product)


@router.post(
    "/products/{product_id}/deactivate",
    response_model=HealthProductResponse,
)
def deactivate_health_product(
    product_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.products.manage")),
    ],
) -> HealthProductResponse:
    product = HealthService(database_session).set_product_active_status(
        current_user.farm_id,
        product_id,
        is_active=False,
    )
    return HealthProductResponse.model_validate(product)


@router.get(
    "/vaccinations/reminders",
    response_model=VaccinationReminderSummaryResponse,
)
def get_vaccination_reminders(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.view")),
    ],
    upcoming_days: Annotated[
        int,
        Query(ge=0, le=90),
    ] = 7,
) -> VaccinationReminderSummaryResponse:
    schedules, counts = HealthService(database_session).get_reminders(
        current_user.farm_id,
        upcoming_days=upcoming_days,
    )
    return VaccinationReminderSummaryResponse(
        as_of_date=date.today(),
        upcoming_days=upcoming_days,
        due_today=counts.get(
            VaccinationScheduleStatus.DUE.value,
            0,
        ),
        upcoming=counts.get(
            VaccinationScheduleStatus.SCHEDULED.value,
            0,
        ),
        missed=counts.get(
            VaccinationScheduleStatus.MISSED.value,
            0,
        ),
        completed=counts.get(
            VaccinationScheduleStatus.COMPLETED.value,
            0,
        ),
        cancelled=counts.get(
            VaccinationScheduleStatus.CANCELLED.value,
            0,
        ),
        items=[build_schedule_response(item) for item in schedules],
    )


@router.post(
    "/vaccinations",
    response_model=VaccinationScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_vaccination_schedule(
    payload: VaccinationScheduleCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.vaccinations.schedule")),
    ],
) -> VaccinationScheduleResponse:
    schedule = HealthService(database_session).create_schedule(
        current_user.farm_id,
        current_user.id,
        payload,
    )
    return build_schedule_response(schedule)


@router.get(
    "/vaccinations",
    response_model=VaccinationScheduleListResponse,
)
def list_vaccination_schedules(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.view")),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    date_from: date | None = None,
    date_to: date | None = None,
    flock_id: UUID | None = None,
    product_id: UUID | None = None,
    schedule_status: Annotated[
        VaccinationScheduleStatus | None,
        Query(alias="status"),
    ] = None,
    search: Annotated[
        str | None,
        Query(min_length=1, max_length=100),
    ] = None,
) -> VaccinationScheduleListResponse:
    schedules, total = HealthService(database_session).list_schedules(
        current_user.farm_id,
        offset=offset,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        flock_id=flock_id,
        product_id=product_id,
        schedule_status=(
            schedule_status.value if schedule_status is not None else None
        ),
        search=search,
    )
    return VaccinationScheduleListResponse(
        items=[build_schedule_response(item) for item in schedules],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/vaccinations/{schedule_id}",
    response_model=VaccinationScheduleResponse,
)
def get_vaccination_schedule(
    schedule_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.view")),
    ],
) -> VaccinationScheduleResponse:
    schedule = HealthService(database_session).get_schedule(
        current_user.farm_id,
        schedule_id,
    )
    return build_schedule_response(schedule)


@router.patch(
    "/vaccinations/{schedule_id}",
    response_model=VaccinationScheduleResponse,
)
def update_vaccination_schedule(
    schedule_id: UUID,
    payload: VaccinationScheduleUpdate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.vaccinations.schedule")),
    ],
) -> VaccinationScheduleResponse:
    schedule = HealthService(database_session).update_schedule(
        current_user.farm_id,
        schedule_id,
        payload,
    )
    return build_schedule_response(schedule)


@router.post(
    "/vaccinations/{schedule_id}/complete",
    response_model=VaccinationScheduleResponse,
)
def complete_vaccination_schedule(
    schedule_id: UUID,
    payload: VaccinationAdministrationCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.vaccinations.complete")),
    ],
) -> VaccinationScheduleResponse:
    schedule = HealthService(database_session).complete_schedule(
        current_user.farm_id,
        schedule_id,
        current_user.id,
        payload,
    )
    return build_schedule_response(schedule)


@router.post(
    "/vaccinations/{schedule_id}/cancel",
    response_model=VaccinationScheduleResponse,
)
def cancel_vaccination_schedule(
    schedule_id: UUID,
    payload: VaccinationCancellationRequest,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.vaccinations.schedule")),
    ],
) -> VaccinationScheduleResponse:
    schedule = HealthService(database_session).cancel_schedule(
        current_user.farm_id,
        schedule_id,
        current_user.id,
        payload.reason,
    )
    return build_schedule_response(schedule)


@router.post(
    "/incidents",
    response_model=HealthIncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_health_incident(
    payload: HealthIncidentCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.incidents.manage")),
    ],
) -> HealthIncidentResponse:
    incident = HealthService(database_session).create_incident(
        current_user.farm_id,
        current_user.id,
        payload,
    )
    return build_incident_response(incident)


@router.get(
    "/incidents",
    response_model=HealthIncidentListResponse,
)
def list_health_incidents(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.view")),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    date_from: date | None = None,
    date_to: date | None = None,
    flock_id: UUID | None = None,
    severity: HealthIncidentSeverity | None = None,
    incident_status: Annotated[
        HealthIncidentStatus | None,
        Query(alias="status"),
    ] = None,
    search: Annotated[
        str | None,
        Query(min_length=1, max_length=100),
    ] = None,
) -> HealthIncidentListResponse:
    incidents, total = HealthService(database_session).list_incidents(
        current_user.farm_id,
        offset=offset,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        flock_id=flock_id,
        severity=(severity.value if severity is not None else None),
        incident_status=(
            incident_status.value if incident_status is not None else None
        ),
        search=search,
    )
    return HealthIncidentListResponse(
        items=[build_incident_response(item) for item in incidents],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/incidents/{incident_id}",
    response_model=HealthIncidentResponse,
)
def get_health_incident(
    incident_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.view")),
    ],
) -> HealthIncidentResponse:
    incident = HealthService(database_session).get_incident(
        current_user.farm_id,
        incident_id,
    )
    return build_incident_response(incident)


@router.patch(
    "/incidents/{incident_id}",
    response_model=HealthIncidentResponse,
)
def update_health_incident(
    incident_id: UUID,
    payload: HealthIncidentUpdate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.incidents.manage")),
    ],
) -> HealthIncidentResponse:
    incident = HealthService(database_session).update_incident(
        current_user.farm_id,
        incident_id,
        payload,
    )
    return build_incident_response(incident)


@router.post(
    "/incidents/{incident_id}/resolve",
    response_model=HealthIncidentResponse,
)
def resolve_health_incident(
    incident_id: UUID,
    payload: HealthIncidentResolutionRequest,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.resolve")),
    ],
) -> HealthIncidentResponse:
    incident = HealthService(database_session).resolve_incident(
        current_user.farm_id,
        incident_id,
        current_user.id,
        resolution_date=payload.resolution_date,
        resolution_notes=payload.resolution_notes,
    )
    return build_incident_response(incident)


@router.get(
    "/withdrawals",
    response_model=TreatmentRecordListResponse,
)
def list_active_withdrawals(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.view")),
    ],
    flock_id: UUID | None = None,
) -> TreatmentRecordListResponse:
    treatments, total = HealthService(database_session).list_treatments(
        current_user.farm_id,
        offset=0,
        limit=100,
        date_from=None,
        date_to=None,
        flock_id=flock_id,
        health_incident_id=None,
        product_id=None,
        treatment_status=None,
        active_withdrawal_only=True,
        search=None,
    )
    return TreatmentRecordListResponse(
        items=[build_treatment_response(item) for item in treatments],
        total=total,
        offset=0,
        limit=100,
    )


@router.post(
    "/treatments",
    response_model=TreatmentRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_treatment_record(
    payload: TreatmentRecordCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.treatments.manage")),
    ],
) -> TreatmentRecordResponse:
    treatment = HealthService(database_session).create_treatment(
        current_user.farm_id,
        current_user.id,
        payload,
    )
    return build_treatment_response(treatment)


@router.get(
    "/treatments",
    response_model=TreatmentRecordListResponse,
)
def list_treatment_records(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.view")),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    date_from: date | None = None,
    date_to: date | None = None,
    flock_id: UUID | None = None,
    health_incident_id: UUID | None = None,
    product_id: UUID | None = None,
    treatment_status: Annotated[
        TreatmentStatus | None,
        Query(alias="status"),
    ] = None,
    active_withdrawal_only: bool = False,
    search: Annotated[
        str | None,
        Query(min_length=1, max_length=100),
    ] = None,
) -> TreatmentRecordListResponse:
    treatments, total = HealthService(database_session).list_treatments(
        current_user.farm_id,
        offset=offset,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        flock_id=flock_id,
        health_incident_id=health_incident_id,
        product_id=product_id,
        treatment_status=(
            treatment_status.value if treatment_status is not None else None
        ),
        active_withdrawal_only=(active_withdrawal_only),
        search=search,
    )
    return TreatmentRecordListResponse(
        items=[build_treatment_response(item) for item in treatments],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/treatments/{treatment_id}",
    response_model=TreatmentRecordResponse,
)
def get_treatment_record(
    treatment_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.view")),
    ],
) -> TreatmentRecordResponse:
    treatment = HealthService(database_session).get_treatment(
        current_user.farm_id,
        treatment_id,
    )
    return build_treatment_response(treatment)


@router.post(
    "/treatments/{treatment_id}/complete",
    response_model=TreatmentRecordResponse,
)
def complete_treatment_record(
    treatment_id: UUID,
    payload: TreatmentCompletionRequest,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.resolve")),
    ],
) -> TreatmentRecordResponse:
    treatment = HealthService(database_session).complete_treatment(
        current_user.farm_id,
        treatment_id,
        current_user.id,
        end_date=payload.end_date,
        notes=payload.notes,
    )
    return build_treatment_response(treatment)


@router.post(
    "/treatments/{treatment_id}/cancel",
    response_model=TreatmentRecordResponse,
)
def cancel_treatment_record(
    treatment_id: UUID,
    payload: TreatmentCancellationRequest,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.treatments.manage")),
    ],
) -> TreatmentRecordResponse:
    treatment = HealthService(database_session).cancel_treatment(
        current_user.farm_id,
        treatment_id,
        reason=payload.reason,
    )
    return build_treatment_response(treatment)


@router.get(
    "/summary",
    response_model=HealthSummaryResponse,
)
def get_health_summary(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.view")),
    ],
) -> HealthSummaryResponse:
    summary = HealthService(database_session).get_summary(current_user.farm_id)
    return HealthSummaryResponse(**summary)


@router.get(
    "/flocks/{flock_id}/history",
    response_model=FlockHealthHistoryResponse,
)
def get_flock_health_history(
    flock_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("health.view")),
    ],
) -> FlockHealthHistoryResponse:
    (
        flock,
        schedules,
        incidents,
        treatments,
    ) = HealthService(database_session).get_flock_history(
        current_user.farm_id,
        flock_id,
    )
    return FlockHealthHistoryResponse(
        flock_id=flock.id,
        flock_code=flock.flock_code,
        flock_name=flock.name,
        vaccination_schedules=[build_schedule_response(item) for item in schedules],
        health_incidents=[build_incident_response(item) for item in incidents],
        treatment_records=[build_treatment_response(item) for item in treatments],
    )
