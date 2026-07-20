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
from app.modules.feed.constants import (
    FeedCategory,
    FeedInventoryTransactionType,
    FeedPurchaseStatus,
    FeedUsagePeriod,
)
from app.modules.feed.models import (
    FeedInventoryTransaction,
    FeedPurchase,
    FeedUsage,
)
from app.modules.feed.schemas import (
    FeedInventoryAdjustmentCreate,
    FeedInventoryReversalCreate,
    FeedInventorySummaryResponse,
    FeedInventoryTransactionListResponse,
    FeedInventoryTransactionResponse,
    FeedItemCreate,
    FeedItemListResponse,
    FeedItemResponse,
    FeedItemUpdate,
    FeedPurchaseCreate,
    FeedPurchaseListResponse,
    FeedPurchaseResponse,
    FeedPurchaseVoidRequest,
    FeedUsageCreate,
    FeedUsageListResponse,
    FeedUsageResponse,
    FeedWastageCreate,
)
from app.modules.feed.service import FeedService
from app.modules.users.models import User


router = APIRouter(
    prefix="/feed",
    tags=["Feed Management"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


def build_purchase_response(
    purchase: FeedPurchase,
) -> FeedPurchaseResponse:
    return FeedPurchaseResponse(
        id=purchase.id,
        farm_id=purchase.farm_id,
        feed_item_id=purchase.feed_item_id,
        feed_code=purchase.feed_item.feed_code,
        feed_name=purchase.feed_item.name,
        supplier_id=purchase.supplier_id,
        supplier_code=(
            purchase.supplier.supplier_code if purchase.supplier is not None else None
        ),
        supplier_name=(
            purchase.supplier.name if purchase.supplier is not None else None
        ),
        purchase_date=purchase.purchase_date,
        invoice_number=purchase.invoice_number,
        quantity_kg=purchase.quantity_kg,
        unit_cost=purchase.unit_cost,
        total_cost=purchase.total_cost,
        status=purchase.status,
        notes=purchase.notes,
        created_by=purchase.created_by,
        voided_by=purchase.voided_by,
        voided_at=purchase.voided_at,
        created_at=purchase.created_at,
        updated_at=purchase.updated_at,
    )


def build_usage_response(
    usage: FeedUsage,
    birds_present: int,
) -> FeedUsageResponse:
    grams_per_bird = FeedService.calculate_grams_per_bird(
        usage.quantity_kg,
        birds_present,
    )

    return FeedUsageResponse(
        id=usage.id,
        farm_id=usage.farm_id,
        flock_id=usage.flock_id,
        flock_code=usage.flock.flock_code,
        flock_name=usage.flock.name,
        feed_item_id=usage.feed_item_id,
        feed_code=usage.feed_item.feed_code,
        feed_name=usage.feed_item.name,
        usage_date=usage.usage_date,
        feeding_period=usage.feeding_period,
        quantity_kg=usage.quantity_kg,
        birds_present=birds_present,
        grams_per_bird=grams_per_bird,
        notes=usage.notes,
        created_by=usage.created_by,
        created_at=usage.created_at,
    )


def build_inventory_transaction_response(
    transaction: FeedInventoryTransaction,
) -> FeedInventoryTransactionResponse:
    return FeedInventoryTransactionResponse(
        id=transaction.id,
        farm_id=transaction.farm_id,
        transaction_group_id=(transaction.transaction_group_id),
        feed_item_id=transaction.feed_item_id,
        feed_code=transaction.feed_item.feed_code,
        feed_name=transaction.feed_item.name,
        inventory_date=transaction.inventory_date,
        transaction_type=transaction.transaction_type,
        quantity_kg=transaction.quantity_kg,
        signed_quantity_kg=(transaction.signed_quantity_kg),
        direction=transaction.direction,
        source_type=transaction.source_type,
        source_id=transaction.source_id,
        reference=transaction.reference,
        description=transaction.description,
        created_by=transaction.created_by,
        reversed_transaction_id=(transaction.reversed_transaction_id),
        is_reversal=transaction.is_reversal,
        created_at=transaction.created_at,
    )


@router.post(
    "/items",
    response_model=FeedItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a feed item",
)
def create_feed_item(
    payload: FeedItemCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("feed.items.manage")),
    ],
) -> FeedItemResponse:
    item = FeedService(database_session).create_item(
        current_user.farm_id,
        payload,
    )

    return FeedItemResponse.model_validate(item)


