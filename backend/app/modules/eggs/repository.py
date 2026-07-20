from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.eggs.models import (
    EggInventoryTransaction,
)
from app.modules.farms.models import FarmSettings


class EggInventoryRepository:
    """Database operations for egg inventory."""

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

    def get_transaction(
        self,
        farm_id: UUID,
        transaction_id: UUID,
        *,
        for_update: bool = False,
    ) -> EggInventoryTransaction | None:
        statement = select(EggInventoryTransaction).where(
            EggInventoryTransaction.farm_id == farm_id,
            EggInventoryTransaction.id == transaction_id,
        )

        if for_update:
            statement = statement.with_for_update()

        return self.database_session.scalar(statement)

    def get_source_transactions(
        self,
        farm_id: UUID,
        *,
        source_type: str,
        source_id: UUID,
        transaction_type: str,
    ) -> list[EggInventoryTransaction]:
        statement = select(EggInventoryTransaction).where(
            EggInventoryTransaction.farm_id == farm_id,
            EggInventoryTransaction.source_type == source_type,
            EggInventoryTransaction.source_id == source_id,
            EggInventoryTransaction.transaction_type == transaction_type,
        )

        return list(self.database_session.scalars(statement).all())

    def get_existing_source_transaction(
        self,
        farm_id: UUID,
        *,
        source_type: str,
        source_id: UUID,
        egg_grade: str,
        transaction_type: str,
    ) -> EggInventoryTransaction | None:
        statement = select(EggInventoryTransaction).where(
            EggInventoryTransaction.farm_id == farm_id,
            EggInventoryTransaction.source_type == source_type,
            EggInventoryTransaction.source_id == source_id,
            EggInventoryTransaction.egg_grade == egg_grade,
            EggInventoryTransaction.transaction_type == transaction_type,
        )

        return self.database_session.scalar(statement)

    def get_reversal_for_transaction(
        self,
        farm_id: UUID,
        transaction_id: UUID,
    ) -> EggInventoryTransaction | None:
        statement = select(EggInventoryTransaction).where(
            EggInventoryTransaction.farm_id == farm_id,
            EggInventoryTransaction.reversed_transaction_id == transaction_id,
        )

        return self.database_session.scalar(statement)

    def get_balance(
        self,
        farm_id: UUID,
        egg_grade: str,
    ) -> int:
        statement = select(
            func.coalesce(
                func.sum(EggInventoryTransaction.signed_quantity),
                0,
            )
        ).where(
            EggInventoryTransaction.farm_id == farm_id,
            EggInventoryTransaction.egg_grade == egg_grade,
        )

        return int(self.database_session.scalar(statement) or 0)

    def get_balances(
        self,
        farm_id: UUID,
    ) -> dict[str, int]:
        statement = (
            select(
                EggInventoryTransaction.egg_grade,
                func.coalesce(
                    func.sum(EggInventoryTransaction.signed_quantity),
                    0,
                ),
            )
            .where(EggInventoryTransaction.farm_id == farm_id)
            .group_by(EggInventoryTransaction.egg_grade)
        )

        return {
            egg_grade: int(balance or 0)
            for egg_grade, balance in self.database_session.execute(statement).all()
        }

    def list_transactions(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        date_from: date | None,
        date_to: date | None,
        egg_grade: str | None,
        transaction_type: str | None,
        source_type: str | None,
    ) -> tuple[
        list[EggInventoryTransaction],
        int,
    ]:
        conditions = [EggInventoryTransaction.farm_id == farm_id]

        if date_from is not None:
            conditions.append(EggInventoryTransaction.inventory_date >= date_from)

        if date_to is not None:
            conditions.append(EggInventoryTransaction.inventory_date <= date_to)

        if egg_grade is not None:
            conditions.append(EggInventoryTransaction.egg_grade == egg_grade)

        if transaction_type is not None:
            conditions.append(
                EggInventoryTransaction.transaction_type == transaction_type
            )

        if source_type is not None:
            conditions.append(EggInventoryTransaction.source_type == source_type)

        records_statement = (
            select(EggInventoryTransaction)
            .where(*conditions)
            .order_by(
                EggInventoryTransaction.inventory_date.desc(),
                EggInventoryTransaction.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        count_statement = select(func.count(EggInventoryTransaction.id)).where(
            *conditions
        )

        records = list(self.database_session.scalars(records_statement).all())

        total = self.database_session.scalar(count_statement) or 0

        return records, total

    def add(
        self,
        transaction: EggInventoryTransaction,
    ) -> EggInventoryTransaction:
        self.database_session.add(transaction)
        return transaction

    def add_all(
        self,
        transactions: list[EggInventoryTransaction],
    ) -> None:
        self.database_session.add_all(transactions)
