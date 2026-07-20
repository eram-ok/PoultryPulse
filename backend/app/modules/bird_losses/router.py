from datetime import date
from decimal import Decimal
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
from app.modules.bird_losses.constants import (
    BirdLossReason,
    BirdLossRecordStatus,
    BirdLossType,
)
from app.modules.bird_losses.models import (
    BirdLossRecord,
)
from app.modules.bird_losses.schemas import (
    BirdLossCreate,
    BirdLossListResponse,
    BirdLossResponse,
    BirdLossReversalCreate,
    BirdLossSummaryResponse,
)
from app.modules.bird_losses.service import (
    BirdLossService,
)
from app.modules.users.models import User


router = APIRouter(
    prefix="/bird-losses",
    tags=["Mortality and Culling"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


def build_bird_loss_response(
    service: BirdLossService,
    farm_id: UUID,
    record: BirdLossRecord,
) -> BirdLossResponse:
    (
        current_population,
        daily_mortality,
        daily_percentage,
        threshold,
        alert,
    ) = service.get_response_metrics(
        farm_id,
        record,
    )

    return BirdLossResponse(
        id=record.id,
        farm_id=record.farm_id,
        flock_id=record.flock_id,
        flock_code=record.flock.flock_code,
        flock_name=record.flock.name,
        house_id=record.flock.house_id,
        house_code=record.flock.house.house_code,
        house_name=record.flock.house.name,
        loss_date=record.loss_date,
        loss_type=record.loss_type,
        quantity=record.quantity,
        reason_category=record.reason_category,
        cause_details=record.cause_details,
        disposal_method=record.disposal_method,
        disposal_details=record.disposal_details,
        location=record.location,
        reference=record.reference,
        notes=record.notes,
        population_before=record.population_before,
        population_after=record.population_after,
        current_population=current_population,
        loss_percentage=record.loss_percentage,
        daily_mortality_quantity=daily_mortality,
        daily_mortality_percentage=(daily_percentage),
        mortality_threshold_percentage=threshold,
        mortality_alert=alert,
        status=record.status,
        is_reversed=record.is_reversed,
        population_transaction_id=(record.population_transaction_id),
        reversal_population_transaction_id=(record.reversal_population_transaction_id),
        recorded_by=record.recorded_by,
        reversed_by=record.reversed_by,
        reversed_at=record.reversed_at,
        reversal_reason=record.reversal_reason,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.post(
    "",
    response_model=BirdLossResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record mortality or culling",
)
def create_bird_loss(
    payload: BirdLossCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("bird_losses.record")),
    ],
) -> BirdLossResponse:
    service = BirdLossService(database_session)

    record = service.create_record(
        current_user.farm_id,
        current_user.id,
        payload,
    )

    return build_bird_loss_response(
        service,
        current_user.farm_id,
        record,
    )


@router.get(
    "",
    response_model=BirdLossListResponse,
    summary="List mortality and culling records",
)
def list_bird_losses(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("bird_losses.view")),
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
    flock_id: UUID | None = None,
    loss_type: BirdLossType | None = None,
    reason_category: BirdLossReason | None = None,
    record_status: Annotated[
        BirdLossRecordStatus | None,
        Query(alias="status"),
    ] = None,
    search: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
        ),
    ] = None,
) -> BirdLossListResponse:
    service = BirdLossService(database_session)

    records, total = service.list_records(
        current_user.farm_id,
        offset=offset,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        flock_id=flock_id,
        loss_type=loss_type,
        reason_category=(
            reason_category.value if reason_category is not None else None
        ),
        record_status=record_status,
        search=search,
    )

    return BirdLossListResponse(
        items=[
            build_bird_loss_response(
                service,
                current_user.farm_id,
                record,
            )
            for record in records
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/summary",
    response_model=BirdLossSummaryResponse,
    summary="Get mortality and culling summary",
)
def get_bird_loss_summary(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("bird_losses.view")),
    ],
    date_from: date | None = None,
    date_to: date | None = None,
    flock_id: UUID | None = None,
) -> BirdLossSummaryResponse:
    (
        resolved_date_from,
        resolved_date_to,
        threshold,
        summary,
        current_population,
    ) = BirdLossService(database_session).get_summary(
        current_user.farm_id,
        date_from=date_from,
        date_to=date_to,
        flock_id=flock_id,
    )

    mortality_quantity = int(summary["mortality_quantity"])
    culling_quantity = int(summary["culling_quantity"])

    return BirdLossSummaryResponse(
        date_from=resolved_date_from,
        date_to=resolved_date_to,
        flock_id=flock_id,
        active_record_count=int(summary["active_record_count"]),
        reversed_record_count=int(summary["reversed_record_count"]),
        mortality_quantity=mortality_quantity,
        culling_quantity=culling_quantity,
        total_loss_quantity=(mortality_quantity + culling_quantity),
        average_incident_loss_percentage=(
            Decimal(str(summary["average_incident_loss_percentage"])).quantize(
                Decimal("0.0001")
            )
        ),
        maximum_incident_loss_percentage=(
            Decimal(str(summary["maximum_incident_loss_percentage"])).quantize(
                Decimal("0.0001")
            )
        ),
        mortality_threshold_percentage=threshold,
        high_mortality_incidents=int(summary["high_mortality_incidents"]),
        current_flock_population=(current_population),
    )


@router.get(
    "/{record_id}",
    response_model=BirdLossResponse,
    summary="Get one mortality or culling record",
)
def get_bird_loss(
    record_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("bird_losses.view")),
    ],
) -> BirdLossResponse:
    service = BirdLossService(database_session)

    record = service.get_record(
        current_user.farm_id,
        record_id,
    )

    return build_bird_loss_response(
        service,
        current_user.farm_id,
        record,
    )


@router.post(
    "/{record_id}/reverse",
    response_model=BirdLossResponse,
    summary="Reverse mortality or culling",
)
def reverse_bird_loss(
    record_id: UUID,
    payload: BirdLossReversalCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("bird_losses.reverse")),
    ],
) -> BirdLossResponse:
    service = BirdLossService(database_session)

    record = service.reverse_record(
        current_user.farm_id,
        record_id,
        current_user.id,
        reversal_date=payload.reversal_date,
        reason=payload.reason,
    )

    return build_bird_loss_response(
        service,
        current_user.farm_id,
        record,
    )
