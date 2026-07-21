from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_database_session
from app.modules.auth.dependencies import require_permissions
from app.modules.finance.constants import (
    CashFlowDirection,
    CashLedgerEntryType,
    FinanceDocumentStatus,
    FinancePaymentStatus,
    SupplierBillStatus,
)
from app.modules.finance.models import (
    CashLedgerEntry,
    Expense,
    SupplierBill,
    SupplierBillPayment,
)
from app.modules.finance.schemas import (
    CashAdjustmentCreate,
    CashFlowReportResponse,
    CashLedgerEntryResponse,
    CashLedgerListResponse,
    ExpenseCategoryCreate,
    ExpenseCategoryListResponse,
    ExpenseCategoryResponse,
    ExpenseCategoryUpdate,
    ExpenseCreate,
    ExpenseListResponse,
    ExpenseResponse,
    FinanceSummaryResponse,
    ProfitabilityReportResponse,
    SalesReceiptSyncResponse,
    SupplierBillCreate,
    SupplierBillListResponse,
    SupplierBillResponse,
    SupplierPaymentCreate,
    SupplierPaymentListResponse,
    SupplierPaymentResponse,
    SupplierStatementResponse,
    VoidRequest,
)
from app.modules.finance.service import FinanceService
from app.modules.users.models import User

router = APIRouter(prefix="/finance", tags=["Expenses, Supplier Bills and Finance"])
DatabaseSession = Annotated[Session, Depends(get_database_session)]


def expense_response(item: Expense) -> ExpenseResponse:
    return ExpenseResponse(
        id=item.id,
        farm_id=item.farm_id,
        category_id=item.category_id,
        category_code=item.category.category_code,
        category_name=item.category.name,
        supplier_id=item.supplier_id,
        supplier_name=item.supplier.name if item.supplier else None,
        expense_number=item.expense_number,
        expense_date=item.expense_date,
        description=item.description,
        amount=item.amount,
        payment_method=item.payment_method,
        reference_number=item.reference_number,
        status=item.status,
        notes=item.notes,
        recorded_by=item.recorded_by,
        voided_by=item.voided_by,
        voided_at=item.voided_at,
        void_reason=item.void_reason,
        is_posted=item.is_posted,
        is_voided=item.is_voided,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def bill_response(item: SupplierBill) -> SupplierBillResponse:
    return SupplierBillResponse(
        id=item.id,
        farm_id=item.farm_id,
        supplier_id=item.supplier_id,
        supplier_code=item.supplier.supplier_code,
        supplier_name=item.supplier.name,
        feed_purchase_id=item.feed_purchase_id,
        bill_number=item.bill_number,
        supplier_invoice_number=item.supplier_invoice_number,
        bill_date=item.bill_date,
        due_date=item.due_date,
        description=item.description,
        subtotal=item.subtotal,
        tax_amount=item.tax_amount,
        total_amount=item.total_amount,
        amount_paid=item.amount_paid,
        balance_due=item.balance_due,
        status=item.status,
        notes=item.notes,
        recorded_by=item.recorded_by,
        voided_by=item.voided_by,
        voided_at=item.voided_at,
        void_reason=item.void_reason,
        is_paid=item.is_paid,
        is_voided=item.is_voided,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def payment_response(item: SupplierBillPayment) -> SupplierPaymentResponse:
    return SupplierPaymentResponse(
        id=item.id,
        farm_id=item.farm_id,
        supplier_id=item.supplier_id,
        supplier_code=item.supplier.supplier_code,
        supplier_name=item.supplier.name,
        supplier_bill_id=item.supplier_bill_id,
        bill_number=item.supplier_bill.bill_number,
        payment_number=item.payment_number,
        payment_date=item.payment_date,
        amount=item.amount,
        method=item.method,
        reference_number=item.reference_number,
        status=item.status,
        notes=item.notes,
        paid_by=item.paid_by,
        reversed_by=item.reversed_by,
        reversed_at=item.reversed_at,
        reversal_reason=item.reversal_reason,
        is_reversed=item.is_reversed,
        created_at=item.created_at,
    )


def cash_response(item: CashLedgerEntry) -> CashLedgerEntryResponse:
    return CashLedgerEntryResponse(
        id=item.id,
        farm_id=item.farm_id,
        entry_date=item.entry_date,
        entry_type=item.entry_type,
        direction=item.direction,
        amount=item.amount,
        signed_amount=item.signed_amount,
        balance_after=item.balance_after,
        description=item.description,
        expense_id=item.expense_id,
        supplier_bill_payment_id=item.supplier_bill_payment_id,
        sale_payment_id=item.sale_payment_id,
        source_type=item.source_type,
        source_id=item.source_id,
        created_by=item.created_by,
        created_at=item.created_at,
    )


@router.post(
    "/expense-categories", response_model=ExpenseCategoryResponse, status_code=201
)
def create_category(
    payload: ExpenseCategoryCreate,
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("expense_categories.manage"))],
):
    return ExpenseCategoryResponse.model_validate(
        FinanceService(db).create_category(user.farm_id, payload)
    )


