from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.modules.farms.models import Farm, FarmSettings
from app.modules.farms.repository import FarmRepository
from app.modules.farms.schemas import (
    FarmCreate,
    FarmSettingsUpdate,
    FarmUpdate,
)


class FarmService:
    """Business operations for PoultryPulse farm management."""

    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session
        self.repository = FarmRepository(database_session)

    def create_farm(self, payload: FarmCreate) -> Farm:
        existing_farm = self.repository.get_by_code(payload.farm_code)

        if existing_farm is not None:
            raise ResourceConflictError(
                "A farm with this farm code already exists.",
                error_code="farm_code_already_exists",
            )

        farm_data = payload.model_dump(exclude={"settings"})
        settings_data = payload.settings.model_dump()

        farm = Farm(**farm_data)
        farm.settings = FarmSettings(**settings_data)

        self.repository.add(farm)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The farm could not be created because a unique value already exists.",
                error_code="farm_creation_conflict",
            ) from exc

        created_farm = self.repository.get_by_id(farm.id)

        if created_farm is None:
            raise ResourceNotFoundError(
                "The farm was created but could not be retrieved.",
                error_code="created_farm_not_found",
            )

        return created_farm

    def list_farms(
        self,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[Farm], int]:
        return self.repository.list_farms(
            offset=offset,
            limit=limit,
        )

    def get_farm(self, farm_id: UUID) -> Farm:
        farm = self.repository.get_by_id(farm_id)

        if farm is None:
            raise ResourceNotFoundError(
                "The requested farm does not exist.",
                error_code="farm_not_found",
            )

        return farm

    def update_farm(
        self,
        farm_id: UUID,
        payload: FarmUpdate,
    ) -> Farm:
        farm = self.get_farm(farm_id)
        changes = payload.model_dump(exclude_unset=True)

        requested_farm_code = changes.get("farm_code")

        if requested_farm_code is not None and requested_farm_code != farm.farm_code:
            conflicting_farm = self.repository.get_by_code(requested_farm_code)

            if conflicting_farm is not None:
                raise ResourceConflictError(
                    "Another farm already uses this farm code.",
                    error_code="farm_code_already_exists",
                )

        self.repository.update_farm(farm, changes)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The farm could not be updated because a unique value already exists.",
                error_code="farm_update_conflict",
            ) from exc

        updated_farm = self.repository.get_by_id(farm_id)

        if updated_farm is None:
            raise ResourceNotFoundError(
                "The updated farm could not be retrieved.",
                error_code="updated_farm_not_found",
            )

        return updated_farm

    def get_settings(self, farm_id: UUID) -> FarmSettings:
        farm = self.get_farm(farm_id)

        if farm.settings is None:
            raise ResourceNotFoundError(
                "Settings have not been configured for this farm.",
                error_code="farm_settings_not_found",
            )

        return farm.settings

    def update_settings(
        self,
        farm_id: UUID,
        payload: FarmSettingsUpdate,
    ) -> FarmSettings:
        settings = self.get_settings(farm_id)
        changes = payload.model_dump(exclude_unset=True)

        self.repository.update_settings(settings, changes)
        self.database_session.commit()
        self.database_session.refresh(settings)

        return settings
