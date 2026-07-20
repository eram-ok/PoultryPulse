from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.farms.models import Farm
from app.modules.flocks.models import Flock
from app.modules.health.constants import (
    HealthIncidentSeverity,
    HealthIncidentStatus,
    HealthProductType,
    TreatmentStatus,
    VaccinationRoute,
    VaccinationScheduleStatus,
)


class HealthProduct(Base):
    """Represents a vaccine, medicine or health product."""

    __tablename__ = "health_products"

    __table_args__ = (
        UniqueConstraint(
            "farm_id",
            "product_code",
            name="uq_health_products_farm_code",
        ),
        CheckConstraint(
            "product_type IN ("
            "'VACCINE', "
            "'ANTIBIOTIC', "
            "'ANTIPARASITIC', "
            "'ANTIFUNGAL', "
            "'VITAMIN', "
            "'MINERAL', "
            "'ELECTROLYTE', "
            "'DISINFECTANT', "
            "'PROBIOTIC', "
            "'OTHER'"
            ")",
            name="ck_health_products_valid_type",
        ),
        CheckConstraint(
            "default_egg_withdrawal_days >= 0",
            name=("ck_health_products_egg_withdrawal_nonnegative"),
        ),
        CheckConstraint(
            "default_meat_withdrawal_days >= 0",
            name=("ck_health_products_meat_withdrawal_nonnegative"),
        ),
        Index(
            "ix_health_products_farm_type",
            "farm_id",
            "product_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "farms.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    product_code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    product_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default=HealthProductType.OTHER.value,
        server_default=HealthProductType.OTHER.value,
        index=True,
    )

    manufacturer: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    active_ingredient: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    default_egg_withdrawal_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    default_meat_withdrawal_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    farm: Mapped[Farm] = relationship(
        lazy="selectin",
    )

    @property
    def is_vaccine(self) -> bool:
        return self.product_type == HealthProductType.VACCINE.value

    def __repr__(self) -> str:
        return (
            "HealthProduct("
            f"id={self.id!r}, "
            f"product_code={self.product_code!r}, "
            f"name={self.name!r}, "
            f"product_type={self.product_type!r}"
            ")"
        )


class VaccinationSchedule(Base):
    """Represents a planned vaccination for one flock."""

    __tablename__ = "vaccination_schedules"

    __table_args__ = (
        UniqueConstraint(
            "farm_id",
            "flock_id",
            "vaccine_name",
            "scheduled_date",
            name=("uq_vaccination_schedules_farm_flock_vaccine_date"),
        ),
        CheckConstraint(
            "target_age_days IS NULL OR target_age_days >= 0",
            name=("ck_vaccination_schedules_target_age_nonnegative"),
        ),
        CheckConstraint(
            "reminder_date IS NULL OR reminder_date <= scheduled_date",
            name=("ck_vaccination_schedules_reminder_before_schedule"),
        ),
        CheckConstraint(
            "status IN ('SCHEDULED', 'DUE', 'COMPLETED', 'MISSED', 'CANCELLED')",
            name=("ck_vaccination_schedules_valid_status"),
        ),
        CheckConstraint(
            "("
            "status = 'CANCELLED' "
            "AND cancelled_by IS NOT NULL "
            "AND cancelled_at IS NOT NULL "
            "AND cancellation_reason IS NOT NULL"
            ") OR ("
            "status <> 'CANCELLED' "
            "AND cancelled_by IS NULL "
            "AND cancelled_at IS NULL "
            "AND cancellation_reason IS NULL"
            ")",
            name=("ck_vaccination_schedules_cancellation_fields"),
        ),
        Index(
            "ix_vaccination_schedules_farm_date",
            "farm_id",
            "scheduled_date",
        ),
        Index(
            "ix_vaccination_schedules_flock_date",
            "flock_id",
            "scheduled_date",
        ),
        Index(
            "ix_vaccination_schedules_farm_status",
            "farm_id",
            "status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "farms.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    flock_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "flocks.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "health_products.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    vaccine_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    disease_target: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    scheduled_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    reminder_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    target_age_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    planned_dose: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    route: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default=VaccinationRoute.OTHER.value,
        server_default=VaccinationRoute.OTHER.value,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=VaccinationScheduleStatus.SCHEDULED.value,
        server_default=(VaccinationScheduleStatus.SCHEDULED.value),
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    cancelled_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    cancellation_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    farm: Mapped[Farm] = relationship(
        lazy="selectin",
    )

    flock: Mapped[Flock] = relationship(
        lazy="selectin",
    )

    product: Mapped[HealthProduct | None] = relationship(
        lazy="selectin",
    )

    administration: Mapped[VaccinationAdministration | None] = relationship(
        back_populates="schedule",
        uselist=False,
        lazy="selectin",
    )

    @property
    def is_completed(self) -> bool:
        return self.status == VaccinationScheduleStatus.COMPLETED.value

    @property
    def is_cancelled(self) -> bool:
        return self.status == VaccinationScheduleStatus.CANCELLED.value

    @property
    def is_overdue(self) -> bool:
        return (
            self.status
            in {
                VaccinationScheduleStatus.SCHEDULED.value,
                VaccinationScheduleStatus.DUE.value,
                VaccinationScheduleStatus.MISSED.value,
            }
            and self.scheduled_date < date.today()
        )

    def __repr__(self) -> str:
        return (
            "VaccinationSchedule("
            f"id={self.id!r}, "
            f"flock_id={self.flock_id!r}, "
            f"vaccine_name={self.vaccine_name!r}, "
            f"scheduled_date={self.scheduled_date!r}, "
            f"status={self.status!r}"
            ")"
        )


class VaccinationAdministration(Base):
    """Represents a completed vaccination administration."""

    __tablename__ = "vaccination_administrations"

    __table_args__ = (
        UniqueConstraint(
            "schedule_id",
            name=("uq_vaccination_administrations_schedule"),
        ),
        CheckConstraint(
            "birds_vaccinated > 0",
            name=("ck_vaccination_administrations_birds_positive"),
        ),
        CheckConstraint(
            "expiry_date IS NULL OR expiry_date >= administration_date",
            name=("ck_vaccination_administrations_expiry_valid"),
        ),
        Index(
            "ix_vaccination_administrations_farm_date",
            "farm_id",
            "administration_date",
        ),
        Index(
            "ix_vaccination_administrations_flock_date",
            "flock_id",
            "administration_date",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "farms.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "vaccination_schedules.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    flock_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "flocks.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "health_products.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    administration_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    birds_vaccinated: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    dose: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    route: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default=VaccinationRoute.OTHER.value,
        server_default=VaccinationRoute.OTHER.value,
    )

    batch_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    administered_by_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    veterinarian_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    recorded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    schedule: Mapped[VaccinationSchedule] = relationship(
        back_populates="administration",
        lazy="selectin",
    )

    flock: Mapped[Flock] = relationship(
        lazy="selectin",
    )

    product: Mapped[HealthProduct | None] = relationship(
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            "VaccinationAdministration("
            f"id={self.id!r}, "
            f"schedule_id={self.schedule_id!r}, "
            f"administration_date="
            f"{self.administration_date!r}, "
            f"birds_vaccinated={self.birds_vaccinated!r}"
            ")"
        )


class HealthIncident(Base):
    """Represents a disease, symptom or flock health incident."""

    __tablename__ = "health_incidents"

    __table_args__ = (
        UniqueConstraint(
            "farm_id",
            "incident_code",
            name="uq_health_incidents_farm_code",
        ),
        CheckConstraint(
            "affected_birds > 0",
            name="ck_health_incidents_affected_positive",
        ),
        CheckConstraint(
            "severity IN ('LOW', 'MODERATE', 'HIGH', 'CRITICAL')",
            name="ck_health_incidents_valid_severity",
        ),
        CheckConstraint(
            "status IN ('OPEN', 'UNDER_TREATMENT', 'MONITORING', 'RESOLVED', 'CLOSED')",
            name="ck_health_incidents_valid_status",
        ),
        CheckConstraint(
            "resolution_date IS NULL OR resolution_date >= incident_date",
            name=("ck_health_incidents_resolution_date_valid"),
        ),
        CheckConstraint(
            "("
            "status IN ('RESOLVED', 'CLOSED') "
            "AND resolution_date IS NOT NULL "
            "AND resolved_by IS NOT NULL"
            ") OR ("
            "status NOT IN ('RESOLVED', 'CLOSED') "
            "AND resolution_date IS NULL "
            "AND resolved_by IS NULL"
            ")",
            name=("ck_health_incidents_resolution_fields"),
        ),
        Index(
            "ix_health_incidents_farm_date",
            "farm_id",
            "incident_date",
        ),
        Index(
            "ix_health_incidents_flock_date",
            "flock_id",
            "incident_date",
        ),
        Index(
            "ix_health_incidents_farm_status",
            "farm_id",
            "status",
        ),
        Index(
            "ix_health_incidents_farm_severity",
            "farm_id",
            "severity",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "farms.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    flock_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "flocks.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    incident_code: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    incident_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    severity: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=HealthIncidentSeverity.MODERATE.value,
        server_default=(HealthIncidentSeverity.MODERATE.value),
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=HealthIncidentStatus.OPEN.value,
        server_default=HealthIncidentStatus.OPEN.value,
        index=True,
    )

    affected_birds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    symptoms: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    suspected_cause: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    diagnosis: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    veterinarian_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    isolation_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    isolation_details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    resolution_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    resolution_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    recorded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    farm: Mapped[Farm] = relationship(
        lazy="selectin",
    )

    flock: Mapped[Flock] = relationship(
        lazy="selectin",
    )

    treatments: Mapped[list[TreatmentRecord]] = relationship(
        back_populates="health_incident",
        lazy="selectin",
    )

    @property
    def is_resolved(self) -> bool:
        return self.status in {
            HealthIncidentStatus.RESOLVED.value,
            HealthIncidentStatus.CLOSED.value,
        }

    def __repr__(self) -> str:
        return (
            "HealthIncident("
            f"id={self.id!r}, "
            f"incident_code={self.incident_code!r}, "
            f"flock_id={self.flock_id!r}, "
            f"severity={self.severity!r}, "
            f"status={self.status!r}"
            ")"
        )


class TreatmentRecord(Base):
    """Represents treatment given to a flock."""

    __tablename__ = "treatment_records"

    __table_args__ = (
        CheckConstraint(
            "birds_treated > 0",
            name="ck_treatment_records_birds_positive",
        ),
        CheckConstraint(
            "treatment_cost >= 0",
            name="ck_treatment_records_cost_nonnegative",
        ),
        CheckConstraint(
            "egg_withdrawal_days >= 0",
            name=("ck_treatment_records_egg_withdrawal_nonnegative"),
        ),
        CheckConstraint(
            "meat_withdrawal_days >= 0",
            name=("ck_treatment_records_meat_withdrawal_nonnegative"),
        ),
        CheckConstraint(
            "end_date IS NULL OR end_date >= treatment_date",
            name="ck_treatment_records_end_date_valid",
        ),
        CheckConstraint(
            "egg_withdrawal_until IS NULL OR egg_withdrawal_until >= treatment_date",
            name=("ck_treatment_records_egg_withdrawal_valid"),
        ),
        CheckConstraint(
            "meat_withdrawal_until IS NULL OR meat_withdrawal_until >= treatment_date",
            name=("ck_treatment_records_meat_withdrawal_valid"),
        ),
        CheckConstraint(
            "status IN ('PLANNED', 'ACTIVE', 'COMPLETED', 'CANCELLED')",
            name="ck_treatment_records_valid_status",
        ),
        CheckConstraint(
            "("
            "status = 'COMPLETED' "
            "AND completed_by IS NOT NULL "
            "AND completed_at IS NOT NULL"
            ") OR ("
            "status <> 'COMPLETED' "
            "AND completed_by IS NULL "
            "AND completed_at IS NULL"
            ")",
            name=("ck_treatment_records_completion_fields"),
        ),
        Index(
            "ix_treatment_records_farm_date",
            "farm_id",
            "treatment_date",
        ),
        Index(
            "ix_treatment_records_flock_date",
            "flock_id",
            "treatment_date",
        ),
        Index(
            "ix_treatment_records_incident",
            "health_incident_id",
        ),
        Index(
            "ix_treatment_records_farm_status",
            "farm_id",
            "status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "farms.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    flock_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "flocks.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    health_incident_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "health_incidents.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "health_products.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    product_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    treatment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    birds_treated: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    dose: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    route: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default=VaccinationRoute.OTHER.value,
        server_default=VaccinationRoute.OTHER.value,
    )

    purpose: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    prescribed_by: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    treatment_cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    egg_withdrawal_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    meat_withdrawal_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    egg_withdrawal_until: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    meat_withdrawal_until: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=TreatmentStatus.ACTIVE.value,
        server_default=TreatmentStatus.ACTIVE.value,
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    recorded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    completed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    farm: Mapped[Farm] = relationship(
        lazy="selectin",
    )

    flock: Mapped[Flock] = relationship(
        lazy="selectin",
    )

    health_incident: Mapped[HealthIncident | None] = relationship(
        back_populates="treatments",
        lazy="selectin",
    )

    product: Mapped[HealthProduct | None] = relationship(
        lazy="selectin",
    )

    @property
    def is_egg_withdrawal_active(self) -> bool:
        return (
            self.egg_withdrawal_until is not None
            and self.egg_withdrawal_until >= date.today()
            and self.status != TreatmentStatus.CANCELLED.value
        )

    @property
    def is_meat_withdrawal_active(self) -> bool:
        return (
            self.meat_withdrawal_until is not None
            and self.meat_withdrawal_until >= date.today()
            and self.status != TreatmentStatus.CANCELLED.value
        )

    @property
    def is_completed(self) -> bool:
        return self.status == TreatmentStatus.COMPLETED.value

    def __repr__(self) -> str:
        return (
            "TreatmentRecord("
            f"id={self.id!r}, "
            f"flock_id={self.flock_id!r}, "
            f"product_name={self.product_name!r}, "
            f"treatment_date={self.treatment_date!r}, "
            f"status={self.status!r}"
            ")"
        )


def calculate_withdrawal_until(
    treatment_date: date,
    withdrawal_days: int,
) -> date | None:
    """Calculate the final withdrawal date."""

    if withdrawal_days < 0:
        raise ValueError("Withdrawal days cannot be negative.")

    if withdrawal_days == 0:
        return None

    return treatment_date + timedelta(days=withdrawal_days)