@router.get("/expense-categories", response_model=ExpenseCategoryListResponse)
def list_categories(
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("finance.view"))],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    active_only: bool | None = None,
    search: str | None = None,
):
    items, total = FinanceService(db).repo.categories(
        user.farm_id, offset, limit, active_only, search
    )
    return ExpenseCategoryListResponse(
        items=[ExpenseCategoryResponse.model_validate(i) for i in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.patch(
    "/expense-categories/{category_id}", response_model=ExpenseCategoryResponse
)
def update_category(
    category_id: UUID,
    payload: ExpenseCategoryUpdate,
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("expense_categories.manage"))],
):
    return ExpenseCategoryResponse.model_validate(
        FinanceService(db).update_category(user.farm_id, category_id, payload)
    )


@router.post("/expenses", response_model=ExpenseResponse, status_code=201)
def create_expense(
    payload: ExpenseCreate,
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("expenses.record"))],
):
    return expense_response(
        FinanceService(db).create_expense(user.farm_id, user.id, payload)
    )


@router.get("/expenses", response_model=ExpenseListResponse)
def list_expenses(
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("finance.view"))],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: UUID | None = None,
    expense_status: Annotated[
        FinanceDocumentStatus | None, Query(alias="status")
    ] = None,
    search: str | None = None,
):
    service = FinanceService(db)
    service.validate_dates(date_from, date_to)
    items, total = service.repo.expenses(
        user.farm_id,
        offset,
        limit,
        date_from,
        date_to,
        category_id,
        expense_status.value if expense_status else None,
        search,
    )
    return ExpenseListResponse(
        items=[expense_response(i) for i in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/expenses/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: UUID,
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("finance.view"))],
):
    return expense_response(FinanceService(db).expense(user.farm_id, expense_id))


@router.post("/expenses/{expense_id}/void", response_model=ExpenseResponse)
def void_expense(
    expense_id: UUID,
    payload: VoidRequest,
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("expenses.void"))],
):
    return expense_response(
        FinanceService(db).void_expense(
            user.farm_id, expense_id, user.id, payload.reason
        )
    )


@router.post("/supplier-bills", response_model=SupplierBillResponse, status_code=201)
def create_bill(
    payload: SupplierBillCreate,
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("supplier_bills.manage"))],
):
    return bill_response(FinanceService(db).create_bill(user.farm_id, user.id, payload))


@router.get("/supplier-bills", response_model=SupplierBillListResponse)
def list_bills(
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("finance.view"))],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    date_from: date | None = None,
    date_to: date | None = None,
    supplier_id: UUID | None = None,
    bill_status: Annotated[SupplierBillStatus | None, Query(alias="status")] = None,
    overdue_only: bool = False,
    search: str | None = None,
):
    service = FinanceService(db)
    service.validate_dates(date_from, date_to)
    items, total = service.repo.bills(
        user.farm_id,
        offset,
        limit,
        date_from,
        date_to,
        supplier_id,
        bill_status.value if bill_status else None,
        overdue_only,
        search,
    )
    return SupplierBillListResponse(
        items=[bill_response(i) for i in items], total=total, offset=offset, limit=limit
    )


@router.get("/supplier-bills/{bill_id}", response_model=SupplierBillResponse)
def get_bill(
    bill_id: UUID,
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("finance.view"))],
):
    return bill_response(FinanceService(db).bill(user.farm_id, bill_id))


@router.post("/supplier-bills/{bill_id}/void", response_model=SupplierBillResponse)
def void_bill(
    bill_id: UUID,
    payload: VoidRequest,
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("supplier_bills.manage"))],
):
    return bill_response(
        FinanceService(db).void_bill(user.farm_id, bill_id, user.id, payload.reason)
    )


@router.post(
    "/supplier-payments", response_model=SupplierPaymentResponse, status_code=201
)
def create_payment(
    payload: SupplierPaymentCreate,
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("supplier_payments.record"))],
):
    return payment_response(
        FinanceService(db).record_payment(user.farm_id, user.id, payload)
    )


