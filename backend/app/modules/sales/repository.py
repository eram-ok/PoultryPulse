from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.eggs.models import EggInventoryTransaction
from app.modules.sales.constants import (
    CustomerStatus,
    PaymentStatus,
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
)


class SalesRepository:
    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session

    def get_customer(
        self,
        farm_id: UUID,
        customer_id: UUID,
        *,
        for_update: bool = False,
    ) -> Customer | None:
        statement = select(Customer).where(
            Customer.farm_id == farm_id,
            Customer.id == customer_id,
        )
        if for_update:
            statement = statement.with_for_update()
        return self.database_session.scalar(statement)

    def get_customer_by_code(
        self,
        farm_id: UUID,
        customer_code: str,
    ) -> Customer | None:
        return self.database_session.scalar(
            select(Customer).where(
                Customer.farm_id == farm_id,
                Customer.customer_code == customer_code,
            )
        )

    def list_customers(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        customer_status: str | None,
        search: str | None,
    ) -> tuple[list[Customer], int]:
        conditions = [Customer.farm_id == farm_id]

        if customer_status is not None:
            conditions.append(Customer.status == customer_status)

        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(
                or_(
                    Customer.customer_code.ilike(pattern),
                    Customer.name.ilike(pattern),
                    Customer.phone_number.ilike(pattern),
                    Customer.email.ilike(pattern),
                )
            )

        records_statement = (
            select(Customer)
            .where(*conditions)
            .order_by(
                Customer.name.asc(),
                Customer.customer_code.asc(),
            )
            .offset(offset)
            .limit(limit)
        )
        count_statement = select(func.count(Customer.id)).where(*conditions)

        return (
            list(self.database_session.scalars(records_statement).all()),
            int(self.database_session.scalar(count_statement) or 0),
        )

    def add_customer(
        self,
        customer: Customer,
    ) -> Customer:
        self.database_session.add(customer)
        return customer

    def update_customer(
        self,
        customer: Customer,
        changes: dict[str, Any],
    ) -> Customer:
        for field_name, field_value in changes.items():
            setattr(customer, field_name, field_value)
        self.database_session.add(customer)
        return customer

    def get_sale(
        self,
        farm_id: UUID,
        sale_id: UUID,
        *,
        for_update: bool = False,
    ) -> Sale | None:
        statement = (
            select(Sale)
            .options(
                selectinload(Sale.customer),
                selectinload(Sale.items),
                selectinload(Sale.payments),
                selectinload(Sale.returns).selectinload(SaleReturn.items),
            )
            .where(
                Sale.farm_id == farm_id,
                Sale.id == sale_id,
            )
        )
        if for_update:
            statement = statement.with_for_update()
        return self.database_session.scalar(statement)

    def get_sale_by_invoice(
        self,
        farm_id: UUID,
        invoice_number: str,
    ) -> Sale | None:
        return self.database_session.scalar(
            select(Sale).where(
                Sale.farm_id == farm_id,
                Sale.invoice_number == invoice_number,
            )
        )

    def list_sales(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        date_from: date | None,
        date_to: date | None,
        customer_id: UUID | None,
        sale_status: str | None,
        search: str | None,
    ) -> tuple[list[Sale], int]:
        conditions = [Sale.farm_id == farm_id]

        if date_from is not None:
            conditions.append(Sale.sale_date >= date_from)
        if date_to is not None:
            conditions.append(Sale.sale_date <= date_to)
        if customer_id is not None:
            conditions.append(Sale.customer_id == customer_id)
        if sale_status is not None:
            conditions.append(Sale.status == sale_status)
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(
                or_(
                    Sale.invoice_number.ilike(pattern),
                    Sale.customer_name_snapshot.ilike(pattern),
                    Customer.customer_code.ilike(pattern),
                    Customer.name.ilike(pattern),
                )
            )

        records_statement = (
            select(Sale)
            .join(Customer, Customer.id == Sale.customer_id)
            .options(
                selectinload(Sale.customer),
                selectinload(Sale.items),
                selectinload(Sale.payments),
                selectinload(Sale.returns),
            )
            .where(*conditions)
            .order_by(
                Sale.sale_date.desc(),
                Sale.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        count_statement = (
            select(func.count(Sale.id))
            .join(Customer, Customer.id == Sale.customer_id)
            .where(*conditions)
        )

        return (
            list(self.database_session.scalars(records_statement).all()),
            int(self.database_session.scalar(count_statement) or 0),
        )

    def add_sale(self, sale: Sale) -> Sale:
        self.database_session.add(sale)
        return sale

    def get_sale_item(
        self,
        farm_id: UUID,
        sale_item_id: UUID,
    ) -> SaleItem | None:
        return self.database_session.scalar(
            select(SaleItem)
            .join(Sale, Sale.id == SaleItem.sale_id)
            .where(
                Sale.farm_id == farm_id,
                SaleItem.id == sale_item_id,
            )
        )

    def get_payment(
        self,
        farm_id: UUID,
        payment_id: UUID,
        *,
        for_update: bool = False,
    ) -> SalePayment | None:
        statement = (
            select(SalePayment)
            .options(
                selectinload(SalePayment.customer),
                selectinload(SalePayment.sale).selectinload(Sale.customer),
            )
            .where(
                SalePayment.farm_id == farm_id,
                SalePayment.id == payment_id,
            )
        )
        if for_update:
            statement = statement.with_for_update()
        return self.database_session.scalar(statement)

    def list_payments(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        date_from: date | None,
        date_to: date | None,
        customer_id: UUID | None,
        sale_id: UUID | None,
        payment_status: str | None,
    ) -> tuple[list[SalePayment], int]:
        conditions = [SalePayment.farm_id == farm_id]

        if date_from is not None:
            conditions.append(SalePayment.payment_date >= date_from)
        if date_to is not None:
            conditions.append(SalePayment.payment_date <= date_to)
        if customer_id is not None:
            conditions.append(SalePayment.customer_id == customer_id)
        if sale_id is not None:
            conditions.append(SalePayment.sale_id == sale_id)
        if payment_status is not None:
            conditions.append(SalePayment.status == payment_status)

        records_statement = (
            select(SalePayment)
            .options(
                selectinload(SalePayment.customer),
                selectinload(SalePayment.sale),
            )
            .where(*conditions)
            .order_by(
                SalePayment.payment_date.desc(),
                SalePayment.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        count_statement = select(func.count(SalePayment.id)).where(*conditions)

        return (
            list(self.database_session.scalars(records_statement).all()),
            int(self.database_session.scalar(count_statement) or 0),
        )

    def add_payment(
        self,
        payment: SalePayment,
    ) -> SalePayment:
        self.database_session.add(payment)
        return payment

    def get_return(
        self,
        farm_id: UUID,
        return_id: UUID,
        *,
        for_update: bool = False,
    ) -> SaleReturn | None:
        statement = (
            select(SaleReturn)
            .options(
                selectinload(SaleReturn.customer),
                selectinload(SaleReturn.sale).selectinload(Sale.customer),
                selectinload(SaleReturn.items).selectinload(SaleReturnItem.sale_item),
            )
            .where(
                SaleReturn.farm_id == farm_id,
                SaleReturn.id == return_id,
            )
        )
        if for_update:
            statement = statement.with_for_update()
        return self.database_session.scalar(statement)

    def list_returns(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        date_from: date | None,
        date_to: date | None,
        customer_id: UUID | None,
        sale_id: UUID | None,
        return_status: str | None,
    ) -> tuple[list[SaleReturn], int]:
        conditions = [SaleReturn.farm_id == farm_id]

        if date_from is not None:
            conditions.append(SaleReturn.return_date >= date_from)
        if date_to is not None:
            conditions.append(SaleReturn.return_date <= date_to)
        if customer_id is not None:
            conditions.append(SaleReturn.customer_id == customer_id)
        if sale_id is not None:
            conditions.append(SaleReturn.sale_id == sale_id)
        if return_status is not None:
            conditions.append(SaleReturn.status == return_status)

        records_statement = (
            select(SaleReturn)
            .options(
                selectinload(SaleReturn.customer),
                selectinload(SaleReturn.sale),
                selectinload(SaleReturn.items).selectinload(SaleReturnItem.sale_item),
            )
            .where(*conditions)
            .order_by(
                SaleReturn.return_date.desc(),
                SaleReturn.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        count_statement = select(func.count(SaleReturn.id)).where(*conditions)

        return (
            list(self.database_session.scalars(records_statement).all()),
            int(self.database_session.scalar(count_statement) or 0),
        )

    def add_return(
        self,
        sale_return: SaleReturn,
    ) -> SaleReturn:
        self.database_session.add(sale_return)
        return sale_return

    def add_ledger_entry(
        self,
        entry: CustomerLedgerEntry,
    ) -> CustomerLedgerEntry:
        self.database_session.add(entry)
        return entry

    def list_ledger_entries(
        self,
        farm_id: UUID,
        customer_id: UUID,
        *,
        date_from: date | None,
        date_to: date | None,
    ) -> list[CustomerLedgerEntry]:
        conditions = [
            CustomerLedgerEntry.farm_id == farm_id,
            CustomerLedgerEntry.customer_id == customer_id,
        ]
        if date_from is not None:
            conditions.append(CustomerLedgerEntry.entry_date >= date_from)
        if date_to is not None:
            conditions.append(CustomerLedgerEntry.entry_date <= date_to)

        return list(
            self.database_session.scalars(
                select(CustomerLedgerEntry)
                .where(*conditions)
                .order_by(
                    CustomerLedgerEntry.entry_date.asc(),
                    CustomerLedgerEntry.created_at.asc(),
                )
            ).all()
        )

    def get_ledger_balance_before(
        self,
        farm_id: UUID,
        customer_id: UUID,
        before_date: date | None,
    ) -> Decimal:
        if before_date is None:
            return Decimal("0.00")

        entry = self.database_session.scalar(
            select(CustomerLedgerEntry)
            .where(
                CustomerLedgerEntry.farm_id == farm_id,
                CustomerLedgerEntry.customer_id == customer_id,
                CustomerLedgerEntry.entry_date < before_date,
            )
            .order_by(
                CustomerLedgerEntry.entry_date.desc(),
                CustomerLedgerEntry.created_at.desc(),
            )
            .limit(1)
        )
        return entry.balance_after if entry is not None else Decimal("0.00")

    def get_inventory_balance(
        self,
        farm_id: UUID,
        egg_grade: str,
    ) -> int:
        statement = select(
            func.coalesce(
                func.sum(EggInventoryTransaction.signed_quantity),
                0,
            )
        ).where(
            EggInventoryTransaction.farm_id == farm_id,
            EggInventoryTransaction.egg_grade == egg_grade,
        )
        return int(self.database_session.scalar(statement) or 0)

    def get_inventory_by_grade(
        self,
        farm_id: UUID,
    ) -> dict[str, int]:
        statement = (
            select(
                EggInventoryTransaction.egg_grade,
                func.coalesce(
                    func.sum(EggInventoryTransaction.signed_quantity),
                    0,
                ),
            )
            .where(EggInventoryTransaction.farm_id == farm_id)
            .group_by(EggInventoryTransaction.egg_grade)
        )
        return {
            grade: int(balance)
            for grade, balance in self.database_session.execute(statement).all()
        }

    def get_inventory_transactions(
        self,
        farm_id: UUID,
        *,
        source_type: str,
        source_id: UUID,
        transaction_type: str,
    ) -> list[EggInventoryTransaction]:
        return list(
            self.database_session.scalars(
                select(EggInventoryTransaction).where(
                    EggInventoryTransaction.farm_id == farm_id,
                    EggInventoryTransaction.source_type == source_type,
                    EggInventoryTransaction.source_id == source_id,
                    EggInventoryTransaction.transaction_type == transaction_type,
                )
            ).all()
        )

    def add_inventory_transaction(
        self,
        transaction: EggInventoryTransaction,
    ) -> EggInventoryTransaction:
        self.database_session.add(transaction)
        return transaction

    def summary_counts(
        self,
        farm_id: UUID,
    ) -> dict[str, int | Decimal]:
        active_customers = int(
            self.database_session.scalar(
                select(func.count(Customer.id)).where(
                    Customer.farm_id == farm_id,
                    Customer.status == CustomerStatus.ACTIVE.value,
                )
            )
            or 0
        )

        status_rows = self.database_session.execute(
            select(Sale.status, func.count(Sale.id))
            .where(Sale.farm_id == farm_id)
            .group_by(Sale.status)
        ).all()
        status_counts = {
            item_status: int(item_count) for item_status, item_count in status_rows
        }

        gross_sales_value = Decimal(
            self.database_session.scalar(
                select(
                    func.coalesce(
                        func.sum(Sale.total_amount),
                        0,
                    )
                ).where(
                    Sale.farm_id == farm_id,
                    Sale.status != SaleStatus.CANCELLED.value,
                )
            )
            or 0
        )

        outstanding = Decimal(
            self.database_session.scalar(
                select(
                    func.coalesce(
                        func.sum(Sale.balance_due),
                        0,
                    )
                ).where(
                    Sale.farm_id == farm_id,
                    Sale.status != SaleStatus.CANCELLED.value,
                )
            )
            or 0
        )

        payments = Decimal(
            self.database_session.scalar(
                select(
                    func.coalesce(
                        func.sum(SalePayment.amount),
                        0,
                    )
                ).where(
                    SalePayment.farm_id == farm_id,
                    SalePayment.status == PaymentStatus.POSTED.value,
                )
            )
            or 0
        )

        returns = Decimal(
            self.database_session.scalar(
                select(
                    func.coalesce(
                        func.sum(SaleReturn.total_refund),
                        0,
                    )
                ).where(
                    SaleReturn.farm_id == farm_id,
                    SaleReturn.status == SaleReturnStatus.POSTED.value,
                )
            )
            or 0
        )

        return {
            "active_customers": active_customers,
            "draft_sales": status_counts.get(
                SaleStatus.DRAFT.value,
                0,
            ),
            "confirmed_sales": status_counts.get(
                SaleStatus.CONFIRMED.value,
                0,
            ),
            "paid_sales": status_counts.get(
                SaleStatus.PAID.value,
                0,
            ),
            "outstanding_receivables": outstanding,
            "gross_sales_value": gross_sales_value,
            "posted_payments": payments,
            "posted_returns": returns,
        }
