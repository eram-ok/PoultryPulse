from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.modules.houses.constants import PoultryHouseStatus
from app.modules.houses.models import PoultryHouse
from app.modules.houses.repository import (
    PoultryHouseRepository,
)
from app.modules.houses.schemas import (
    PoultryHouseCreate,
    PoultryHouseUpdate,
)


class PoultryHouseService:
    """Business operations for poultry-house management."""

    def __init__(
        self,
        database_session: Session,
    ) -> None:
        self.database_session = database_session
        self.repository = PoultryHouseRepository(database_session)

    def create_house(
        self,
        farm_id: UUID,
        payload: PoultryHouseCreate,
    ) -> PoultryHouse:
        existing_house = self.repository.get_by_code(
            farm_id,
            payload.house_code,
        )

        if existing_house is not None:
            raise ResourceConflictError(
                "A poultry house with this code already exists on the farm.",
                error_code="house_code_already_exists",
            )

        house_data = payload.model_dump(mode="json")

        poultry_house = PoultryHouse(
            farm_id=farm_id,
            **house_data,
        )

        self.repository.add(poultry_house)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The poultry house could not be "
                "created because one of its values "
                "conflicts with an existing record.",
                error_code="house_creation_conflict",
            ) from exc

        created_house = self.repository.get_by_id(
            farm_id,
            poultry_house.id,
        )

        if created_house is None:
            raise ResourceNotFoundError(
                "The poultry house was created but could not be retrieved.",
                error_code="created_house_not_found",
            )

        return created_house

    def list_houses(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        house_status: PoultryHouseStatus | None,
        search: str | None,
    ) -> tuple[list[PoultryHouse], int]:
        return self.repository.list_houses(
            farm_id,
            offset=offset,
            limit=limit,
            house_status=(house_status.value if house_status is not None else None),
            search=search,
        )

    def get_house(
        self,
        farm_id: UUID,
        house_id: UUID,
    ) -> PoultryHouse:
        poultry_house = self.repository.get_by_id(
            farm_id,
            house_id,
        )

        if poultry_house is None:
            raise ResourceNotFoundError(
                "The requested poultry house does not exist.",
                error_code="poultry_house_not_found",
            )

        return poultry_house

    def update_house(
        self,
        farm_id: UUID,
        house_id: UUID,
        payload: PoultryHouseUpdate,
    ) -> PoultryHouse:
        poultry_house = self.get_house(
            farm_id,
            house_id,
        )

        changes = payload.model_dump(
            exclude_unset=True,
            mode="json",
        )

        requested_code = changes.get("house_code")

        if requested_code is not None and requested_code != poultry_house.house_code:
            conflicting_house = self.repository.get_by_code(
                farm_id,
                requested_code,
            )

            if conflicting_house is not None:
                raise ResourceConflictError(
                    "Another poultry house already uses this house code.",
                    error_code=("house_code_already_exists"),
                )

        if not changes:
            return poultry_house

        self.repository.update(
            poultry_house,
            changes,
        )

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The poultry house could not be updated.",
                error_code="house_update_conflict",
            ) from exc

        updated_house = self.repository.get_by_id(
            farm_id,
            house_id,
        )

        if updated_house is None:
            raise ResourceNotFoundError(
                "The updated poultry house could not be retrieved.",
                error_code="updated_house_not_found",
            )

        return updated_house

    def activate_house(
        self,
        farm_id: UUID,
        house_id: UUID,
    ) -> PoultryHouse:
        poultry_house = self.get_house(
            farm_id,
            house_id,
        )

        poultry_house.status = PoultryHouseStatus.ACTIVE.value

        self.database_session.commit()

        return self.get_house(
            farm_id,
            house_id,
        )

    def deactivate_house(
        self,
        farm_id: UUID,
        house_id: UUID,
    ) -> PoultryHouse:
        poultry_house = self.get_house(
            farm_id,
            house_id,
        )

        poultry_house.status = PoultryHouseStatus.INACTIVE.value

        self.database_session.commit()

        return self.get_house(
            farm_id,
            house_id,
        )
