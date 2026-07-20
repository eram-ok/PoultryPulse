from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.houses.models import PoultryHouse


class PoultryHouseRepository:
    """Database operations for poultry houses."""

    def __init__(
        self,
        database_session: Session,
    ) -> None:
        self.database_session = database_session

    def get_by_id(
        self,
        farm_id: UUID,
        house_id: UUID,
    ) -> PoultryHouse | None:
        statement = select(PoultryHouse).where(
            PoultryHouse.farm_id == farm_id,
            PoultryHouse.id == house_id,
        )

        return self.database_session.scalar(statement)

    def get_by_code(
        self,
        farm_id: UUID,
        house_code: str,
    ) -> PoultryHouse | None:
        statement = select(PoultryHouse).where(
            PoultryHouse.farm_id == farm_id,
            PoultryHouse.house_code == house_code,
        )

        return self.database_session.scalar(statement)

    def list_houses(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        house_status: str | None,
        search: str | None,
    ) -> tuple[list[PoultryHouse], int]:
        conditions = [PoultryHouse.farm_id == farm_id]

        if house_status is not None:
            conditions.append(PoultryHouse.status == house_status)

        if search:
            search_pattern = f"%{search.strip()}%"

            conditions.append(
                or_(
                    PoultryHouse.house_code.ilike(search_pattern),
                    PoultryHouse.name.ilike(search_pattern),
                    PoultryHouse.location.ilike(search_pattern),
                )
            )

        houses_statement = (
            select(PoultryHouse)
            .where(*conditions)
            .order_by(
                PoultryHouse.name.asc(),
                PoultryHouse.house_code.asc(),
            )
            .offset(offset)
            .limit(limit)
        )

        count_statement = select(func.count(PoultryHouse.id)).where(*conditions)

        houses = list(self.database_session.scalars(houses_statement).all())

        total = self.database_session.scalar(count_statement) or 0

        return houses, total

    def add(
        self,
        poultry_house: PoultryHouse,
    ) -> PoultryHouse:
        self.database_session.add(poultry_house)

        return poultry_house

    def update(
        self,
        poultry_house: PoultryHouse,
        changes: dict[str, Any],
    ) -> PoultryHouse:
        for field_name, field_value in changes.items():
            setattr(
                poultry_house,
                field_name,
                field_value,
            )

        self.database_session.add(poultry_house)

        return poultry_house
