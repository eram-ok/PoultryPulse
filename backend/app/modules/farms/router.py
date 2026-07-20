from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_database_session
from app.modules.farms.schemas import (
    FarmCreate,
    FarmListResponse,
    FarmResponse,
    FarmSettingsResponse,
    FarmSettingsUpdate,
    FarmUpdate,
)
from app.modules.farms.service import FarmService


router = APIRouter(
    prefix="/farms",
    tags=["Farms"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


@router.post(
    "",
    response_model=FarmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new poultry farm",
)
def create_farm(
    payload: FarmCreate,
    database_session: DatabaseSession,
) -> FarmResponse:
    """Register a farm and automatically create its settings."""

    farm = FarmService(database_session).create_farm(payload)
    return FarmResponse.model_validate(farm)


@router.get(
    "",
    response_model=FarmListResponse,
    summary="List registered farms",
)
def list_farms(
    database_session: DatabaseSession,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> FarmListResponse:
    """Return a paginated collection of farms."""

    farms, total = FarmService(database_session).list_farms(
        offset=offset,
        limit=limit,
    )

    return FarmListResponse(
        items=[FarmResponse.model_validate(farm) for farm in farms],
        total=total,
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
) -> FarmResponse:
    """Return one farm using its unique identifier."""

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
) -> FarmResponse:
    """Update selected farm fields."""

    farm = FarmService(database_session).update_farm(
        farm_id,
        payload,
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
) -> FarmSettingsResponse:
    """Return the operational settings for one farm."""

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
) -> FarmSettingsResponse:
    """Update selected operational settings for one farm."""

    settings = FarmService(database_session).update_settings(
        farm_id,
        payload,
    )

    return FarmSettingsResponse.model_validate(settings)
