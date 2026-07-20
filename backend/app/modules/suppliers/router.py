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
from app.modules.suppliers.constants import SupplierType
from app.modules.suppliers.schemas import (
    SupplierCreate,
    SupplierListResponse,
    SupplierResponse,
    SupplierUpdate,
)
from app.modules.suppliers.service import SupplierService
from app.modules.users.models import User


router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


@router.post(
    "",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a supplier",
)
def create_supplier(
    payload: SupplierCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("suppliers.create")),
    ],
) -> SupplierResponse:
    supplier = SupplierService(database_session).create_supplier(
        current_user.farm_id,
        payload,
    )

    return SupplierResponse.model_validate(supplier)


@router.get(
    "",
    response_model=SupplierListResponse,
    summary="List farm suppliers",
)
def list_suppliers(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("suppliers.view")),
    ],
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
    supplier_type: SupplierType | None = None,
    is_active: bool | None = None,
    search: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
        ),
    ] = None,
) -> SupplierListResponse:
    suppliers, total = SupplierService(database_session).list_suppliers(
        current_user.farm_id,
        offset=offset,
        limit=limit,
        supplier_type=supplier_type,
        is_active=is_active,
        search=search,
    )

    return SupplierListResponse(
        items=[SupplierResponse.model_validate(supplier) for supplier in suppliers],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Get one supplier",
)
def get_supplier(
    supplier_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("suppliers.view")),
    ],
) -> SupplierResponse:
    supplier = SupplierService(database_session).get_supplier(
        current_user.farm_id,
        supplier_id,
    )

    return SupplierResponse.model_validate(supplier)


@router.patch(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Update a supplier",
)
def update_supplier(
    supplier_id: UUID,
    payload: SupplierUpdate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("suppliers.update")),
    ],
) -> SupplierResponse:
    supplier = SupplierService(database_session).update_supplier(
        current_user.farm_id,
        supplier_id,
        payload,
    )

    return SupplierResponse.model_validate(supplier)


@router.post(
    "/{supplier_id}/activate",
    response_model=SupplierResponse,
    summary="Activate a supplier",
)
def activate_supplier(
    supplier_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("suppliers.update")),
    ],
) -> SupplierResponse:
    supplier = SupplierService(database_session).activate_supplier(
        current_user.farm_id,
        supplier_id,
    )

    return SupplierResponse.model_validate(supplier)


@router.post(
    "/{supplier_id}/deactivate",
    response_model=SupplierResponse,
    summary="Deactivate a supplier",
)
def deactivate_supplier(
    supplier_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("suppliers.update")),
    ],
) -> SupplierResponse:
    supplier = SupplierService(database_session).deactivate_supplier(
        current_user.farm_id,
        supplier_id,
    )

    return SupplierResponse.model_validate(supplier)
