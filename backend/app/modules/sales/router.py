from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_database_session
from app.modules.auth.dependencies import require_permissions
from app.modules.sales.constants import (
    CustomerStatus,
    PaymentStatus,
    SaleReturnStatus,
    SaleStatus,
)
from app.modules.sales.models import (
    Customer,
    Sale,
    SaleItem,
    SalePayment,
    SaleReturn,
    SaleReturnItem,
)
from app.modules.sales.schemas import (
    CustomerCreate,
    CustomerListResponse,
    CustomerResponse,
    CustomerStatementResponse,
    CustomerUpdate,
    LedgerEntryResponse,
    PaymentCreate,
    PaymentListResponse,
    PaymentResponse,
    PaymentReversalRequest,
    SaleCancellationRequest,
    SaleConfirmationRequest,
    SaleCreate,
    SaleItemResponse,
    SaleListResponse,
    SaleResponse,
    SaleReturnCreate,
    SaleReturnItemResponse,
    SaleReturnListResponse,
    SaleReturnResponse,
    SaleReturnReversalRequest,
    SaleUpdate,
    SalesSummaryResponse,
)
from app.modules.sales.service import SalesService
from app.modules.users.models import User


router = APIRouter(
    prefix="/sales",
    tags=["Customers, Egg Sales and Payments"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


def build_customer_response(
    customer: Customer,
) -> CustomerResponse:
    return CustomerResponse.model_validate(customer)


def build_sale_item_response(
    item: SaleItem,
) -> SaleItemResponse:
    return SaleItemResponse(
        id=item.id,
        egg_grade=item.egg_grade,
        unit=item.unit,
        eggs_per_unit=item.eggs_per_unit,
        quantity=item.quantity,
        quantity_returned=item.quantity_returned,
        remaining_returnable_quantity=(item.remaining_returnable_quantity),
        unit_price=item.unit_price,
        line_total=item.line_total,
        total_eggs=(item.quantity * item.eggs_per_unit),
        notes=item.notes,
        created_at=item.created_at,
    )


def build_sale_response(sale: Sale) -> SaleResponse:
    return SaleResponse(
        id=sale.id,
        farm_id=sale.farm_id,
        customer_id=sale.customer_id,
        customer_code=sale.customer.customer_code,
        customer_name=sale.customer.name,
        invoice_number=sale.invoice_number,
        sale_date=sale.sale_date,
        due_date=sale.due_date,
        payment_terms=sale.payment_terms,
        status=sale.status,
        subtotal=sale.subtotal,
        discount_amount=sale.discount_amount,
        tax_amount=sale.tax_amount,
        total_amount=sale.total_amount,
        amount_paid=sale.amount_paid,
        balance_due=sale.balance_due,
        is_paid=sale.is_paid,
        is_cancelled=sale.is_cancelled,
        is_confirmed=sale.is_confirmed,
        notes=sale.notes,
        created_by=sale.created_by,
        confirmed_by=sale.confirmed_by,
        confirmed_at=sale.confirmed_at,
        cancelled_by=sale.cancelled_by,
        cancelled_at=sale.cancelled_at,
        cancellation_reason=sale.cancellation_reason,
        items=[build_sale_item_response(item) for item in sale.items],
        created_at=sale.created_at,
        updated_at=sale.updated_at,
    )


def build_payment_response(
    payment: SalePayment,
) -> PaymentResponse:
    return PaymentResponse(
        id=payment.id,
        farm_id=payment.farm_id,
        customer_id=payment.customer_id,
        customer_code=payment.customer.customer_code,
        customer_name=payment.customer.name,
        sale_id=payment.sale_id,
        invoice_number=payment.sale.invoice_number,
        payment_number=payment.payment_number,
        payment_date=payment.payment_date,
        amount=payment.amount,
        method=payment.method,
        reference_number=payment.reference_number,
        status=payment.status,
        notes=payment.notes,
        received_by=payment.received_by,
        reversed_by=payment.reversed_by,
        reversed_at=payment.reversed_at,
        reversal_reason=payment.reversal_reason,
        is_reversed=payment.is_reversed,
        created_at=payment.created_at,
    )


def build_return_item_response(
    item: SaleReturnItem,
) -> SaleReturnItemResponse:
    return SaleReturnItemResponse(
        id=item.id,
        sale_item_id=item.sale_item_id,
        egg_grade=item.egg_grade,
        unit=item.unit,
        quantity=item.quantity,
        unit_price=item.unit_price,
        line_total=item.line_total,
        total_eggs=(item.quantity * item.sale_item.eggs_per_unit),
        reason=item.reason,
    )


def build_return_response(
    sale_return: SaleReturn,
) -> SaleReturnResponse:
    return SaleReturnResponse(
        id=sale_return.id,
        farm_id=sale_return.farm_id,
        sale_id=sale_return.sale_id,
        invoice_number=sale_return.sale.invoice_number,
        customer_id=sale_return.customer_id,
        customer_code=(sale_return.customer.customer_code),
        customer_name=sale_return.customer.name,
        return_number=sale_return.return_number,
        return_date=sale_return.return_date,
        total_refund=sale_return.total_refund,
        status=sale_return.status,
        reason=sale_return.reason,
        notes=sale_return.notes,
        recorded_by=sale_return.recorded_by,
        reversed_by=sale_return.reversed_by,
        reversed_at=sale_return.reversed_at,
        reversal_reason=sale_return.reversal_reason,
        is_reversed=sale_return.is_reversed,
        items=[build_return_item_response(item) for item in sale_return.items],
        created_at=sale_return.created_at,
    )


@router.post(
    "/customers",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    payload: CustomerCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("customers.manage")),
    ],
) -> CustomerResponse:
    customer = SalesService(database_session).create_customer(
        current_user.farm_id,
        current_user.id,
        payload,
    )
    return build_customer_response(customer)


