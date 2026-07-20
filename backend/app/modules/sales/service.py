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
from app.modules.eggs.constants import (
    EggGrade,
    EggInventoryTransactionType,
)
from app.modules.eggs.models import EggInventoryTransaction
from app.modules.sales.constants import (
    CustomerLedgerEntryType,
    CustomerStatus,
    PaymentStatus,
    SalePaymentTerms,
    SaleReturnStatus,
    SaleStatus,
)
from app.modules.sales.models import (
    Customer,
    CustomerLedgerEntry,
    Sale,
    SaleItem,
    SalePayment,
    SaleReturn,
    SaleReturnItem,
    calculate_line_total,
    normalize_money,
)
from app.modules.sales.repository import SalesRepository
from app.modules.sales.schemas import (
    CustomerCreate,
    CustomerUpdate,
    PaymentCreate,
    SaleCreate,
    SaleReturnCreate,
    SaleUpdate,
)


SALEABLE_GRADES = {
    EggGrade.LARGE.value,
    EggGrade.MEDIUM.value,
    EggGrade.SMALL.value,
}


class SalesService:
    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session
        self.repository = SalesRepository(database_session)

    @staticmethod
    def _number(prefix: str) -> str:
        return f"{prefix}-{date.today():%Y%m%d}-{uuid4().hex[:8].upper()}"

    @staticmethod
    def _validate_date_range(
        date_from: date | None,
        date_to: date | None,
    ) -> None:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise BusinessRuleError(
                "The start date cannot be after the end date.",
                error_code="invalid_sales_date_range",
            )

    def _get_customer(
        self,
        farm_id: UUID,
        customer_id: UUID,
        *,
        for_update: bool = False,
    ) -> Customer:
        customer = self.repository.get_customer(
            farm_id,
            customer_id,
            for_update=for_update,
        )
        if customer is None:
            raise ResourceNotFoundError(
                "The selected customer does not exist.",
                error_code="customer_not_found",
            )
        return customer

    def _get_active_customer(
        self,
        farm_id: UUID,
        customer_id: UUID,
        *,
        for_update: bool = False,
    ) -> Customer:
        customer = self._get_customer(
            farm_id,
            customer_id,
            for_update=for_update,
        )
        if customer.status != CustomerStatus.ACTIVE.value:
            raise BusinessRuleError(
                "The selected customer is not active.",
                error_code="customer_not_active",
            )
        return customer

    def _get_sale(
        self,
        farm_id: UUID,
        sale_id: UUID,
        *,
        for_update: bool = False,
    ) -> Sale:
        sale = self.repository.get_sale(
            farm_id,
            sale_id,
            for_update=for_update,
        )
        if sale is None:
            raise ResourceNotFoundError(
                "The selected sale does not exist.",
                error_code="sale_not_found",
            )
        return sale

    def _get_payment(
        self,
        farm_id: UUID,
        payment_id: UUID,
        *,
        for_update: bool = False,
    ) -> SalePayment:
        payment = self.repository.get_payment(
            farm_id,
            payment_id,
            for_update=for_update,
        )
        if payment is None:
            raise ResourceNotFoundError(
                "The selected payment does not exist.",
                error_code="payment_not_found",
            )
        return payment

    def _get_return(
        self,
        farm_id: UUID,
        return_id: UUID,
        *,
        for_update: bool = False,
    ) -> SaleReturn:
        sale_return = self.repository.get_return(
            farm_id,
            return_id,
            for_update=for_update,
        )
        if sale_return is None:
            raise ResourceNotFoundError(
                "The selected sale return does not exist.",
                error_code="sale_return_not_found",
            )
        return sale_return

    def _commit(self, message: str, error_code: str) -> None:
        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()
            raise ResourceConflictError(
                message,
                error_code=error_code,
            ) from exc

    @staticmethod
    def _sale_item_total_eggs(item: SaleItem) -> int:
        return item.quantity * item.eggs_per_unit

    @staticmethod
    def _refresh_sale_status(sale: Sale) -> None:
        if sale.status == SaleStatus.CANCELLED.value:
            return

        total_quantity = sum(item.quantity for item in sale.items)
        returned_quantity = sum(item.quantity_returned for item in sale.items)

        if total_quantity > 0 and returned_quantity == total_quantity:
            sale.status = SaleStatus.RETURNED.value
        elif returned_quantity > 0:
            sale.status = SaleStatus.PARTIALLY_RETURNED.value
        elif sale.balance_due == Decimal("0.00"):
            sale.status = SaleStatus.PAID.value
        elif sale.amount_paid > Decimal("0.00"):
            sale.status = SaleStatus.PARTIALLY_PAID.value
        else:
            sale.status = SaleStatus.CONFIRMED.value

    def _add_ledger_entry(
        self,
        *,
        farm_id: UUID,
        customer: Customer,
        created_by: UUID,
        entry_date: date,
        entry_type: str,
        description: str,
        debit_amount: Decimal = Decimal("0.00"),
        credit_amount: Decimal = Decimal("0.00"),
        sale_id: UUID | None = None,
        payment_id: UUID | None = None,
        sale_return_id: UUID | None = None,
    ) -> CustomerLedgerEntry:
        entry = CustomerLedgerEntry(
            farm_id=farm_id,
            customer_id=customer.id,
            sale_id=sale_id,
            payment_id=payment_id,
            sale_return_id=sale_return_id,
            entry_date=entry_date,
            entry_type=entry_type,
            description=description,
            debit_amount=normalize_money(debit_amount),
            credit_amount=normalize_money(credit_amount),
            balance_after=normalize_money(customer.current_balance),
            created_by=created_by,
        )
        self.repository.add_ledger_entry(entry)
        return entry

    def create_customer(
        self,
        farm_id: UUID,
        created_by: UUID,
        payload: CustomerCreate,
    ) -> Customer:
        if (
            self.repository.get_customer_by_code(
                farm_id,
                payload.customer_code,
            )
            is not None
        ):
            raise ResourceConflictError(
                "A customer with this code already exists.",
                error_code="customer_code_already_exists",
            )

        customer = Customer(
            farm_id=farm_id,
            customer_code=payload.customer_code,
            name=payload.name,
            phone_number=payload.phone_number,
            email=(str(payload.email) if payload.email is not None else None),
            address=payload.address,
            tax_number=payload.tax_number,
            contact_person=payload.contact_person,
            credit_limit=normalize_money(payload.credit_limit),
            opening_balance=normalize_money(payload.opening_balance),
            current_balance=normalize_money(payload.opening_balance),
            status=CustomerStatus.ACTIVE.value,
            notes=payload.notes,
        )
        self.repository.add_customer(customer)
        self.database_session.flush()

        if customer.opening_balance > Decimal("0.00"):
            self._add_ledger_entry(
                farm_id=farm_id,
                customer=customer,
                created_by=created_by,
                entry_date=date.today(),
                entry_type=(CustomerLedgerEntryType.OPENING_BALANCE.value),
                description="Customer opening balance",
                debit_amount=customer.opening_balance,
            )

        self._commit(
            "The customer could not be created.",
            "customer_creation_conflict",
        )
        return self._get_customer(farm_id, customer.id)

    def update_customer(
        self,
        farm_id: UUID,
        customer_id: UUID,
        payload: CustomerUpdate,
    ) -> Customer:
        customer = self._get_customer(
            farm_id,
            customer_id,
            for_update=True,
        )
        changes = payload.model_dump(exclude_unset=True)

        if payload.customer_code is not None:
            conflicting = self.repository.get_customer_by_code(
                farm_id,
                payload.customer_code,
            )
            if conflicting is not None and conflicting.id != customer.id:
                raise ResourceConflictError(
                    "Another customer already uses this code.",
                    error_code="customer_code_already_exists",
                )

        if payload.email is not None:
            changes["email"] = str(payload.email)
        if payload.status is not None:
            changes["status"] = payload.status.value
        if payload.credit_limit is not None:
            new_limit = normalize_money(payload.credit_limit)
            if new_limit < customer.current_balance:
                raise BusinessRuleError(
                    "Credit limit cannot be below the current balance.",
                    error_code=("credit_limit_below_customer_balance"),
                )
            changes["credit_limit"] = new_limit

        self.repository.update_customer(
            customer,
            changes,
        )
        self._commit(
            "The customer could not be updated.",
            "customer_update_conflict",
        )
        return self._get_customer(farm_id, customer_id)

    def list_customers(self, farm_id: UUID, **kwargs):
        return self.repository.list_customers(
            farm_id,
            **kwargs,
        )

    def get_customer(
        self,
        farm_id: UUID,
        customer_id: UUID,
    ) -> Customer:
        return self._get_customer(farm_id, customer_id)

    def _build_sale_items(
        self,
        sale: Sale,
        payload_items,
    ) -> None:
        sale.items.clear()

        for payload_item in payload_items:
            if payload_item.egg_grade.value not in SALEABLE_GRADES:
                raise BusinessRuleError(
                    "Damaged and rejected eggs cannot be sold.",
                    error_code="egg_grade_not_saleable",
                )

            line_total = calculate_line_total(
                payload_item.quantity,
                payload_item.unit_price,
            )
            sale.items.append(
                SaleItem(
                    egg_grade=payload_item.egg_grade.value,
                    unit=payload_item.unit.value,
                    eggs_per_unit=(payload_item.eggs_per_unit),
                    quantity=payload_item.quantity,
                    quantity_returned=0,
                    unit_price=normalize_money(payload_item.unit_price),
                    line_total=line_total,
                    notes=payload_item.notes,
                )
            )

    def _calculate_sale_totals(self, sale: Sale) -> None:
        subtotal = normalize_money(
            sum(
                (item.line_total for item in sale.items),
                Decimal("0.00"),
            )
        )
        if sale.discount_amount > subtotal:
            raise BusinessRuleError(
                "Discount cannot exceed the sale subtotal.",
                error_code="discount_exceeds_subtotal",
            )

        total_amount = normalize_money(
            subtotal - sale.discount_amount + sale.tax_amount
        )
        sale.subtotal = subtotal
        sale.total_amount = total_amount
        sale.balance_due = normalize_money(total_amount - sale.amount_paid)

    def create_sale(
        self,
        farm_id: UUID,
        created_by: UUID,
        payload: SaleCreate,
    ) -> Sale:
        customer = self._get_active_customer(
            farm_id,
            payload.customer_id,
        )

        sale = Sale(
            farm_id=farm_id,
            customer_id=customer.id,
            invoice_number=self._number("INV"),
            sale_date=payload.sale_date,
            due_date=payload.due_date,
            payment_terms=payload.payment_terms.value,
            status=SaleStatus.DRAFT.value,
            subtotal=Decimal("0.00"),
            discount_amount=normalize_money(payload.discount_amount),
            tax_amount=normalize_money(payload.tax_amount),
            total_amount=Decimal("0.00"),
            amount_paid=Decimal("0.00"),
            balance_due=Decimal("0.00"),
            customer_name_snapshot=customer.name,
            customer_phone_snapshot=(customer.phone_number),
            notes=payload.notes,
            created_by=created_by,
        )
        self._build_sale_items(sale, payload.items)
        self._calculate_sale_totals(sale)
        self.repository.add_sale(sale)

        self._commit(
            "The sale could not be created.",
            "sale_creation_conflict",
        )
        self.database_session.expire_all()
        return self._get_sale(farm_id, sale.id)

    def update_sale(
        self,
        farm_id: UUID,
        sale_id: UUID,
        payload: SaleUpdate,
    ) -> Sale:
        sale = self._get_sale(
            farm_id,
            sale_id,
            for_update=True,
        )
        if sale.status != SaleStatus.DRAFT.value:
            raise BusinessRuleError(
                "Only draft sales can be edited.",
                error_code="sale_not_editable",
            )

        changes = payload.model_dump(
            exclude_unset=True,
            exclude={"items"},
        )

        payment_terms = (
            payload.payment_terms.value
            if payload.payment_terms is not None
            else sale.payment_terms
        )
        due_date = payload.due_date if "due_date" in changes else sale.due_date

        if payment_terms == SalePaymentTerms.CREDIT.value and due_date is None:
            raise BusinessRuleError(
                "Credit sales require a due date.",
                error_code="credit_sale_due_date_required",
            )
        if due_date is not None and due_date < sale.sale_date:
            raise BusinessRuleError(
                "Due date cannot be before the sale date.",
                error_code="invalid_sale_due_date",
            )

        if payload.payment_terms is not None:
            changes["payment_terms"] = payload.payment_terms.value
        if payload.discount_amount is not None:
            changes["discount_amount"] = normalize_money(payload.discount_amount)
        if payload.tax_amount is not None:
            changes["tax_amount"] = normalize_money(payload.tax_amount)

        for field_name, field_value in changes.items():
            setattr(sale, field_name, field_value)

        if payload.items is not None:
            self._build_sale_items(
                sale,
                payload.items,
            )

        self._calculate_sale_totals(sale)
        self._commit(
            "The sale could not be updated.",
            "sale_update_conflict",
        )
        self.database_session.expire_all()
        return self._get_sale(farm_id, sale_id)

    def confirm_sale(
        self,
        farm_id: UUID,
        sale_id: UUID,
        confirmed_by: UUID,
        *,
        notes: str | None,
    ) -> Sale:
        sale = self._get_sale(
            farm_id,
            sale_id,
            for_update=True,
        )
        if sale.status != SaleStatus.DRAFT.value:
            raise BusinessRuleError(
                "Only draft sales can be confirmed.",
                error_code="sale_not_confirmable",
            )

        customer = self._get_active_customer(
            farm_id,
            sale.customer_id,
            for_update=True,
        )

        if (
            sale.payment_terms == SalePaymentTerms.CREDIT.value
            and customer.current_balance + sale.total_amount > customer.credit_limit
        ):
            raise BusinessRuleError(
                "The sale exceeds the customer's available credit.",
                error_code="customer_credit_limit_exceeded",
            )

        required_by_grade: dict[str, int] = {}
        for item in sale.items:
            required_by_grade[item.egg_grade] = required_by_grade.get(
                item.egg_grade,
                0,
            ) + self._sale_item_total_eggs(item)

        for egg_grade, required_quantity in required_by_grade.items():
            available = self.repository.get_inventory_balance(
                farm_id,
                egg_grade,
            )
            if required_quantity > available:
                raise BusinessRuleError(
                    (
                        f"Insufficient {egg_grade.lower()} egg "
                        f"inventory. Required {required_quantity}, "
                        f"available {available}."
                    ),
                    error_code="insufficient_egg_inventory",
                )

        group_id = uuid4()
        for egg_grade, required_quantity in required_by_grade.items():
            self.repository.add_inventory_transaction(
                EggInventoryTransaction(
                    farm_id=farm_id,
                    transaction_group_id=group_id,
                    inventory_date=sale.sale_date,
                    egg_grade=egg_grade,
                    transaction_type=(EggInventoryTransactionType.SALE_OUT.value),
                    quantity=required_quantity,
                    signed_quantity=-required_quantity,
                    source_type="SALE",
                    source_id=sale.id,
                    reference=sale.invoice_number,
                    description=(f"Egg sale {sale.invoice_number}"),
                    created_by=confirmed_by,
                )
            )

        customer.current_balance = normalize_money(
            customer.current_balance + sale.total_amount
        )
        sale.status = SaleStatus.CONFIRMED.value
        sale.confirmed_by = confirmed_by
        sale.confirmed_at = datetime.now(UTC)

        if notes:
            sale.notes = f"{sale.notes}\n{notes}" if sale.notes else notes

        self._add_ledger_entry(
            farm_id=farm_id,
            customer=customer,
            created_by=confirmed_by,
            entry_date=sale.sale_date,
            entry_type=CustomerLedgerEntryType.SALE.value,
            description=f"Invoice {sale.invoice_number}",
            debit_amount=sale.total_amount,
            sale_id=sale.id,
        )

        self._commit(
            "The sale could not be confirmed.",
            "sale_confirmation_conflict",
        )
        self.database_session.expire_all()
        return self._get_sale(farm_id, sale_id)

    def cancel_sale(
        self,
        farm_id: UUID,
        sale_id: UUID,
        cancelled_by: UUID,
        reason: str,
    ) -> Sale:
        sale = self._get_sale(
            farm_id,
            sale_id,
            for_update=True,
        )
        if sale.status != SaleStatus.DRAFT.value:
            raise BusinessRuleError(
                (
                    "Only draft sales can be cancelled. "
                    "Use a sale return for confirmed invoices."
                ),
                error_code="confirmed_sale_cannot_cancel",
            )

        sale.status = SaleStatus.CANCELLED.value
        sale.cancelled_by = cancelled_by
        sale.cancelled_at = datetime.now(UTC)
        sale.cancellation_reason = reason
        self.database_session.commit()
        self.database_session.expire_all()
        return self._get_sale(farm_id, sale_id)

    def list_sales(
        self,
        farm_id: UUID,
        *,
        date_from: date | None,
        date_to: date | None,
        **kwargs,
    ):
        self._validate_date_range(date_from, date_to)
        return self.repository.list_sales(
            farm_id,
            date_from=date_from,
            date_to=date_to,
            **kwargs,
        )

    def get_sale(
        self,
        farm_id: UUID,
        sale_id: UUID,
    ) -> Sale:
        return self._get_sale(farm_id, sale_id)

    def record_payment(
        self,
        farm_id: UUID,
        received_by: UUID,
        payload: PaymentCreate,
    ) -> SalePayment:
        sale = self._get_sale(
            farm_id,
            payload.sale_id,
            for_update=True,
        )
        if sale.status in {
            SaleStatus.DRAFT.value,
            SaleStatus.CANCELLED.value,
            SaleStatus.RETURNED.value,
        }:
            raise BusinessRuleError(
                "Payments cannot be posted to this sale.",
                error_code="sale_not_payable",
            )

        amount = normalize_money(payload.amount)
        if amount > sale.balance_due:
            raise BusinessRuleError(
                "Payment cannot exceed the invoice balance.",
                error_code="payment_exceeds_balance",
            )

        customer = self._get_customer(
            farm_id,
            sale.customer_id,
            for_update=True,
        )

        payment = SalePayment(
            farm_id=farm_id,
            customer_id=customer.id,
            sale_id=sale.id,
            payment_number=self._number("PAY"),
            payment_date=payload.payment_date,
            amount=amount,
            method=payload.method.value,
            reference_number=payload.reference_number,
            status=PaymentStatus.POSTED.value,
            notes=payload.notes,
            received_by=received_by,
        )
        self.repository.add_payment(payment)
        self.database_session.flush()

        sale.amount_paid = normalize_money(sale.amount_paid + amount)
        sale.balance_due = normalize_money(sale.total_amount - sale.amount_paid)
        customer.current_balance = normalize_money(customer.current_balance - amount)
        self._refresh_sale_status(sale)

        self._add_ledger_entry(
            farm_id=farm_id,
            customer=customer,
            created_by=received_by,
            entry_date=payload.payment_date,
            entry_type=CustomerLedgerEntryType.PAYMENT.value,
            description=f"Payment {payment.payment_number}",
            credit_amount=amount,
            sale_id=sale.id,
            payment_id=payment.id,
        )

        self._commit(
            "The payment could not be recorded.",
            "payment_creation_conflict",
        )
        self.database_session.expire_all()
        return self._get_payment(farm_id, payment.id)

    def reverse_payment(
        self,
        farm_id: UUID,
        payment_id: UUID,
        reversed_by: UUID,
        reason: str,
    ) -> SalePayment:
        payment = self._get_payment(
            farm_id,
            payment_id,
            for_update=True,
        )
        if payment.status == PaymentStatus.REVERSED.value:
            raise ResourceConflictError(
                "This payment is already reversed.",
                error_code="payment_already_reversed",
            )

        sale = self._get_sale(
            farm_id,
            payment.sale_id,
            for_update=True,
        )
        customer = self._get_customer(
            farm_id,
            payment.customer_id,
            for_update=True,
        )

        sale.amount_paid = normalize_money(sale.amount_paid - payment.amount)
        sale.balance_due = normalize_money(sale.total_amount - sale.amount_paid)
        customer.current_balance = normalize_money(
            customer.current_balance + payment.amount
        )
        payment.status = PaymentStatus.REVERSED.value
        payment.reversed_by = reversed_by
        payment.reversed_at = datetime.now(UTC)
        payment.reversal_reason = reason
        self._refresh_sale_status(sale)

        self._add_ledger_entry(
            farm_id=farm_id,
            customer=customer,
            created_by=reversed_by,
            entry_date=date.today(),
            entry_type=CustomerLedgerEntryType.REVERSAL.value,
            description=(f"Reversal of payment {payment.payment_number}"),
            debit_amount=payment.amount,
            sale_id=sale.id,
            payment_id=payment.id,
        )

        self.database_session.commit()
        self.database_session.expire_all()
        return self._get_payment(farm_id, payment_id)

    def list_payments(
        self,
        farm_id: UUID,
        *,
        date_from: date | None,
        date_to: date | None,
        **kwargs,
    ):
        self._validate_date_range(date_from, date_to)
        return self.repository.list_payments(
            farm_id,
            date_from=date_from,
            date_to=date_to,
            **kwargs,
        )

    def get_payment(
        self,
        farm_id: UUID,
        payment_id: UUID,
    ) -> SalePayment:
        return self._get_payment(farm_id, payment_id)

    def create_return(
        self,
        farm_id: UUID,
        recorded_by: UUID,
        payload: SaleReturnCreate,
    ) -> SaleReturn:
        sale = self._get_sale(
            farm_id,
            payload.sale_id,
            for_update=True,
        )
        if sale.status in {
            SaleStatus.DRAFT.value,
            SaleStatus.CANCELLED.value,
            SaleStatus.RETURNED.value,
        }:
            raise BusinessRuleError(
                "Items cannot be returned against this sale.",
                error_code="sale_not_returnable",
            )
        if payload.return_date < sale.sale_date:
            raise BusinessRuleError(
                "Return date cannot be before the sale date.",
                error_code="return_before_sale_date",
            )

        requested_item_ids = [item.sale_item_id for item in payload.items]
        if len(requested_item_ids) != len(set(requested_item_ids)):
            raise BusinessRuleError(
                "Each sale item may appear only once per return.",
                error_code="duplicate_return_item",
            )

        sale_items_by_id = {item.id: item for item in sale.items}
        total_refund = Decimal("0.00")
        prepared: list[tuple[SaleItem, int, str | None, Decimal]] = []

        for payload_item in payload.items:
            sale_item = sale_items_by_id.get(payload_item.sale_item_id)
            if sale_item is None:
                raise BusinessRuleError(
                    "A return item does not belong to this sale.",
                    error_code="return_item_sale_mismatch",
                )
            if payload_item.quantity > sale_item.remaining_returnable_quantity:
                raise BusinessRuleError(
                    "Return quantity exceeds the returnable quantity.",
                    error_code="return_quantity_exceeded",
                )

            line_total = calculate_line_total(
                payload_item.quantity,
                sale_item.unit_price,
            )
            total_refund = normalize_money(total_refund + line_total)
            prepared.append(
                (
                    sale_item,
                    payload_item.quantity,
                    payload_item.reason,
                    line_total,
                )
            )

        if total_refund > sale.balance_due:
            raise BusinessRuleError(
                (
                    "This return exceeds the unpaid invoice balance. "
                    "Cash-refund returns are not supported in Stage 13."
                ),
                error_code=("return_exceeds_outstanding_balance"),
            )

        customer = self._get_customer(
            farm_id,
            sale.customer_id,
            for_update=True,
        )

        sale_return = SaleReturn(
            farm_id=farm_id,
            sale_id=sale.id,
            customer_id=customer.id,
            return_number=self._number("RET"),
            return_date=payload.return_date,
            total_refund=total_refund,
            status=SaleReturnStatus.POSTED.value,
            reason=payload.reason,
            notes=payload.notes,
            recorded_by=recorded_by,
        )
        self.repository.add_return(sale_return)
        self.database_session.flush()

        group_id = uuid4()
        for (
            sale_item,
            quantity,
            item_reason,
            line_total,
        ) in prepared:
            sale_item.quantity_returned += quantity

            return_item = SaleReturnItem(
                sale_return_id=sale_return.id,
                sale_item_id=sale_item.id,
                egg_grade=sale_item.egg_grade,
                unit=sale_item.unit,
                quantity=quantity,
                unit_price=sale_item.unit_price,
                line_total=line_total,
                reason=item_reason,
            )
            sale_return.items.append(return_item)

            egg_quantity = quantity * sale_item.eggs_per_unit
            self.repository.add_inventory_transaction(
                EggInventoryTransaction(
                    farm_id=farm_id,
                    transaction_group_id=group_id,
                    inventory_date=payload.return_date,
                    egg_grade=sale_item.egg_grade,
                    transaction_type=(EggInventoryTransactionType.SALE_RETURN_IN.value),
                    quantity=egg_quantity,
                    signed_quantity=egg_quantity,
                    source_type="SALE_RETURN",
                    source_id=sale_return.id,
                    reference=sale_return.return_number,
                    description=(f"Return against {sale.invoice_number}"),
                    created_by=recorded_by,
                )
            )

        sale.total_amount = normalize_money(sale.total_amount - total_refund)
        sale.balance_due = normalize_money(sale.balance_due - total_refund)
        customer.current_balance = normalize_money(
            customer.current_balance - total_refund
        )
        self._refresh_sale_status(sale)

        self._add_ledger_entry(
            farm_id=farm_id,
            customer=customer,
            created_by=recorded_by,
            entry_date=payload.return_date,
            entry_type=(CustomerLedgerEntryType.SALE_RETURN.value),
            description=(f"Sale return {sale_return.return_number}"),
            credit_amount=total_refund,
            sale_id=sale.id,
            sale_return_id=sale_return.id,
        )

        self._commit(
            "The sale return could not be posted.",
            "sale_return_creation_conflict",
        )
        self.database_session.expire_all()
        return self._get_return(farm_id, sale_return.id)

    def reverse_return(
        self,
        farm_id: UUID,
        return_id: UUID,
        reversed_by: UUID,
        reason: str,
    ) -> SaleReturn:
        sale_return = self._get_return(
            farm_id,
            return_id,
            for_update=True,
        )
        if sale_return.status == (SaleReturnStatus.REVERSED.value):
            raise ResourceConflictError(
                "This sale return is already reversed.",
                error_code="sale_return_already_reversed",
            )

        sale = self._get_sale(
            farm_id,
            sale_return.sale_id,
            for_update=True,
        )
        customer = self._get_customer(
            farm_id,
            sale_return.customer_id,
            for_update=True,
        )

        original_transactions = self.repository.get_inventory_transactions(
            farm_id,
            source_type="SALE_RETURN",
            source_id=sale_return.id,
            transaction_type=(EggInventoryTransactionType.SALE_RETURN_IN.value),
        )
        transactions_by_grade = {
            transaction.egg_grade: transaction for transaction in original_transactions
        }

        group_id = uuid4()
        for return_item in sale_return.items:
            original = transactions_by_grade.get(return_item.egg_grade)
            if original is None:
                raise BusinessRuleError(
                    "The return inventory entry is missing.",
                    error_code=("return_inventory_transaction_missing"),
                )

            sale_item = return_item.sale_item
            sale_item.quantity_returned -= return_item.quantity

            egg_quantity = return_item.quantity * sale_item.eggs_per_unit
            available = self.repository.get_inventory_balance(
                farm_id,
                return_item.egg_grade,
            )
            if egg_quantity > available:
                raise BusinessRuleError(
                    (
                        "The return cannot be reversed because "
                        "the restored eggs are no longer in stock."
                    ),
                    error_code=("insufficient_inventory_for_return_reversal"),
                )

            self.repository.add_inventory_transaction(
                EggInventoryTransaction(
                    farm_id=farm_id,
                    transaction_group_id=group_id,
                    inventory_date=date.today(),
                    egg_grade=return_item.egg_grade,
                    transaction_type=(EggInventoryTransactionType.REVERSAL.value),
                    quantity=egg_quantity,
                    signed_quantity=-egg_quantity,
                    source_type="SALE_RETURN",
                    source_id=sale_return.id,
                    reference=sale_return.return_number,
                    description=(f"Reversal of {sale_return.return_number}"),
                    created_by=reversed_by,
                    reversed_transaction_id=original.id,
                )
            )

        sale.total_amount = normalize_money(
            sale.total_amount + sale_return.total_refund
        )
        sale.balance_due = normalize_money(sale.balance_due + sale_return.total_refund)
        customer.current_balance = normalize_money(
            customer.current_balance + sale_return.total_refund
        )
        sale_return.status = SaleReturnStatus.REVERSED.value
        sale_return.reversed_by = reversed_by
        sale_return.reversed_at = datetime.now(UTC)
        sale_return.reversal_reason = reason
        self._refresh_sale_status(sale)

        self._add_ledger_entry(
            farm_id=farm_id,
            customer=customer,
            created_by=reversed_by,
            entry_date=date.today(),
            entry_type=CustomerLedgerEntryType.REVERSAL.value,
            description=(f"Reversal of return {sale_return.return_number}"),
            debit_amount=sale_return.total_refund,
            sale_id=sale.id,
            sale_return_id=sale_return.id,
        )

        self._commit(
            "The sale return could not be reversed.",
            "sale_return_reversal_conflict",
        )
        self.database_session.expire_all()
        return self._get_return(farm_id, return_id)

    def list_returns(
        self,
        farm_id: UUID,
        *,
        date_from: date | None,
        date_to: date | None,
        **kwargs,
    ):
        self._validate_date_range(date_from, date_to)
        return self.repository.list_returns(
            farm_id,
            date_from=date_from,
            date_to=date_to,
            **kwargs,
        )

    def get_return(
        self,
        farm_id: UUID,
        return_id: UUID,
    ) -> SaleReturn:
        return self._get_return(farm_id, return_id)

    def get_statement(
        self,
        farm_id: UUID,
        customer_id: UUID,
        *,
        date_from: date | None,
        date_to: date | None,
    ):
        self._validate_date_range(date_from, date_to)
        customer = self._get_customer(
            farm_id,
            customer_id,
        )
        opening_balance = self.repository.get_ledger_balance_before(
            farm_id,
            customer_id,
            date_from,
        )
        entries = self.repository.list_ledger_entries(
            farm_id,
            customer_id,
            date_from=date_from,
            date_to=date_to,
        )
        closing_balance = entries[-1].balance_after if entries else opening_balance
        return (
            customer,
            opening_balance,
            closing_balance,
            entries,
        )

    def get_summary(
        self,
        farm_id: UUID,
    ) -> dict:
        summary = self.repository.summary_counts(farm_id)
        summary["as_of_date"] = date.today()
        summary["inventory_by_grade"] = self.repository.get_inventory_by_grade(farm_id)
        return summary
