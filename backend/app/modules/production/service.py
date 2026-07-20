from datetime import UTC, date, datetime
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BusinessRuleError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.modules.flocks.constants import (
    FlockProductionStage,
    FlockStatus,
)
from app.modules.production.constants import (
    ProductionRecordStatus,
)
from app.modules.production.models import (
    DailyEggProduction,
)
from app.modules.production.repository import (
    DailyEggProductionRepository,
)
from app.modules.production.schemas import (
    DailyEggProductionCreate,
    DailyEggProductionUpdate,
)


ALLOWED_FLOCK_STATUSES = {
    FlockStatus.ACTIVE.value,
    FlockStatus.SUSPENDED.value,
}

ALLOWED_PRODUCTION_STAGES = {
    FlockProductionStage.POINT_OF_LAY.value,
    FlockProductionStage.LAYING.value,
    FlockProductionStage.MOLTING.value,
}

EDITABLE_PRODUCTION_STATUSES = {
    ProductionRecordStatus.DRAFT.value,
    ProductionRecordStatus.REJECTED.value,
}


class DailyEggProductionService:
    """Business operations for daily egg production."""

    def __init__(
        self,
        database_session: Session,
    ) -> None:
        self.database_session = database_session
        self.repository = DailyEggProductionRepository(database_session)

    @staticmethod
    def _get_counts(
        production: DailyEggProduction,
    ) -> dict[str, int]:
        return {
            "morning_eggs": production.morning_eggs,
            "afternoon_eggs": production.afternoon_eggs,
            "evening_eggs": production.evening_eggs,
            "large_eggs": production.large_eggs,
            "medium_eggs": production.medium_eggs,
            "small_eggs": production.small_eggs,
            "damaged_eggs": production.damaged_eggs,
            "rejected_eggs": production.rejected_eggs,
        }

    @staticmethod
    def _calculate_total_collected(
        counts: dict[str, int],
    ) -> int:
        return (
            counts["morning_eggs"] + counts["afternoon_eggs"] + counts["evening_eggs"]
        )

    @staticmethod
    def _calculate_total_graded(
        counts: dict[str, int],
    ) -> int:
        return (
            counts["large_eggs"]
            + counts["medium_eggs"]
            + counts["small_eggs"]
            + counts["damaged_eggs"]
            + counts["rejected_eggs"]
        )

    def _validate_counts(
        self,
        *,
        counts: dict[str, int],
        birds_present: int,
        require_complete_grading: bool,
    ) -> None:
        total_collected = self._calculate_total_collected(counts)

        total_graded = self._calculate_total_graded(counts)

        if total_graded > total_collected:
            raise BusinessRuleError(
                "Total graded eggs cannot exceed total collected eggs.",
                error_code=("production_grading_exceeds_collection"),
            )

        if total_collected > birds_present:
            raise BusinessRuleError(
                "Total collected eggs cannot exceed the number of birds present.",
                error_code=("production_exceeds_birds_present"),
            )

        if require_complete_grading and total_graded != total_collected:
            raise BusinessRuleError(
                "Every collected egg must be graded before the record is submitted.",
                error_code="production_grading_incomplete",
            )

        if require_complete_grading and total_collected <= 0:
            raise BusinessRuleError(
                "A production record must contain at "
                "least one collected egg before submission.",
                error_code="production_collection_empty",
            )

    def _get_record(
        self,
        farm_id: UUID,
        production_id: UUID,
        *,
        for_update: bool = False,
    ) -> DailyEggProduction:
        production = self.repository.get_by_id(
            farm_id,
            production_id,
            for_update=for_update,
        )

        if production is None:
            raise ResourceNotFoundError(
                "The requested production record does not exist.",
                error_code="production_record_not_found",
            )

        return production

    def create_record(
        self,
        farm_id: UUID,
        recorded_by: UUID,
        payload: DailyEggProductionCreate,
    ) -> DailyEggProduction:
        flock = self.repository.get_flock(
            farm_id,
            payload.flock_id,
        )

        if flock is None:
            raise ResourceNotFoundError(
                "The selected flock does not exist.",
                error_code="flock_not_found",
            )

        if payload.production_date < flock.arrival_date:
            raise BusinessRuleError(
                "Production cannot be recorded before the flock arrival date.",
                error_code=("production_date_before_flock_arrival"),
            )

        if flock.status not in ALLOWED_FLOCK_STATUSES:
            raise BusinessRuleError(
                "Production cannot be recorded for a closed or planned flock.",
                error_code="flock_not_open_for_production",
            )

        if flock.production_stage not in ALLOWED_PRODUCTION_STAGES:
            raise BusinessRuleError(
                "The selected flock is not currently in an egg-producing stage.",
                error_code="flock_not_in_production_stage",
            )

        existing_record = self.repository.get_by_flock_and_date(
            farm_id,
            payload.flock_id,
            payload.production_date,
        )

        if existing_record is not None:
            raise ResourceConflictError(
                "A production record already exists for this flock and date.",
                error_code=("production_record_already_exists"),
            )

        birds_present = self.repository.get_population_as_of_date(
            farm_id,
            payload.flock_id,
            payload.production_date,
        )

        if birds_present <= 0:
            raise BusinessRuleError(
                "The flock had no live birds on the selected production date.",
                error_code=("no_flock_population_on_production_date"),
            )

        production = DailyEggProduction(
            farm_id=farm_id,
            flock_id=payload.flock_id,
            production_date=payload.production_date,
            birds_present=birds_present,
            morning_eggs=payload.morning_eggs,
            afternoon_eggs=payload.afternoon_eggs,
            evening_eggs=payload.evening_eggs,
            large_eggs=payload.large_eggs,
            medium_eggs=payload.medium_eggs,
            small_eggs=payload.small_eggs,
            damaged_eggs=payload.damaged_eggs,
            rejected_eggs=payload.rejected_eggs,
            status=ProductionRecordStatus.DRAFT.value,
            notes=payload.notes,
            rejection_reason=None,
            revision_number=1,
            recorded_by=recorded_by,
            last_updated_by=recorded_by,
        )

        self._validate_counts(
            counts=self._get_counts(production),
            birds_present=birds_present,
            require_complete_grading=False,
        )

        self.repository.add(production)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The production record could not be "
                "created because a record already exists "
                "for this flock and date.",
                error_code="production_creation_conflict",
            ) from exc

        return self._get_record(
            farm_id,
            production.id,
        )

    def list_records(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        date_from: date | None,
        date_to: date | None,
        record_status: ProductionRecordStatus | None,
        flock_id: UUID | None,
        search: str | None,
    ) -> tuple[list[DailyEggProduction], int]:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise BusinessRuleError(
                "The start date cannot be after the end date.",
                error_code="invalid_production_date_range",
            )

        return self.repository.list_records(
            farm_id,
            offset=offset,
            limit=limit,
            date_from=date_from,
            date_to=date_to,
            record_status=(record_status.value if record_status is not None else None),
            flock_id=flock_id,
            search=search,
        )

    def get_record(
        self,
        farm_id: UUID,
        production_id: UUID,
    ) -> DailyEggProduction:
        return self._get_record(
            farm_id,
            production_id,
        )

    def update_record(
        self,
        farm_id: UUID,
        production_id: UUID,
        updated_by: UUID,
        payload: DailyEggProductionUpdate,
    ) -> DailyEggProduction:
        production = self._get_record(
            farm_id,
            production_id,
            for_update=True,
        )

        if production.status not in EDITABLE_PRODUCTION_STATUSES:
            raise BusinessRuleError(
                "Only draft or rejected production records may be edited.",
                error_code="production_record_locked",
            )

        changes = payload.model_dump(exclude_unset=True)

        if not changes:
            return production

        current_counts = self._get_counts(production)

        for field_name in current_counts:
            if field_name in changes:
                current_counts[field_name] = changes[field_name]

        self._validate_counts(
            counts=current_counts,
            birds_present=production.birds_present,
            require_complete_grading=False,
        )

        changes["last_updated_by"] = updated_by
        changes["revision_number"] = production.revision_number + 1

        if production.status == ProductionRecordStatus.REJECTED.value:
            changes.update(
                {
                    "status": (ProductionRecordStatus.DRAFT.value),
                    "rejection_reason": None,
                    "rejected_by": None,
                    "rejected_at": None,
                    "submitted_by": None,
                    "submitted_at": None,
                }
            )

        self.repository.update(
            production,
            changes,
        )

        self.database_session.commit()

        return self._get_record(
            farm_id,
            production_id,
        )

    def submit_record(
        self,
        farm_id: UUID,
        production_id: UUID,
        submitted_by: UUID,
    ) -> DailyEggProduction:
        production = self._get_record(
            farm_id,
            production_id,
            for_update=True,
        )

        if production.status != ProductionRecordStatus.DRAFT.value:
            raise BusinessRuleError(
                "Only a draft production record may be submitted.",
                error_code="production_not_draft",
            )

        self._validate_counts(
            counts=self._get_counts(production),
            birds_present=production.birds_present,
            require_complete_grading=True,
        )

        production.status = ProductionRecordStatus.SUBMITTED.value
        production.submitted_by = submitted_by
        production.submitted_at = datetime.now(UTC)
        production.last_updated_by = submitted_by
        production.rejection_reason = None
        production.rejected_by = None
        production.rejected_at = None

        self.database_session.commit()

        return self._get_record(
            farm_id,
            production_id,
        )

    def confirm_record(
        self,
        farm_id: UUID,
        production_id: UUID,
        confirmed_by: UUID,
    ) -> DailyEggProduction:
        production = self._get_record(
            farm_id,
            production_id,
            for_update=True,
        )

        if production.status != ProductionRecordStatus.SUBMITTED.value:
            raise BusinessRuleError(
                "Only a submitted production record may be confirmed.",
                error_code="production_not_submitted",
            )

        self._validate_counts(
            counts=self._get_counts(production),
            birds_present=production.birds_present,
            require_complete_grading=True,
        )

        production.status = ProductionRecordStatus.CONFIRMED.value
        production.confirmed_by = confirmed_by
        production.confirmed_at = datetime.now(UTC)
        production.last_updated_by = confirmed_by

        try:
            self.database_session.flush()

            from app.modules.eggs.service import (
                EggInventoryService,
            )

            EggInventoryService(self.database_session).post_confirmed_production(
                production,
                confirmed_by,
                commit=False,
            )

            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The production record could not be "
                "confirmed or posted to egg inventory.",
                error_code=("production_confirmation_conflict"),
            ) from exc

        return self._get_record(
            farm_id,
            production_id,
        )

    def reject_record(
        self,
        farm_id: UUID,
        production_id: UUID,
        rejected_by: UUID,
        reason: str,
    ) -> DailyEggProduction:
        production = self._get_record(
            farm_id,
            production_id,
            for_update=True,
        )

        if production.status != ProductionRecordStatus.SUBMITTED.value:
            raise BusinessRuleError(
                "Only a submitted production record may be rejected.",
                error_code="production_not_submitted",
            )

        production.status = ProductionRecordStatus.REJECTED.value
        production.rejection_reason = reason
        production.rejected_by = rejected_by
        production.rejected_at = datetime.now(UTC)
        production.confirmed_by = None
        production.confirmed_at = None
        production.last_updated_by = rejected_by

        self.database_session.commit()

        return self._get_record(
            farm_id,
            production_id,
        )

    def get_summary(
        self,
        farm_id: UUID,
        *,
        date_from: date | None,
        date_to: date | None,
        record_status: ProductionRecordStatus | None,
        flock_id: UUID | None,
    ) -> tuple[
        date,
        date,
        dict[str, int],
        Decimal,
    ]:
        resolved_date_from = date_from or date.today()

        resolved_date_to = date_to or date.today()

        if resolved_date_from > resolved_date_to:
            raise BusinessRuleError(
                "The start date cannot be after the end date.",
                error_code="invalid_production_date_range",
            )

        if resolved_date_to > date.today():
            raise BusinessRuleError(
                "Production summary end date cannot be in the future.",
                error_code="future_production_summary_date",
            )

        summary = self.repository.get_summary(
            farm_id,
            date_from=resolved_date_from,
            date_to=resolved_date_to,
            record_status=(record_status.value if record_status is not None else None),
            flock_id=flock_id,
        )

        if summary["bird_days"] <= 0:
            weighted_percentage = Decimal("0.00")
        else:
            weighted_percentage = (
                Decimal(summary["total_collected"])
                / Decimal(summary["bird_days"])
                * Decimal("100")
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )

        return (
            resolved_date_from,
            resolved_date_to,
            summary,
            weighted_percentage,
        )
