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
from app.modules.auth.dependencies import require_permissions
from app.modules.flocks.constants import (
    FlockProductionStage,
    FlockStatus,
)
from app.modules.flocks.models import Flock
from app.modules.flocks.schemas import (
    FlockCreate,
    FlockListResponse,
    FlockPopulationSummaryResponse,
    FlockResponse,
    FlockUpdate,
    PopulationTransactionCreate,
    PopulationTransactionListResponse,
    PopulationTransactionResponse,
)
from app.modules.flocks.service import FlockService
from app.modules.users.models import User


router = APIRouter(
    prefix="/flocks",
    tags=["Flocks"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


def build_flock_response(
    flock: Flock,
    current_population: int,
) -> FlockResponse:
    """Convert a flock model into an API response."""

    return FlockResponse(
        id=flock.id,
        farm_id=flock.farm_id,
        house_id=flock.house_id,
        house_code=flock.house.house_code,
        house_name=flock.house.name,
        house_capacity=flock.house.capacity,
        supplier_id=flock.supplier_id,
        supplier_code=(
            flock.supplier.supplier_code if flock.supplier is not None else None
        ),
        supplier_name=(flock.supplier.name if flock.supplier is not None else None),
        flock_code=flock.flock_code,
        name=flock.name,
        breed=flock.breed,
        arrival_date=flock.arrival_date,
        hatch_date=flock.hatch_date,
        age_at_arrival_days=(flock.age_at_arrival_days),
        initial_population=flock.initial_population,
        current_population=current_population,
        purchase_cost=flock.purchase_cost,
        production_stage=flock.production_stage,
        status=flock.status,
        notes=flock.notes,
        created_at=flock.created_at,
        updated_at=flock.updated_at,
    )


@router.post(
    "",
    response_model=FlockResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a poultry flock",
)
def create_flock(
    payload: FlockCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("flocks.create")),
    ],
) -> FlockResponse:
    flock, current_population = FlockService(database_session).create_flock(
        current_user.farm_id,
        current_user.id,
        payload,
    )

    return build_flock_response(
        flock,
        current_population,
    )


@router.get(
    "",
    response_model=FlockListResponse,
    summary="List poultry flocks",
)
def list_flocks(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("flocks.view")),
    ],
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
    flock_status: Annotated[
        FlockStatus | None,
        Query(alias="status"),
    ] = None,
    production_stage: (FlockProductionStage | None) = None,
    house_id: UUID | None = None,
    supplier_id: UUID | None = None,
    search: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
        ),
    ] = None,
) -> FlockListResponse:
    flock_records, total = FlockService(database_session).list_flocks(
        current_user.farm_id,
        offset=offset,
        limit=limit,
        flock_status=flock_status,
        production_stage=production_stage,
        house_id=house_id,
        supplier_id=supplier_id,
        search=search,
    )

    return FlockListResponse(
        items=[
            build_flock_response(
                flock,
                current_population,
            )
            for flock, current_population in flock_records
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{flock_id}",
    response_model=FlockResponse,
    summary="Get one poultry flock",
)
def get_flock(
    flock_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("flocks.view")),
    ],
) -> FlockResponse:
    flock, current_population = FlockService(database_session).get_flock(
        current_user.farm_id,
        flock_id,
    )

    return build_flock_response(
        flock,
        current_population,
    )


@router.patch(
    "/{flock_id}",
    response_model=FlockResponse,
    summary="Update a poultry flock",
)
def update_flock(
    flock_id: UUID,
    payload: FlockUpdate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("flocks.update")),
    ],
) -> FlockResponse:
    flock, current_population = FlockService(database_session).update_flock(
        current_user.farm_id,
        flock_id,
        payload,
    )

    return build_flock_response(
        flock,
        current_population,
    )


@router.get(
    "/{flock_id}/population",
    response_model=FlockPopulationSummaryResponse,
    summary="Get flock population summary",
)
def get_population_summary(
    flock_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("flocks.view")),
    ],
) -> FlockPopulationSummaryResponse:
    (
        flock,
        current_population,
        house_occupancy,
    ) = FlockService(database_session).get_population_summary(
        current_user.farm_id,
        flock_id,
    )

    return FlockPopulationSummaryResponse(
        flock_id=flock.id,
        flock_code=flock.flock_code,
        house_id=flock.house_id,
        house_code=flock.house.house_code,
        initial_population=flock.initial_population,
        current_population=current_population,
        house_capacity=flock.house.capacity,
        house_occupancy=house_occupancy,
        available_house_capacity=max(
            flock.house.capacity - house_occupancy,
            0,
        ),
    )


@router.get(
    "/{flock_id}/population-transactions",
    response_model=PopulationTransactionListResponse,
    summary="List flock population transactions",
)
def list_population_transactions(
    flock_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("flocks.view")),
    ],
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
) -> PopulationTransactionListResponse:
    transactions, total = FlockService(database_session).list_population_transactions(
        current_user.farm_id,
        flock_id,
        offset=offset,
        limit=limit,
    )

    return PopulationTransactionListResponse(
        items=[
            PopulationTransactionResponse.model_validate(transaction)
            for transaction in transactions
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post(
    "/{flock_id}/population-transactions",
    response_model=PopulationTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a flock population adjustment",
)
def create_population_transaction(
    flock_id: UUID,
    payload: PopulationTransactionCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("flocks.population.adjust")),
    ],
) -> PopulationTransactionResponse:
    transaction, _ = FlockService(database_session).create_population_transaction(
        current_user.farm_id,
        flock_id,
        current_user.id,
        payload,
    )

    return PopulationTransactionResponse.model_validate(transaction)
