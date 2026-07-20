from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.flocks.models import (
    Flock,
    FlockPopulationTransaction,
)
from app.modules.houses.models import PoultryHouse


class FlockRepository:
    """Database operations for flocks and population ledgers."""

    def __init__(
        self,
        database_session: Session,
    ) -> None:
        self.database_session = database_session

    def get_by_id(
        self,
        farm_id: UUID,
        flock_id: UUID,
        *,
        for_update: bool = False,
    ) -> Flock | None:
        statement = (
            select(Flock)
            .options(
                selectinload(Flock.house),
                selectinload(Flock.supplier),
            )
            .where(
                Flock.farm_id == farm_id,
                Flock.id == flock_id,
            )
        )

        if for_update:
            statement = statement.with_for_update()

        return self.database_session.scalar(statement)

    def get_by_code(
        self,
        farm_id: UUID,
        flock_code: str,
    ) -> Flock | None:
        statement = select(Flock).where(
            Flock.farm_id == farm_id,
            Flock.flock_code == flock_code,
        )

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

    def list_flocks(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        flock_status: str | None,
        production_stage: str | None,
        house_id: UUID | None,
        supplier_id: UUID | None,
        search: str | None,
    ) -> tuple[list[Flock], int]:
        conditions = [Flock.farm_id == farm_id]

        if flock_status is not None:
            conditions.append(Flock.status == flock_status)

        if production_stage is not None:
            conditions.append(Flock.production_stage == production_stage)

        if house_id is not None:
            conditions.append(Flock.house_id == house_id)

        if supplier_id is not None:
            conditions.append(Flock.supplier_id == supplier_id)

        if search:
            search_pattern = f"%{search.strip()}%"

            conditions.append(
                or_(
                    Flock.flock_code.ilike(search_pattern),
                    Flock.name.ilike(search_pattern),
                    Flock.breed.ilike(search_pattern),
                )
            )

        flocks_statement = (
            select(Flock)
            .options(
                selectinload(Flock.house),
                selectinload(Flock.supplier),
            )
            .where(*conditions)
            .order_by(
                Flock.arrival_date.desc(),
                Flock.flock_code.asc(),
            )
            .offset(offset)
            .limit(limit)
        )

        count_statement = select(func.count(Flock.id)).where(*conditions)

        flocks = list(self.database_session.scalars(flocks_statement).all())

        total = self.database_session.scalar(count_statement) or 0

        return flocks, total

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

    def get_population_totals(
        self,
        farm_id: UUID,
        flock_ids: list[UUID],
    ) -> dict[UUID, int]:
        if not flock_ids:
            return {}

        statement = (
            select(
                FlockPopulationTransaction.flock_id,
                func.coalesce(
                    func.sum(FlockPopulationTransaction.signed_quantity),
                    0,
                ),
            )
            .where(
                FlockPopulationTransaction.farm_id == farm_id,
                FlockPopulationTransaction.flock_id.in_(flock_ids),
            )
            .group_by(FlockPopulationTransaction.flock_id)
        )

        return {
            flock_id: int(population)
            for flock_id, population in self.database_session.execute(statement).all()
        }

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

    def list_population_transactions(
        self,
        farm_id: UUID,
        flock_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[
        list[FlockPopulationTransaction],
        int,
    ]:
        conditions = [
            FlockPopulationTransaction.farm_id == farm_id,
            FlockPopulationTransaction.flock_id == flock_id,
        ]

        transactions_statement = (
            select(FlockPopulationTransaction)
            .where(*conditions)
            .order_by(
                FlockPopulationTransaction.transaction_date.desc(),
                FlockPopulationTransaction.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        count_statement = select(func.count(FlockPopulationTransaction.id)).where(
            *conditions
        )

        transactions = list(self.database_session.scalars(transactions_statement).all())

        total = self.database_session.scalar(count_statement) or 0

        return transactions, total

    def add_flock(self, flock: Flock) -> Flock:
        self.database_session.add(flock)
        return flock

    def add_population_transaction(
        self,
        transaction: FlockPopulationTransaction,
    ) -> FlockPopulationTransaction:
        self.database_session.add(transaction)
        return transaction

    def update_flock(
        self,
        flock: Flock,
        changes: dict[str, Any],
    ) -> Flock:
        for field_name, field_value in changes.items():
            setattr(
                flock,
                field_name,
                field_value,
            )

        self.database_session.add(flock)
        return flock
