from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.farms.models import Farm, FarmSettings


class FarmRepository:
    """Database operations for farms and farm settings."""

    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session

    def get_by_id(self, farm_id: UUID) -> Farm | None:
        statement = (
            select(Farm).options(selectinload(Farm.settings)).where(Farm.id == farm_id)
        )

        return self.database_session.scalar(statement)

    def get_by_code(self, farm_code: str) -> Farm | None:
        statement = (
            select(Farm)
            .options(selectinload(Farm.settings))
            .where(Farm.farm_code == farm_code)
        )

        return self.database_session.scalar(statement)

    def list_farms(
        self,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[Farm], int]:
        farms_statement = (
            select(Farm)
            .options(selectinload(Farm.settings))
            .order_by(Farm.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        total_statement = select(func.count(Farm.id))

        farms = list(self.database_session.scalars(farms_statement).all())
        total = self.database_session.scalar(total_statement) or 0

        return farms, total

    def add(self, farm: Farm) -> Farm:
        self.database_session.add(farm)
        return farm

    def update_farm(
        self,
        farm: Farm,
        changes: dict[str, Any],
    ) -> Farm:
        for field_name, field_value in changes.items():
            setattr(farm, field_name, field_value)

        self.database_session.add(farm)
        return farm

    def update_settings(
        self,
        settings: FarmSettings,
        changes: dict[str, Any],
    ) -> FarmSettings:
        for field_name, field_value in changes.items():
            setattr(settings, field_name, field_value)

        self.database_session.add(settings)
        return settings
