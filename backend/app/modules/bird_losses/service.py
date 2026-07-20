from datetime import UTC, date, datetime
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BusinessRuleError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.modules.bird_losses.constants import (
    BirdLossRecordStatus,
    BirdLossType,
)
from app.modules.bird_losses.models import (
    BirdLossRecord,
    calculate_bird_loss_percentage,
    calculate_population_after,
)
from app.modules.bird_losses.repository import (
    BirdLossRepository,
)
from app.modules.bird_losses.schemas import (
    BirdLossCreate,
)
from app.modules.flocks.constants import (
    FlockStatus,
    PopulationTransactionType,
)
from app.modules.flocks.models import (
    FlockPopulationTransaction,
)


RECORDABLE_FLOCK_STATUSES = {
    FlockStatus.ACTIVE.value,
    FlockStatus.SUSPENDED.value,
}

NON_REVERSIBLE_FLOCK_STATUSES = {
    FlockStatus.SOLD.value,
    FlockStatus.ARCHIVED.value,
}


class BirdLossService:
    """Business operations for mortality and culling."""

    def __init__(
        self,
        database_session: Session,
    ) -> None:
        self.database_session = database_session
        self.repository = BirdLossRepository(database_session)

    @staticmethod
    def _quantize_percentage(
        value: Decimal,
    ) -> Decimal:
        return value.quantize(
            Decimal("0.0001"),
            rounding=ROUND_HALF_UP,
        )

    def _get_mortality_threshold(
        self,
        farm_id: UUID,
    ) -> Decimal:
        settings = self.repository.get_farm_settings(farm_id)

        if settings is None:
            raise ResourceNotFoundError(
                "Farm settings were not found.",
                error_code="farm_settings_not_found",
            )

        possible_field_names = (
            "mortality_alert_threshold_percentage",
            "mortality_alert_threshold_percent",
            "mortality_threshold_percentage",
            "mortality_threshold_percent",
            "mortality_threshold",
        )

        for field_name in possible_field_names:
            value = getattr(
                settings,
                field_name,
                None,
            )

            if value is not None:
                return self._quantize_percentage(Decimal(str(value)))

        return Decimal("1.0000")

    def _get_record(
        self,
        farm_id: UUID,
        record_id: UUID,
        *,
        for_update: bool = False,
    ) -> BirdLossRecord:
        record = self.repository.get_record(
            farm_id,
            record_id,
            for_update=for_update,
        )

        if record is None:
            raise ResourceNotFoundError(
                "The requested mortality or culling record does not exist.",
                error_code="bird_loss_record_not_found",
            )

        return record

    def _get_daily_mortality_metrics(
        self,
        farm_id: UUID,
        flock_id: UUID,
        loss_date: date,
    ) -> tuple[int, Decimal, Decimal, bool]:
        daily_mortality = self.repository.get_daily_active_mortality(
            farm_id,
            flock_id,
            loss_date,
        )

        population_after_daily_events = self.repository.get_population_as_of_date(
            farm_id,
            flock_id,
            loss_date,
        )

        estimated_start_population = population_after_daily_events + daily_mortality

        if estimated_start_population <= 0:
            daily_percentage = Decimal("0.0000")
        else:
            daily_percentage = (
                Decimal(daily_mortality)
                / Decimal(estimated_start_population)
                * Decimal("100")
            ).quantize(
                Decimal("0.0001"),
                rounding=ROUND_HALF_UP,
            )

        threshold = self._get_mortality_threshold(farm_id)

        return (
            daily_mortality,
            daily_percentage,
            threshold,
            (daily_percentage >= threshold and daily_mortality > 0),
        )

    def create_record(
        self,
        farm_id: UUID,
        recorded_by: UUID,
        payload: BirdLossCreate,
    ) -> BirdLossRecord:
        flock = self.repository.get_flock(
            farm_id,
            payload.flock_id,
            for_update=True,
        )

        if flock is None:
            raise ResourceNotFoundError(
                "The selected flock does not exist.",
                error_code="flock_not_found",
            )

        if flock.status not in RECORDABLE_FLOCK_STATUSES:
            raise BusinessRuleError(
                "Mortality or culling cannot be recorded for this flock status.",
                error_code="flock_not_open_for_bird_loss",
            )

        if payload.loss_date < flock.arrival_date:
            raise BusinessRuleError(
                "Bird loss cannot occur before the flock arrival date.",
                error_code="bird_loss_before_arrival",
            )

        population_before = self.repository.get_population_as_of_date(
            farm_id,
            flock.id,
            payload.loss_date,
        )

        current_population = self.repository.get_current_population(
            farm_id,
            flock.id,
        )

        if population_before <= 0:
            raise BusinessRuleError(
                "The flock had no live birds on the selected loss date.",
                error_code=("no_flock_population_on_loss_date"),
            )

        if payload.quantity > population_before:
            raise BusinessRuleError(
                "The recorded loss exceeds the flock population on the selected date.",
                error_code=("bird_loss_exceeds_historical_population"),
            )

        if payload.quantity > current_population:
            raise BusinessRuleError(
                "The recorded loss would make the current flock population negative.",
                error_code=("bird_loss_exceeds_current_population"),
            )

        population_after = calculate_population_after(
            population_before,
            payload.quantity,
        )

        current_population_after = current_population - payload.quantity

        loss_percentage = calculate_bird_loss_percentage(
            payload.quantity,
            population_before,
        )

        record_id = uuid4()
        transaction_id = uuid4()

        transaction_type = (
            PopulationTransactionType.MORTALITY.value
            if payload.loss_type == BirdLossType.MORTALITY
            else PopulationTransactionType.CULLING.value
        )

        population_transaction = FlockPopulationTransaction(
            id=transaction_id,
            farm_id=farm_id,
            flock_id=flock.id,
            transaction_date=payload.loss_date,
            transaction_type=transaction_type,
            quantity=payload.quantity,
            signed_quantity=-payload.quantity,
            source_type="BIRD_LOSS_RECORD",
            source_id=record_id,
            description=(
                "Automatic flock-population reduction "
                "created from a mortality or "
                "culling record."
            ),
            created_by=recorded_by,
        )

        record = BirdLossRecord(
            id=record_id,
            farm_id=farm_id,
            flock_id=flock.id,
            loss_date=payload.loss_date,
            loss_type=payload.loss_type.value,
            quantity=payload.quantity,
            reason_category=(payload.reason_category.value),
            cause_details=payload.cause_details,
            disposal_method=(payload.disposal_method.value),
            disposal_details=payload.disposal_details,
            location=payload.location,
            reference=payload.reference,
            population_before=population_before,
            population_after=population_after,
            loss_percentage=loss_percentage,
            notes=payload.notes,
            status=BirdLossRecordStatus.ACTIVE.value,
            population_transaction_id=transaction_id,
            recorded_by=recorded_by,
        )

        self.repository.add_population_transaction(population_transaction)
        self.repository.add_record(record)

        if current_population_after == 0:
            flock.status = FlockStatus.DEPLETED.value

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The mortality or culling record could not be saved.",
                error_code="bird_loss_creation_conflict",
            ) from exc

        return self._get_record(
            farm_id,
            record_id,
        )

    def get_record(
        self,
        farm_id: UUID,
        record_id: UUID,
    ) -> BirdLossRecord:
        return self._get_record(
            farm_id,
            record_id,
        )

    def list_records(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        date_from: date | None,
        date_to: date | None,
        flock_id: UUID | None,
        loss_type: BirdLossType | None,
        reason_category: str | None,
        record_status: BirdLossRecordStatus | None,
        search: str | None,
    ) -> tuple[list[BirdLossRecord], int]:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise BusinessRuleError(
                "The start date cannot be after the end date.",
                error_code="invalid_bird_loss_date_range",
            )

        return self.repository.list_records(
            farm_id,
            offset=offset,
            limit=limit,
            date_from=date_from,
            date_to=date_to,
            flock_id=flock_id,
            loss_type=(loss_type.value if loss_type is not None else None),
            reason_category=reason_category,
            record_status=(record_status.value if record_status is not None else None),
            search=search,
        )

    def reverse_record(
        self,
        farm_id: UUID,
        record_id: UUID,
        reversed_by: UUID,
        *,
        reversal_date: date,
        reason: str,
    ) -> BirdLossRecord:
        record = self._get_record(
            farm_id,
            record_id,
            for_update=True,
        )

        if record.status != BirdLossRecordStatus.ACTIVE.value:
            raise ResourceConflictError(
                "This mortality or culling record has already been reversed.",
                error_code=("bird_loss_record_already_reversed"),
            )

        if reversal_date < record.loss_date:
            raise BusinessRuleError(
                "The reversal date cannot be before the original loss date.",
                error_code=("bird_loss_reversal_before_loss"),
            )

        flock = self.repository.get_flock(
            farm_id,
            record.flock_id,
            for_update=True,
        )

        if flock is None:
            raise ResourceNotFoundError(
                "The associated flock does not exist.",
                error_code="flock_not_found",
            )

        if flock.status in NON_REVERSIBLE_FLOCK_STATUSES:
            raise BusinessRuleError(
                "Bird loss cannot be reversed for a sold or archived flock.",
                error_code=("flock_closed_for_loss_reversal"),
            )

        house = self.repository.get_house(
            farm_id,
            flock.house_id,
            for_update=True,
        )

        if house is None:
            raise ResourceNotFoundError(
                "The associated poultry house does not exist.",
                error_code="poultry_house_not_found",
            )

        house_occupancy = self.repository.get_house_occupancy(
            farm_id,
            house.id,
        )

        projected_occupancy = house_occupancy + record.quantity

        if projected_occupancy > house.capacity:
            available_capacity = max(
                house.capacity - house_occupancy,
                0,
            )

            raise BusinessRuleError(
                "The loss cannot be reversed because "
                "the poultry house lacks capacity. "
                f"Available spaces: {available_capacity}.",
                error_code=("bird_loss_reversal_exceeds_capacity"),
            )

        reversal_transaction_id = uuid4()

        reversal_transaction = FlockPopulationTransaction(
            id=reversal_transaction_id,
            farm_id=farm_id,
            flock_id=record.flock_id,
            transaction_date=reversal_date,
            transaction_type=(PopulationTransactionType.REVERSAL.value),
            quantity=record.quantity,
            signed_quantity=record.quantity,
            source_type="BIRD_LOSS_REVERSAL",
            source_id=record.id,
            description=(
                "Population restoration created "
                "from a mortality or culling "
                f"reversal: {reason}"
            ),
            created_by=reversed_by,
            reversed_transaction_id=(record.population_transaction_id),
        )

        record.status = BirdLossRecordStatus.REVERSED.value
        record.reversal_population_transaction_id = reversal_transaction_id
        record.reversed_by = reversed_by
        record.reversed_at = datetime.now(UTC)
        record.reversal_reason = reason

        current_population = self.repository.get_current_population(
            farm_id,
            flock.id,
        )

        restored_population = current_population + record.quantity

        if restored_population > 0 and flock.status == FlockStatus.DEPLETED.value:
            flock.status = FlockStatus.ACTIVE.value

        self.repository.add_population_transaction(reversal_transaction)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The mortality or culling record could not be reversed.",
                error_code="bird_loss_reversal_conflict",
            ) from exc

        return self._get_record(
            farm_id,
            record_id,
        )

    def get_response_metrics(
        self,
        farm_id: UUID,
        record: BirdLossRecord,
    ) -> tuple[int, int, Decimal, Decimal, bool]:
        current_population = self.repository.get_current_population(
            farm_id,
            record.flock_id,
        )

        (
            daily_mortality,
            daily_percentage,
            threshold,
            alert,
        ) = self._get_daily_mortality_metrics(
            farm_id,
            record.flock_id,
            record.loss_date,
        )

        return (
            current_population,
            daily_mortality,
            daily_percentage,
            threshold,
            alert,
        )

    def get_summary(
        self,
        farm_id: UUID,
        *,
        date_from: date | None,
        date_to: date | None,
        flock_id: UUID | None,
    ) -> tuple[
        date,
        date,
        Decimal,
        dict[str, int | Decimal],
        int | None,
    ]:
        resolved_date_from = date_from or date.today()
        resolved_date_to = date_to or date.today()

        if resolved_date_from > resolved_date_to:
            raise BusinessRuleError(
                "The start date cannot be after the end date.",
                error_code="invalid_bird_loss_date_range",
            )

        if resolved_date_to > date.today():
            raise BusinessRuleError(
                "Summary end date cannot be in the future.",
                error_code="future_bird_loss_summary_date",
            )

        threshold = self._get_mortality_threshold(farm_id)

        if flock_id is not None:
            flock = self.repository.get_flock(
                farm_id,
                flock_id,
            )

            if flock is None:
                raise ResourceNotFoundError(
                    "The selected flock does not exist.",
                    error_code="flock_not_found",
                )

            current_population: int | None = self.repository.get_current_population(
                farm_id,
                flock_id,
            )
        else:
            current_population = None

        summary = self.repository.get_summary(
            farm_id,
            date_from=resolved_date_from,
            date_to=resolved_date_to,
            flock_id=flock_id,
            mortality_threshold=threshold,
        )

        return (
            resolved_date_from,
            resolved_date_to,
            threshold,
            summary,
            current_population,
        )
