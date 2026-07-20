from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.modules.suppliers.constants import SupplierType
from app.modules.suppliers.models import Supplier
from app.modules.suppliers.repository import SupplierRepository
from app.modules.suppliers.schemas import (
    SupplierCreate,
    SupplierUpdate,
)


class SupplierService:
    """Business operations for supplier management."""

    def __init__(
        self,
        database_session: Session,
    ) -> None:
        self.database_session = database_session
        self.repository = SupplierRepository(database_session)

    def create_supplier(
        self,
        farm_id: UUID,
        payload: SupplierCreate,
    ) -> Supplier:
        existing_supplier = self.repository.get_by_code(
            farm_id,
            payload.supplier_code,
        )

        if existing_supplier is not None:
            raise ResourceConflictError(
                "A supplier with this code already exists on the farm.",
                error_code=("supplier_code_already_exists"),
            )

        supplier_data = payload.model_dump(mode="json")

        supplier = Supplier(
            farm_id=farm_id,
            **supplier_data,
        )

        self.repository.add(supplier)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The supplier could not be created "
                "because one of its values conflicts "
                "with an existing record.",
                error_code="supplier_creation_conflict",
            ) from exc

        created_supplier = self.repository.get_by_id(
            farm_id,
            supplier.id,
        )

        if created_supplier is None:
            raise ResourceNotFoundError(
                "The supplier was created but could not be retrieved.",
                error_code="created_supplier_not_found",
            )

        return created_supplier

    def list_suppliers(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        supplier_type: SupplierType | None,
        is_active: bool | None,
        search: str | None,
    ) -> tuple[list[Supplier], int]:
        return self.repository.list_suppliers(
            farm_id,
            offset=offset,
            limit=limit,
            supplier_type=(supplier_type.value if supplier_type is not None else None),
            is_active=is_active,
            search=search,
        )

    def get_supplier(
        self,
        farm_id: UUID,
        supplier_id: UUID,
    ) -> Supplier:
        supplier = self.repository.get_by_id(
            farm_id,
            supplier_id,
        )

        if supplier is None:
            raise ResourceNotFoundError(
                "The requested supplier does not exist.",
                error_code="supplier_not_found",
            )

        return supplier

    def update_supplier(
        self,
        farm_id: UUID,
        supplier_id: UUID,
        payload: SupplierUpdate,
    ) -> Supplier:
        supplier = self.get_supplier(
            farm_id,
            supplier_id,
        )

        changes = payload.model_dump(
            exclude_unset=True,
            mode="json",
        )

        requested_code = changes.get("supplier_code")

        if requested_code is not None and requested_code != supplier.supplier_code:
            conflicting_supplier = self.repository.get_by_code(
                farm_id,
                requested_code,
            )

            if conflicting_supplier is not None:
                raise ResourceConflictError(
                    "Another supplier already uses this supplier code.",
                    error_code=("supplier_code_already_exists"),
                )

        if not changes:
            return supplier

        self.repository.update(
            supplier,
            changes,
        )

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The supplier could not be updated.",
                error_code="supplier_update_conflict",
            ) from exc

        return self.get_supplier(
            farm_id,
            supplier_id,
        )

    def activate_supplier(
        self,
        farm_id: UUID,
        supplier_id: UUID,
    ) -> Supplier:
        supplier = self.get_supplier(
            farm_id,
            supplier_id,
        )

        supplier.is_active = True
        self.database_session.commit()

        return self.get_supplier(
            farm_id,
            supplier_id,
        )

    def deactivate_supplier(
        self,
        farm_id: UUID,
        supplier_id: UUID,
    ) -> Supplier:
        supplier = self.get_supplier(
            farm_id,
            supplier_id,
        )

        supplier.is_active = False
        self.database_session.commit()

        return self.get_supplier(
            farm_id,
            supplier_id,
        )
