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
from app.modules.farms.models import FarmSettings
from app.modules.feed.constants import (
    FeedCategory,
    FeedInventoryTransactionType,
    FeedPurchaseStatus,
    FeedUsagePeriod,
)
from app.modules.feed.models import (
    FeedInventoryTransaction,
    FeedItem,
    FeedPurchase,
    FeedUsage,
    get_signed_feed_quantity,
)
from app.modules.feed.repository import FeedRepository
from app.modules.feed.schemas import (
    FeedInventoryAdjustmentCreate,
    FeedItemCreate,
    FeedItemUpdate,
    FeedPurchaseCreate,
    FeedUsageCreate,
    FeedWastageCreate,
)
from app.modules.flocks.constants import FlockStatus
from app.modules.suppliers.constants import SupplierType
from app.modules.suppliers.models import Supplier


OPEN_FLOCK_STATUSES = {
    FlockStatus.ACTIVE.value,
    FlockStatus.SUSPENDED.value,
}

MANUALLY_REVERSIBLE_SOURCE_TYPES = {
    "MANUAL_FEED_ADJUSTMENT",
    "FEED_WASTAGE",
    "FLOCK_FEED_USAGE",
}


class FeedService:
    """Business operations for feed management."""

    def __init__(
        self,
        database_session: Session,
    ) -> None:
        self.database_session = database_session
        self.repository = FeedRepository(database_session)

    @staticmethod
    def _quantize_kg(value: Decimal) -> Decimal:
        return value.quantize(
            Decimal("0.001"),
            rounding=ROUND_HALF_UP,
        )

    def _get_settings(
        self,
        farm_id: UUID,
    ) -> FarmSettings:
        settings = self.repository.get_farm_settings(farm_id)

        if settings is None:
            raise ResourceNotFoundError(
                "Farm settings were not found.",
                error_code="farm_settings_not_found",
            )

        return settings

    def _get_item(
        self,
        farm_id: UUID,
        feed_item_id: UUID,
        *,
        for_update: bool = False,
    ) -> FeedItem:
        feed_item = self.repository.get_item(
            farm_id,
            feed_item_id,
            for_update=for_update,
        )

        if feed_item is None:
            raise ResourceNotFoundError(
                "The requested feed item does not exist.",
                error_code="feed_item_not_found",
            )

        return feed_item

    def _get_active_item(
        self,
        farm_id: UUID,
        feed_item_id: UUID,
        *,
        for_update: bool = False,
    ) -> FeedItem:
        feed_item = self._get_item(
            farm_id,
            feed_item_id,
            for_update=for_update,
        )

        if not feed_item.is_active:
            raise BusinessRuleError(
                "The selected feed item is inactive.",
                error_code="feed_item_inactive",
            )

        return feed_item

    def _get_valid_feed_supplier(
        self,
        farm_id: UUID,
        supplier_id: UUID | None,
    ) -> Supplier | None:
        if supplier_id is None:
            return None

        supplier = self.repository.get_supplier(
            farm_id,
            supplier_id,
        )

        if supplier is None:
            raise ResourceNotFoundError(
                "The selected supplier does not exist.",
                error_code="supplier_not_found",
            )

        if not supplier.is_active:
            raise BusinessRuleError(
                "The selected supplier is inactive.",
                error_code="inactive_supplier",
            )

        allowed_types = {
            SupplierType.FEED_SUPPLIER.value,
            SupplierType.GENERAL_SUPPLIER.value,
        }

        if supplier.supplier_type not in allowed_types:
            raise BusinessRuleError(
                "The selected supplier is not registered "
                "as a feed or general supplier.",
                error_code="invalid_feed_supplier",
            )

        return supplier

    def _ensure_stock_available(
        self,
        farm_id: UUID,
        feed_item_id: UUID,
        quantity_kg: Decimal,
    ) -> None:
        self._get_active_item(
            farm_id,
            feed_item_id,
            for_update=True,
        )

        settings = self._get_settings(farm_id)

        if settings.allow_negative_stock:
            return

        current_balance = self.repository.get_balance(
            farm_id,
            feed_item_id,
        )

        if quantity_kg > current_balance:
            raise BusinessRuleError(
                "The requested feed quantity exceeds "
                "the available stock. Available feed: "
                f"{current_balance} kg.",
                error_code="insufficient_feed_stock",
            )

    def create_item(
        self,
        farm_id: UUID,
        payload: FeedItemCreate,
    ) -> FeedItem:
        existing = self.repository.get_item_by_code(
            farm_id,
            payload.feed_code,
        )

        if existing is not None:
            raise ResourceConflictError(
                "A feed item with this code already exists.",
                error_code="feed_code_already_exists",
            )

        feed_item = FeedItem(
            farm_id=farm_id,
            feed_code=payload.feed_code,
            name=payload.name,
            category=payload.category.value,
            brand=payload.brand,
            manufacturer=payload.manufacturer,
            description=payload.description,
            reorder_level_kg=self._quantize_kg(payload.reorder_level_kg),
            is_active=True,
        )

        self.repository.add_item(feed_item)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The feed item could not be created.",
                error_code="feed_item_creation_conflict",
            ) from exc

        return self._get_item(
            farm_id,
            feed_item.id,
        )

    def list_items(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        category: FeedCategory | None,
        is_active: bool | None,
        search: str | None,
    ) -> tuple[list[FeedItem], int]:
        return self.repository.list_items(
            farm_id,
            offset=offset,
            limit=limit,
            category=(category.value if category is not None else None),
            is_active=is_active,
            search=search,
        )

    def get_item(
        self,
        farm_id: UUID,
        feed_item_id: UUID,
    ) -> FeedItem:
        return self._get_item(
            farm_id,
            feed_item_id,
        )

    def update_item(
        self,
        farm_id: UUID,
        feed_item_id: UUID,
        payload: FeedItemUpdate,
    ) -> FeedItem:
        feed_item = self._get_item(
            farm_id,
            feed_item_id,
            for_update=True,
        )

        changes = payload.model_dump(
            exclude_unset=True,
            mode="json",
        )

        requested_code = changes.get("feed_code")

        if requested_code is not None and requested_code != feed_item.feed_code:
            conflicting_item = self.repository.get_item_by_code(
                farm_id,
                requested_code,
            )

            if conflicting_item is not None:
                raise ResourceConflictError(
                    "Another feed item already uses this feed code.",
                    error_code=("feed_code_already_exists"),
                )

        if "category" in changes:
            changes["category"] = payload.category.value

        if "reorder_level_kg" in changes:
            changes["reorder_level_kg"] = self._quantize_kg(payload.reorder_level_kg)

        if not changes:
            return feed_item

        self.repository.update_item(
            feed_item,
            changes,
        )

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The feed item could not be updated.",
                error_code="feed_item_update_conflict",
            ) from exc

        return self._get_item(
            farm_id,
            feed_item_id,
        )

    def set_item_active_status(
        self,
        farm_id: UUID,
        feed_item_id: UUID,
        *,
        is_active: bool,
    ) -> FeedItem:
        feed_item = self._get_item(
            farm_id,
            feed_item_id,
            for_update=True,
        )

        feed_item.is_active = is_active
        self.database_session.commit()

        return self._get_item(
            farm_id,
            feed_item_id,
        )

    def create_purchase(
        self,
        farm_id: UUID,
        created_by: UUID,
        payload: FeedPurchaseCreate,
    ) -> FeedPurchase:
        self._get_active_item(
            farm_id,
            payload.feed_item_id,
            for_update=True,
        )

        self._get_valid_feed_supplier(
            farm_id,
            payload.supplier_id,
        )

        duplicate = self.repository.get_duplicate_purchase(
            farm_id,
            payload.supplier_id,
            payload.invoice_number,
            payload.feed_item_id,
        )

        if duplicate is not None:
            raise ResourceConflictError(
                "This supplier invoice and feed item have already been recorded.",
                error_code=("feed_purchase_already_exists"),
            )

        quantity_kg = self._quantize_kg(payload.quantity_kg)

        purchase = FeedPurchase(
            farm_id=farm_id,
            feed_item_id=payload.feed_item_id,
            supplier_id=payload.supplier_id,
            purchase_date=payload.purchase_date,
            invoice_number=payload.invoice_number,
            quantity_kg=quantity_kg,
            unit_cost=payload.unit_cost,
            status=FeedPurchaseStatus.RECEIVED.value,
            notes=payload.notes,
            created_by=created_by,
        )

        self.repository.add_purchase(purchase)

        try:
            self.database_session.flush()

            inventory_transaction = FeedInventoryTransaction(
                farm_id=farm_id,
                transaction_group_id=uuid4(),
                feed_item_id=payload.feed_item_id,
                inventory_date=payload.purchase_date,
                transaction_type=(FeedInventoryTransactionType.PURCHASE_IN.value),
                quantity_kg=quantity_kg,
                signed_quantity_kg=quantity_kg,
                source_type="FEED_PURCHASE",
                source_id=purchase.id,
                reference=payload.invoice_number,
                description=(
                    "Automatic feed inventory receipt created from a feed purchase."
                ),
                created_by=created_by,
            )

            self.repository.add_inventory_transaction(inventory_transaction)

            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The feed purchase could not be recorded.",
                error_code="feed_purchase_conflict",
            ) from exc

        created_purchase = self.repository.get_purchase(
            farm_id,
            purchase.id,
        )

        if created_purchase is None:
            raise ResourceNotFoundError(
                "The purchase was saved but could not be retrieved.",
                error_code="created_feed_purchase_not_found",
            )

        return created_purchase

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
        purchase_status: FeedPurchaseStatus | None,
        search: str | None,
    ) -> tuple[list[FeedPurchase], int]:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise BusinessRuleError(
                "The start date cannot be after the end date.",
                error_code="invalid_feed_date_range",
            )

        return self.repository.list_purchases(
            farm_id,
            offset=offset,
            limit=limit,
            date_from=date_from,
            date_to=date_to,
            feed_item_id=feed_item_id,
            supplier_id=supplier_id,
            purchase_status=(
                purchase_status.value if purchase_status is not None else None
            ),
            search=search,
        )

    def get_purchase(
        self,
        farm_id: UUID,
        purchase_id: UUID,
    ) -> FeedPurchase:
        purchase = self.repository.get_purchase(
            farm_id,
            purchase_id,
        )

        if purchase is None:
            raise ResourceNotFoundError(
                "The requested feed purchase does not exist.",
                error_code="feed_purchase_not_found",
            )

        return purchase

    def void_purchase(
        self,
        farm_id: UUID,
        purchase_id: UUID,
        voided_by: UUID,
        reason: str,
    ) -> FeedPurchase:
        purchase = self.repository.get_purchase(
            farm_id,
            purchase_id,
            for_update=True,
        )

        if purchase is None:
            raise ResourceNotFoundError(
                "The requested feed purchase does not exist.",
                error_code="feed_purchase_not_found",
            )

        if purchase.status != FeedPurchaseStatus.RECEIVED.value:
            raise BusinessRuleError(
                "Only a received purchase may be voided.",
                error_code="feed_purchase_not_received",
            )

        original_transaction = self.repository.get_source_transaction(
            farm_id,
            source_type="FEED_PURCHASE",
            source_id=purchase.id,
            transaction_type=(FeedInventoryTransactionType.PURCHASE_IN.value),
        )

        if original_transaction is None:
            raise ResourceNotFoundError(
                "The purchase inventory transaction could not be found.",
                error_code=("feed_purchase_transaction_not_found"),
            )

        existing_reversal = self.repository.get_reversal(
            farm_id,
            original_transaction.id,
        )

        if existing_reversal is not None:
            raise ResourceConflictError(
                "This purchase has already been reversed.",
                error_code=("feed_purchase_already_reversed"),
            )

        self._ensure_stock_available(
            farm_id,
            purchase.feed_item_id,
            purchase.quantity_kg,
        )

        reversal = FeedInventoryTransaction(
            farm_id=farm_id,
            transaction_group_id=uuid4(),
            feed_item_id=purchase.feed_item_id,
            inventory_date=date.today(),
            transaction_type=(FeedInventoryTransactionType.REVERSAL.value),
            quantity_kg=purchase.quantity_kg,
            signed_quantity_kg=-purchase.quantity_kg,
            source_type="FEED_PURCHASE_VOID",
            source_id=purchase.id,
            reference=purchase.invoice_number,
            description=(f"Feed purchase voided: {reason}"),
            created_by=voided_by,
            reversed_transaction_id=(original_transaction.id),
        )

        purchase.status = FeedPurchaseStatus.VOIDED.value
        purchase.voided_by = voided_by
        purchase.voided_at = datetime.now(UTC)

        self.repository.add_inventory_transaction(reversal)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The feed purchase could not be voided.",
                error_code="feed_purchase_void_conflict",
            ) from exc

        return self.get_purchase(
            farm_id,
            purchase_id,
        )

    def create_usage(
        self,
        farm_id: UUID,
        created_by: UUID,
        payload: FeedUsageCreate,
    ) -> tuple[FeedUsage, int]:
        self._get_active_item(
            farm_id,
            payload.feed_item_id,
            for_update=True,
        )

        flock = self.repository.get_flock(
            farm_id,
            payload.flock_id,
        )

        if flock is None:
            raise ResourceNotFoundError(
                "The selected flock does not exist.",
                error_code="flock_not_found",
            )

        if flock.status not in OPEN_FLOCK_STATUSES:
            raise BusinessRuleError(
                "Feed usage cannot be recorded for a closed or planned flock.",
                error_code="flock_not_open_for_feeding",
            )

        if payload.usage_date < flock.arrival_date:
            raise BusinessRuleError(
                "Feed usage cannot occur before the flock arrival date.",
                error_code="feed_usage_before_arrival",
            )

        birds_present = self.repository.get_population_as_of_date(
            farm_id,
            payload.flock_id,
            payload.usage_date,
        )

        if birds_present <= 0:
            raise BusinessRuleError(
                "The flock had no live birds on the selected feed-usage date.",
                error_code=("no_flock_population_on_usage_date"),
            )

        quantity_kg = self._quantize_kg(payload.quantity_kg)

        self._ensure_stock_available(
            farm_id,
            payload.feed_item_id,
            quantity_kg,
        )

        usage = FeedUsage(
            farm_id=farm_id,
            flock_id=payload.flock_id,
            feed_item_id=payload.feed_item_id,
            usage_date=payload.usage_date,
            feeding_period=(payload.feeding_period.value),
            quantity_kg=quantity_kg,
            notes=payload.notes,
            created_by=created_by,
        )

        self.repository.add_usage(usage)

        try:
            self.database_session.flush()

            transaction = FeedInventoryTransaction(
                farm_id=farm_id,
                transaction_group_id=uuid4(),
                feed_item_id=payload.feed_item_id,
                inventory_date=payload.usage_date,
                transaction_type=(FeedInventoryTransactionType.USAGE_OUT.value),
                quantity_kg=quantity_kg,
                signed_quantity_kg=-quantity_kg,
                source_type="FLOCK_FEED_USAGE",
                source_id=usage.id,
                reference=flock.flock_code,
                description=(
                    "Automatic feed inventory reduction created from flock feed usage."
                ),
                created_by=created_by,
            )

            self.repository.add_inventory_transaction(transaction)

            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The feed usage could not be recorded.",
                error_code="feed_usage_conflict",
            ) from exc

        created_usage = self.repository.get_usage(
            farm_id,
            usage.id,
        )

        if created_usage is None:
            raise ResourceNotFoundError(
                "The feed usage was saved but could not be retrieved.",
                error_code="created_feed_usage_not_found",
            )

        return created_usage, birds_present

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
        feeding_period: FeedUsagePeriod | None,
        search: str | None,
    ) -> tuple[list[tuple[FeedUsage, int]], int]:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise BusinessRuleError(
                "The start date cannot be after the end date.",
                error_code="invalid_feed_date_range",
            )

        records, total = self.repository.list_usages(
            farm_id,
            offset=offset,
            limit=limit,
            date_from=date_from,
            date_to=date_to,
            flock_id=flock_id,
            feed_item_id=feed_item_id,
            feeding_period=(
                feeding_period.value if feeding_period is not None else None
            ),
            search=search,
        )

        return [
            (
                usage,
                self.repository.get_population_as_of_date(
                    farm_id,
                    usage.flock_id,
                    usage.usage_date,
                ),
            )
            for usage in records
        ], total

    def get_usage(
        self,
        farm_id: UUID,
        usage_id: UUID,
    ) -> tuple[FeedUsage, int]:
        usage = self.repository.get_usage(
            farm_id,
            usage_id,
        )

        if usage is None:
            raise ResourceNotFoundError(
                "The requested feed usage does not exist.",
                error_code="feed_usage_not_found",
            )

        birds_present = self.repository.get_population_as_of_date(
            farm_id,
            usage.flock_id,
            usage.usage_date,
        )

        return usage, birds_present

    @staticmethod
    def calculate_grams_per_bird(
        quantity_kg: Decimal,
        birds_present: int,
    ) -> Decimal:
        if birds_present <= 0:
            return Decimal("0.000")

        grams_per_bird = quantity_kg * Decimal("1000") / Decimal(birds_present)

        return grams_per_bird.quantize(
            Decimal("0.001"),
            rounding=ROUND_HALF_UP,
        )

    def create_adjustment(
        self,
        farm_id: UUID,
        created_by: UUID,
        payload: FeedInventoryAdjustmentCreate,
    ) -> FeedInventoryTransaction:
        self._get_active_item(
            farm_id,
            payload.feed_item_id,
            for_update=True,
        )

        transaction_type = payload.transaction_type.value

        quantity_kg = self._quantize_kg(payload.quantity_kg)

        signed_quantity = get_signed_feed_quantity(
            transaction_type,
            quantity_kg,
        )

        if signed_quantity < 0:
            self._ensure_stock_available(
                farm_id,
                payload.feed_item_id,
                quantity_kg,
            )

        transaction = FeedInventoryTransaction(
            farm_id=farm_id,
            transaction_group_id=uuid4(),
            feed_item_id=payload.feed_item_id,
            inventory_date=payload.inventory_date,
            transaction_type=transaction_type,
            quantity_kg=quantity_kg,
            signed_quantity_kg=signed_quantity,
            source_type="MANUAL_FEED_ADJUSTMENT",
            source_id=None,
            reference=payload.reference,
            description=payload.description,
            created_by=created_by,
        )

        self.repository.add_inventory_transaction(transaction)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The feed adjustment could not be saved.",
                error_code="feed_adjustment_conflict",
            ) from exc

        created_transaction = self.repository.get_inventory_transaction(
            farm_id,
            transaction.id,
        )

        if created_transaction is None:
            raise ResourceNotFoundError(
                "The adjustment was saved but could not be retrieved.",
                error_code=("created_feed_adjustment_not_found"),
            )

        return created_transaction

    def create_wastage(
        self,
        farm_id: UUID,
        created_by: UUID,
        payload: FeedWastageCreate,
    ) -> FeedInventoryTransaction:
        self._ensure_stock_available(
            farm_id,
            payload.feed_item_id,
            payload.quantity_kg,
        )

        quantity_kg = self._quantize_kg(payload.quantity_kg)

        transaction = FeedInventoryTransaction(
            farm_id=farm_id,
            transaction_group_id=uuid4(),
            feed_item_id=payload.feed_item_id,
            inventory_date=payload.inventory_date,
            transaction_type=(FeedInventoryTransactionType.WASTAGE_OUT.value),
            quantity_kg=quantity_kg,
            signed_quantity_kg=-quantity_kg,
            source_type="FEED_WASTAGE",
            source_id=None,
            reference=payload.reference,
            description=payload.description,
            created_by=created_by,
        )

        self.repository.add_inventory_transaction(transaction)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The feed wastage could not be saved.",
                error_code="feed_wastage_conflict",
            ) from exc

        created_transaction = self.repository.get_inventory_transaction(
            farm_id,
            transaction.id,
        )

        if created_transaction is None:
            raise ResourceNotFoundError(
                "The wastage was saved but could not be retrieved.",
                error_code=("created_feed_wastage_not_found"),
            )

        return created_transaction

    def reverse_transaction(
        self,
        farm_id: UUID,
        transaction_id: UUID,
        reversed_by: UUID,
        *,
        inventory_date: date,
        reason: str,
    ) -> FeedInventoryTransaction:
        original = self.repository.get_inventory_transaction(
            farm_id,
            transaction_id,
            for_update=True,
        )

        if original is None:
            raise ResourceNotFoundError(
                "The requested feed inventory transaction does not exist.",
                error_code=("feed_inventory_transaction_not_found"),
            )

        if original.is_reversal:
            raise BusinessRuleError(
                "A reversal cannot itself be reversed.",
                error_code=("feed_reversal_cannot_be_reversed"),
            )

        if original.source_type not in MANUALLY_REVERSIBLE_SOURCE_TYPES:
            raise BusinessRuleError(
                "This transaction must be reversed by its source module.",
                error_code=("feed_transaction_source_controlled"),
            )

        existing_reversal = self.repository.get_reversal(
            farm_id,
            original.id,
        )

        if existing_reversal is not None:
            raise ResourceConflictError(
                "This feed transaction has already been reversed.",
                error_code=("feed_transaction_already_reversed"),
            )

        reversal_signed_quantity = -original.signed_quantity_kg

        if reversal_signed_quantity < 0:
            self._ensure_stock_available(
                farm_id,
                original.feed_item_id,
                abs(reversal_signed_quantity),
            )

        reversal = FeedInventoryTransaction(
            farm_id=farm_id,
            transaction_group_id=uuid4(),
            feed_item_id=original.feed_item_id,
            inventory_date=inventory_date,
            transaction_type=(FeedInventoryTransactionType.REVERSAL.value),
            quantity_kg=original.quantity_kg,
            signed_quantity_kg=(reversal_signed_quantity),
            source_type="FEED_TRANSACTION_REVERSAL",
            source_id=original.id,
            reference=original.reference,
            description=(f"Reversal of transaction {original.id}: {reason}"),
            created_by=reversed_by,
            reversed_transaction_id=original.id,
        )

        self.repository.add_inventory_transaction(reversal)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The feed transaction could not be reversed.",
                error_code="feed_reversal_conflict",
            ) from exc

        created_reversal = self.repository.get_inventory_transaction(
            farm_id,
            reversal.id,
        )

        if created_reversal is None:
            raise ResourceNotFoundError(
                "The reversal was saved but could not be retrieved.",
                error_code=("created_feed_reversal_not_found"),
            )

        return created_reversal

    def get_inventory_summary(
        self,
        farm_id: UUID,
    ) -> dict[str, object]:
        items = self.repository.list_all_items(farm_id)

        balance_map = self.repository.get_balances(farm_id)

        balances: list[dict[str, object]] = []
        total_feed_kg = Decimal("0.000")
        active_feed_items = 0
        low_stock_items = 0
        out_of_stock_items = 0

        for item in items:
            balance = self._quantize_kg(
                balance_map.get(
                    item.id,
                    Decimal("0.000"),
                )
            )

            reorder_level = self._quantize_kg(item.reorder_level_kg)

            is_out_of_stock = balance <= 0

            is_low_stock = (
                item.is_active and reorder_level > 0 and balance <= reorder_level
            )

            if item.is_active:
                active_feed_items += 1

            if is_low_stock:
                low_stock_items += 1

            if item.is_active and is_out_of_stock:
                out_of_stock_items += 1

            total_feed_kg += balance

            balances.append(
                {
                    "feed_item_id": item.id,
                    "feed_code": item.feed_code,
                    "feed_name": item.name,
                    "category": item.category,
                    "balance_kg": balance,
                    "reorder_level_kg": reorder_level,
                    "is_low_stock": is_low_stock,
                    "is_out_of_stock": (is_out_of_stock),
                    "is_active": item.is_active,
                }
            )

        return {
            "balances": balances,
            "total_feed_kg": self._quantize_kg(total_feed_kg),
            "active_feed_items": active_feed_items,
            "low_stock_items": low_stock_items,
            "out_of_stock_items": (out_of_stock_items),
        }

    def list_inventory_transactions(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        date_from: date | None,
        date_to: date | None,
        feed_item_id: UUID | None,
        transaction_type: (FeedInventoryTransactionType | None),
        source_type: str | None,
    ) -> tuple[
        list[FeedInventoryTransaction],
        int,
    ]:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise BusinessRuleError(
                "The start date cannot be after the end date.",
                error_code="invalid_feed_date_range",
            )

        return self.repository.list_inventory_transactions(
            farm_id,
            offset=offset,
            limit=limit,
            date_from=date_from,
            date_to=date_to,
            feed_item_id=feed_item_id,
            transaction_type=(
                transaction_type.value if transaction_type is not None else None
            ),
            source_type=source_type,
        )