@router.get(
    "/items",
    response_model=FeedItemListResponse,
    summary="List feed items",
)
def list_feed_items(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("feed.view")),
    ],
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
    category: FeedCategory | None = None,
    is_active: bool | None = None,
    search: Annotated[
        str | None,
        Query(min_length=1, max_length=100),
    ] = None,
) -> FeedItemListResponse:
    items, total = FeedService(database_session).list_items(
        current_user.farm_id,
        offset=offset,
        limit=limit,
        category=category,
        is_active=is_active,
        search=search,
    )

    return FeedItemListResponse(
        items=[FeedItemResponse.model_validate(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/items/{feed_item_id}",
    response_model=FeedItemResponse,
    summary="Get one feed item",
)
def get_feed_item(
    feed_item_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("feed.view")),
    ],
) -> FeedItemResponse:
    item = FeedService(database_session).get_item(
        current_user.farm_id,
        feed_item_id,
    )

    return FeedItemResponse.model_validate(item)


@router.patch(
    "/items/{feed_item_id}",
    response_model=FeedItemResponse,
    summary="Update a feed item",
)
def update_feed_item(
    feed_item_id: UUID,
    payload: FeedItemUpdate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("feed.items.manage")),
    ],
) -> FeedItemResponse:
    item = FeedService(database_session).update_item(
        current_user.farm_id,
        feed_item_id,
        payload,
    )

    return FeedItemResponse.model_validate(item)


@router.post(
    "/items/{feed_item_id}/activate",
    response_model=FeedItemResponse,
    summary="Activate a feed item",
)
def activate_feed_item(
    feed_item_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("feed.items.manage")),
    ],
) -> FeedItemResponse:
    item = FeedService(database_session).set_item_active_status(
        current_user.farm_id,
        feed_item_id,
        is_active=True,
    )

    return FeedItemResponse.model_validate(item)


@router.post(
    "/items/{feed_item_id}/deactivate",
    response_model=FeedItemResponse,
    summary="Deactivate a feed item",
)
def deactivate_feed_item(
    feed_item_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("feed.items.manage")),
    ],
) -> FeedItemResponse:
    item = FeedService(database_session).set_item_active_status(
        current_user.farm_id,
        feed_item_id,
        is_active=False,
    )

    return FeedItemResponse.model_validate(item)


@router.post(
    "/purchases",
    response_model=FeedPurchaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a feed purchase",
)
def create_feed_purchase(
    payload: FeedPurchaseCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("feed.purchases.create")),
    ],
) -> FeedPurchaseResponse:
    purchase = FeedService(database_session).create_purchase(
        current_user.farm_id,
        current_user.id,
        payload,
    )

    return build_purchase_response(purchase)


@router.get(
    "/purchases",
    response_model=FeedPurchaseListResponse,
    summary="List feed purchases",
)
def list_feed_purchases(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("feed.view")),
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
    feed_item_id: UUID | None = None,
    supplier_id: UUID | None = None,
    purchase_status: Annotated[
        FeedPurchaseStatus | None,
        Query(alias="status"),
    ] = None,
    search: Annotated[
        str | None,
        Query(min_length=1, max_length=100),
    ] = None,
) -> FeedPurchaseListResponse:
    purchases, total = FeedService(database_session).list_purchases(
        current_user.farm_id,
        offset=offset,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        feed_item_id=feed_item_id,
        supplier_id=supplier_id,
        purchase_status=purchase_status,
        search=search,
    )

    return FeedPurchaseListResponse(
        items=[build_purchase_response(purchase) for purchase in purchases],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/purchases/{purchase_id}",
    response_model=FeedPurchaseResponse,
    summary="Get one feed purchase",
)
def get_feed_purchase(
    purchase_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("feed.view")),
    ],
) -> FeedPurchaseResponse:
    purchase = FeedService(database_session).get_purchase(
        current_user.farm_id,
        purchase_id,
    )

    return build_purchase_response(purchase)


@router.post(
    "/purchases/{purchase_id}/void",
    response_model=FeedPurchaseResponse,
    summary="Void a feed purchase",
)
def void_feed_purchase(
    purchase_id: UUID,
    payload: FeedPurchaseVoidRequest,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("feed.reverse")),
    ],
) -> FeedPurchaseResponse:
    purchase = FeedService(database_session).void_purchase(
        current_user.farm_id,
        purchase_id,
        current_user.id,
        payload.reason,
    )

    return build_purchase_response(purchase)


