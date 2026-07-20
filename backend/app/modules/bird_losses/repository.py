from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.bird_losses.constants import (
    BirdLossRecordStatus,
    BirdLossType,
)
from app.modules.bird_losses.models import (
    BirdLossRecord,
)
from app.modules.farms.models import FarmSettings
from app.modules.flocks.models import (
    Flock,
    FlockPopulationTransaction,
)
from app.modules.houses.models import PoultryHouse


class BirdLossRepository:
    """Database operations for mortality and culling."""

    def __init__(
        self,
        database_session: Session,
    ) -> None:
        self.database_session = database_session

    def get_farm_settings(
        self,
        farm_id: UUID,
    ) -> FarmSettings | None:
        statement = select(FarmSettings).where(FarmSettings.farm_id == farm_id)

        return self.database_session.scalar(statement)

    def get_flock(
        self,
        farm_id: UUID,
        flock_id: UUID,
        *,
        for_update: bool = False,
    ) -> Flock | None:
        statement = (
            select(Flock)
            .options(selectinload(Flock.house))
            .where(
                Flock.farm_id == farm_id,
                Flock.id == flock_id,
            )
        )

        if for_update:
            statement = statement.with_for_update()

        return self.database_session.scalar(statement)

    def get_house(
        self,
        farm_id: UUID,
        house_id: UUID,
        *,
        for_update: bool = False,
    ) -> PoultryHouse | None:
        statement = select(PoultryHouse).where(
            PoultryHouse.farm_id == farm_id,
            PoultryHouse.id == house_id,
        )

        if for_update:
            statement = statement.with_for_update()

        return self.database_session.scalar(statement)

    def get_record(
        self,
        farm_id: UUID,
        record_id: UUID,
        *,
        for_update: bool = False,
    ) -> BirdLossRecord | None:
        statement = (
            select(BirdLossRecord)
            .options(
                selectinload(BirdLossRecord.flock).selectinload(Flock.house),
                selectinload(BirdLossRecord.population_transaction),
                selectinload(BirdLossRecord.reversal_population_transaction),
            )
            .where(
                BirdLossRecord.farm_id == farm_id,
                BirdLossRecord.id == record_id,
            )
        )

        if for_update:
            statement = statement.with_for_update()

        return self.database_session.scalar(statement)

    def get_current_population(
        self,
        farm_id: UUID,
        flock_id: UUID,
    ) -> int:
        statement = select(
            func.coalesce(
                func.sum(FlockPopulationTransaction.signed_quantity),
                0,
            )
        ).where(
            FlockPopulationTransaction.farm_id == farm_id,
            FlockPopulationTransaction.flock_id == flock_id,
        )

        return int(self.database_session.scalar(statement) or 0)

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

    def get_house_occupancy(
        self,
        farm_id: UUID,
        house_id: UUID,
    ) -> int:
        statement = (
            select(
                func.coalesce(
                    func.sum(FlockPopulationTransaction.signed_quantity),
                    0,
                )
            )
            .join(
                Flock,
                Flock.id == FlockPopulationTransaction.flock_id,
            )
            .where(
                Flock.farm_id == farm_id,
                Flock.house_id == house_id,
            )
        )

        return int(self.database_session.scalar(statement) or 0)

    def get_daily_active_mortality(
        self,
        farm_id: UUID,
        flock_id: UUID,
        loss_date: date,
    ) -> int:
        statement = select(
            func.coalesce(
                func.sum(BirdLossRecord.quantity),
                0,
            )
        ).where(
            BirdLossRecord.farm_id == farm_id,
            BirdLossRecord.flock_id == flock_id,
            BirdLossRecord.loss_date == loss_date,
            BirdLossRecord.loss_type == BirdLossType.MORTALITY.value,
            BirdLossRecord.status == BirdLossRecordStatus.ACTIVE.value,
        )

        return int(self.database_session.scalar(statement) or 0)

    def list_records(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        date_from: date | None,
        date_to: date | None,
        flock_id: UUID | None,
        loss_type: str | None,
        reason_category: str | None,
        record_status: str | None,
        search: str | None,
    ) -> tuple[list[BirdLossRecord], int]:
        conditions = [BirdLossRecord.farm_id == farm_id]

        if date_from is not None:
            conditions.append(BirdLossRecord.loss_date >= date_from)

        if date_to is not None:
            conditions.append(BirdLossRecord.loss_date <= date_to)

        if flock_id is not None:
            conditions.append(BirdLossRecord.flock_id == flock_id)

        if loss_type is not None:
            conditions.append(BirdLossRecord.loss_type == loss_type)

        if reason_category is not None:
            conditions.append(BirdLossRecord.reason_category == reason_category)

        if record_status is not None:
            conditions.append(BirdLossRecord.status == record_status)

        if search:
            search_pattern = f"%{search.strip()}%"

            conditions.append(
                or_(
                    Flock.flock_code.ilike(search_pattern),
                    Flock.name.ilike(search_pattern),
                    BirdLossRecord.cause_details.ilike(search_pattern),
                    BirdLossRecord.reference.ilike(search_pattern),
                    BirdLossRecord.notes.ilike(search_pattern),
                )
            )

        records_statement = (
            select(BirdLossRecord)
            .join(
                Flock,
                Flock.id == BirdLossRecord.flock_id,
            )
            .options(
                selectinload(BirdLossRecord.flock).selectinload(Flock.house),
                selectinload(BirdLossRecord.population_transaction),
                selectinload(BirdLossRecord.reversal_population_transaction),
            )
            .where(*conditions)
            .order_by(
                BirdLossRecord.loss_date.desc(),
                BirdLossRecord.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        count_statement = (
            select(func.count(BirdLossRecord.id))
            .join(
                Flock,
                Flock.id == BirdLossRecord.flock_id,
            )
            .where(*conditions)
        )

        records = list(self.database_session.scalars(records_statement).all())

        total = self.database_session.scalar(count_statement) or 0

        return records, total

    def get_summary(
        self,
        farm_id: UUID,
        *,
        date_from: date,
        date_to: date,
        flock_id: UUID | None,
        mortality_threshold: Decimal,
    ) -> dict[str, int | Decimal]:
        base_conditions = [
            BirdLossRecord.farm_id == farm_id,
            BirdLossRecord.loss_date >= date_from,
            BirdLossRecord.loss_date <= date_to,
        ]

        if flock_id is not None:
            base_conditions.append(BirdLossRecord.flock_id == flock_id)

        active_conditions = [
            *base_conditions,
            BirdLossRecord.status == BirdLossRecordStatus.ACTIVE.value,
        ]

        aggregate_statement = select(
            func.count(BirdLossRecord.id).label("active_record_count"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            BirdLossRecord.loss_type == BirdLossType.MORTALITY.value,
                            BirdLossRecord.quantity,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("mortality_quantity"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            BirdLossRecord.loss_type == BirdLossType.CULLING.value,
                            BirdLossRecord.quantity,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("culling_quantity"),
            func.coalesce(
                func.avg(BirdLossRecord.loss_percentage),
                0,
            ).label("average_incident_loss_percentage"),
            func.coalesce(
                func.max(BirdLossRecord.loss_percentage),
                0,
            ).label("maximum_incident_loss_percentage"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            (BirdLossRecord.loss_type == BirdLossType.MORTALITY.value)
                            & (BirdLossRecord.loss_percentage >= mortality_threshold),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("high_mortality_incidents"),
        ).where(*active_conditions)

        aggregate_row = self.database_session.execute(aggregate_statement).one()

        reversed_count = (
            self.database_session.scalar(
                select(func.count(BirdLossRecord.id)).where(
                    *base_conditions,
                    BirdLossRecord.status == BirdLossRecordStatus.REVERSED.value,
                )
            )
            or 0
        )

        mapping = aggregate_row._mapping

        return {
            "active_record_count": int(mapping["active_record_count"] or 0),
            "reversed_record_count": int(reversed_count),
            "mortality_quantity": int(mapping["mortality_quantity"] or 0),
            "culling_quantity": int(mapping["culling_quantity"] or 0),
            "average_incident_loss_percentage": (
                Decimal(str(mapping["average_incident_loss_percentage"] or 0))
            ),
            "maximum_incident_loss_percentage": (
                Decimal(str(mapping["maximum_incident_loss_percentage"] or 0))
            ),
            "high_mortality_incidents": int(mapping["high_mortality_incidents"] or 0),
        }

    def add_record(
        self,
        record: BirdLossRecord,
    ) -> BirdLossRecord:
        self.database_session.add(record)
        return record

    def add_population_transaction(
        self,
        transaction: FlockPopulationTransaction,
    ) -> FlockPopulationTransaction:
        self.database_session.add(transaction)
        return transaction