@router.get(
    "/customers",
    response_model=CustomerListResponse,
)
def list_customers(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("sales.view")),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    customer_status: Annotated[
        CustomerStatus | None,
        Query(alias="status"),
    ] = None,
    search: Annotated[
        str | None,
        Query(min_length=1, max_length=100),
    ] = None,
) -> CustomerListResponse:
    customers, total = SalesService(database_session).list_customers(
        current_user.farm_id,
        offset=offset,
        limit=limit,
        customer_status=(
            customer_status.value if customer_status is not None else None
        ),
        search=search,
    )
    return CustomerListResponse(
        items=[build_customer_response(item) for item in customers],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/customers/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    customer_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("sales.view")),
    ],
) -> CustomerResponse:
    customer = SalesService(database_session).get_customer(
        current_user.farm_id,
        customer_id,
    )
    return build_customer_response(customer)


@router.patch(
    "/customers/{customer_id}",
    response_model=CustomerResponse,
)
def update_customer(
    customer_id: UUID,
    payload: CustomerUpdate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("customers.manage")),
    ],
) -> CustomerResponse:
    customer = SalesService(database_session).update_customer(
        current_user.farm_id,
        customer_id,
        payload,
    )
    return build_customer_response(customer)


@router.get(
    "/customers/{customer_id}/statement",
    response_model=CustomerStatementResponse,
)
def get_customer_statement(
    customer_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("sales.view")),
    ],
    date_from: date | None = None,
    date_to: date | None = None,
) -> CustomerStatementResponse:
    (
        customer,
        opening_balance,
        closing_balance,
        entries,
    ) = SalesService(database_session).get_statement(
        current_user.farm_id,
        customer_id,
        date_from=date_from,
        date_to=date_to,
    )
    return CustomerStatementResponse(
        customer=build_customer_response(customer),
        date_from=date_from,
        date_to=date_to,
        opening_balance=opening_balance,
        closing_balance=closing_balance,
        entries=[LedgerEntryResponse.model_validate(item) for item in entries],
    )


@router.post(
    "/invoices",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sale(
    payload: SaleCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("sales.create")),
    ],
) -> SaleResponse:
    sale = SalesService(database_session).create_sale(
        current_user.farm_id,
        current_user.id,
        payload,
    )
    return build_sale_response(sale)


@router.get(
    "/invoices",
    response_model=SaleListResponse,
)
def list_sales(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("sales.view")),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    date_from: date | None = None,
    date_to: date | None = None,
    customer_id: UUID | None = None,
    sale_status: Annotated[
        SaleStatus | None,
        Query(alias="status"),
    ] = None,
    search: Annotated[
        str | None,
        Query(min_length=1, max_length=100),
    ] = None,
) -> SaleListResponse:
    sales, total = SalesService(database_session).list_sales(
        current_user.farm_id,
        offset=offset,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        customer_id=customer_id,
        sale_status=(sale_status.value if sale_status is not None else None),
        search=search,
    )
    return SaleListResponse(
        items=[build_sale_response(item) for item in sales],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/invoices/{sale_id}",
    response_model=SaleResponse,
)
def get_sale(
    sale_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("sales.view")),
    ],
) -> SaleResponse:
    sale = SalesService(database_session).get_sale(
        current_user.farm_id,
        sale_id,
    )
    return build_sale_response(sale)


@router.patch(
    "/invoices/{sale_id}",
    response_model=SaleResponse,
)
def update_sale(
    sale_id: UUID,
    payload: SaleUpdate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("sales.create")),
    ],
) -> SaleResponse:
    sale = SalesService(database_session).update_sale(
        current_user.farm_id,
        sale_id,
        payload,
    )
    return build_sale_response(sale)