@router.post(
    "/usages",
    response_model=FeedUsageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record flock feed usage",
)
def create_feed_usage(
    payload: FeedUsageCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("feed.usage.record")),
    ],
) -> FeedUsageResponse:
    usage, birds_present = FeedService(database_session).create_usage(
        current_user.farm_id,
        current_user.id,
        payload,
    )

    return build_usage_response(
        usage,
        birds_present,
    )


@router.get(
    "/usages",
    response_model=FeedUsageListResponse,
    summary="List flock feed usage",
)
def list_feed_usages(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("feed.view")),
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
    feed_item_id: UUID | None = None,
    feeding_period: FeedUsagePeriod | None = None,
    search: Annotated[
        str | None,
        Query(min_length=1, max_length=100),
    ] = None,
) -> FeedUsageListResponse:
    usage_records, total = FeedService(database_session).list_usages(
        current_user.farm_id,
        offset=offset,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        flock_id=flock_id,
        feed_item_id=feed_item_id,
        feeding_period=feeding_period,
        search=search,
    )

    return FeedUsageListResponse(
        items=[
            build_usage_response(
                usage,
                birds_present,
            )
            for usage, birds_present in usage_records
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/usages/{usage_id}",
    response_model=FeedUsageResponse,
    summary="Get one flock feed usage record",
)
def get_feed_usage(
    usage_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("feed.view")),
    ],
) -> FeedUsageResponse:
    usage, birds_present = FeedService(database_session).get_usage(
        current_user.farm_id,
        usage_id,
    )

    return build_usage_response(
        usage,
        birds_present,
    )


@router.get(
    "/inventory/balances",
    response_model=FeedInventorySummaryResponse,
    summary="Get current feed inventory balances",
)
def get_feed_inventory_balances(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("feed.view")),
    ],
) -> FeedInventorySummaryResponse:
    summary = FeedService(database_session).get_inventory_summary(current_user.farm_id)

    return FeedInventorySummaryResponse(**summary)


@router.get(
    "/inventory/transactions",
    response_model=(FeedInventoryTransactionListResponse),
    summary="List feed inventory transactions",
)
def list_feed_inventory_transactions(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("feed.view")),
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
    feed_item_id: UUID | None = None,
    transaction_type: (FeedInventoryTransactionType | None) = None,
    source_type: Annotated[
        str | None,
        Query(min_length=2, max_length=60),
    ] = None,
) -> FeedInventoryTransactionListResponse:
    transactions, total = FeedService(database_session).list_inventory_transactions(
        current_user.farm_id,
        offset=offset,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        feed_item_id=feed_item_id,
        transaction_type=transaction_type,
        source_type=source_type,
    )

    return FeedInventoryTransactionListResponse(
        items=[
            build_inventory_transaction_response(transaction)
            for transaction in transactions
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post(
    "/inventory/adjustments",
    response_model=FeedInventoryTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a feed inventory adjustment",
)
def create_feed_inventory_adjustment(
    payload: FeedInventoryAdjustmentCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("feed.adjust")),
    ],
) -> FeedInventoryTransactionResponse:
    transaction = FeedService(database_session).create_adjustment(
        current_user.farm_id,
        current_user.id,
        payload,
    )

    return build_inventory_transaction_response(transaction)


@router.post(
    "/inventory/wastage",
    response_model=FeedInventoryTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record feed wastage",
)
def create_feed_wastage(
    payload: FeedWastageCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("feed.adjust")),
    ],
) -> FeedInventoryTransactionResponse:
    transaction = FeedService(database_session).create_wastage(
        current_user.farm_id,
        current_user.id,
        payload,
    )

    return build_inventory_transaction_response(transaction)


@router.post(
    "/inventory/transactions/{transaction_id}/reverse",
    response_model=FeedInventoryTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Reverse a feed inventory transaction",
)
def reverse_feed_inventory_transaction(
    transaction_id: UUID,
    payload: FeedInventoryReversalCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("feed.reverse")),
    ],
) -> FeedInventoryTransactionResponse:
    transaction = FeedService(database_session).reverse_transaction(
        current_user.farm_id,
        transaction_id,
        current_user.id,
        inventory_date=payload.inventory_date,
        reason=payload.reason,
    )

    return build_inventory_transaction_response(transaction)
