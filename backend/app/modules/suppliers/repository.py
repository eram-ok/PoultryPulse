from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.suppliers.models import Supplier


class SupplierRepository:
    """Database operations for farm suppliers."""

    def __init__(
        self,
        database_session: Session,
    ) -> None:
        self.database_session = database_session

    def get_by_id(
        self,
        farm_id: UUID,
        supplier_id: UUID,
    ) -> Supplier | None:
        statement = select(Supplier).where(
            Supplier.farm_id == farm_id,
            Supplier.id == supplier_id,
        )

        return self.database_session.scalar(statement)

    def get_by_code(
        self,
        farm_id: UUID,
        supplier_code: str,
    ) -> Supplier | None:
        statement = select(Supplier).where(
            Supplier.farm_id == farm_id,
            Supplier.supplier_code == supplier_code,
        )

        return self.database_session.scalar(statement)

    def list_suppliers(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        supplier_type: str | None,
        is_active: bool | None,
        search: str | None,
    ) -> tuple[list[Supplier], int]:
        conditions = [Supplier.farm_id == farm_id]

        if supplier_type is not None:
            conditions.append(Supplier.supplier_type == supplier_type)

        if is_active is not None:
            conditions.append(Supplier.is_active.is_(is_active))

        if search:
            search_pattern = f"%{search.strip()}%"

            conditions.append(
                or_(
                    Supplier.supplier_code.ilike(search_pattern),
                    Supplier.name.ilike(search_pattern),
                    Supplier.telephone.ilike(search_pattern),
                    Supplier.email.ilike(search_pattern),
                )
            )

        suppliers_statement = (
            select(Supplier)
            .where(*conditions)
            .order_by(
                Supplier.name.asc(),
                Supplier.supplier_code.asc(),
            )
            .offset(offset)
            .limit(limit)
        )

        count_statement = select(func.count(Supplier.id)).where(*conditions)

        suppliers = list(self.database_session.scalars(suppliers_statement).all())

        total = self.database_session.scalar(count_statement) or 0

        return suppliers, total

    def add(self, supplier: Supplier) -> Supplier:
        self.database_session.add(supplier)
        return supplier

    def update(
        self,
        supplier: Supplier,
        changes: dict[str, Any],
    ) -> Supplier:
        for field_name, field_value in changes.items():
            setattr(
                supplier,
                field_name,
                field_value,
            )

        self.database_session.add(supplier)
        return supplier
