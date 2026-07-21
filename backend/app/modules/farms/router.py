from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_database_session
from app.core.exceptions import ResourceNotFoundError
from app.modules.audit.constants import AuditAction
from app.modules.audit.integration import (
    farm_settings_snapshot,
    farm_snapshot,
    record_audit_safely,
    record_failure_safely,
)
from app.modules.auth.dependencies import require_permissions
from app.modules.farms.schemas import (
    FarmCreate,
    FarmListResponse,
    FarmResponse,
    FarmSettingsResponse,
    FarmSettingsUpdate,
    FarmUpdate,
)
from app.modules.farms.service import FarmService
from app.modules.users.models import User


router = APIRouter(
    prefix="/farms",
    tags=["Farms"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


def verify_farm_access(
    current_user: User,
    farm_id: UUID,
) -> None:
    """Prevent users from accessing another farm's records."""

    if current_user.farm_id != farm_id:
        raise ResourceNotFoundError(
            "The requested farm does not exist.",
            error_code="farm_not_found",
        )


@router.post(
    "",
    response_model=FarmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new poultry farm",
)
def create_farm(
    payload: FarmCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("farms.create")),
    ],
) -> FarmResponse:
    service = FarmService(database_session)

    try:
        farm = service.create_farm(payload)
    except Exception as error:
        record_failure_safely(
            database_session,
            module="farms",
            action=AuditAction.CREATE,
            description="A farm-registration attempt failed.",
            error=error,
            farm_id=current_user.farm_id,
            actor_user_id=current_user.id,
            actor_username=current_user.username,
            resource_type="Farm",
            metadata={
                "requested_farm_code": payload.farm_code,
                "requested_name": payload.name,
            },
        )
        raise

    record_audit_safely(
        database_session,
        module="farms",
        action=AuditAction.CREATE,
        description="Registered a poultry farm.",
        farm_id=current_user.farm_id,
        actor_user_id=current_user.id,
        actor_username=current_user.username,
        resource_type="Farm",
        resource_id=farm.id,
        after_values=farm_snapshot(farm),
        metadata={
            "target_farm_id": farm.id,
        },
    )
    return FarmResponse.model_validate(farm)


@router.get(
    "",
    response_model=FarmListResponse,
    summary="List accessible farms",
)
def list_farms(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("farms.view")),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> FarmListResponse:
    farm = FarmService(database_session).get_farm(current_user.farm_id)

    items = []

    if offset == 0 and limit > 0:
        items.append(FarmResponse.model_validate(farm))

    return FarmListResponse(
        items=items,
        total=1,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{farm_id}",
    response_model=FarmResponse,
    summary="Get one farm",
)
def get_farm(
    farm_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("farms.view")),
    ],
) -> FarmResponse:
    verify_farm_access(current_user, farm_id)

    farm = FarmService(database_session).get_farm(farm_id)
    return FarmResponse.model_validate(farm)


@router.patch(
    "/{farm_id}",
    response_model=FarmResponse,
    summary="Update a farm",
)
def update_farm(
    farm_id: UUID,
    payload: FarmUpdate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("farms.update")),
    ],
) -> FarmResponse:
    verify_farm_access(current_user, farm_id)
    service = FarmService(database_session)
    before_values = farm_snapshot(service.get_farm(farm_id))

    try:
        farm = service.update_farm(
            farm_id,
            payload,
        )
    except Exception as error:
        record_failure_safely(
            database_session,
            module="farms",
            action=AuditAction.UPDATE,
            description="A farm-profile update failed.",
            error=error,
            farm_id=current_user.farm_id,
            actor_user_id=current_user.id,
            actor_username=current_user.username,
            resource_type="Farm",
            resource_id=farm_id,
            metadata={
                "requested_fields": sorted(payload.model_dump(exclude_unset=True)),
            },
        )
        raise

    record_audit_safely(
        database_session,
        module="farms",
        action=AuditAction.UPDATE,
        description="Updated the farm profile.",
        farm_id=current_user.farm_id,
        actor_user_id=current_user.id,
        actor_username=current_user.username,
        resource_type="Farm",
        resource_id=farm.id,
        before_values=before_values,
        after_values=farm_snapshot(farm),
    )
    return FarmResponse.model_validate(farm)


@router.get(
    "/{farm_id}/settings",
    response_model=FarmSettingsResponse,
    summary="Get farm settings",
)
def get_farm_settings(
    farm_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("farms.view")),
    ],
) -> FarmSettingsResponse:
    verify_farm_access(current_user, farm_id)

    settings = FarmService(database_session).get_settings(farm_id)

    return FarmSettingsResponse.model_validate(settings)


@router.patch(
    "/{farm_id}/settings",
    response_model=FarmSettingsResponse,
    summary="Update farm settings",
)
def update_farm_settings(
    farm_id: UUID,
    payload: FarmSettingsUpdate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("farms.settings.update")),
    ],
) -> FarmSettingsResponse:
    verify_farm_access(current_user, farm_id)
    service = FarmService(database_session)
    before_values = farm_settings_snapshot(service.get_settings(farm_id))

    try:
        settings = service.update_settings(
            farm_id,
            payload,
        )
    except Exception as error:
        record_failure_safely(
            database_session,
            module="farms",
            action=AuditAction.UPDATE,
            description="A farm-settings update failed.",
            error=error,
            farm_id=current_user.farm_id,
            actor_user_id=current_user.id,
            actor_username=current_user.username,
            resource_type="FarmSettings",
            resource_id=farm_id,
            metadata={
                "requested_fields": sorted(payload.model_dump(exclude_unset=True)),
            },
        )
        raise

    record_audit_safely(
        database_session,
        module="farms",
        action=AuditAction.UPDATE,
        description="Updated farm settings.",
        farm_id=current_user.farm_id,
        actor_user_id=current_user.id,
        actor_username=current_user.username,
        resource_type="FarmSettings",
        resource_id=settings.id,
        before_values=before_values,
        after_values=farm_settings_snapshot(settings),
    )
    return FarmSettingsResponse.model_validate(settings)
