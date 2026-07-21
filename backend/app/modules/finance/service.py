from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BusinessRuleError,
    ResourceConflictError,
    ResourceNotFoundError,
)
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
    ExpenseCategory,
    SupplierBill,
    SupplierBillPayment,
    normalize_finance_money,
)
from app.modules.finance.repository import FinanceRepository
from app.modules.finance.schemas import (
    CashAdjustmentCreate,
    ExpenseCategoryCreate,
    ExpenseCategoryUpdate,
    ExpenseCreate,
    SupplierBillCreate,
    SupplierPaymentCreate,
)


class FinanceService:
    def __init__(self, database_session: Session) -> None:
        self.db = database_session
        self.repo = FinanceRepository(database_session)

    @staticmethod
    def number(prefix: str) -> str:
        return f"{prefix}-{date.today():%Y%m%d}-{uuid4().hex[:8].upper()}"

    @staticmethod
    def validate_dates(date_from: date | None, date_to: date | None) -> None:
        if date_from and date_to and date_from > date_to:
            raise BusinessRuleError(
                "The start date cannot be after the end date.",
                error_code="invalid_finance_date_range",
            )

    def commit(self, message: str, code: str) -> None:
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ResourceConflictError(message, error_code=code) from exc

    def category(self, farm_id: UUID, category_id: UUID):
        item = self.repo.category(farm_id, category_id)
        if item is None:
            raise ResourceNotFoundError(
                "The selected expense category does not exist.",
                error_code="expense_category_not_found",
            )
        return item

    def supplier(self, farm_id: UUID, supplier_id: UUID):
        item = self.repo.supplier(farm_id, supplier_id)
        if item is None:
            raise ResourceNotFoundError(
                "The selected supplier does not exist.", error_code="supplier_not_found"
            )
        return item

    def expense(self, farm_id: UUID, expense_id: UUID, for_update: bool = False):
        item = self.repo.expense(farm_id, expense_id, for_update)
        if item is None:
            raise ResourceNotFoundError(
                "The selected expense does not exist.", error_code="expense_not_found"
            )
        return item

    def bill(self, farm_id: UUID, bill_id: UUID, for_update: bool = False):
        item = self.repo.bill(farm_id, bill_id, for_update)
        if item is None:
            raise ResourceNotFoundError(
                "The selected supplier bill does not exist.",
                error_code="supplier_bill_not_found",
            )
        return item

    def payment(self, farm_id: UUID, payment_id: UUID, for_update: bool = False):
        item = self.repo.payment(farm_id, payment_id, for_update)
        if item is None:
            raise ResourceNotFoundError(
                "The selected supplier payment does not exist.",
                error_code="supplier_payment_not_found",
            )
        return item

    def cash_entry(
        self,
        farm_id: UUID,
        user_id: UUID,
        entry_date: date,
        entry_type: str,
        direction: str,
        amount: Decimal,
        description: str,
        **links,
    ):
        amount = normalize_finance_money(amount)
        current = normalize_finance_money(self.repo.cash_balance(farm_id))
        balance = normalize_finance_money(
            current + amount if direction == "INFLOW" else current - amount
        )
        entry = CashLedgerEntry(
            farm_id=farm_id,
            entry_date=entry_date,
            entry_type=entry_type,
            direction=direction,
            amount=amount,
            balance_after=balance,
            description=description,
            created_by=user_id,
            **links,
        )
        self.db.add(entry)
        return entry

    def create_category(self, farm_id: UUID, payload: ExpenseCategoryCreate):
        if self.repo.category_by_code(farm_id, payload.category_code):
            raise ResourceConflictError(
                "An expense category with this code already exists.",
                error_code="expense_category_code_already_exists",
            )
        item = ExpenseCategory(
            farm_id=farm_id,
            category_code=payload.category_code,
            name=payload.name,
            kind=payload.kind.value,
            description=payload.description,
            is_active=True,
        )
        self.db.add(item)
        self.commit(
            "The expense category could not be created.",
            "expense_category_creation_conflict",
        )
        return self.category(farm_id, item.id)

    def update_category(
        self, farm_id: UUID, category_id: UUID, payload: ExpenseCategoryUpdate
    ):
        item = self.category(farm_id, category_id)
        changes = payload.model_dump(exclude_unset=True)
        if payload.category_code:
            existing = self.repo.category_by_code(farm_id, payload.category_code)
            if existing and existing.id != item.id:
                raise ResourceConflictError(
                    "Another category already uses this code.",
                    error_code="expense_category_code_already_exists",
                )
        if payload.kind is not None:
            changes["kind"] = payload.kind.value
        for key, value in changes.items():
            setattr(item, key, value)
        self.commit(
            "The expense category could not be updated.",
            "expense_category_update_conflict",
        )
        return self.category(farm_id, category_id)

    def create_expense(self, farm_id: UUID, user_id: UUID, payload: ExpenseCreate):
        category = self.category(farm_id, payload.category_id)
        if not category.is_active:
            raise BusinessRuleError(
                "The selected expense category is inactive.",
                error_code="expense_category_inactive",
            )
        if payload.supplier_id:
            self.supplier(farm_id, payload.supplier_id)
        item = Expense(
            farm_id=farm_id,
            category_id=category.id,
            supplier_id=payload.supplier_id,
            expense_number=self.number("EXP"),
            expense_date=payload.expense_date,
            description=payload.description,
            amount=normalize_finance_money(payload.amount),
            payment_method=payload.payment_method.value,
            reference_number=payload.reference_number,
            status=FinanceDocumentStatus.POSTED.value,
            notes=payload.notes,
            recorded_by=user_id,
        )
        self.db.add(item)
        self.db.flush()
        self.cash_entry(
            farm_id,
            user_id,
            item.expense_date,
            CashLedgerEntryType.EXPENSE_PAYMENT.value,
            CashFlowDirection.OUTFLOW.value,
            item.amount,
            f"Expense {item.expense_number}: {item.description}",
            expense_id=item.id,
            source_type="EXPENSE",
            source_id=item.id,
        )
        self.commit("The expense could not be recorded.", "expense_creation_conflict")
        self.db.expire_all()
        return self.expense(farm_id, item.id)

    def void_expense(self, farm_id: UUID, expense_id: UUID, user_id: UUID, reason: str):
        item = self.expense(farm_id, expense_id, True)
        if item.status == FinanceDocumentStatus.VOIDED.value:
            raise ResourceConflictError(
                "This expense is already voided.", error_code="expense_already_voided"
            )
        item.status = FinanceDocumentStatus.VOIDED.value
        item.voided_by = user_id
        item.voided_at = datetime.now(UTC)
        item.void_reason = reason
        self.cash_entry(
            farm_id,
            user_id,
            date.today(),
            CashLedgerEntryType.REVERSAL.value,
            CashFlowDirection.INFLOW.value,
            item.amount,
            f"Reversal of expense {item.expense_number}",
            expense_id=item.id,
            source_type="EXPENSE_VOID",
            source_id=item.id,
        )
        self.commit("The expense could not be voided.", "expense_void_conflict")
        self.db.expire_all()
        return self.expense(farm_id, expense_id)

    def create_bill(self, farm_id: UUID, user_id: UUID, payload: SupplierBillCreate):
        supplier = self.supplier(farm_id, payload.supplier_id)
        if not supplier.is_active:
            raise BusinessRuleError(
                "The selected supplier is inactive.", error_code="supplier_inactive"
            )
        subtotal = payload.subtotal
        source_type = None
        source_id = None
        if payload.feed_purchase_id:
            purchase = self.repo.feed_purchase(farm_id, payload.feed_purchase_id)
            if purchase is None:
                raise ResourceNotFoundError(
                    "The linked feed purchase does not exist.",
                    error_code="feed_purchase_not_found",
                )
            if purchase.supplier_id and purchase.supplier_id != supplier.id:
                raise BusinessRuleError(
                    "The feed purchase belongs to another supplier.",
                    error_code="feed_purchase_supplier_mismatch",
                )
            calculated = normalize_finance_money(
                purchase.quantity_kg * purchase.unit_cost
            )
            if subtotal is not None and normalize_finance_money(subtotal) != calculated:
                raise BusinessRuleError(
                    "Subtotal must match the linked feed purchase value.",
                    error_code="feed_purchase_subtotal_mismatch",
                )
            subtotal = calculated
            source_type = "FEED_PURCHASE"
            source_id = purchase.id
        assert subtotal is not None
        subtotal = normalize_finance_money(subtotal)
        tax = normalize_finance_money(payload.tax_amount)
        total = normalize_finance_money(subtotal + tax)
        item = SupplierBill(
            farm_id=farm_id,
            supplier_id=supplier.id,
            feed_purchase_id=payload.feed_purchase_id,
            bill_number=self.number("BILL"),
            supplier_invoice_number=payload.supplier_invoice_number,
            bill_date=payload.bill_date,
            due_date=payload.due_date,
            description=payload.description,
            subtotal=subtotal,
            tax_amount=tax,
            total_amount=total,
            amount_paid=Decimal("0.00"),
            balance_due=total,
            status=SupplierBillStatus.UNPAID.value,
            source_type=source_type,
            source_id=source_id,
            notes=payload.notes,
            recorded_by=user_id,
        )
        self.db.add(item)
        self.commit(
            "The supplier bill could not be created.", "supplier_bill_creation_conflict"
        )
        self.db.expire_all()
        return self.bill(farm_id, item.id)

    def void_bill(self, farm_id: UUID, bill_id: UUID, user_id: UUID, reason: str):
        item = self.bill(farm_id, bill_id, True)
        if item.status == SupplierBillStatus.VOIDED.value:
            raise ResourceConflictError(
                "This supplier bill is already voided.",
                error_code="supplier_bill_already_voided",
            )
        if item.amount_paid > Decimal("0.00"):
            raise BusinessRuleError(
                "A supplier bill with posted payments cannot be voided.",
                error_code="paid_supplier_bill_cannot_void",
            )
        item.status = SupplierBillStatus.VOIDED.value
        item.voided_by = user_id
        item.voided_at = datetime.now(UTC)
        item.void_reason = reason
        self.db.commit()
        self.db.expire_all()
        return self.bill(farm_id, bill_id)

    def record_payment(
        self, farm_id: UUID, user_id: UUID, payload: SupplierPaymentCreate
    ):
        bill = self.bill(farm_id, payload.supplier_bill_id, True)
        if bill.status == SupplierBillStatus.VOIDED.value:
            raise BusinessRuleError(
                "Payments cannot be posted to a voided bill.",
                error_code="supplier_bill_not_payable",
            )
        amount = normalize_finance_money(payload.amount)
        if amount > bill.balance_due:
            raise BusinessRuleError(
                "Payment cannot exceed the supplier bill balance.",
                error_code="supplier_payment_exceeds_balance",
            )
        item = SupplierBillPayment(
            farm_id=farm_id,
            supplier_id=bill.supplier_id,
            supplier_bill_id=bill.id,
            payment_number=self.number("SPAY"),
            payment_date=payload.payment_date,
            amount=amount,
            method=payload.method.value,
            reference_number=payload.reference_number,
            status=FinancePaymentStatus.POSTED.value,
            notes=payload.notes,
            paid_by=user_id,
        )
        self.db.add(item)
        self.db.flush()
        bill.amount_paid = normalize_finance_money(bill.amount_paid + amount)
        bill.balance_due = normalize_finance_money(bill.total_amount - bill.amount_paid)
        bill.status = (
            SupplierBillStatus.PAID.value
            if bill.balance_due == Decimal("0.00")
            else SupplierBillStatus.PARTIALLY_PAID.value
        )
        self.cash_entry(
            farm_id,
            user_id,
            item.payment_date,
            CashLedgerEntryType.SUPPLIER_BILL_PAYMENT.value,
            CashFlowDirection.OUTFLOW.value,
            amount,
            f"Supplier payment {item.payment_number}",
            supplier_bill_payment_id=item.id,
            source_type="SUPPLIER_PAYMENT",
            source_id=item.id,
        )
        self.commit(
            "The supplier payment could not be recorded.",
            "supplier_payment_creation_conflict",
        )
        self.db.expire_all()
        return self.payment(farm_id, item.id)

    def reverse_payment(
        self, farm_id: UUID, payment_id: UUID, user_id: UUID, reason: str
    ):
        item = self.payment(farm_id, payment_id, True)
        if item.status == FinancePaymentStatus.REVERSED.value:
            raise ResourceConflictError(
                "This supplier payment is already reversed.",
                error_code="supplier_payment_already_reversed",
            )
        bill = self.bill(farm_id, item.supplier_bill_id, True)
        item.status = FinancePaymentStatus.REVERSED.value
        item.reversed_by = user_id
        item.reversed_at = datetime.now(UTC)
        item.reversal_reason = reason
        bill.amount_paid = normalize_finance_money(bill.amount_paid - item.amount)
        bill.balance_due = normalize_finance_money(bill.total_amount - bill.amount_paid)
        bill.status = (
            SupplierBillStatus.UNPAID.value
            if bill.amount_paid == Decimal("0.00")
            else SupplierBillStatus.PARTIALLY_PAID.value
        )
        self.cash_entry(
            farm_id,
            user_id,
            date.today(),
            CashLedgerEntryType.REVERSAL.value,
            CashFlowDirection.INFLOW.value,
            item.amount,
            f"Reversal of supplier payment {item.payment_number}",
            supplier_bill_payment_id=item.id,
            source_type="SUPPLIER_PAYMENT_REVERSAL",
            source_id=item.id,
        )
        self.commit(
            "The supplier payment could not be reversed.",
            "supplier_payment_reversal_conflict",
        )
        self.db.expire_all()
        return self.payment(farm_id, payment_id)

    def cash_adjustment(
        self, farm_id: UUID, user_id: UUID, payload: CashAdjustmentCreate
    ):
        item = self.cash_entry(
            farm_id,
            user_id,
            payload.entry_date,
            CashLedgerEntryType.ADJUSTMENT.value,
            payload.direction.value,
            payload.amount,
            payload.description,
            source_type="CASH_ADJUSTMENT",
            source_id=uuid4(),
        )
        self.commit(
            "The cash adjustment could not be recorded.", "cash_adjustment_conflict"
        )
        return item

    def sync_receipts(self, farm_id: UUID, user_id: UUID):
        created = reversed_count = 0
        for payment in self.repo.unsynced_receipts(farm_id):
            self.cash_entry(
                farm_id,
                user_id,
                payment.payment_date,
                CashLedgerEntryType.SALES_RECEIPT.value,
                CashFlowDirection.INFLOW.value,
                payment.amount,
                f"Customer payment {payment.payment_number}",
                sale_payment_id=payment.id,
                source_type="SALE_PAYMENT",
                source_id=payment.id,
            )
            self.db.flush()
            created += 1
        for payment in self.repo.reversed_receipts(farm_id):
            self.cash_entry(
                farm_id,
                user_id,
                date.today(),
                CashLedgerEntryType.REVERSAL.value,
                CashFlowDirection.OUTFLOW.value,
                payment.amount,
                f"Reversal of customer payment {payment.payment_number}",
                sale_payment_id=payment.id,
                source_type="SALE_PAYMENT_REVERSAL",
                source_id=payment.id,
            )
            self.db.flush()
            reversed_count += 1
        self.commit(
            "Sales receipts could not be synchronized.", "sales_receipt_sync_conflict"
        )
        return (
            created,
            reversed_count,
            normalize_finance_money(self.repo.cash_balance(farm_id)),
        )

    def statement(
        self,
        farm_id: UUID,
        supplier_id: UUID,
        date_from: date | None,
        date_to: date | None,
    ):
        self.validate_dates(date_from, date_to)
        supplier = self.supplier(farm_id, supplier_id)
        bills, payments = self.repo.supplier_statement(
            farm_id, supplier_id, date_from, date_to
        )
        total_billed = normalize_finance_money(
            sum(
                (b.total_amount for b in bills if b.status != "VOIDED"), Decimal("0.00")
            )
        )
        total_paid = normalize_finance_money(
            sum((p.amount for p in payments if p.status == "POSTED"), Decimal("0.00"))
        )
        outstanding = normalize_finance_money(
            sum((b.balance_due for b in bills if b.status != "VOIDED"), Decimal("0.00"))
        )
        return supplier, bills, payments, total_billed, total_paid, outstanding

    def cash_flow(self, farm_id: UUID, date_from: date | None, date_to: date | None):
        self.validate_dates(date_from, date_to)
        inflows = {}
        outflows = {}
        for entry_type, direction, amount in self.repo.cash_flow_rows(
            farm_id, date_from, date_to
        ):
            (inflows if direction == "INFLOW" else outflows)[entry_type] = (
                normalize_finance_money(amount)
            )
        total_in = normalize_finance_money(sum(inflows.values(), Decimal("0.00")))
        total_out = normalize_finance_money(sum(outflows.values(), Decimal("0.00")))
        return {
            "date_from": date_from,
            "date_to": date_to,
            "total_inflows": total_in,
            "total_outflows": total_out,
            "net_cash_flow": normalize_finance_money(total_in - total_out),
            "current_balance": normalize_finance_money(self.repo.cash_balance(farm_id)),
            "inflows_by_type": inflows,
            "outflows_by_type": outflows,
        }

    def profitability(
        self, farm_id: UUID, date_from: date | None, date_to: date | None
    ):
        self.validate_dates(date_from, date_to)
        revenue, expenses, bills, by_category = self.repo.profitability(
            farm_id, date_from, date_to
        )
        costs = normalize_finance_money(expenses + bills)
        profit = normalize_finance_money(revenue - costs)
        margin = (
            normalize_finance_money(profit / revenue * Decimal("100"))
            if revenue > 0
            else Decimal("0.00")
        )
        return {
            "date_from": date_from,
            "date_to": date_to,
            "sales_revenue": normalize_finance_money(revenue),
            "operating_expenses": normalize_finance_money(expenses),
            "supplier_bill_costs": normalize_finance_money(bills),
            "total_costs": costs,
            "gross_profit": profit,
            "profit_margin_percent": margin,
            "expenses_by_category": {
                k: normalize_finance_money(v) for k, v in by_category.items()
            },
        }

    def summary(self, farm_id: UUID, user_id: UUID):
        self.sync_receipts(farm_id, user_id)
        cash = normalize_finance_money(self.repo.cash_balance(farm_id))
        _, bills_total = self.repo.bills(
            farm_id, 0, 100000, None, None, None, None, False, None
        )
        del bills_total
        outstanding = normalize_finance_money(
            sum((b.balance_due for b, _ in []), Decimal("0.00"))
        )
        bills, _ = self.repo.bills(
            farm_id, 0, 100000, None, None, None, None, False, None
        )
        expenses, _ = self.repo.expenses(
            farm_id, 0, 100000, None, None, None, "POSTED", None
        )
        entries, _ = self.repo.cash_entries(
            farm_id, 0, 100000, None, None, "SALES_RECEIPT", "INFLOW"
        )
        outstanding = normalize_finance_money(
            sum((b.balance_due for b in bills if b.status != "VOIDED"), Decimal("0.00"))
        )
        posted_expenses = normalize_finance_money(
            sum((e.amount for e in expenses), Decimal("0.00"))
        )
        receipts = normalize_finance_money(
            sum((e.amount for e in entries), Decimal("0.00"))
        )
        return {
            "as_of_date": date.today(),
            "current_cash_balance": cash,
            "outstanding_supplier_payables": outstanding,
            "posted_expenses": posted_expenses,
            "sales_receipts": receipts,
            "net_cash_flow": cash,
        }