@router.get("/supplier-payments", response_model=SupplierPaymentListResponse)
def list_payments(
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("finance.view"))],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    date_from: date | None = None,
    date_to: date | None = None,
    supplier_id: UUID | None = None,
    bill_id: UUID | None = None,
    payment_status: Annotated[
        FinancePaymentStatus | None, Query(alias="status")
    ] = None,
):
    service = FinanceService(db)
    service.validate_dates(date_from, date_to)
    items, total = service.repo.payments(
        user.farm_id,
        offset,
        limit,
        date_from,
        date_to,
        supplier_id,
        bill_id,
        payment_status.value if payment_status else None,
    )
    return SupplierPaymentListResponse(
        items=[payment_response(i) for i in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/supplier-payments/{payment_id}", response_model=SupplierPaymentResponse)
def get_payment(
    payment_id: UUID,
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("finance.view"))],
):
    return payment_response(FinanceService(db).payment(user.farm_id, payment_id))


@router.post(
    "/supplier-payments/{payment_id}/reverse", response_model=SupplierPaymentResponse
)
def reverse_payment(
    payment_id: UUID,
    payload: VoidRequest,
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("supplier_payments.reverse"))],
):
    return payment_response(
        FinanceService(db).reverse_payment(
            user.farm_id, payment_id, user.id, payload.reason
        )
    )


@router.post(
    "/cash-ledger/adjustments", response_model=CashLedgerEntryResponse, status_code=201
)
def cash_adjustment(
    payload: CashAdjustmentCreate,
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("cash_ledger.adjust"))],
):
    return cash_response(
        FinanceService(db).cash_adjustment(user.farm_id, user.id, payload)
    )


@router.get("/cash-ledger", response_model=CashLedgerListResponse)
def cash_ledger(
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("finance.view"))],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    date_from: date | None = None,
    date_to: date | None = None,
    entry_type: CashLedgerEntryType | None = None,
    direction: CashFlowDirection | None = None,
):
    service = FinanceService(db)
    service.validate_dates(date_from, date_to)
    items, total = service.repo.cash_entries(
        user.farm_id,
        offset,
        limit,
        date_from,
        date_to,
        entry_type.value if entry_type else None,
        direction.value if direction else None,
    )
    return CashLedgerListResponse(
        items=[cash_response(i) for i in items],
        total=total,
        offset=offset,
        limit=limit,
        current_balance=service.repo.cash_balance(user.farm_id),
    )


@router.post("/sync/sales-receipts", response_model=SalesReceiptSyncResponse)
def sync_receipts(
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("finance.view"))],
):
    created, reversals, balance = FinanceService(db).sync_receipts(
        user.farm_id, user.id
    )
    return SalesReceiptSyncResponse(
        receipts_created=created, reversals_created=reversals, current_balance=balance
    )


@router.get(
    "/suppliers/{supplier_id}/statement", response_model=SupplierStatementResponse
)
def supplier_statement(
    supplier_id: UUID,
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("finance.reports"))],
    date_from: date | None = None,
    date_to: date | None = None,
):
    supplier, bills, payments, total_billed, total_paid, outstanding = FinanceService(
        db
    ).statement(user.farm_id, supplier_id, date_from, date_to)
    return SupplierStatementResponse(
        supplier_id=supplier.id,
        supplier_code=supplier.supplier_code,
        supplier_name=supplier.name,
        date_from=date_from,
        date_to=date_to,
        total_billed=total_billed,
        total_paid=total_paid,
        outstanding_balance=outstanding,
        bills=[bill_response(i) for i in bills],
        payments=[payment_response(i) for i in payments],
    )


@router.get("/reports/cash-flow", response_model=CashFlowReportResponse)
def cash_flow(
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("finance.reports"))],
    date_from: date | None = None,
    date_to: date | None = None,
):
    return CashFlowReportResponse(
        **FinanceService(db).cash_flow(user.farm_id, date_from, date_to)
    )


@router.get("/reports/profitability", response_model=ProfitabilityReportResponse)
def profitability(
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("finance.reports"))],
    date_from: date | None = None,
    date_to: date | None = None,
):
    return ProfitabilityReportResponse(
        **FinanceService(db).profitability(user.farm_id, date_from, date_to)
    )


@router.get("/summary", response_model=FinanceSummaryResponse)
def summary(
    db: DatabaseSession,
    user: Annotated[User, Depends(require_permissions("finance.view"))],
):
    return FinanceSummaryResponse(**FinanceService(db).summary(user.farm_id, user.id))
