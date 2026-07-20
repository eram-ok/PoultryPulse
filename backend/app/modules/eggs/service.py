from datetime import date
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BusinessRuleError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.modules.eggs.constants import (
    EggGrade,
    EggInventoryTransactionType,
    SALEABLE_EGG_GRADES,
)
from app.modules.eggs.models import (
    EggInventoryTransaction,
    get_signed_egg_quantity,
)
from app.modules.eggs.repository import (
    EggInventoryRepository,
)
from app.modules.eggs.schemas import (
    EggInventoryAdjustmentCreate,
    EggInventoryIssueCreate,
)
from app.modules.production.constants import (
    ProductionRecordStatus,
)
from app.modules.production.models import (
    DailyEggProduction,
)


MANUAL_REVERSIBLE_SOURCE_TYPES = {
    "MANUAL_ADJUSTMENT",
    "MANUAL_ISSUE",
}


class EggInventoryService:
    """Business operations for egg inventory."""

    def __init__(
        self,
        database_session: Session,
    ) -> None:
        self.database_session = database_session
        self.repository = EggInventoryRepository(database_session)

    def _get_inventory_settings(
        self,
        farm_id: UUID,
    ) -> tuple[int, bool]:
        settings = self.repository.get_farm_settings(farm_id)

        if settings is None:
            raise ResourceNotFoundError(
                "Farm inventory settings were not found.",
                error_code="farm_settings_not_found",
            )

        return (
            settings.eggs_per_tray,
            settings.allow_negative_stock,
        )

    @staticmethod
    def _convert_to_trays(
        egg_count: int,
        eggs_per_tray: int,
    ) -> tuple[int, int]:
        if egg_count >= 0:
            return divmod(
                egg_count,
                eggs_per_tray,
            )

        trays, loose_eggs = divmod(
            abs(egg_count),
            eggs_per_tray,
        )

        return -trays, -loose_eggs

    def _ensure_stock_available(
        self,
        farm_id: UUID,
        egg_grade: str,
        quantity: int,
    ) -> None:
        _, allow_negative_stock = self._get_inventory_settings(farm_id)

        if allow_negative_stock:
            return

        current_balance = self.repository.get_balance(
            farm_id,
            egg_grade,
        )

        if quantity > current_balance:
            raise BusinessRuleError(
                "The requested egg quantity exceeds "
                "the available stock. Available eggs: "
                f"{current_balance}.",
                error_code="insufficient_egg_stock",
            )

    def post_confirmed_production(
        self,
        production: DailyEggProduction,
        created_by: UUID,
        *,
        commit: bool = False,
    ) -> list[EggInventoryTransaction]:
        """Post confirmed production into egg stock."""

        if production.status != ProductionRecordStatus.CONFIRMED.value:
            raise BusinessRuleError(
                "Only confirmed production can be posted into egg inventory.",
                error_code="production_not_confirmed",
            )

        grade_quantities = {
            EggGrade.LARGE.value: production.large_eggs,
            EggGrade.MEDIUM.value: production.medium_eggs,
            EggGrade.SMALL.value: production.small_eggs,
            EggGrade.DAMAGED.value: production.damaged_eggs,
            EggGrade.REJECTED.value: production.rejected_eggs,
        }

        existing_transactions = self.repository.get_source_transactions(
            production.farm_id,
            source_type="DAILY_EGG_PRODUCTION",
            source_id=production.id,
            transaction_type=(EggInventoryTransactionType.PRODUCTION_IN.value),
        )

        if existing_transactions:
            transaction_group_id = existing_transactions[0].transaction_group_id
        else:
            transaction_group_id = uuid4()

        created_transactions: list[EggInventoryTransaction] = []

        for egg_grade, quantity in grade_quantities.items():
            if quantity <= 0:
                continue

            existing_transaction = self.repository.get_existing_source_transaction(
                production.farm_id,
                source_type=("DAILY_EGG_PRODUCTION"),
                source_id=production.id,
                egg_grade=egg_grade,
                transaction_type=(EggInventoryTransactionType.PRODUCTION_IN.value),
            )

            if existing_transaction is not None:
                continue

            transaction = EggInventoryTransaction(
                farm_id=production.farm_id,
                transaction_group_id=(transaction_group_id),
                inventory_date=(production.production_date),
                egg_grade=egg_grade,
                transaction_type=(EggInventoryTransactionType.PRODUCTION_IN.value),
                quantity=quantity,
                signed_quantity=quantity,
                source_type="DAILY_EGG_PRODUCTION",
                source_id=production.id,
                reference=(f"Production {production.production_date}"),
                description=(
                    "Automatic inventory receipt from confirmed daily egg production."
                ),
                created_by=created_by,
            )

            created_transactions.append(transaction)

        if created_transactions:
            self.repository.add_all(created_transactions)

        try:
            if commit:
                self.database_session.commit()
            else:
                self.database_session.flush()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "Production inventory could not be "
                "posted because it was already processed.",
                error_code=("production_inventory_posting_conflict"),
            ) from exc

        return created_transactions

    def create_adjustment(
        self,
        farm_id: UUID,
        created_by: UUID,
        payload: EggInventoryAdjustmentCreate,
    ) -> EggInventoryTransaction:
        transaction_type = payload.transaction_type.value

        signed_quantity = get_signed_egg_quantity(
            transaction_type,
            payload.quantity,
        )

        if signed_quantity < 0:
            self._ensure_stock_available(
                farm_id,
                payload.egg_grade.value,
                payload.quantity,
            )

        transaction = EggInventoryTransaction(
            farm_id=farm_id,
            transaction_group_id=uuid4(),
            inventory_date=payload.inventory_date,
            egg_grade=payload.egg_grade.value,
            transaction_type=transaction_type,
            quantity=payload.quantity,
            signed_quantity=signed_quantity,
            source_type="MANUAL_ADJUSTMENT",
            source_id=None,
            reference=payload.reference,
            description=payload.description,
            created_by=created_by,
        )

        self.repository.add(transaction)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The egg inventory adjustment could not be saved.",
                error_code=("egg_adjustment_conflict"),
            ) from exc

        self.database_session.refresh(transaction)

        return transaction

    def create_issue(
        self,
        farm_id: UUID,
        created_by: UUID,
        payload: EggInventoryIssueCreate,
    ) -> EggInventoryTransaction:
        transaction_type = payload.transaction_type.value

        self._ensure_stock_available(
            farm_id,
            payload.egg_grade.value,
            payload.quantity,
        )

        signed_quantity = get_signed_egg_quantity(
            transaction_type,
            payload.quantity,
        )

        transaction = EggInventoryTransaction(
            farm_id=farm_id,
            transaction_group_id=uuid4(),
            inventory_date=payload.inventory_date,
            egg_grade=payload.egg_grade.value,
            transaction_type=transaction_type,
            quantity=payload.quantity,
            signed_quantity=signed_quantity,
            source_type="MANUAL_ISSUE",
            source_id=None,
            reference=payload.reference,
            description=payload.description,
            created_by=created_by,
        )

        self.repository.add(transaction)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The egg issue transaction could not be saved.",
                error_code="egg_issue_conflict",
            ) from exc

        self.database_session.refresh(transaction)

        return transaction

    def reverse_transaction(
        self,
        farm_id: UUID,
        transaction_id: UUID,
        reversed_by: UUID,
        *,
        inventory_date: date,
        reason: str,
    ) -> EggInventoryTransaction:
        original = self.repository.get_transaction(
            farm_id,
            transaction_id,
            for_update=True,
        )

        if original is None:
            raise ResourceNotFoundError(
                "The requested inventory transaction does not exist.",
                error_code=("egg_inventory_transaction_not_found"),
            )

        if original.is_reversal:
            raise BusinessRuleError(
                "A reversal transaction cannot itself be reversed.",
                error_code=("egg_reversal_cannot_be_reversed"),
            )

        if original.source_type not in MANUAL_REVERSIBLE_SOURCE_TYPES:
            raise BusinessRuleError(
                "This transaction must be reversed by "
                "its source module rather than through "
                "manual egg inventory.",
                error_code=("egg_transaction_source_controlled"),
            )

        existing_reversal = self.repository.get_reversal_for_transaction(
            farm_id,
            original.id,
        )

        if existing_reversal is not None:
            raise ResourceConflictError(
                "This inventory transaction has already been reversed.",
                error_code=("egg_transaction_already_reversed"),
            )

        reversal_signed_quantity = -original.signed_quantity

        if reversal_signed_quantity < 0:
            self._ensure_stock_available(
                farm_id,
                original.egg_grade,
                abs(reversal_signed_quantity),
            )

        reversal = EggInventoryTransaction(
            farm_id=farm_id,
            transaction_group_id=uuid4(),
            inventory_date=inventory_date,
            egg_grade=original.egg_grade,
            transaction_type=(EggInventoryTransactionType.REVERSAL.value),
            quantity=original.quantity,
            signed_quantity=(reversal_signed_quantity),
            source_type=("EGG_TRANSACTION_REVERSAL"),
            source_id=original.id,
            reference=original.reference,
            description=(f"Reversal of transaction {original.id}: {reason}"),
            created_by=reversed_by,
            reversed_transaction_id=original.id,
        )

        self.repository.add(reversal)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The inventory transaction could not be reversed.",
                error_code="egg_reversal_conflict",
            ) from exc

        self.database_session.refresh(reversal)

        return reversal

    def get_summary(
        self,
        farm_id: UUID,
    ) -> dict[str, object]:
        eggs_per_tray, _ = self._get_inventory_settings(farm_id)

        stored_balances = self.repository.get_balances(farm_id)

        balance_items: list[dict[str, object]] = []

        total_saleable_eggs = 0
        total_non_saleable_eggs = 0
        total_all_eggs = 0

        for egg_grade in EggGrade:
            balance = stored_balances.get(
                egg_grade.value,
                0,
            )

            trays, loose_eggs = self._convert_to_trays(
                balance,
                eggs_per_tray,
            )

            is_saleable = egg_grade.value in SALEABLE_EGG_GRADES

            if is_saleable:
                total_saleable_eggs += balance
            else:
                total_non_saleable_eggs += balance

            total_all_eggs += balance

            balance_items.append(
                {
                    "egg_grade": egg_grade,
                    "balance_eggs": balance,
                    "trays": trays,
                    "loose_eggs": loose_eggs,
                    "eggs_per_tray": eggs_per_tray,
                    "is_saleable": is_saleable,
                }
            )

        (
            total_saleable_trays,
            total_saleable_loose_eggs,
        ) = self._convert_to_trays(
            total_saleable_eggs,
            eggs_per_tray,
        )

        return {
            "eggs_per_tray": eggs_per_tray,
            "balances": balance_items,
            "total_saleable_eggs": (total_saleable_eggs),
            "total_saleable_trays": (total_saleable_trays),
            "total_saleable_loose_eggs": (total_saleable_loose_eggs),
            "total_non_saleable_eggs": (total_non_saleable_eggs),
            "total_all_eggs": total_all_eggs,
        }

    def list_transactions(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        date_from: date | None,
        date_to: date | None,
        egg_grade: EggGrade | None,
        transaction_type: (EggInventoryTransactionType | None),
        source_type: str | None,
    ) -> tuple[
        list[EggInventoryTransaction],
        int,
    ]:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise BusinessRuleError(
                "The start date cannot be after the end date.",
                error_code=("invalid_inventory_date_range"),
            )

        return self.repository.list_transactions(
            farm_id,
            offset=offset,
            limit=limit,
            date_from=date_from,
            date_to=date_to,
            egg_grade=(egg_grade.value if egg_grade is not None else None),
            transaction_type=(
                transaction_type.value if transaction_type is not None else None
            ),
            source_type=source_type,
        )