@router.post(
    "/invoices/{sale_id}/confirm",
    response_model=SaleResponse,
)
def confirm_sale(
    sale_id: UUID,
    payload: SaleConfirmationRequest,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("sales.confirm")),
    ],
) -> SaleResponse:
    sale = SalesService(database_session).confirm_sale(
        current_user.farm_id,
        sale_id,
        current_user.id,
        notes=payload.notes,
    )
    return build_sale_response(sale)


@router.post(
    "/invoices/{sale_id}/cancel",
    response_model=SaleResponse,
)
def cancel_sale(
    sale_id: UUID,
    payload: SaleCancellationRequest,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("sales.cancel")),
    ],
) -> SaleResponse:
    sale = SalesService(database_session).cancel_sale(
        current_user.farm_id,
        sale_id,
        current_user.id,
        payload.reason,
    )
    return build_sale_response(sale)


@router.post(
    "/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    payload: PaymentCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("payments.record")),
    ],
) -> PaymentResponse:
    payment = SalesService(database_session).record_payment(
        current_user.farm_id,
        current_user.id,
        payload,
    )
    return build_payment_response(payment)


@router.get(
    "/payments",
    response_model=PaymentListResponse,
)
def list_payments(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("sales.view")),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    date_from: date | None = None,
    date_to: date | None = None,
    customer_id: UUID | None = None,
    sale_id: UUID | None = None,
    payment_status: Annotated[
        PaymentStatus | None,
        Query(alias="status"),
    ] = None,
) -> PaymentListResponse:
    payments, total = SalesService(database_session).list_payments(
        current_user.farm_id,
        offset=offset,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        customer_id=customer_id,
        sale_id=sale_id,
        payment_status=(payment_status.value if payment_status is not None else None),
    )
    return PaymentListResponse(
        items=[build_payment_response(item) for item in payments],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/payments/{payment_id}",
    response_model=PaymentResponse,
)
def get_payment(
    payment_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("sales.view")),
    ],
) -> PaymentResponse:
    payment = SalesService(database_session).get_payment(
        current_user.farm_id,
        payment_id,
    )
    return build_payment_response(payment)


@router.post(
    "/payments/{payment_id}/reverse",
    response_model=PaymentResponse,
)
def reverse_payment(
    payment_id: UUID,
    payload: PaymentReversalRequest,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("payments.reverse")),
    ],
) -> PaymentResponse:
    payment = SalesService(database_session).reverse_payment(
        current_user.farm_id,
        payment_id,
        current_user.id,
        payload.reason,
    )
    return build_payment_response(payment)


@router.post(
    "/returns",
    response_model=SaleReturnResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sale_return(
    payload: SaleReturnCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("sales.returns")),
    ],
) -> SaleReturnResponse:
    sale_return = SalesService(database_session).create_return(
        current_user.farm_id,
        current_user.id,
        payload,
    )
    return build_return_response(sale_return)


@router.get(
    "/returns",
    response_model=SaleReturnListResponse,
)
def list_sale_returns(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("sales.view")),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    date_from: date | None = None,
    date_to: date | None = None,
    customer_id: UUID | None = None,
    sale_id: UUID | None = None,
    return_status: Annotated[
        SaleReturnStatus | None,
        Query(alias="status"),
    ] = None,
) -> SaleReturnListResponse:
    returns, total = SalesService(database_session).list_returns(
        current_user.farm_id,
        offset=offset,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        customer_id=customer_id,
        sale_id=sale_id,
        return_status=(return_status.value if return_status is not None else None),
    )
    return SaleReturnListResponse(
        items=[build_return_response(item) for item in returns],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/returns/{return_id}",
    response_model=SaleReturnResponse,
)
def get_sale_return(
    return_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("sales.view")),
    ],
) -> SaleReturnResponse:
    sale_return = SalesService(database_session).get_return(
        current_user.farm_id,
        return_id,
    )
    return build_return_response(sale_return)


@router.post(
    "/returns/{return_id}/reverse",
    response_model=SaleReturnResponse,
)
def reverse_sale_return(
    return_id: UUID,
    payload: SaleReturnReversalRequest,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("sales.returns")),
    ],
) -> SaleReturnResponse:
    sale_return = SalesService(database_session).reverse_return(
        current_user.farm_id,
        return_id,
        current_user.id,
        payload.reason,
    )
    return build_return_response(sale_return)


@router.get(
    "/summary",
    response_model=SalesSummaryResponse,
)
def get_sales_summary(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("sales.view")),
    ],
) -> SalesSummaryResponse:
    summary = SalesService(database_session).get_summary(current_user.farm_id)
    return SalesSummaryResponse(**summary)
