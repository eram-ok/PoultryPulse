from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Header,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_database_session
from app.modules.farms.constants import FarmLifecycleStatus
from app.modules.platform.dependencies import (
    CurrentPlatformSuperAdmin,
)
from app.modules.platform.farm_schemas import (
    PlatformActivationRequest,
    PlatformFarmCreateRequest,
    PlatformFarmDetailResponse,
    PlatformFarmListResponse,
    PlatformFarmOnboardingResponse,
    PlatformFarmUpdateRequest,
    PlatformLifecycleReasonRequest,
)
from app.modules.platform.farm_service import (
    PlatformFarmService,
)
from app.modules.platform.models import PlatformUser
from app.modules.platform.service import (
    PlatformAuthService,
)


router = APIRouter(
    prefix="/platform/farms",
    tags=["Platform Farms"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


def record_failure(
    *,
    database_session: Session,
    actor: PlatformUser,
    farm_id: UUID | None,
    action: str,
    description: str,
    error: Exception,
    metadata: dict[str, object] | None = None,
) -> None:
    PlatformAuthService(
        database_session
    ).record_event(
        action=action,
        outcome="FAILURE",
        description=description,
        user=actor,
        target_farm_id=farm_id,
        resource_type="Farm",
        resource_id=farm_id,
        metadata=metadata,
        error=error,
    )


@router.get(
    "",
    response_model=PlatformFarmListResponse,
    summary="List customer farms",
)
def list_farms(
    database_session: DatabaseSession,
    current_user: CurrentPlatformSuperAdmin,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
    search: Annotated[
        str | None,
        Query(min_length=1, max_length=150),
    ] = None,
    lifecycle_status: Annotated[
        FarmLifecycleStatus | None,
        Query(alias="status"),
    ] = None,
) -> PlatformFarmListResponse:
    return PlatformFarmService(
        database_session
    ).list_farms(
        offset=offset,
        limit=limit,
        search=search,
        lifecycle_status=lifecycle_status,
    )


@router.post(
    "",
    response_model=PlatformFarmOnboardingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a customer farm and first administrator",
)
def create_farm(
    payload: PlatformFarmCreateRequest,
    response: Response,
    database_session: DatabaseSession,
    current_user: CurrentPlatformSuperAdmin,
    idempotency_key: Annotated[
        str | None,
        Header(
            alias="Idempotency-Key",
            min_length=8,
            max_length=128,
        ),
    ] = None,
) -> PlatformFarmOnboardingResponse:
    response.headers["Cache-Control"] = (
        "no-store, max-age=0"
    )
    response.headers["Pragma"] = "no-cache"
    service = PlatformFarmService(database_session)

    try:
        return service.create_farm(
            payload,
            actor=current_user,
            idempotency_key=idempotency_key,
        )
    except Exception as error:
        record_failure(
            database_session=database_session,
            actor=current_user,
            farm_id=None,
            action="FARM_CREATE",
            description=(
                "A platform farm-onboarding attempt failed."
            ),
            error=error,
            metadata={
                "requested_farm_code": payload.farm_code,
                "requested_name": payload.name,
                "requested_administrator_username": (
                    payload.first_administrator.username
                ),
                "idempotency_key_supplied": (
                    idempotency_key is not None
                ),
            },
        )
        raise


@router.get(
    "/{farm_id}",
    response_model=PlatformFarmDetailResponse,
    summary="Get one customer farm",
)
def get_farm(
    farm_id: UUID,
    database_session: DatabaseSession,
    current_user: CurrentPlatformSuperAdmin,
) -> PlatformFarmDetailResponse:
    return PlatformFarmService(
        database_session
    ).get_farm(farm_id)


@router.patch(
    "/{farm_id}",
    response_model=PlatformFarmDetailResponse,
    summary="Update a customer farm profile",
)
def update_farm(
    farm_id: UUID,
    payload: PlatformFarmUpdateRequest,
    database_session: DatabaseSession,
    current_user: CurrentPlatformSuperAdmin,
) -> PlatformFarmDetailResponse:
    service = PlatformFarmService(database_session)

    try:
        return service.update_farm(
            farm_id,
            payload,
            actor=current_user,
        )
    except Exception as error:
        record_failure(
            database_session=database_session,
            actor=current_user,
            farm_id=farm_id,
            action="FARM_UPDATE",
            description=(
                "A platform farm-profile update failed."
            ),
            error=error,
            metadata={
                "requested_fields": sorted(
                    payload.model_dump(
                        exclude_unset=True
                    )
                ),
            },
        )
        raise


@router.post(
    "/{farm_id}/activate",
    response_model=PlatformFarmDetailResponse,
    summary="Activate a customer farm",
)
def activate_farm(
    farm_id: UUID,
    payload: PlatformActivationRequest,
    database_session: DatabaseSession,
    current_user: CurrentPlatformSuperAdmin,
) -> PlatformFarmDetailResponse:
    service = PlatformFarmService(database_session)

    try:
        return service.activate_farm(
            farm_id,
            payload,
            actor=current_user,
        )
    except Exception as error:
        record_failure(
            database_session=database_session,
            actor=current_user,
            farm_id=farm_id,
            action="FARM_ACTIVATE",
            description=(
                "A platform farm-activation attempt failed."
            ),
            error=error,
            metadata={
                "reason_supplied": (
                    payload.reason is not None
                ),
            },
        )
        raise


@router.post(
    "/{farm_id}/suspend",
    response_model=PlatformFarmDetailResponse,
    summary="Suspend a customer farm",
)
def suspend_farm(
    farm_id: UUID,
    payload: PlatformLifecycleReasonRequest,
    database_session: DatabaseSession,
    current_user: CurrentPlatformSuperAdmin,
) -> PlatformFarmDetailResponse:
    service = PlatformFarmService(database_session)

    try:
        return service.suspend_farm(
            farm_id,
            payload,
            actor=current_user,
        )
    except Exception as error:
        record_failure(
            database_session=database_session,
            actor=current_user,
            farm_id=farm_id,
            action="FARM_SUSPEND",
            description=(
                "A platform farm-suspension attempt failed."
            ),
            error=error,
            metadata={
                "reason_length": len(payload.reason),
            },
        )
        raise


@router.post(
    "/{farm_id}/deactivate",
    response_model=PlatformFarmDetailResponse,
    summary="Deactivate a customer farm",
)
def deactivate_farm(
    farm_id: UUID,
    payload: PlatformLifecycleReasonRequest,
    database_session: DatabaseSession,
    current_user: CurrentPlatformSuperAdmin,
) -> PlatformFarmDetailResponse:
    service = PlatformFarmService(database_session)

    try:
        return service.deactivate_farm(
            farm_id,
            payload,
            actor=current_user,
        )
    except Exception as error:
        record_failure(
            database_session=database_session,
            actor=current_user,
            farm_id=farm_id,
            action="FARM_DEACTIVATE",
            description=(
                "A platform farm-deactivation attempt failed."
            ),
            error=error,
            metadata={
                "reason_length": len(payload.reason),
            },
        )
        raise
