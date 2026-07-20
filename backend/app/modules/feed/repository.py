from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.farms.models import FarmSettings
from app.modules.feed.models import (
    FeedInventoryTransaction,
    FeedItem,
    FeedPurchase,
    FeedUsage,
)
from app.modules.flocks.models import (
    Flock,
    FlockPopulationTransaction,
)
from app.modules.suppliers.models import Supplier


class FeedRepository:
    """Database operations for feed management."""

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

    def get_item(
        self,
        farm_id: UUID,
        feed_item_id: UUID,
        *,
        for_update: bool = False,
    ) -> FeedItem | None:
        statement = select(FeedItem).where(
            FeedItem.farm_id == farm_id,
            FeedItem.id == feed_item_id,
        )

        if for_update:
            statement = statement.with_for_update()

        return self.database_session.scalar(statement)

    def get_item_by_code(
        self,
        farm_id: UUID,
        feed_code: str,
    ) -> FeedItem | None:
        statement = select(FeedItem).where(
            FeedItem.farm_id == farm_id,
            FeedItem.feed_code == feed_code,
        )

        return self.database_session.scalar(statement)

    def list_items(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        category: str | None,
        is_active: bool | None,
        search: str | None,
    ) -> tuple[list[FeedItem], int]:
        conditions = [FeedItem.farm_id == farm_id]

        if category is not None:
            conditions.append(FeedItem.category == category)

        if is_active is not None:
            conditions.append(FeedItem.is_active.is_(is_active))

        if search:
            pattern = f"%{search.strip()}%"

            conditions.append(
                or_(
                    FeedItem.feed_code.ilike(pattern),
                    FeedItem.name.ilike(pattern),
                    FeedItem.brand.ilike(pattern),
                    FeedItem.manufacturer.ilike(pattern),
                )
            )

        records_statement = (
            select(FeedItem)
            .where(*conditions)
            .order_by(
                FeedItem.name.asc(),
                FeedItem.feed_code.asc(),
            )
            .offset(offset)
            .limit(limit)
        )

        count_statement = select(func.count(FeedItem.id)).where(*conditions)

        records = list(self.database_session.scalars(records_statement).all())

        total = self.database_session.scalar(count_statement) or 0

        return records, total

    def list_all_items(
        self,
        farm_id: UUID,
    ) -> list[FeedItem]:
        statement = (
            select(FeedItem)
            .where(FeedItem.farm_id == farm_id)
            .order_by(FeedItem.name.asc())
        )

        return list(self.database_session.scalars(statement).all())

    def add_item(
        self,
        feed_item: FeedItem,
    ) -> FeedItem:
        self.database_session.add(feed_item)
        return feed_item

    def update_item(
        self,
        feed_item: FeedItem,
        changes: dict[str, Any],
    ) -> FeedItem:
        for field_name, field_value in changes.items():
            setattr(
                feed_item,
                field_name,
                field_value,
            )

        self.database_session.add(feed_item)
        return feed_item

    def get_supplier(
        self,
        farm_id: UUID,
        supplier_id: UUID,
    ) -> Supplier | None:
        statement = select(Supplier).where(
            Supplier.farm_id == farm_id,
            Supplier.id == supplier_id,
        )

        return self.database_session.scalar(statement)

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
        usage_date: date,
    ) -> int:
        statement = select(
            func.coalesce(
                func.sum(FlockPopulationTransaction.signed_quantity),
                0,
            )
        ).where(
            FlockPopulationTransaction.farm_id == farm_id,
            FlockPopulationTransaction.flock_id == flock_id,
            FlockPopulationTransaction.transaction_date <= usage_date,
        )

        return int(self.database_session.scalar(statement) or 0)

    def get_purchase(
        self,
        farm_id: UUID,
        purchase_id: UUID,
        *,
        for_update: bool = False,
    ) -> FeedPurchase | None:
        statement = (
            select(FeedPurchase)
            .options(
                selectinload(FeedPurchase.feed_item),
                selectinload(FeedPurchase.supplier),
            )
            .where(
                FeedPurchase.farm_id == farm_id,
                FeedPurchase.id == purchase_id,
            )
        )

        if for_update:
            statement = statement.with_for_update()

        return self.database_session.scalar(statement)

    def get_duplicate_purchase(
        self,
        farm_id: UUID,
        supplier_id: UUID | None,
        invoice_number: str | None,
        feed_item_id: UUID,
    ) -> FeedPurchase | None:
        if supplier_id is None or invoice_number is None:
            return None

        statement = select(FeedPurchase).where(
            FeedPurchase.farm_id == farm_id,
            FeedPurchase.supplier_id == supplier_id,
            FeedPurchase.invoice_number == invoice_number,
            FeedPurchase.feed_item_id == feed_item_id,
        )

        return self.database_session.scalar(statement)

    def list_purchases(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        date_from: date | None,
        date_to: date | None,
        feed_item_id: UUID | None,
        supplier_id: UUID | None,
        purchase_status: str | None,
        search: str | None,
    ) -> tuple[list[FeedPurchase], int]:
        conditions = [FeedPurchase.farm_id == farm_id]

        if date_from is not None:
            conditions.append(FeedPurchase.purchase_date >= date_from)

        if date_to is not None:
            conditions.append(FeedPurchase.purchase_date <= date_to)

        if feed_item_id is not None:
            conditions.append(FeedPurchase.feed_item_id == feed_item_id)

        if supplier_id is not None:
            conditions.append(FeedPurchase.supplier_id == supplier_id)

        if purchase_status is not None:
            conditions.append(FeedPurchase.status == purchase_status)

        if search:
            pattern = f"%{search.strip()}%"

            conditions.append(
                or_(
                    FeedPurchase.invoice_number.ilike(pattern),
                    FeedItem.feed_code.ilike(pattern),
                    FeedItem.name.ilike(pattern),
                    Supplier.name.ilike(pattern),
                )
            )

        records_statement = (
            select(FeedPurchase)
            .join(
                FeedItem,
                FeedItem.id == FeedPurchase.feed_item_id,
            )
            .outerjoin(
                Supplier,
                Supplier.id == FeedPurchase.supplier_id,
            )
            .options(
                selectinload(FeedPurchase.feed_item),
                selectinload(FeedPurchase.supplier),
            )
            .where(*conditions)
            .order_by(
                FeedPurchase.purchase_date.desc(),
                FeedPurchase.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        count_statement = (
            select(func.count(FeedPurchase.id))
            .join(
                FeedItem,
                FeedItem.id == FeedPurchase.feed_item_id,
            )
            .outerjoin(
                Supplier,
                Supplier.id == FeedPurchase.supplier_id,
            )
            .where(*conditions)
        )

        records = list(self.database_session.scalars(records_statement).all())

        total = self.database_session.scalar(count_statement) or 0

        return records, total

    def add_purchase(
        self,
        purchase: FeedPurchase,
    ) -> FeedPurchase:
        self.database_session.add(purchase)
        return purchase

    def get_usage(
        self,
        farm_id: UUID,
        usage_id: UUID,
    ) -> FeedUsage | None:
        statement = (
            select(FeedUsage)
            .options(
                selectinload(FeedUsage.flock).selectinload(Flock.house),
                selectinload(FeedUsage.feed_item),
            )
            .where(
                FeedUsage.farm_id == farm_id,
                FeedUsage.id == usage_id,
            )
        )

        return self.database_session.scalar(statement)

    def list_usages(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        date_from: date | None,
        date_to: date | None,
        flock_id: UUID | None,
        feed_item_id: UUID | None,
        feeding_period: str | None,
        search: str | None,
    ) -> tuple[list[FeedUsage], int]:
        conditions = [FeedUsage.farm_id == farm_id]

        if date_from is not None:
            conditions.append(FeedUsage.usage_date >= date_from)

        if date_to is not None:
            conditions.append(FeedUsage.usage_date <= date_to)

        if flock_id is not None:
            conditions.append(FeedUsage.flock_id == flock_id)

        if feed_item_id is not None:
            conditions.append(FeedUsage.feed_item_id == feed_item_id)

        if feeding_period is not None:
            conditions.append(FeedUsage.feeding_period == feeding_period)

        if search:
            pattern = f"%{search.strip()}%"

            conditions.append(
                or_(
                    Flock.flock_code.ilike(pattern),
                    Flock.name.ilike(pattern),
                    FeedItem.feed_code.ilike(pattern),
                    FeedItem.name.ilike(pattern),
                )
            )

        records_statement = (
            select(FeedUsage)
            .join(Flock, Flock.id == FeedUsage.flock_id)
            .join(
                FeedItem,
                FeedItem.id == FeedUsage.feed_item_id,
            )
            .options(
                selectinload(FeedUsage.flock).selectinload(Flock.house),
                selectinload(FeedUsage.feed_item),
            )
            .where(*conditions)
            .order_by(
                FeedUsage.usage_date.desc(),
                FeedUsage.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        count_statement = (
            select(func.count(FeedUsage.id))
            .join(Flock, Flock.id == FeedUsage.flock_id)
            .join(
                FeedItem,
                FeedItem.id == FeedUsage.feed_item_id,
            )
            .where(*conditions)
        )

        records = list(self.database_session.scalars(records_statement).all())

        total = self.database_session.scalar(count_statement) or 0

        return records, total

    def add_usage(
        self,
        usage: FeedUsage,
    ) -> FeedUsage:
        self.database_session.add(usage)
        return usage

    def get_balance(
        self,
        farm_id: UUID,
        feed_item_id: UUID,
    ) -> Decimal:
        statement = select(
            func.coalesce(
                func.sum(FeedInventoryTransaction.signed_quantity_kg),
                0,
            )
        ).where(
            FeedInventoryTransaction.farm_id == farm_id,
            FeedInventoryTransaction.feed_item_id == feed_item_id,
        )

        value = self.database_session.scalar(statement)

        return Decimal(str(value or 0))

    def get_balances(
        self,
        farm_id: UUID,
    ) -> dict[UUID, Decimal]:
        statement = (
            select(
                FeedInventoryTransaction.feed_item_id,
                func.coalesce(
                    func.sum(FeedInventoryTransaction.signed_quantity_kg),
                    0,
                ),
            )
            .where(FeedInventoryTransaction.farm_id == farm_id)
            .group_by(FeedInventoryTransaction.feed_item_id)
        )

        return {
            feed_item_id: Decimal(str(balance or 0))
            for feed_item_id, balance in self.database_session.execute(statement).all()
        }

    def get_inventory_transaction(
        self,
        farm_id: UUID,
        transaction_id: UUID,
        *,
        for_update: bool = False,
    ) -> FeedInventoryTransaction | None:
        statement = (
            select(FeedInventoryTransaction)
            .options(selectinload(FeedInventoryTransaction.feed_item))
            .where(
                FeedInventoryTransaction.farm_id == farm_id,
                FeedInventoryTransaction.id == transaction_id,
            )
        )

        if for_update:
            statement = statement.with_for_update()

        return self.database_session.scalar(statement)

    def get_source_transaction(
        self,
        farm_id: UUID,
        *,
        source_type: str,
        source_id: UUID,
        transaction_type: str,
    ) -> FeedInventoryTransaction | None:
        statement = select(FeedInventoryTransaction).where(
            FeedInventoryTransaction.farm_id == farm_id,
            FeedInventoryTransaction.source_type == source_type,
            FeedInventoryTransaction.source_id == source_id,
            FeedInventoryTransaction.transaction_type == transaction_type,
        )

        return self.database_session.scalar(statement)

    def get_reversal(
        self,
        farm_id: UUID,
        transaction_id: UUID,
    ) -> FeedInventoryTransaction | None:
        statement = select(FeedInventoryTransaction).where(
            FeedInventoryTransaction.farm_id == farm_id,
            FeedInventoryTransaction.reversed_transaction_id == transaction_id,
        )

        return self.database_session.scalar(statement)

    def list_inventory_transactions(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        date_from: date | None,
        date_to: date | None,
        feed_item_id: UUID | None,
        transaction_type: str | None,
        source_type: str | None,
    ) -> tuple[
        list[FeedInventoryTransaction],
        int,
    ]:
        conditions = [FeedInventoryTransaction.farm_id == farm_id]

        if date_from is not None:
            conditions.append(FeedInventoryTransaction.inventory_date >= date_from)

        if date_to is not None:
            conditions.append(FeedInventoryTransaction.inventory_date <= date_to)

        if feed_item_id is not None:
            conditions.append(FeedInventoryTransaction.feed_item_id == feed_item_id)

        if transaction_type is not None:
            conditions.append(
                FeedInventoryTransaction.transaction_type == transaction_type
            )

        if source_type is not None:
            conditions.append(FeedInventoryTransaction.source_type == source_type)

        records_statement = (
            select(FeedInventoryTransaction)
            .options(selectinload(FeedInventoryTransaction.feed_item))
            .where(*conditions)
            .order_by(
                FeedInventoryTransaction.inventory_date.desc(),
                FeedInventoryTransaction.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        count_statement = select(func.count(FeedInventoryTransaction.id)).where(
            *conditions
        )

        records = list(self.database_session.scalars(records_statement).all())

        total = self.database_session.scalar(count_statement) or 0

        return records, total

    def add_inventory_transaction(
        self,
        transaction: FeedInventoryTransaction,
    ) -> FeedInventoryTransaction:
        self.database_session.add(transaction)
        return transaction
