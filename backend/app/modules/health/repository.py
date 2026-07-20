from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.flocks.models import Flock, FlockPopulationTransaction
from app.modules.health.constants import (
    HealthIncidentSeverity,
    HealthIncidentStatus,
    TreatmentStatus,
    VaccinationScheduleStatus,
)
from app.modules.health.models import (
    HealthIncident,
    HealthProduct,
    TreatmentRecord,
    VaccinationAdministration,
    VaccinationSchedule,
)


class HealthRepository:
    """Database operations for vaccination and poultry health."""

    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session

    def get_flock(
        self,
        farm_id: UUID,
        flock_id: UUID,
    ) -> Flock | None:
        statement = (
            select(Flock)
            .options(selectinload(Flock.house))
            .where(
                Flock.farm_id == farm_id,
                Flock.id == flock_id,
            )
        )
        return self.database_session.scalar(statement)

    def get_population_as_of_date(
        self,
        farm_id: UUID,
        flock_id: UUID,
        as_of_date: date,
    ) -> int:
        statement = select(
            func.coalesce(
                func.sum(FlockPopulationTransaction.signed_quantity),
                0,
            )
        ).where(
            FlockPopulationTransaction.farm_id == farm_id,
            FlockPopulationTransaction.flock_id == flock_id,
            FlockPopulationTransaction.transaction_date <= as_of_date,
        )
        return int(self.database_session.scalar(statement) or 0)

    def get_product(
        self,
        farm_id: UUID,
        product_id: UUID,
        *,
        for_update: bool = False,
    ) -> HealthProduct | None:
        statement = select(HealthProduct).where(
            HealthProduct.farm_id == farm_id,
            HealthProduct.id == product_id,
        )
        if for_update:
            statement = statement.with_for_update()
        return self.database_session.scalar(statement)

    def get_product_by_code(
        self,
        farm_id: UUID,
        product_code: str,
    ) -> HealthProduct | None:
        statement = select(HealthProduct).where(
            HealthProduct.farm_id == farm_id,
            HealthProduct.product_code == product_code,
        )
        return self.database_session.scalar(statement)

    def list_products(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        product_type: str | None,
        is_active: bool | None,
        search: str | None,
    ) -> tuple[list[HealthProduct], int]:
        conditions = [HealthProduct.farm_id == farm_id]

        if product_type is not None:
            conditions.append(HealthProduct.product_type == product_type)

        if is_active is not None:
            conditions.append(HealthProduct.is_active.is_(is_active))

        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(
                or_(
                    HealthProduct.product_code.ilike(pattern),
                    HealthProduct.name.ilike(pattern),
                    HealthProduct.manufacturer.ilike(pattern),
                    HealthProduct.active_ingredient.ilike(pattern),
                )
            )

        records_statement = (
            select(HealthProduct)
            .where(*conditions)
            .order_by(
                HealthProduct.name.asc(),
                HealthProduct.product_code.asc(),
            )
            .offset(offset)
            .limit(limit)
        )
        count_statement = select(func.count(HealthProduct.id)).where(*conditions)

        records = list(self.database_session.scalars(records_statement).all())
        total = int(self.database_session.scalar(count_statement) or 0)
        return records, total

    def add_product(
        self,
        product: HealthProduct,
    ) -> HealthProduct:
        self.database_session.add(product)
        return product

    def update_product(
        self,
        product: HealthProduct,
        changes: dict[str, Any],
    ) -> HealthProduct:
        for field_name, field_value in changes.items():
            setattr(product, field_name, field_value)
        self.database_session.add(product)
        return product

    def get_schedule(
        self,
        farm_id: UUID,
        schedule_id: UUID,
        *,
        for_update: bool = False,
    ) -> VaccinationSchedule | None:
        statement = (
            select(VaccinationSchedule)
            .options(
                selectinload(VaccinationSchedule.flock).selectinload(Flock.house),
                selectinload(VaccinationSchedule.product),
                selectinload(VaccinationSchedule.administration).selectinload(
                    VaccinationAdministration.product
                ),
            )
            .where(
                VaccinationSchedule.farm_id == farm_id,
                VaccinationSchedule.id == schedule_id,
            )
        )
        if for_update:
            statement = statement.with_for_update()
        return self.database_session.scalar(statement)

    def get_duplicate_schedule(
        self,
        farm_id: UUID,
        flock_id: UUID,
        vaccine_name: str,
        scheduled_date: date,
        *,
        exclude_schedule_id: UUID | None = None,
    ) -> VaccinationSchedule | None:
        conditions = [
            VaccinationSchedule.farm_id == farm_id,
            VaccinationSchedule.flock_id == flock_id,
            VaccinationSchedule.vaccine_name == vaccine_name,
            VaccinationSchedule.scheduled_date == scheduled_date,
        ]
        if exclude_schedule_id is not None:
            conditions.append(VaccinationSchedule.id != exclude_schedule_id)
        return self.database_session.scalar(
            select(VaccinationSchedule).where(*conditions)
        )

    def list_pending_schedules(
        self,
        farm_id: UUID,
    ) -> list[VaccinationSchedule]:
        statement = select(VaccinationSchedule).where(
            VaccinationSchedule.farm_id == farm_id,
            VaccinationSchedule.status.in_(
                {
                    VaccinationScheduleStatus.SCHEDULED.value,
                    VaccinationScheduleStatus.DUE.value,
                    VaccinationScheduleStatus.MISSED.value,
                }
            ),
        )
        return list(self.database_session.scalars(statement).all())

    def list_schedules(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        date_from: date | None,
        date_to: date | None,
        flock_id: UUID | None,
        product_id: UUID | None,
        schedule_status: str | None,
        search: str | None,
    ) -> tuple[list[VaccinationSchedule], int]:
        conditions = [VaccinationSchedule.farm_id == farm_id]

        if date_from is not None:
            conditions.append(VaccinationSchedule.scheduled_date >= date_from)
        if date_to is not None:
            conditions.append(VaccinationSchedule.scheduled_date <= date_to)
        if flock_id is not None:
            conditions.append(VaccinationSchedule.flock_id == flock_id)
        if product_id is not None:
            conditions.append(VaccinationSchedule.product_id == product_id)
        if schedule_status is not None:
            conditions.append(VaccinationSchedule.status == schedule_status)
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(
                or_(
                    VaccinationSchedule.vaccine_name.ilike(pattern),
                    VaccinationSchedule.disease_target.ilike(pattern),
                    Flock.flock_code.ilike(pattern),
                    Flock.name.ilike(pattern),
                )
            )

        records_statement = (
            select(VaccinationSchedule)
            .join(
                Flock,
                Flock.id == VaccinationSchedule.flock_id,
            )
            .options(
                selectinload(VaccinationSchedule.flock).selectinload(Flock.house),
                selectinload(VaccinationSchedule.product),
                selectinload(VaccinationSchedule.administration).selectinload(
                    VaccinationAdministration.product
                ),
            )
            .where(*conditions)
            .order_by(
                VaccinationSchedule.scheduled_date.asc(),
                VaccinationSchedule.created_at.asc(),
            )
            .offset(offset)
            .limit(limit)
        )
        count_statement = (
            select(func.count(VaccinationSchedule.id))
            .join(
                Flock,
                Flock.id == VaccinationSchedule.flock_id,
            )
            .where(*conditions)
        )

        records = list(self.database_session.scalars(records_statement).all())
        total = int(self.database_session.scalar(count_statement) or 0)
        return records, total

    def list_reminder_schedules(
        self,
        farm_id: UUID,
        *,
        end_date: date,
    ) -> list[VaccinationSchedule]:
        statement = (
            select(VaccinationSchedule)
            .options(
                selectinload(VaccinationSchedule.flock).selectinload(Flock.house),
                selectinload(VaccinationSchedule.product),
                selectinload(VaccinationSchedule.administration).selectinload(
                    VaccinationAdministration.product
                ),
            )
            .where(
                VaccinationSchedule.farm_id == farm_id,
                VaccinationSchedule.status.in_(
                    {
                        VaccinationScheduleStatus.SCHEDULED.value,
                        VaccinationScheduleStatus.DUE.value,
                        VaccinationScheduleStatus.MISSED.value,
                    }
                ),
                VaccinationSchedule.scheduled_date <= end_date,
            )
            .order_by(VaccinationSchedule.scheduled_date.asc())
        )
        return list(self.database_session.scalars(statement).all())

    def add_schedule(
        self,
        schedule: VaccinationSchedule,
    ) -> VaccinationSchedule:
        self.database_session.add(schedule)
        return schedule

    def add_administration(
        self,
        administration: VaccinationAdministration,
    ) -> VaccinationAdministration:
        self.database_session.add(administration)
        return administration

    def get_incident(
        self,
        farm_id: UUID,
        incident_id: UUID,
        *,
        for_update: bool = False,
    ) -> HealthIncident | None:
        statement = (
            select(HealthIncident)
            .options(
                selectinload(HealthIncident.flock).selectinload(Flock.house),
                selectinload(HealthIncident.treatments).selectinload(
                    TreatmentRecord.product
                ),
            )
            .where(
                HealthIncident.farm_id == farm_id,
                HealthIncident.id == incident_id,
            )
        )
        if for_update:
            statement = statement.with_for_update()
        return self.database_session.scalar(statement)

    def get_incident_by_code(
        self,
        farm_id: UUID,
        incident_code: str,
    ) -> HealthIncident | None:
        return self.database_session.scalar(
            select(HealthIncident).where(
                HealthIncident.farm_id == farm_id,
                HealthIncident.incident_code == incident_code,
            )
        )

    def list_incidents(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        date_from: date | None,
        date_to: date | None,
        flock_id: UUID | None,
        severity: str | None,
        incident_status: str | None,
        search: str | None,
    ) -> tuple[list[HealthIncident], int]:
        conditions = [HealthIncident.farm_id == farm_id]

        if date_from is not None:
            conditions.append(HealthIncident.incident_date >= date_from)
        if date_to is not None:
            conditions.append(HealthIncident.incident_date <= date_to)
        if flock_id is not None:
            conditions.append(HealthIncident.flock_id == flock_id)
        if severity is not None:
            conditions.append(HealthIncident.severity == severity)
        if incident_status is not None:
            conditions.append(HealthIncident.status == incident_status)
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(
                or_(
                    HealthIncident.incident_code.ilike(pattern),
                    HealthIncident.symptoms.ilike(pattern),
                    HealthIncident.diagnosis.ilike(pattern),
                    Flock.flock_code.ilike(pattern),
                    Flock.name.ilike(pattern),
                )
            )

        records_statement = (
            select(HealthIncident)
            .join(
                Flock,
                Flock.id == HealthIncident.flock_id,
            )
            .options(
                selectinload(HealthIncident.flock).selectinload(Flock.house),
                selectinload(HealthIncident.treatments),
            )
            .where(*conditions)
            .order_by(
                HealthIncident.incident_date.desc(),
                HealthIncident.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        count_statement = (
            select(func.count(HealthIncident.id))
            .join(
                Flock,
                Flock.id == HealthIncident.flock_id,
            )
            .where(*conditions)
        )

        records = list(self.database_session.scalars(records_statement).all())
        total = int(self.database_session.scalar(count_statement) or 0)
        return records, total

    def add_incident(
        self,
        incident: HealthIncident,
    ) -> HealthIncident:
        self.database_session.add(incident)
        return incident

    def get_treatment(
        self,
        farm_id: UUID,
        treatment_id: UUID,
        *,
        for_update: bool = False,
    ) -> TreatmentRecord | None:
        statement = (
            select(TreatmentRecord)
            .options(
                selectinload(TreatmentRecord.flock).selectinload(Flock.house),
                selectinload(TreatmentRecord.product),
                selectinload(TreatmentRecord.health_incident),
            )
            .where(
                TreatmentRecord.farm_id == farm_id,
                TreatmentRecord.id == treatment_id,
            )
        )
        if for_update:
            statement = statement.with_for_update()
        return self.database_session.scalar(statement)

    def list_treatments(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        date_from: date | None,
        date_to: date | None,
        flock_id: UUID | None,
        health_incident_id: UUID | None,
        product_id: UUID | None,
        treatment_status: str | None,
        active_withdrawal_only: bool,
        search: str | None,
    ) -> tuple[list[TreatmentRecord], int]:
        conditions = [TreatmentRecord.farm_id == farm_id]

        if date_from is not None:
            conditions.append(TreatmentRecord.treatment_date >= date_from)
        if date_to is not None:
            conditions.append(TreatmentRecord.treatment_date <= date_to)
        if flock_id is not None:
            conditions.append(TreatmentRecord.flock_id == flock_id)
        if health_incident_id is not None:
            conditions.append(TreatmentRecord.health_incident_id == health_incident_id)
        if product_id is not None:
            conditions.append(TreatmentRecord.product_id == product_id)
        if treatment_status is not None:
            conditions.append(TreatmentRecord.status == treatment_status)
        if active_withdrawal_only:
            conditions.extend(
                [
                    TreatmentRecord.status != TreatmentStatus.CANCELLED.value,
                    or_(
                        TreatmentRecord.egg_withdrawal_until >= date.today(),
                        TreatmentRecord.meat_withdrawal_until >= date.today(),
                    ),
                ]
            )
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(
                or_(
                    TreatmentRecord.product_name.ilike(pattern),
                    TreatmentRecord.purpose.ilike(pattern),
                    Flock.flock_code.ilike(pattern),
                    Flock.name.ilike(pattern),
                )
            )

        records_statement = (
            select(TreatmentRecord)
            .join(
                Flock,
                Flock.id == TreatmentRecord.flock_id,
            )
            .options(
                selectinload(TreatmentRecord.flock).selectinload(Flock.house),
                selectinload(TreatmentRecord.product),
                selectinload(TreatmentRecord.health_incident),
            )
            .where(*conditions)
            .order_by(
                TreatmentRecord.treatment_date.desc(),
                TreatmentRecord.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        count_statement = (
            select(func.count(TreatmentRecord.id))
            .join(
                Flock,
                Flock.id == TreatmentRecord.flock_id,
            )
            .where(*conditions)
        )

        records = list(self.database_session.scalars(records_statement).all())
        total = int(self.database_session.scalar(count_statement) or 0)
        return records, total

    def add_treatment(
        self,
        treatment: TreatmentRecord,
    ) -> TreatmentRecord:
        self.database_session.add(treatment)
        return treatment

    def get_schedule_status_counts(
        self,
        farm_id: UUID,
    ) -> dict[str, int]:
        statement = (
            select(
                VaccinationSchedule.status,
                func.count(VaccinationSchedule.id),
            )
            .where(VaccinationSchedule.farm_id == farm_id)
            .group_by(VaccinationSchedule.status)
        )
        return {
            item_status: int(item_count)
            for item_status, item_count in self.database_session.execute(
                statement
            ).all()
        }

    def get_incident_status_counts(
        self,
        farm_id: UUID,
    ) -> dict[str, int]:
        statement = (
            select(
                HealthIncident.status,
                func.count(HealthIncident.id),
            )
            .where(HealthIncident.farm_id == farm_id)
            .group_by(HealthIncident.status)
        )
        return {
            item_status: int(item_count)
            for item_status, item_count in self.database_session.execute(
                statement
            ).all()
        }

    def count_critical_incidents(
        self,
        farm_id: UUID,
    ) -> int:
        statement = select(func.count(HealthIncident.id)).where(
            HealthIncident.farm_id == farm_id,
            HealthIncident.severity == HealthIncidentSeverity.CRITICAL.value,
            HealthIncident.status.notin_(
                {
                    HealthIncidentStatus.RESOLVED.value,
                    HealthIncidentStatus.CLOSED.value,
                }
            ),
        )
        return int(self.database_session.scalar(statement) or 0)

    def get_treatment_status_counts(
        self,
        farm_id: UUID,
    ) -> dict[str, int]:
        statement = (
            select(
                TreatmentRecord.status,
                func.count(TreatmentRecord.id),
            )
            .where(TreatmentRecord.farm_id == farm_id)
            .group_by(TreatmentRecord.status)
        )
        return {
            item_status: int(item_count)
            for item_status, item_count in self.database_session.execute(
                statement
            ).all()
        }

    def count_active_withdrawals(
        self,
        farm_id: UUID,
        *,
        as_of_date: date,
    ) -> tuple[int, int]:
        egg_count = int(
            self.database_session.scalar(
                select(func.count(TreatmentRecord.id)).where(
                    TreatmentRecord.farm_id == farm_id,
                    TreatmentRecord.status != TreatmentStatus.CANCELLED.value,
                    TreatmentRecord.egg_withdrawal_until >= as_of_date,
                )
            )
            or 0
        )
        meat_count = int(
            self.database_session.scalar(
                select(func.count(TreatmentRecord.id)).where(
                    TreatmentRecord.farm_id == farm_id,
                    TreatmentRecord.status != TreatmentStatus.CANCELLED.value,
                    TreatmentRecord.meat_withdrawal_until >= as_of_date,
                )
            )
            or 0
        )
        return egg_count, meat_count

    def list_flock_schedules(
        self,
        farm_id: UUID,
        flock_id: UUID,
    ) -> list[VaccinationSchedule]:
        records, _ = self.list_schedules(
            farm_id,
            offset=0,
            limit=1000,
            date_from=None,
            date_to=None,
            flock_id=flock_id,
            product_id=None,
            schedule_status=None,
            search=None,
        )
        return records

    def list_flock_incidents(
        self,
        farm_id: UUID,
        flock_id: UUID,
    ) -> list[HealthIncident]:
        records, _ = self.list_incidents(
            farm_id,
            offset=0,
            limit=1000,
            date_from=None,
            date_to=None,
            flock_id=flock_id,
            severity=None,
            incident_status=None,
            search=None,
        )
        return records

    def list_flock_treatments(
        self,
        farm_id: UUID,
        flock_id: UUID,
    ) -> list[TreatmentRecord]:
        records, _ = self.list_treatments(
            farm_id,
            offset=0,
            limit=1000,
            date_from=None,
            date_to=None,
            flock_id=flock_id,
            health_incident_id=None,
            product_id=None,
            treatment_status=None,
            active_withdrawal_only=False,
            search=None,
        )
        return records
