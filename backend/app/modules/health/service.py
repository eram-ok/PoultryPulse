from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BusinessRuleError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.modules.health.constants import (
    HealthIncidentStatus,
    HealthProductType,
    TreatmentStatus,
    VaccinationScheduleStatus,
)
from app.modules.health.models import (
    HealthIncident,
    HealthProduct,
    TreatmentRecord,
    VaccinationAdministration,
    VaccinationSchedule,
    calculate_withdrawal_until,
)
from app.modules.health.repository import HealthRepository
from app.modules.health.schemas import (
    HealthIncidentCreate,
    HealthIncidentUpdate,
    HealthProductCreate,
    HealthProductUpdate,
    TreatmentRecordCreate,
    VaccinationAdministrationCreate,
    VaccinationScheduleCreate,
    VaccinationScheduleUpdate,
)


VACCINATION_ALLOWED_FLOCK_STATUSES = {
    "PLANNED",
    "ACTIVE",
    "SUSPENDED",
}

HEALTH_ALLOWED_FLOCK_STATUSES = {
    "ACTIVE",
    "SUSPENDED",
}

ACTIVE_INCIDENT_STATUSES = {
    HealthIncidentStatus.OPEN.value,
    HealthIncidentStatus.UNDER_TREATMENT.value,
    HealthIncidentStatus.MONITORING.value,
}


