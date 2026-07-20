from datetime import date
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
from app.modules.production.constants import (
    ProductionRecordStatus,
)
from app.modules.production.models import (
    DailyEggProduction,
)
from app.modules.production.schemas import (
    DailyEggProductionCreate,
    DailyEggProductionListResponse,
    DailyEggProductionResponse,
    DailyEggProductionUpdate,
    ProductionRejectionRequest,
    ProductionSummaryResponse,
)
from app.modules.production.service import (
    DailyEggProductionService,
)
from app.modules.users.models import User


router = APIRouter(
    prefix="/production-records",
    tags=["Daily Egg Production"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


def build_production_response(
    production: DailyEggProduction,
) -> DailyEggProductionResponse:
    """Convert a production model into an API response."""

    return DailyEggProductionResponse(
        id=production.id,
        farm_id=production.farm_id,
        flock_id=production.flock_id,
        flock_code=production.flock.flock_code,
        flock_name=production.flock.name,
        house_id=production.flock.house_id,
        house_code=production.flock.house.house_code,
        production_date=production.production_date,
        birds_present=production.birds_present,
        morning_eggs=production.morning_eggs,
        afternoon_eggs=production.afternoon_eggs,
        evening_eggs=production.evening_eggs,
        total_collected=production.total_collected,
        large_eggs=production.large_eggs,
        medium_eggs=production.medium_eggs,
        small_eggs=production.small_eggs,
        damaged_eggs=production.damaged_eggs,
        rejected_eggs=production.rejected_eggs,
        total_graded=production.total_graded,
        saleable_eggs=production.saleable_eggs,
        ungraded_eggs=production.ungraded_eggs,
        laying_percentage=(production.laying_percentage),
        status=production.status,
        notes=production.notes,
        rejection_reason=(production.rejection_reason),
        revision_number=production.revision_number,
        recorded_by=production.recorded_by,
        last_updated_by=production.last_updated_by,
        submitted_by=production.submitted_by,
        submitted_at=production.submitted_at,
        confirmed_by=production.confirmed_by,
        confirmed_at=production.confirmed_at,
        rejected_by=production.rejected_by,
        rejected_at=production.rejected_at,
        created_at=production.created_at,
        updated_at=production.updated_at,
    )


@router.post(
    "",
    response_model=DailyEggProductionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a daily production draft",
)
def create_production_record(
    payload: DailyEggProductionCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("production.create")),
    ],
) -> DailyEggProductionResponse:
    production = DailyEggProductionService(database_session).create_record(
        current_user.farm_id,
        current_user.id,
        payload,
    )

    return build_production_response(production)


@router.get(
    "",
    response_model=DailyEggProductionListResponse,
    summary="List daily production records",
)
def list_production_records(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("production.view")),
    ],
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
    date_from: date | None = None,
    date_to: date | None = None,
    record_status: Annotated[
        ProductionRecordStatus | None,
        Query(alias="status"),
    ] = None,
    flock_id: UUID | None = None,
    search: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
        ),
    ] = None,
) -> DailyEggProductionListResponse:
    records, total = DailyEggProductionService(database_session).list_records(
        current_user.farm_id,
        offset=offset,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        record_status=record_status,
        flock_id=flock_id,
        search=search,
    )

    return DailyEggProductionListResponse(
        items=[build_production_response(record) for record in records],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/summary",
    response_model=ProductionSummaryResponse,
    summary="Get an egg-production summary",
)
def get_production_summary(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("production.view")),
    ],
    date_from: date | None = None,
    date_to: date | None = None,
    record_status: Annotated[
        ProductionRecordStatus | None,
        Query(alias="status"),
    ] = ProductionRecordStatus.CONFIRMED,
    flock_id: UUID | None = None,
) -> ProductionSummaryResponse:
    (
        resolved_date_from,
        resolved_date_to,
        summary,
        weighted_percentage,
    ) = DailyEggProductionService(database_session).get_summary(
        current_user.farm_id,
        date_from=date_from,
        date_to=date_to,
        record_status=record_status,
        flock_id=flock_id,
    )

    return ProductionSummaryResponse(
        date_from=resolved_date_from,
        date_to=resolved_date_to,
        status=record_status,
        record_count=summary["record_count"],
        bird_days=summary["bird_days"],
        morning_eggs=summary["morning_eggs"],
        afternoon_eggs=summary["afternoon_eggs"],
        evening_eggs=summary["evening_eggs"],
        total_collected=summary["total_collected"],
        large_eggs=summary["large_eggs"],
        medium_eggs=summary["medium_eggs"],
        small_eggs=summary["small_eggs"],
        damaged_eggs=summary["damaged_eggs"],
        rejected_eggs=summary["rejected_eggs"],
        saleable_eggs=summary["saleable_eggs"],
        weighted_laying_percentage=(weighted_percentage),
    )


@router.get(
    "/{production_id}",
    response_model=DailyEggProductionResponse,
    summary="Get one production record",
)
def get_production_record(
    production_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("production.view")),
    ],
) -> DailyEggProductionResponse:
    production = DailyEggProductionService(database_session).get_record(
        current_user.farm_id,
        production_id,
    )

    return build_production_response(production)


@router.patch(
    "/{production_id}",
    response_model=DailyEggProductionResponse,
    summary="Edit a draft production record",
)
def update_production_record(
    production_id: UUID,
    payload: DailyEggProductionUpdate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("production.create")),
    ],
) -> DailyEggProductionResponse:
    production = DailyEggProductionService(database_session).update_record(
        current_user.farm_id,
        production_id,
        current_user.id,
        payload,
    )

    return build_production_response(production)


@router.post(
    "/{production_id}/submit",
    response_model=DailyEggProductionResponse,
    summary="Submit a production record",
)
def submit_production_record(
    production_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("production.submit")),
    ],
) -> DailyEggProductionResponse:
    production = DailyEggProductionService(database_session).submit_record(
        current_user.farm_id,
        production_id,
        current_user.id,
    )

    return build_production_response(production)


@router.post(
    "/{production_id}/confirm",
    response_model=DailyEggProductionResponse,
    summary="Confirm a submitted production record",
)
def confirm_production_record(
    production_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("production.confirm")),
    ],
) -> DailyEggProductionResponse:
    production = DailyEggProductionService(database_session).confirm_record(
        current_user.farm_id,
        production_id,
        current_user.id,
    )

    return build_production_response(production)


@router.post(
    "/{production_id}/reject",
    response_model=DailyEggProductionResponse,
    summary="Reject a submitted production record",
)
def reject_production_record(
    production_id: UUID,
    payload: ProductionRejectionRequest,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("production.confirm")),
    ],
) -> DailyEggProductionResponse:
    production = DailyEggProductionService(database_session).reject_record(
        current_user.farm_id,
        production_id,
        current_user.id,
        payload.reason,
    )

    return build_production_response(production)
