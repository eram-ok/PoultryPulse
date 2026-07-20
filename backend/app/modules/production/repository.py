from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.flocks.models import (
    Flock,
    FlockPopulationTransaction,
)
from app.modules.production.models import (
    DailyEggProduction,
)


class DailyEggProductionRepository:
    """Database operations for daily egg production."""

    def __init__(
        self,
        database_session: Session,
    ) -> None:
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
        production_date: date,
    ) -> int:
        statement = select(
            func.coalesce(
                func.sum(FlockPopulationTransaction.signed_quantity),
                0,
            )
        ).where(
            FlockPopulationTransaction.farm_id == farm_id,
            FlockPopulationTransaction.flock_id == flock_id,
            FlockPopulationTransaction.transaction_date <= production_date,
        )

        return int(self.database_session.scalar(statement) or 0)

    def get_by_id(
        self,
        farm_id: UUID,
        production_id: UUID,
        *,
        for_update: bool = False,
    ) -> DailyEggProduction | None:
        statement = (
            select(DailyEggProduction)
            .options(selectinload(DailyEggProduction.flock).selectinload(Flock.house))
            .where(
                DailyEggProduction.farm_id == farm_id,
                DailyEggProduction.id == production_id,
            )
        )

        if for_update:
            statement = statement.with_for_update()

        return self.database_session.scalar(statement)

    def get_by_flock_and_date(
        self,
        farm_id: UUID,
        flock_id: UUID,
        production_date: date,
    ) -> DailyEggProduction | None:
        statement = select(DailyEggProduction).where(
            DailyEggProduction.farm_id == farm_id,
            DailyEggProduction.flock_id == flock_id,
            DailyEggProduction.production_date == production_date,
        )

        return self.database_session.scalar(statement)

    def list_records(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        date_from: date | None,
        date_to: date | None,
        record_status: str | None,
        flock_id: UUID | None,
        search: str | None,
    ) -> tuple[list[DailyEggProduction], int]:
        conditions = [DailyEggProduction.farm_id == farm_id]

        if date_from is not None:
            conditions.append(DailyEggProduction.production_date >= date_from)

        if date_to is not None:
            conditions.append(DailyEggProduction.production_date <= date_to)

        if record_status is not None:
            conditions.append(DailyEggProduction.status == record_status)

        if flock_id is not None:
            conditions.append(DailyEggProduction.flock_id == flock_id)

        if search:
            search_pattern = f"%{search.strip()}%"

            conditions.append(
                or_(
                    Flock.flock_code.ilike(search_pattern),
                    Flock.name.ilike(search_pattern),
                    Flock.breed.ilike(search_pattern),
                )
            )

        records_statement = (
            select(DailyEggProduction)
            .join(
                Flock,
                Flock.id == DailyEggProduction.flock_id,
            )
            .options(selectinload(DailyEggProduction.flock).selectinload(Flock.house))
            .where(*conditions)
            .order_by(
                DailyEggProduction.production_date.desc(),
                DailyEggProduction.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        count_statement = (
            select(func.count(DailyEggProduction.id))
            .join(
                Flock,
                Flock.id == DailyEggProduction.flock_id,
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
        record_status: str | None,
        flock_id: UUID | None,
    ) -> dict[str, int]:
        conditions = [
            DailyEggProduction.farm_id == farm_id,
            DailyEggProduction.production_date >= date_from,
            DailyEggProduction.production_date <= date_to,
        ]

        if record_status is not None:
            conditions.append(DailyEggProduction.status == record_status)

        if flock_id is not None:
            conditions.append(DailyEggProduction.flock_id == flock_id)

        total_collected_expression = (
            DailyEggProduction.morning_eggs
            + DailyEggProduction.afternoon_eggs
            + DailyEggProduction.evening_eggs
        )

        saleable_expression = (
            DailyEggProduction.large_eggs
            + DailyEggProduction.medium_eggs
            + DailyEggProduction.small_eggs
        )

        statement = select(
            func.count(DailyEggProduction.id).label("record_count"),
            func.coalesce(
                func.sum(DailyEggProduction.birds_present),
                0,
            ).label("bird_days"),
            func.coalesce(
                func.sum(DailyEggProduction.morning_eggs),
                0,
            ).label("morning_eggs"),
            func.coalesce(
                func.sum(DailyEggProduction.afternoon_eggs),
                0,
            ).label("afternoon_eggs"),
            func.coalesce(
                func.sum(DailyEggProduction.evening_eggs),
                0,
            ).label("evening_eggs"),
            func.coalesce(
                func.sum(total_collected_expression),
                0,
            ).label("total_collected"),
            func.coalesce(
                func.sum(DailyEggProduction.large_eggs),
                0,
            ).label("large_eggs"),
            func.coalesce(
                func.sum(DailyEggProduction.medium_eggs),
                0,
            ).label("medium_eggs"),
            func.coalesce(
                func.sum(DailyEggProduction.small_eggs),
                0,
            ).label("small_eggs"),
            func.coalesce(
                func.sum(DailyEggProduction.damaged_eggs),
                0,
            ).label("damaged_eggs"),
            func.coalesce(
                func.sum(DailyEggProduction.rejected_eggs),
                0,
            ).label("rejected_eggs"),
            func.coalesce(
                func.sum(saleable_expression),
                0,
            ).label("saleable_eggs"),
        ).where(*conditions)

        row = self.database_session.execute(statement).one()

        return {key: int(value or 0) for key, value in row._mapping.items()}

    def add(
        self,
        production: DailyEggProduction,
    ) -> DailyEggProduction:
        self.database_session.add(production)
        return production

    def update(
        self,
        production: DailyEggProduction,
        changes: dict[str, Any],
    ) -> DailyEggProduction:
        for field_name, field_value in changes.items():
            setattr(
                production,
                field_name,
                field_value,
            )

        self.database_session.add(production)
        return production