class HealthService:
    """Business operations for vaccination and poultry health."""

    def __init__(
        self,
        database_session: Session,
    ) -> None:
        self.database_session = database_session
        self.repository = HealthRepository(database_session)

    def _get_flock(
        self,
        farm_id: UUID,
        flock_id: UUID,
    ):
        flock = self.repository.get_flock(
            farm_id,
            flock_id,
        )
        if flock is None:
            raise ResourceNotFoundError(
                "The selected flock does not exist.",
                error_code="flock_not_found",
            )
        return flock

    def _get_product(
        self,
        farm_id: UUID,
        product_id: UUID,
        *,
        for_update: bool = False,
    ) -> HealthProduct:
        product = self.repository.get_product(
            farm_id,
            product_id,
            for_update=for_update,
        )
        if product is None:
            raise ResourceNotFoundError(
                "The selected health product does not exist.",
                error_code="health_product_not_found",
            )
        return product

    def _get_active_product(
        self,
        farm_id: UUID,
        product_id: UUID,
    ) -> HealthProduct:
        product = self._get_product(
            farm_id,
            product_id,
        )
        if not product.is_active:
            raise BusinessRuleError(
                "The selected health product is inactive.",
                error_code="health_product_inactive",
            )
        return product

    def _get_schedule(
        self,
        farm_id: UUID,
        schedule_id: UUID,
        *,
        for_update: bool = False,
    ) -> VaccinationSchedule:
        schedule = self.repository.get_schedule(
            farm_id,
            schedule_id,
            for_update=for_update,
        )
        if schedule is None:
            raise ResourceNotFoundError(
                "The vaccination schedule does not exist.",
                error_code="vaccination_schedule_not_found",
            )
        return schedule

    def _get_incident(
        self,
        farm_id: UUID,
        incident_id: UUID,
        *,
        for_update: bool = False,
    ) -> HealthIncident:
        incident = self.repository.get_incident(
            farm_id,
            incident_id,
            for_update=for_update,
        )
        if incident is None:
            raise ResourceNotFoundError(
                "The health incident does not exist.",
                error_code="health_incident_not_found",
            )
        return incident

    def _get_treatment(
        self,
        farm_id: UUID,
        treatment_id: UUID,
        *,
        for_update: bool = False,
    ) -> TreatmentRecord:
        treatment = self.repository.get_treatment(
            farm_id,
            treatment_id,
            for_update=for_update,
        )
        if treatment is None:
            raise ResourceNotFoundError(
                "The treatment record does not exist.",
                error_code="treatment_record_not_found",
            )
        return treatment

    @staticmethod
    def _schedule_status(
        scheduled_date: date,
    ) -> str:
        if scheduled_date < date.today():
            return VaccinationScheduleStatus.MISSED.value
        if scheduled_date == date.today():
            return VaccinationScheduleStatus.DUE.value
        return VaccinationScheduleStatus.SCHEDULED.value

    @staticmethod
    def _validate_date_range(
        date_from: date | None,
        date_to: date | None,
    ) -> None:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise BusinessRuleError(
                "The start date cannot be after the end date.",
                error_code="invalid_health_date_range",
            )

    def synchronize_schedule_statuses(
        self,
        farm_id: UUID,
    ) -> None:
        changed = False
        for schedule in self.repository.list_pending_schedules(farm_id):
            expected = self._schedule_status(schedule.scheduled_date)
            if schedule.status != expected:
                schedule.status = expected
                changed = True
        if changed:
            self.database_session.commit()

    def create_product(
        self,
        farm_id: UUID,
        payload: HealthProductCreate,
    ) -> HealthProduct:
        if (
            self.repository.get_product_by_code(
                farm_id,
                payload.product_code,
            )
            is not None
        ):
            raise ResourceConflictError(
                "A health product with this code already exists.",
                error_code=("health_product_code_already_exists"),
            )

        product = HealthProduct(
            farm_id=farm_id,
            product_code=payload.product_code,
            name=payload.name,
            product_type=payload.product_type.value,
            manufacturer=payload.manufacturer,
            active_ingredient=payload.active_ingredient,
            description=payload.description,
            default_egg_withdrawal_days=(payload.default_egg_withdrawal_days),
            default_meat_withdrawal_days=(payload.default_meat_withdrawal_days),
            is_active=True,
        )
        self.repository.add_product(product)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()
            raise ResourceConflictError(
                "The health product could not be created.",
                error_code=("health_product_creation_conflict"),
            ) from exc

        return self._get_product(farm_id, product.id)

    def list_products(
        self,
        farm_id: UUID,
        **kwargs,
    ):
        return self.repository.list_products(
            farm_id,
            **kwargs,
        )

    def get_product(
        self,
        farm_id: UUID,
        product_id: UUID,
    ) -> HealthProduct:
        return self._get_product(farm_id, product_id)

    def update_product(
        self,
        farm_id: UUID,
        product_id: UUID,
        payload: HealthProductUpdate,
    ) -> HealthProduct:
        product = self._get_product(
            farm_id,
            product_id,
            for_update=True,
        )
        changes = payload.model_dump(exclude_unset=True)

        new_code = changes.get("product_code")
        if new_code is not None and new_code != product.product_code:
            conflicting = self.repository.get_product_by_code(
                farm_id,
                new_code,
            )
            if conflicting is not None:
                raise ResourceConflictError(
                    "Another health product already uses this code.",
                    error_code=("health_product_code_already_exists"),
                )

        if payload.product_type is not None:
            changes["product_type"] = payload.product_type.value

        self.repository.update_product(
            product,
            changes,
        )

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()
            raise ResourceConflictError(
                "The health product could not be updated.",
                error_code="health_product_update_conflict",
            ) from exc

        return self._get_product(farm_id, product_id)

    def set_product_active_status(
        self,
        farm_id: UUID,
        product_id: UUID,
        *,
        is_active: bool,
    ) -> HealthProduct:
        product = self._get_product(
            farm_id,
            product_id,
            for_update=True,
        )
        product.is_active = is_active
        self.database_session.commit()
        return self._get_product(farm_id, product_id)

    def create_schedule(
        self,
        farm_id: UUID,
        created_by: UUID,
        payload: VaccinationScheduleCreate,
    ) -> VaccinationSchedule:
        flock = self._get_flock(
            farm_id,
            payload.flock_id,
        )
        if flock.status not in (VACCINATION_ALLOWED_FLOCK_STATUSES):
            raise BusinessRuleError(
                "Vaccination cannot be scheduled for this flock status.",
                error_code="flock_closed_for_vaccination",
            )
        if payload.scheduled_date < flock.arrival_date:
            raise BusinessRuleError(
                "Vaccination cannot be scheduled before flock arrival.",
                error_code="vaccination_before_flock_arrival",
            )

        if payload.product_id is not None:
            product = self._get_active_product(
                farm_id,
                payload.product_id,
            )
            if product.product_type != (HealthProductType.VACCINE.value):
                raise BusinessRuleError(
                    "The selected product is not a vaccine.",
                    error_code="product_is_not_vaccine",
                )

        duplicate = self.repository.get_duplicate_schedule(
            farm_id,
            payload.flock_id,
            payload.vaccine_name,
            payload.scheduled_date,
        )
        if duplicate is not None:
            raise ResourceConflictError(
                "This vaccination is already scheduled.",
                error_code=("vaccination_schedule_already_exists"),
            )

        schedule = VaccinationSchedule(
            farm_id=farm_id,
            flock_id=payload.flock_id,
            product_id=payload.product_id,
            vaccine_name=payload.vaccine_name,
            disease_target=payload.disease_target,
            scheduled_date=payload.scheduled_date,
            reminder_date=payload.reminder_date,
            target_age_days=payload.target_age_days,
            planned_dose=payload.planned_dose,
            route=payload.route.value,
            status=self._schedule_status(payload.scheduled_date),
            notes=payload.notes,
            created_by=created_by,
        )
        self.repository.add_schedule(schedule)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()
            raise ResourceConflictError(
                "The vaccination schedule could not be created.",
                error_code="vaccination_schedule_conflict",
            ) from exc

        return self._get_schedule(farm_id, schedule.id)

    def update_schedule(
        self,
        farm_id: UUID,
        schedule_id: UUID,
        payload: VaccinationScheduleUpdate,
    ) -> VaccinationSchedule:
        schedule = self._get_schedule(
            farm_id,
            schedule_id,
            for_update=True,
        )
        if schedule.status in {
            VaccinationScheduleStatus.COMPLETED.value,
            VaccinationScheduleStatus.CANCELLED.value,
        }:
            raise BusinessRuleError(
                "Completed or cancelled schedules cannot be edited.",
                error_code="vaccination_schedule_locked",
            )

        changes = payload.model_dump(exclude_unset=True)
        scheduled_date = (
            payload.scheduled_date
            if payload.scheduled_date is not None
            else schedule.scheduled_date
        )
        reminder_date = (
            payload.reminder_date
            if "reminder_date" in changes
            else schedule.reminder_date
        )

        if reminder_date is not None and reminder_date > scheduled_date:
            raise BusinessRuleError(
                "Reminder date cannot be after the scheduled date.",
                error_code=("invalid_vaccination_reminder_date"),
            )
        if scheduled_date < schedule.flock.arrival_date:
            raise BusinessRuleError(
                "Vaccination cannot be scheduled before flock arrival.",
                error_code="vaccination_before_flock_arrival",
            )

        if payload.product_id is not None:
            product = self._get_active_product(
                farm_id,
                payload.product_id,
            )
            if product.product_type != (HealthProductType.VACCINE.value):
                raise BusinessRuleError(
                    "The selected product is not a vaccine.",
                    error_code="product_is_not_vaccine",
                )

        vaccine_name = (
            payload.vaccine_name
            if payload.vaccine_name is not None
            else schedule.vaccine_name
        )
        duplicate = self.repository.get_duplicate_schedule(
            farm_id,
            schedule.flock_id,
            vaccine_name,
            scheduled_date,
            exclude_schedule_id=schedule.id,
        )
        if duplicate is not None:
            raise ResourceConflictError(
                "This vaccination is already scheduled.",
                error_code=("vaccination_schedule_already_exists"),
            )

        if payload.route is not None:
            changes["route"] = payload.route.value
        changes["status"] = self._schedule_status(scheduled_date)

        for field_name, field_value in changes.items():
            setattr(schedule, field_name, field_value)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()
            raise ResourceConflictError(
                "The vaccination schedule could not be updated.",
                error_code=("vaccination_schedule_update_conflict"),
            ) from exc

        return self._get_schedule(farm_id, schedule_id)

    def complete_schedule(
        self,
        farm_id: UUID,
        schedule_id: UUID,
        recorded_by: UUID,
        payload: VaccinationAdministrationCreate,
    ) -> VaccinationSchedule:
        schedule = self._get_schedule(
            farm_id,
            schedule_id,
            for_update=True,
        )
        if schedule.status == (VaccinationScheduleStatus.COMPLETED.value):
            raise ResourceConflictError(
                "This vaccination is already completed.",
                error_code="vaccination_already_completed",
            )
        if schedule.status == (VaccinationScheduleStatus.CANCELLED.value):
            raise BusinessRuleError(
                "A cancelled vaccination cannot be completed.",
                error_code=("cancelled_vaccination_cannot_complete"),
            )
        if payload.administration_date < schedule.flock.arrival_date:
            raise BusinessRuleError(
                "Vaccination cannot occur before flock arrival.",
                error_code="vaccination_before_flock_arrival",
            )

        birds_present = self.repository.get_population_as_of_date(
            farm_id,
            schedule.flock_id,
            payload.administration_date,
        )
        if birds_present <= 0:
            raise BusinessRuleError(
                "The flock had no live birds on the vaccination date.",
                error_code=("no_flock_population_on_vaccination_date"),
            )
        if payload.birds_vaccinated > birds_present:
            raise BusinessRuleError(
                "Birds vaccinated cannot exceed the flock population.",
                error_code=("vaccinated_birds_exceed_population"),
            )

        product_id = payload.product_id or schedule.product_id
        if product_id is not None:
            product = self._get_active_product(
                farm_id,
                product_id,
            )
            if product.product_type != (HealthProductType.VACCINE.value):
                raise BusinessRuleError(
                    "The selected product is not a vaccine.",
                    error_code="product_is_not_vaccine",
                )

        administration = VaccinationAdministration(
            farm_id=farm_id,
            schedule_id=schedule.id,
            flock_id=schedule.flock_id,
            product_id=product_id,
            administration_date=(payload.administration_date),
            birds_vaccinated=payload.birds_vaccinated,
            dose=payload.dose or schedule.planned_dose,
            route=(
                payload.route.value if payload.route is not None else schedule.route
            ),
            batch_number=payload.batch_number,
            expiry_date=payload.expiry_date,
            administered_by_name=(payload.administered_by_name),
            veterinarian_name=(payload.veterinarian_name),
            notes=payload.notes,
            recorded_by=recorded_by,
        )
        schedule.status = VaccinationScheduleStatus.COMPLETED.value
        self.repository.add_administration(administration)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()
            raise ResourceConflictError(
                "The vaccination could not be completed.",
                error_code=("vaccination_completion_conflict"),
            ) from exc

        # Reload the schedule and its newly created
        # administration relationship after commit.
        self.database_session.expire_all()

        return self._get_schedule(farm_id, schedule_id)

    def cancel_schedule(
        self,
        farm_id: UUID,
        schedule_id: UUID,
        cancelled_by: UUID,
        reason: str,
    ) -> VaccinationSchedule:
        schedule = self._get_schedule(
            farm_id,
            schedule_id,
            for_update=True,
        )
        if schedule.status == (VaccinationScheduleStatus.COMPLETED.value):
            raise BusinessRuleError(
                "A completed vaccination cannot be cancelled.",
                error_code=("completed_vaccination_cannot_cancel"),
            )
        if schedule.status == (VaccinationScheduleStatus.CANCELLED.value):
            raise ResourceConflictError(
                "This vaccination is already cancelled.",
                error_code="vaccination_already_cancelled",
            )

        schedule.status = VaccinationScheduleStatus.CANCELLED.value
        schedule.cancelled_by = cancelled_by
        schedule.cancelled_at = datetime.now(UTC)
        schedule.cancellation_reason = reason
        self.database_session.commit()
        return self._get_schedule(farm_id, schedule_id)

    def list_schedules(
        self,
        farm_id: UUID,
        *,
        date_from: date | None,
        date_to: date | None,
        **kwargs,
    ):
        self._validate_date_range(date_from, date_to)
        self.synchronize_schedule_statuses(farm_id)
        return self.repository.list_schedules(
            farm_id,
            date_from=date_from,
            date_to=date_to,
            **kwargs,
        )

    def get_schedule(
        self,
        farm_id: UUID,
        schedule_id: UUID,
    ) -> VaccinationSchedule:
        self.synchronize_schedule_statuses(farm_id)
        return self._get_schedule(farm_id, schedule_id)

    def get_reminders(
        self,
        farm_id: UUID,
        *,
        upcoming_days: int,
    ):
        self.synchronize_schedule_statuses(farm_id)
        end_date = date.today() + timedelta(days=upcoming_days)
        schedules = self.repository.list_reminder_schedules(
            farm_id,
            end_date=end_date,
        )
        counts = self.repository.get_schedule_status_counts(farm_id)
        return schedules, counts

    def create_incident(
        self,
        farm_id: UUID,
        recorded_by: UUID,
        payload: HealthIncidentCreate,
    ) -> HealthIncident:
        flock = self._get_flock(
            farm_id,
            payload.flock_id,
        )
        if flock.status not in HEALTH_ALLOWED_FLOCK_STATUSES:
            raise BusinessRuleError(
                "A health incident cannot be recorded for this flock status.",
                error_code="flock_closed_for_health_incident",
            )
        if payload.incident_date < flock.arrival_date:
            raise BusinessRuleError(
                "A health incident cannot occur before flock arrival.",
                error_code="health_incident_before_arrival",
            )

        population = self.repository.get_population_as_of_date(
            farm_id,
            flock.id,
            payload.incident_date,
        )
        if population <= 0:
            raise BusinessRuleError(
                "The flock had no live birds on the incident date.",
                error_code=("no_flock_population_on_incident_date"),
            )
        if payload.affected_birds > population:
            raise BusinessRuleError(
                "Affected birds cannot exceed the flock population.",
                error_code=("affected_birds_exceed_population"),
            )
        if (
            self.repository.get_incident_by_code(
                farm_id,
                payload.incident_code,
            )
            is not None
        ):
            raise ResourceConflictError(
                "A health incident with this code already exists.",
                error_code=("health_incident_code_already_exists"),
            )

        incident = HealthIncident(
            farm_id=farm_id,
            flock_id=payload.flock_id,
            incident_code=payload.incident_code,
            incident_date=payload.incident_date,
            severity=payload.severity.value,
            status=HealthIncidentStatus.OPEN.value,
            affected_birds=payload.affected_birds,
            symptoms=payload.symptoms,
            suspected_cause=payload.suspected_cause,
            diagnosis=payload.diagnosis,
            veterinarian_name=(payload.veterinarian_name),
            isolation_required=(payload.isolation_required),
            isolation_details=(payload.isolation_details),
            notes=payload.notes,
            recorded_by=recorded_by,
        )
        self.repository.add_incident(incident)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()
            raise ResourceConflictError(
                "The health incident could not be created.",
                error_code=("health_incident_creation_conflict"),
            ) from exc

        return self._get_incident(farm_id, incident.id)

    def update_incident(
        self,
        farm_id: UUID,
        incident_id: UUID,
        payload: HealthIncidentUpdate,
    ) -> HealthIncident:
        incident = self._get_incident(
            farm_id,
            incident_id,
            for_update=True,
        )
        if incident.is_resolved:
            raise BusinessRuleError(
                "Resolved or closed incidents cannot be edited.",
                error_code="health_incident_locked",
            )

        changes = payload.model_dump(exclude_unset=True)
        if payload.status is not None:
            if payload.status.value not in (ACTIVE_INCIDENT_STATUSES):
                raise BusinessRuleError(
                    "Use the resolve endpoint to resolve an incident.",
                    error_code=("invalid_incident_status_transition"),
                )
            changes["status"] = payload.status.value
        if payload.severity is not None:
            changes["severity"] = payload.severity.value

        if payload.affected_birds is not None:
            population = self.repository.get_population_as_of_date(
                farm_id,
                incident.flock_id,
                incident.incident_date,
            )
            if payload.affected_birds > population:
                raise BusinessRuleError(
                    "Affected birds cannot exceed the flock population.",
                    error_code=("affected_birds_exceed_population"),
                )

        for field_name, field_value in changes.items():
            setattr(incident, field_name, field_value)
        self.database_session.commit()
        return self._get_incident(farm_id, incident_id)

    def resolve_incident(
        self,
        farm_id: UUID,
        incident_id: UUID,
        resolved_by: UUID,
        *,
        resolution_date: date,
        resolution_notes: str,
    ) -> HealthIncident:
        incident = self._get_incident(
            farm_id,
            incident_id,
            for_update=True,
        )
        if incident.is_resolved:
            raise ResourceConflictError(
                "This health incident is already resolved.",
                error_code=("health_incident_already_resolved"),
            )
        if resolution_date < incident.incident_date:
            raise BusinessRuleError(
                "Resolution date cannot be before the incident date.",
                error_code=("incident_resolution_before_incident"),
            )

        incident.status = HealthIncidentStatus.RESOLVED.value
        incident.resolution_date = resolution_date
        incident.resolution_notes = resolution_notes
        incident.resolved_by = resolved_by
        self.database_session.commit()
        return self._get_incident(farm_id, incident_id)

    def list_incidents(
        self,
        farm_id: UUID,
        *,
        date_from: date | None,
        date_to: date | None,
        **kwargs,
    ):
        self._validate_date_range(date_from, date_to)
        return self.repository.list_incidents(
            farm_id,
            date_from=date_from,
            date_to=date_to,
            **kwargs,
        )

    def get_incident(
        self,
        farm_id: UUID,
        incident_id: UUID,
    ) -> HealthIncident:
        return self._get_incident(farm_id, incident_id)

    def create_treatment(
        self,
        farm_id: UUID,
        recorded_by: UUID,
        payload: TreatmentRecordCreate,
    ) -> TreatmentRecord:
        flock = self._get_flock(
            farm_id,
            payload.flock_id,
        )
        if flock.status not in HEALTH_ALLOWED_FLOCK_STATUSES:
            raise BusinessRuleError(
                "Treatment cannot be recorded for this flock status.",
                error_code="flock_closed_for_treatment",
            )
        if payload.treatment_date < flock.arrival_date:
            raise BusinessRuleError(
                "Treatment cannot begin before flock arrival.",
                error_code="treatment_before_flock_arrival",
            )

        population = self.repository.get_population_as_of_date(
            farm_id,
            flock.id,
            payload.treatment_date,
        )
        if population <= 0:
            raise BusinessRuleError(
                "The flock had no live birds on the treatment date.",
                error_code=("no_flock_population_on_treatment_date"),
            )
        if payload.birds_treated > population:
            raise BusinessRuleError(
                "Birds treated cannot exceed the flock population.",
                error_code=("treated_birds_exceed_population"),
            )

        incident = None
        if payload.health_incident_id is not None:
            incident = self._get_incident(
                farm_id,
                payload.health_incident_id,
                for_update=True,
            )
            if incident.flock_id != payload.flock_id:
                raise BusinessRuleError(
                    "The treatment flock does not match the incident flock.",
                    error_code=("treatment_incident_flock_mismatch"),
                )

        product = None
        if payload.product_id is not None:
            product = self._get_active_product(
                farm_id,
                payload.product_id,
            )
            if product.product_type == (HealthProductType.VACCINE.value):
                raise BusinessRuleError(
                    "Vaccines must use the vaccination workflow.",
                    error_code=("vaccine_cannot_be_treatment"),
                )

        if product is not None:
            product_name = product.name
        else:
            product_name = (payload.product_name or "").strip()

        if not product_name:
            raise BusinessRuleError(
                "A treatment product name is required.",
                error_code=("treatment_product_name_required"),
            )

        if payload.egg_withdrawal_days is not None:
            egg_withdrawal_days = payload.egg_withdrawal_days
        elif product is not None:
            egg_withdrawal_days = product.default_egg_withdrawal_days
        else:
            egg_withdrawal_days = 0

        if payload.meat_withdrawal_days is not None:
            meat_withdrawal_days = payload.meat_withdrawal_days
        elif product is not None:
            meat_withdrawal_days = product.default_meat_withdrawal_days
        else:
            meat_withdrawal_days = 0

        treatment_status = (
            TreatmentStatus.PLANNED.value
            if payload.treatment_date > date.today()
            else TreatmentStatus.ACTIVE.value
        )

        treatment = TreatmentRecord(
            farm_id=farm_id,
            flock_id=payload.flock_id,
            health_incident_id=(payload.health_incident_id),
            product_id=payload.product_id,
            product_name=product_name,
            treatment_date=payload.treatment_date,
            end_date=payload.end_date,
            birds_treated=payload.birds_treated,
            dose=payload.dose,
            route=payload.route.value,
            purpose=payload.purpose,
            prescribed_by=payload.prescribed_by,
            treatment_cost=payload.treatment_cost,
            egg_withdrawal_days=(egg_withdrawal_days),
            meat_withdrawal_days=(meat_withdrawal_days),
            egg_withdrawal_until=(
                calculate_withdrawal_until(
                    payload.treatment_date,
                    egg_withdrawal_days,
                )
            ),
            meat_withdrawal_until=(
                calculate_withdrawal_until(
                    payload.treatment_date,
                    meat_withdrawal_days,
                )
            ),
            status=treatment_status,
            notes=payload.notes,
            recorded_by=recorded_by,
        )
        self.repository.add_treatment(treatment)

        if (
            incident is not None
            and treatment_status == TreatmentStatus.ACTIVE.value
            and incident.status == HealthIncidentStatus.OPEN.value
        ):
            incident.status = HealthIncidentStatus.UNDER_TREATMENT.value

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()
            raise ResourceConflictError(
                "The treatment record could not be created.",
                error_code=("treatment_record_creation_conflict"),
            ) from exc

        return self._get_treatment(farm_id, treatment.id)

    def complete_treatment(
        self,
        farm_id: UUID,
        treatment_id: UUID,
        completed_by: UUID,
        *,
        end_date: date,
        notes: str | None,
    ) -> TreatmentRecord:
        treatment = self._get_treatment(
            farm_id,
            treatment_id,
            for_update=True,
        )
        if treatment.status == TreatmentStatus.COMPLETED.value:
            raise ResourceConflictError(
                "This treatment is already completed.",
                error_code="treatment_already_completed",
            )
        if treatment.status == TreatmentStatus.CANCELLED.value:
            raise BusinessRuleError(
                "A cancelled treatment cannot be completed.",
                error_code=("cancelled_treatment_cannot_complete"),
            )
        if end_date < treatment.treatment_date:
            raise BusinessRuleError(
                "Completion date cannot be before treatment.",
                error_code=("treatment_completion_before_start"),
            )

        treatment.status = TreatmentStatus.COMPLETED.value
        treatment.end_date = end_date
        treatment.completed_by = completed_by
        treatment.completed_at = datetime.now(UTC)

        if notes:
            treatment.notes = (
                f"{treatment.notes}\n{notes}" if treatment.notes else notes
            )

        if (
            treatment.health_incident is not None
            and treatment.health_incident.status
            == HealthIncidentStatus.UNDER_TREATMENT.value
        ):
            treatment.health_incident.status = HealthIncidentStatus.MONITORING.value

        self.database_session.commit()
        return self._get_treatment(farm_id, treatment_id)

    def cancel_treatment(
        self,
        farm_id: UUID,
        treatment_id: UUID,
        *,
        reason: str,
    ) -> TreatmentRecord:
        treatment = self._get_treatment(
            farm_id,
            treatment_id,
            for_update=True,
        )
        if treatment.status == TreatmentStatus.COMPLETED.value:
            raise BusinessRuleError(
                "A completed treatment cannot be cancelled.",
                error_code=("completed_treatment_cannot_cancel"),
            )
        if treatment.status == TreatmentStatus.CANCELLED.value:
            raise ResourceConflictError(
                "This treatment is already cancelled.",
                error_code="treatment_already_cancelled",
            )

        treatment.status = TreatmentStatus.CANCELLED.value
        treatment.notes = (
            f"{treatment.notes}\nCancelled: {reason}"
            if treatment.notes
            else f"Cancelled: {reason}"
        )
        self.database_session.commit()
        return self._get_treatment(farm_id, treatment_id)

    def list_treatments(
        self,
        farm_id: UUID,
        *,
        date_from: date | None,
        date_to: date | None,
        **kwargs,
    ):
        self._validate_date_range(date_from, date_to)
        return self.repository.list_treatments(
            farm_id,
            date_from=date_from,
            date_to=date_to,
            **kwargs,
        )

    def get_treatment(
        self,
        farm_id: UUID,
        treatment_id: UUID,
    ) -> TreatmentRecord:
        return self._get_treatment(farm_id, treatment_id)

    def get_summary(
        self,
        farm_id: UUID,
    ) -> dict[str, int | date]:
        self.synchronize_schedule_statuses(farm_id)

        schedule_counts = self.repository.get_schedule_status_counts(farm_id)
        incident_counts = self.repository.get_incident_status_counts(farm_id)
        treatment_counts = self.repository.get_treatment_status_counts(farm_id)
        (
            active_egg_withdrawals,
            active_meat_withdrawals,
        ) = self.repository.count_active_withdrawals(
            farm_id,
            as_of_date=date.today(),
        )

        return {
            "as_of_date": date.today(),
            "scheduled_vaccinations": schedule_counts.get(
                VaccinationScheduleStatus.SCHEDULED.value,
                0,
            ),
            "due_vaccinations": schedule_counts.get(
                VaccinationScheduleStatus.DUE.value,
                0,
            ),
            "missed_vaccinations": schedule_counts.get(
                VaccinationScheduleStatus.MISSED.value,
                0,
            ),
            "completed_vaccinations": schedule_counts.get(
                VaccinationScheduleStatus.COMPLETED.value,
                0,
            ),
            "open_incidents": incident_counts.get(
                HealthIncidentStatus.OPEN.value,
                0,
            ),
            "incidents_under_treatment": (
                incident_counts.get(
                    HealthIncidentStatus.UNDER_TREATMENT.value,
                    0,
                )
            ),
            "critical_incidents": (self.repository.count_critical_incidents(farm_id)),
            "active_treatments": treatment_counts.get(
                TreatmentStatus.ACTIVE.value,
                0,
            ),
            "planned_treatments": treatment_counts.get(
                TreatmentStatus.PLANNED.value,
                0,
            ),
            "active_egg_withdrawals": (active_egg_withdrawals),
            "active_meat_withdrawals": (active_meat_withdrawals),
        }

    def get_flock_history(
        self,
        farm_id: UUID,
        flock_id: UUID,
    ):
        flock = self._get_flock(farm_id, flock_id)
        self.synchronize_schedule_statuses(farm_id)
        return (
            flock,
            self.repository.list_flock_schedules(
                farm_id,
                flock_id,
            ),
            self.repository.list_flock_incidents(
                farm_id,
                flock_id,
            ),
            self.repository.list_flock_treatments(
                farm_id,
                flock_id,
            ),
        )
