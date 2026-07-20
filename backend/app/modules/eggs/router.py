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
from app.modules.auth.dependencies import (
    require_permissions,
)
from app.modules.eggs.constants import (
    EggGrade,
    EggInventoryTransactionType,
)
from app.modules.eggs.schemas import (
    EggInventoryAdjustmentCreate,
    EggInventoryIssueCreate,
    EggInventoryReversalCreate,
    EggInventorySummaryResponse,
    EggInventoryTransactionListResponse,
    EggInventoryTransactionResponse,
)
from app.modules.eggs.service import (
    EggInventoryService,
)
from app.modules.users.models import User


router = APIRouter(
    prefix="/egg-inventory",
    tags=["Egg Inventory"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


@router.get(
    "/balances",
    response_model=EggInventorySummaryResponse,
    summary="Get current egg stock balances",
)
def get_inventory_balances(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("eggs.view")),
    ],
) -> EggInventorySummaryResponse:
    summary = EggInventoryService(database_session).get_summary(current_user.farm_id)

    return EggInventorySummaryResponse(**summary)


@router.get(
    "/transactions",
    response_model=(EggInventoryTransactionListResponse),
    summary="List egg inventory transactions",
)
def list_inventory_transactions(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("eggs.view")),
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
    egg_grade: EggGrade | None = None,
    transaction_type: (EggInventoryTransactionType | None) = None,
    source_type: Annotated[
        str | None,
        Query(
            min_length=2,
            max_length=60,
        ),
    ] = None,
) -> EggInventoryTransactionListResponse:
    transactions, total = EggInventoryService(database_session).list_transactions(
        current_user.farm_id,
        offset=offset,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        egg_grade=egg_grade,
        transaction_type=transaction_type,
        source_type=source_type,
    )

    return EggInventoryTransactionListResponse(
        items=[
            EggInventoryTransactionResponse.model_validate(transaction)
            for transaction in transactions
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post(
    "/adjustments",
    response_model=EggInventoryTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an egg inventory adjustment",
)
def create_inventory_adjustment(
    payload: EggInventoryAdjustmentCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("eggs.adjust")),
    ],
) -> EggInventoryTransactionResponse:
    transaction = EggInventoryService(database_session).create_adjustment(
        current_user.farm_id,
        current_user.id,
        payload,
    )

    return EggInventoryTransactionResponse.model_validate(transaction)


@router.post(
    "/issues",
    response_model=EggInventoryTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue eggs from inventory",
)
def create_inventory_issue(
    payload: EggInventoryIssueCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("eggs.issue")),
    ],
) -> EggInventoryTransactionResponse:
    transaction = EggInventoryService(database_session).create_issue(
        current_user.farm_id,
        current_user.id,
        payload,
    )

    return EggInventoryTransactionResponse.model_validate(transaction)


@router.post(
    "/transactions/{transaction_id}/reverse",
    response_model=EggInventoryTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Reverse an egg inventory transaction",
)
def reverse_inventory_transaction(
    transaction_id: UUID,
    payload: EggInventoryReversalCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("eggs.reverse")),
    ],
) -> EggInventoryTransactionResponse:
    reversal = EggInventoryService(database_session).reverse_transaction(
        current_user.farm_id,
        transaction_id,
        current_user.id,
        inventory_date=payload.inventory_date,
        reason=payload.reason,
    )

    return EggInventoryTransactionResponse.model_validate(reversal)
