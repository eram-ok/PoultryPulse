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
    PopulationTransactionType,
)
from app.modules.flocks.models import (
    Flock,
    FlockPopulationTransaction,
    NEGATIVE_POPULATION_TRANSACTION_TYPES,
    POSITIVE_POPULATION_TRANSACTION_TYPES,
)
from app.modules.flocks.repository import FlockRepository
from app.modules.flocks.schemas import (
    FlockCreate,
    FlockUpdate,
    PopulationTransactionCreate,
)
from app.modules.houses.constants import PoultryHouseStatus
from app.modules.suppliers.constants import SupplierType
from app.modules.suppliers.models import Supplier
from app.modules.suppliers.repository import SupplierRepository


TERMINAL_FLOCK_STATUSES = {
    FlockStatus.DEPLETED.value,
    FlockStatus.SOLD.value,
    FlockStatus.ARCHIVED.value,
}

TERMINAL_PRODUCTION_STAGES = {
    FlockProductionStage.DEPLETED.value,
    FlockProductionStage.SOLD.value,
}


class FlockService:
    """Business operations for flock management."""

    def __init__(
        self,
        database_session: Session,
    ) -> None:
        self.database_session = database_session
        self.repository = FlockRepository(database_session)
        self.suppliers = SupplierRepository(database_session)

    def _get_valid_supplier(
        self,
        farm_id: UUID,
        supplier_id: UUID | None,
    ) -> Supplier | None:
        if supplier_id is None:
            return None

        supplier = self.suppliers.get_by_id(
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
            SupplierType.BIRD_SUPPLIER.value,
            SupplierType.GENERAL_SUPPLIER.value,
        }

        if supplier.supplier_type not in allowed_types:
            raise BusinessRuleError(
                "The selected supplier is not registered "
                "as a bird or general supplier.",
                error_code="invalid_bird_supplier",
            )

        return supplier

    def _validate_house_capacity(
        self,
        farm_id: UUID,
        house_id: UUID,
        additional_birds: int,
    ) -> None:
        house = self.repository.get_house(
            farm_id,
            house_id,
            for_update=True,
        )

        if house is None:
            raise ResourceNotFoundError(
                "The selected poultry house does not exist.",
                error_code="poultry_house_not_found",
            )

        if house.status != PoultryHouseStatus.ACTIVE.value:
            raise BusinessRuleError(
                "Birds can only be placed in an active poultry house.",
                error_code="house_not_active",
            )

        occupancy = self.repository.get_house_occupancy(
            farm_id,
            house_id,
        )

        projected_occupancy = occupancy + additional_birds

        if projected_occupancy > house.capacity:
            available_capacity = max(
                house.capacity - occupancy,
                0,
            )

            raise BusinessRuleError(
                "The poultry house does not have enough "
                "capacity. Available spaces: "
                f"{available_capacity}.",
                error_code="house_capacity_exceeded",
            )

    def create_flock(
        self,
        farm_id: UUID,
        created_by: UUID,
        payload: FlockCreate,
    ) -> tuple[Flock, int]:
        existing_flock = self.repository.get_by_code(
            farm_id,
            payload.flock_code,
        )

        if existing_flock is not None:
            raise ResourceConflictError(
                "A flock with this code already exists.",
                error_code="flock_code_already_exists",
            )

        self._validate_house_capacity(
            farm_id,
            payload.house_id,
            payload.initial_population,
        )

        self._get_valid_supplier(
            farm_id,
            payload.supplier_id,
        )

        age_at_arrival_days = payload.age_at_arrival_days

        if age_at_arrival_days is None and payload.hatch_date is not None:
            age_at_arrival_days = (payload.arrival_date - payload.hatch_date).days

        flock = Flock(
            farm_id=farm_id,
            house_id=payload.house_id,
            supplier_id=payload.supplier_id,
            flock_code=payload.flock_code,
            name=payload.name,
            breed=payload.breed,
            arrival_date=payload.arrival_date,
            hatch_date=payload.hatch_date,
            age_at_arrival_days=age_at_arrival_days,
            initial_population=payload.initial_population,
            purchase_cost=payload.purchase_cost,
            production_stage=(payload.production_stage.value),
            status=FlockStatus.ACTIVE.value,
            notes=payload.notes,
        )

        self.repository.add_flock(flock)

        try:
            self.database_session.flush()

            initial_placement = FlockPopulationTransaction(
                farm_id=farm_id,
                flock_id=flock.id,
                transaction_date=payload.arrival_date,
                transaction_type=(PopulationTransactionType.INITIAL_PLACEMENT.value),
                quantity=payload.initial_population,
                signed_quantity=(payload.initial_population),
                source_type="FLOCK_CREATION",
                source_id=flock.id,
                description=("Automatic initial placement created with the flock."),
                created_by=created_by,
            )

            self.repository.add_population_transaction(initial_placement)

            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The flock could not be created because "
                "one of its values conflicts with an "
                "existing record.",
                error_code="flock_creation_conflict",
            ) from exc

        created_flock = self.repository.get_by_id(
            farm_id,
            flock.id,
        )

        if created_flock is None:
            raise ResourceNotFoundError(
                "The flock was created but could not be retrieved.",
                error_code="created_flock_not_found",
            )

        current_population = self.repository.get_current_population(
            farm_id,
            flock.id,
        )

        return created_flock, current_population

    def list_flocks(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        flock_status: FlockStatus | None,
        production_stage: FlockProductionStage | None,
        house_id: UUID | None,
        supplier_id: UUID | None,
        search: str | None,
    ) -> tuple[list[tuple[Flock, int]], int]:
        flocks, total = self.repository.list_flocks(
            farm_id,
            offset=offset,
            limit=limit,
            flock_status=(flock_status.value if flock_status is not None else None),
            production_stage=(
                production_stage.value if production_stage is not None else None
            ),
            house_id=house_id,
            supplier_id=supplier_id,
            search=search,
        )

        population_map = self.repository.get_population_totals(
            farm_id,
            [flock.id for flock in flocks],
        )

        return [
            (
                flock,
                population_map.get(flock.id, 0),
            )
            for flock in flocks
        ], total

    def get_flock(
        self,
        farm_id: UUID,
        flock_id: UUID,
    ) -> tuple[Flock, int]:
        flock = self.repository.get_by_id(
            farm_id,
            flock_id,
        )

        if flock is None:
            raise ResourceNotFoundError(
                "The requested flock does not exist.",
                error_code="flock_not_found",
            )

        current_population = self.repository.get_current_population(
            farm_id,
            flock_id,
        )

        return flock, current_population

    def update_flock(
        self,
        farm_id: UUID,
        flock_id: UUID,
        payload: FlockUpdate,
    ) -> tuple[Flock, int]:
        flock = self.repository.get_by_id(
            farm_id,
            flock_id,
            for_update=True,
        )

        if flock is None:
            raise ResourceNotFoundError(
                "The requested flock does not exist.",
                error_code="flock_not_found",
            )

        current_population = self.repository.get_current_population(
            farm_id,
            flock_id,
        )

        changes = payload.model_dump(
            exclude_unset=True,
            mode="json",
        )

        requested_code = changes.get("flock_code")

        if requested_code is not None and requested_code != flock.flock_code:
            conflicting_flock = self.repository.get_by_code(
                farm_id,
                requested_code,
            )

            if conflicting_flock is not None:
                raise ResourceConflictError(
                    "Another flock already uses this flock code.",
                    error_code=("flock_code_already_exists"),
                )

        requested_supplier_id = changes.get("supplier_id")

        if "supplier_id" in changes:
            self._get_valid_supplier(
                farm_id,
                requested_supplier_id,
            )

        requested_house_id = changes.get("house_id")

        if requested_house_id is not None and requested_house_id != flock.house_id:
            self._validate_house_capacity(
                farm_id,
                requested_house_id,
                current_population,
            )

        requested_status = changes.get("status")

        if requested_status in TERMINAL_FLOCK_STATUSES and current_population > 0:
            raise BusinessRuleError(
                "A flock with live birds cannot be marked depleted, sold or archived.",
                error_code="live_flock_cannot_be_closed",
            )

        requested_stage = changes.get("production_stage")

        if requested_stage in TERMINAL_PRODUCTION_STAGES and current_population > 0:
            raise BusinessRuleError(
                "A flock with live birds cannot use a "
                "depleted or sold production stage.",
                error_code=("live_flock_cannot_use_terminal_stage"),
            )

        if not changes:
            return flock, current_population

        self.repository.update_flock(
            flock,
            changes,
        )

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The flock could not be updated.",
                error_code="flock_update_conflict",
            ) from exc

        return self.get_flock(
            farm_id,
            flock_id,
        )

    def create_population_transaction(
        self,
        farm_id: UUID,
        flock_id: UUID,
        created_by: UUID,
        payload: PopulationTransactionCreate,
    ) -> tuple[FlockPopulationTransaction, int]:
        flock = self.repository.get_by_id(
            farm_id,
            flock_id,
            for_update=True,
        )

        if flock is None:
            raise ResourceNotFoundError(
                "The requested flock does not exist.",
                error_code="flock_not_found",
            )

        if payload.transaction_date < flock.arrival_date:
            raise BusinessRuleError(
                "A population transaction cannot occur before the flock arrival date.",
                error_code=("population_date_before_arrival"),
            )

        if flock.status in TERMINAL_FLOCK_STATUSES:
            raise BusinessRuleError(
                "Population transactions cannot be recorded for a closed flock.",
                error_code="flock_closed",
            )

        current_population = self.repository.get_current_population(
            farm_id,
            flock_id,
        )

        transaction_type = payload.transaction_type.value

        if transaction_type in POSITIVE_POPULATION_TRANSACTION_TYPES:
            signed_quantity = payload.quantity

            self._validate_house_capacity(
                farm_id,
                flock.house_id,
                payload.quantity,
            )

        elif transaction_type in NEGATIVE_POPULATION_TRANSACTION_TYPES:
            if payload.quantity > current_population:
                raise BusinessRuleError(
                    "The population reduction exceeds the flock's current population.",
                    error_code=("insufficient_flock_population"),
                )

            signed_quantity = -payload.quantity

        else:
            raise BusinessRuleError(
                "This population transaction type cannot be entered manually.",
                error_code=("invalid_population_transaction"),
            )

        transaction = FlockPopulationTransaction(
            farm_id=farm_id,
            flock_id=flock_id,
            transaction_date=payload.transaction_date,
            transaction_type=transaction_type,
            quantity=payload.quantity,
            signed_quantity=signed_quantity,
            source_type=("MANUAL_POPULATION_TRANSACTION"),
            source_id=None,
            description=payload.description,
            created_by=created_by,
        )

        self.repository.add_population_transaction(transaction)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The population transaction could not be saved.",
                error_code=("population_transaction_conflict"),
            ) from exc

        self.database_session.refresh(transaction)

        new_population = current_population + signed_quantity

        return transaction, new_population

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
        self.get_flock(farm_id, flock_id)

        return self.repository.list_population_transactions(
            farm_id,
            flock_id,
            offset=offset,
            limit=limit,
        )

    def get_population_summary(
        self,
        farm_id: UUID,
        flock_id: UUID,
    ) -> tuple[Flock, int, int]:
        flock, current_population = self.get_flock(
            farm_id,
            flock_id,
        )

        house_occupancy = self.repository.get_house_occupancy(
            farm_id,
            flock.house_id,
        )

        return (
            flock,
            current_population,
            house_occupancy,
        )
