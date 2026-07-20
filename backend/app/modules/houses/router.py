from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_database_session
from app.modules.auth.dependencies import (
    require_permissions,
)
from app.modules.houses.constants import (
    PoultryHouseStatus,
)
from app.modules.houses.schemas import (
    PoultryHouseCreate,
    PoultryHouseListResponse,
    PoultryHouseResponse,
    PoultryHouseUpdate,
)
from app.modules.houses.service import (
    PoultryHouseService,
)
from app.modules.users.models import User


router = APIRouter(
    prefix="/houses",
    tags=["Poultry Houses"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


@router.post(
    "",
    response_model=PoultryHouseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a poultry house",
)
def create_house(
    payload: PoultryHouseCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("houses.create")),
    ],
) -> PoultryHouseResponse:
    poultry_house = PoultryHouseService(database_session).create_house(
        current_user.farm_id,
        payload,
    )

    return PoultryHouseResponse.model_validate(poultry_house)


@router.get(
    "",
    response_model=PoultryHouseListResponse,
    summary="List poultry houses",
)
def list_houses(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("houses.view")),
    ],
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
    house_status: Annotated[
        PoultryHouseStatus | None,
        Query(alias="status"),
    ] = None,
    search: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
        ),
    ] = None,
) -> PoultryHouseListResponse:
    houses, total = PoultryHouseService(database_session).list_houses(
        current_user.farm_id,
        offset=offset,
        limit=limit,
        house_status=house_status,
        search=search,
    )

    return PoultryHouseListResponse(
        items=[
            PoultryHouseResponse.model_validate(poultry_house)
            for poultry_house in houses
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{house_id}",
    response_model=PoultryHouseResponse,
    summary="Get one poultry house",
)
def get_house(
    house_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("houses.view")),
    ],
) -> PoultryHouseResponse:
    poultry_house = PoultryHouseService(database_session).get_house(
        current_user.farm_id,
        house_id,
    )

    return PoultryHouseResponse.model_validate(poultry_house)


@router.patch(
    "/{house_id}",
    response_model=PoultryHouseResponse,
    summary="Update a poultry house",
)
def update_house(
    house_id: UUID,
    payload: PoultryHouseUpdate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("houses.update")),
    ],
) -> PoultryHouseResponse:
    poultry_house = PoultryHouseService(database_session).update_house(
        current_user.farm_id,
        house_id,
        payload,
    )

    return PoultryHouseResponse.model_validate(poultry_house)


@router.post(
    "/{house_id}/activate",
    response_model=PoultryHouseResponse,
    summary="Activate a poultry house",
)
def activate_house(
    house_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("houses.update")),
    ],
) -> PoultryHouseResponse:
    poultry_house = PoultryHouseService(database_session).activate_house(
        current_user.farm_id,
        house_id,
    )

    return PoultryHouseResponse.model_validate(poultry_house)


@router.post(
    "/{house_id}/deactivate",
    response_model=PoultryHouseResponse,
    summary="Deactivate a poultry house",
)
def deactivate_house(
    house_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("houses.update")),
    ],
) -> PoultryHouseResponse:
    poultry_house = PoultryHouseService(database_session).deactivate_house(
        current_user.farm_id,
        house_id,
    )

    return PoultryHouseResponse.model_validate(poultry_house)
