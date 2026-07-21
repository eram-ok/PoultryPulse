from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.feed.models import FeedPurchase
from app.modules.finance.constants import CashFlowDirection
from app.modules.finance.models import (
    CashLedgerEntry,
    Expense,
    ExpenseCategory,
    SupplierBill,
    SupplierBillPayment,
)
from app.modules.sales.constants import PaymentStatus, SaleStatus
from app.modules.sales.models import Sale, SalePayment
from app.modules.suppliers.models import Supplier


class FinanceRepository:
    def __init__(self, database_session: Session) -> None:
        self.db = database_session

    def category(self, farm_id: UUID, category_id: UUID):
        return self.db.scalar(
            select(ExpenseCategory).where(
                ExpenseCategory.farm_id == farm_id,
                ExpenseCategory.id == category_id,
            )
        )

    def category_by_code(self, farm_id: UUID, code: str):
        return self.db.scalar(
            select(ExpenseCategory).where(
                ExpenseCategory.farm_id == farm_id,
                ExpenseCategory.category_code == code,
            )
        )

    def categories(
        self,
        farm_id: UUID,
        offset: int,
        limit: int,
        active_only: bool | None,
        search: str | None,
    ):
        conditions = [ExpenseCategory.farm_id == farm_id]
        if active_only is not None:
            conditions.append(ExpenseCategory.is_active == active_only)
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(
                or_(
                    ExpenseCategory.category_code.ilike(pattern),
                    ExpenseCategory.name.ilike(pattern),
                )
            )
        items = list(
            self.db.scalars(
                select(ExpenseCategory)
                .where(*conditions)
                .order_by(ExpenseCategory.name)
                .offset(offset)
                .limit(limit)
            ).all()
        )
        total = int(
            self.db.scalar(select(func.count(ExpenseCategory.id)).where(*conditions))
            or 0
        )
        return items, total

    def supplier(self, farm_id: UUID, supplier_id: UUID):
        return self.db.scalar(
            select(Supplier).where(
                Supplier.farm_id == farm_id, Supplier.id == supplier_id
            )
        )

    def feed_purchase(self, farm_id: UUID, purchase_id: UUID):
        return self.db.scalar(
            select(FeedPurchase).where(
                FeedPurchase.farm_id == farm_id, FeedPurchase.id == purchase_id
            )
        )

    def expense(self, farm_id: UUID, expense_id: UUID, for_update: bool = False):
        statement = (
            select(Expense)
            .options(selectinload(Expense.category), selectinload(Expense.supplier))
            .where(Expense.farm_id == farm_id, Expense.id == expense_id)
        )
        if for_update:
            statement = statement.with_for_update()
        return self.db.scalar(statement)

    def expenses(
        self,
        farm_id: UUID,
        offset: int,
        limit: int,
        date_from: date | None,
        date_to: date | None,
        category_id: UUID | None,
        expense_status: str | None,
        search: str | None,
    ):
        conditions = [Expense.farm_id == farm_id]
        if date_from:
            conditions.append(Expense.expense_date >= date_from)
        if date_to:
            conditions.append(Expense.expense_date <= date_to)
        if category_id:
            conditions.append(Expense.category_id == category_id)
        if expense_status:
            conditions.append(Expense.status == expense_status)
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(
                or_(
                    Expense.expense_number.ilike(pattern),
                    Expense.description.ilike(pattern),
                )
            )
        statement = (
            select(Expense)
            .options(selectinload(Expense.category), selectinload(Expense.supplier))
            .where(*conditions)
            .order_by(Expense.expense_date.desc(), Expense.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all()), int(
            self.db.scalar(select(func.count(Expense.id)).where(*conditions)) or 0
        )

    def bill(self, farm_id: UUID, bill_id: UUID, for_update: bool = False):
        statement = (
            select(SupplierBill)
            .options(
                selectinload(SupplierBill.supplier),
                selectinload(SupplierBill.feed_purchase),
                selectinload(SupplierBill.payments),
            )
            .where(SupplierBill.farm_id == farm_id, SupplierBill.id == bill_id)
        )
        if for_update:
            statement = statement.with_for_update()
        return self.db.scalar(statement)

    def bills(
        self,
        farm_id: UUID,
        offset: int,
        limit: int,
        date_from: date | None,
        date_to: date | None,
        supplier_id: UUID | None,
        bill_status: str | None,
        overdue_only: bool,
        search: str | None,
    ):
        conditions = [SupplierBill.farm_id == farm_id]
        if date_from:
            conditions.append(SupplierBill.bill_date >= date_from)
        if date_to:
            conditions.append(SupplierBill.bill_date <= date_to)
        if supplier_id:
            conditions.append(SupplierBill.supplier_id == supplier_id)
        if bill_status:
            conditions.append(SupplierBill.status == bill_status)
        if overdue_only:
            conditions.extend(
                [
                    SupplierBill.due_date < date.today(),
                    SupplierBill.balance_due > 0,
                    SupplierBill.status != "VOIDED",
                ]
            )
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(
                or_(
                    SupplierBill.bill_number.ilike(pattern),
                    SupplierBill.description.ilike(pattern),
                )
            )
        statement = (
            select(SupplierBill)
            .options(
                selectinload(SupplierBill.supplier),
                selectinload(SupplierBill.feed_purchase),
                selectinload(SupplierBill.payments),
            )
            .where(*conditions)
            .order_by(SupplierBill.bill_date.desc(), SupplierBill.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all()), int(
            self.db.scalar(select(func.count(SupplierBill.id)).where(*conditions)) or 0
        )

    def payment(self, farm_id: UUID, payment_id: UUID, for_update: bool = False):
        statement = (
            select(SupplierBillPayment)
            .options(
                selectinload(SupplierBillPayment.supplier),
                selectinload(SupplierBillPayment.supplier_bill).selectinload(
                    SupplierBill.supplier
                ),
            )
            .where(
                SupplierBillPayment.farm_id == farm_id,
                SupplierBillPayment.id == payment_id,
            )
        )
        if for_update:
            statement = statement.with_for_update()
        return self.db.scalar(statement)

    def payments(
        self,
        farm_id: UUID,
        offset: int,
        limit: int,
        date_from: date | None,
        date_to: date | None,
        supplier_id: UUID | None,
        bill_id: UUID | None,
        payment_status: str | None,
    ):
        conditions = [SupplierBillPayment.farm_id == farm_id]
        if date_from:
            conditions.append(SupplierBillPayment.payment_date >= date_from)
        if date_to:
            conditions.append(SupplierBillPayment.payment_date <= date_to)
        if supplier_id:
            conditions.append(SupplierBillPayment.supplier_id == supplier_id)
        if bill_id:
            conditions.append(SupplierBillPayment.supplier_bill_id == bill_id)
        if payment_status:
            conditions.append(SupplierBillPayment.status == payment_status)
        statement = (
            select(SupplierBillPayment)
            .options(
                selectinload(SupplierBillPayment.supplier),
                selectinload(SupplierBillPayment.supplier_bill),
            )
            .where(*conditions)
            .order_by(
                SupplierBillPayment.payment_date.desc(),
                SupplierBillPayment.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all()), int(
            self.db.scalar(
                select(func.count(SupplierBillPayment.id)).where(*conditions)
            )
            or 0
        )

    def cash_balance(self, farm_id: UUID) -> Decimal:
        signed = case(
            (
                CashLedgerEntry.direction == CashFlowDirection.INFLOW.value,
                CashLedgerEntry.amount,
            ),
            else_=-CashLedgerEntry.amount,
        )
        return Decimal(
            self.db.scalar(
                select(func.coalesce(func.sum(signed), 0)).where(
                    CashLedgerEntry.farm_id == farm_id
                )
            )
            or 0
        )

    def cash_entries(
        self,
        farm_id: UUID,
        offset: int,
        limit: int,
        date_from: date | None,
        date_to: date | None,
        entry_type: str | None,
        direction: str | None,
    ):
        conditions = [CashLedgerEntry.farm_id == farm_id]
        if date_from:
            conditions.append(CashLedgerEntry.entry_date >= date_from)
        if date_to:
            conditions.append(CashLedgerEntry.entry_date <= date_to)
        if entry_type:
            conditions.append(CashLedgerEntry.entry_type == entry_type)
        if direction:
            conditions.append(CashLedgerEntry.direction == direction)
        statement = (
            select(CashLedgerEntry)
            .where(*conditions)
            .order_by(
                CashLedgerEntry.entry_date.desc(), CashLedgerEntry.created_at.desc()
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all()), int(
            self.db.scalar(select(func.count(CashLedgerEntry.id)).where(*conditions))
            or 0
        )

    def unsynced_receipts(self, farm_id: UUID):
        return list(
            self.db.scalars(
                select(SalePayment).where(
                    SalePayment.farm_id == farm_id,
                    SalePayment.status == PaymentStatus.POSTED.value,
                    ~select(CashLedgerEntry.id)
                    .where(
                        CashLedgerEntry.farm_id == farm_id,
                        CashLedgerEntry.sale_payment_id == SalePayment.id,
                        CashLedgerEntry.entry_type == "SALES_RECEIPT",
                    )
                    .exists(),
                )
            ).all()
        )

    def reversed_receipts(self, farm_id: UUID):
        return list(
            self.db.scalars(
                select(SalePayment).where(
                    SalePayment.farm_id == farm_id,
                    SalePayment.status == PaymentStatus.REVERSED.value,
                    select(CashLedgerEntry.id)
                    .where(
                        CashLedgerEntry.farm_id == farm_id,
                        CashLedgerEntry.sale_payment_id == SalePayment.id,
                        CashLedgerEntry.entry_type == "SALES_RECEIPT",
                    )
                    .exists(),
                    ~select(CashLedgerEntry.id)
                    .where(
                        CashLedgerEntry.farm_id == farm_id,
                        CashLedgerEntry.source_type == "SALE_PAYMENT_REVERSAL",
                        CashLedgerEntry.source_id == SalePayment.id,
                    )
                    .exists(),
                )
            ).all()
        )

    def supplier_statement(
        self,
        farm_id: UUID,
        supplier_id: UUID,
        date_from: date | None,
        date_to: date | None,
    ):
        bill_conditions = [
            SupplierBill.farm_id == farm_id,
            SupplierBill.supplier_id == supplier_id,
        ]
        payment_conditions = [
            SupplierBillPayment.farm_id == farm_id,
            SupplierBillPayment.supplier_id == supplier_id,
        ]
        if date_from:
            bill_conditions.append(SupplierBill.bill_date >= date_from)
            payment_conditions.append(SupplierBillPayment.payment_date >= date_from)
        if date_to:
            bill_conditions.append(SupplierBill.bill_date <= date_to)
            payment_conditions.append(SupplierBillPayment.payment_date <= date_to)
        bills = list(
            self.db.scalars(
                select(SupplierBill)
                .options(selectinload(SupplierBill.supplier))
                .where(*bill_conditions)
                .order_by(SupplierBill.bill_date)
            ).all()
        )
        payments = list(
            self.db.scalars(
                select(SupplierBillPayment)
                .options(
                    selectinload(SupplierBillPayment.supplier),
                    selectinload(SupplierBillPayment.supplier_bill),
                )
                .where(*payment_conditions)
                .order_by(SupplierBillPayment.payment_date)
            ).all()
        )
        return bills, payments

    def cash_flow_rows(
        self, farm_id: UUID, date_from: date | None, date_to: date | None
    ):
        conditions = [CashLedgerEntry.farm_id == farm_id]
        if date_from:
            conditions.append(CashLedgerEntry.entry_date >= date_from)
        if date_to:
            conditions.append(CashLedgerEntry.entry_date <= date_to)
        return self.db.execute(
            select(
                CashLedgerEntry.entry_type,
                CashLedgerEntry.direction,
                func.sum(CashLedgerEntry.amount),
            )
            .where(*conditions)
            .group_by(CashLedgerEntry.entry_type, CashLedgerEntry.direction)
        ).all()

    def profitability(
        self, farm_id: UUID, date_from: date | None, date_to: date | None
    ):
        sale_conditions = [
            Sale.farm_id == farm_id,
            Sale.status != SaleStatus.CANCELLED.value,
        ]
        expense_conditions = [Expense.farm_id == farm_id, Expense.status == "POSTED"]
        bill_conditions = [
            SupplierBill.farm_id == farm_id,
            SupplierBill.status != "VOIDED",
        ]
        if date_from:
            sale_conditions.append(Sale.sale_date >= date_from)
            expense_conditions.append(Expense.expense_date >= date_from)
            bill_conditions.append(SupplierBill.bill_date >= date_from)
        if date_to:
            sale_conditions.append(Sale.sale_date <= date_to)
            expense_conditions.append(Expense.expense_date <= date_to)
            bill_conditions.append(SupplierBill.bill_date <= date_to)
        revenue = Decimal(
            self.db.scalar(
                select(func.coalesce(func.sum(Sale.total_amount), 0)).where(
                    *sale_conditions
                )
            )
            or 0
        )
        expenses = Decimal(
            self.db.scalar(
                select(func.coalesce(func.sum(Expense.amount), 0)).where(
                    *expense_conditions
                )
            )
            or 0
        )
        bills = Decimal(
            self.db.scalar(
                select(func.coalesce(func.sum(SupplierBill.total_amount), 0)).where(
                    *bill_conditions
                )
            )
            or 0
        )
        rows = self.db.execute(
            select(ExpenseCategory.name, func.sum(Expense.amount))
            .join(Expense, Expense.category_id == ExpenseCategory.id)
            .where(*expense_conditions)
            .group_by(ExpenseCategory.name)
        ).all()
        return (
            revenue,
            expenses,
            bills,
            {name: Decimal(amount) for name, amount in rows},
        )
