from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.modules.bird_losses.models import BirdLossRecord
from app.modules.eggs.models import EggInventoryTransaction
from app.modules.feed.models import (
    FeedInventoryTransaction,
    FeedItem,
    FeedUsage,
)
from app.modules.finance.models import (
    CashLedgerEntry,
    Expense,
    SupplierBill,
)
from app.modules.flocks.models import (
    Flock,
    FlockPopulationTransaction,
)
from app.modules.health.models import (
    HealthIncident,
    VaccinationSchedule,
)
from app.modules.production.models import DailyEggProduction
from app.modules.sales.models import (
    Customer,
    Sale,
    SalePayment,
)


ZERO = Decimal("0")


class ReportsRepository:
    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session

    def scalar_decimal(self, statement) -> Decimal:
        return Decimal(self.database_session.scalar(statement) or 0)

    def scalar_int(self, statement) -> int:
        return int(self.database_session.scalar(statement) or 0)

    def production_totals(
        self,
        farm_id: UUID,
        *,
        date_from: date,
        date_to: date,
    ) -> dict[str, Decimal | int]:
        conditions = [
            DailyEggProduction.farm_id == farm_id,
            DailyEggProduction.production_date >= date_from,
            DailyEggProduction.production_date <= date_to,
            DailyEggProduction.status == "CONFIRMED",
        ]

        total_eggs_expression = (
            DailyEggProduction.morning_eggs
            + DailyEggProduction.afternoon_eggs
            + DailyEggProduction.evening_eggs
        )
        saleable_expression = (
            DailyEggProduction.large_eggs
            + DailyEggProduction.medium_eggs
            + DailyEggProduction.small_eggs
        )
        damaged_expression = (
            DailyEggProduction.damaged_eggs + DailyEggProduction.rejected_eggs
        )
        laying_expression = case(
            (
                DailyEggProduction.birds_present > 0,
                total_eggs_expression
                * Decimal("100")
                / DailyEggProduction.birds_present,
            ),
            else_=0,
        )

        row = self.database_session.execute(
            select(
                func.coalesce(
                    func.sum(total_eggs_expression),
                    0,
                ),
                func.coalesce(
                    func.sum(saleable_expression),
                    0,
                ),
                func.coalesce(
                    func.sum(damaged_expression),
                    0,
                ),
                func.coalesce(
                    func.sum(DailyEggProduction.birds_present),
                    0,
                ),
                func.coalesce(
                    func.avg(laying_expression),
                    0,
                ),
            ).where(*conditions)
        ).one()

        return {
            "total_eggs": int(row[0] or 0),
            "saleable_eggs": int(row[1] or 0),
            "damaged_or_rejected": int(row[2] or 0),
            "birds_present": int(row[3] or 0),
            "average_laying_percentage": Decimal(row[4] or 0),
        }

    def egg_inventory(self, farm_id: UUID) -> dict[str, int]:
        rows = self.database_session.execute(
            select(
                EggInventoryTransaction.egg_grade,
                func.coalesce(
                    func.sum(EggInventoryTransaction.signed_quantity),
                    0,
                ),
            )
            .where(EggInventoryTransaction.farm_id == farm_id)
            .group_by(EggInventoryTransaction.egg_grade)
        ).all()

        balances = {grade: int(quantity or 0) for grade, quantity in rows}

        saleable = sum(balances.get(grade, 0) for grade in ("LARGE", "MEDIUM", "SMALL"))

        return {
            "total": sum(balances.values()),
            "saleable": saleable,
        }

    def feed_inventory(
        self,
        farm_id: UUID,
    ) -> tuple[Decimal, int]:
        balance_subquery = (
            select(
                FeedInventoryTransaction.feed_item_id.label("feed_item_id"),
                func.coalesce(
                    func.sum(FeedInventoryTransaction.signed_quantity_kg),
                    0,
                ).label("balance_kg"),
            )
            .where(FeedInventoryTransaction.farm_id == farm_id)
            .group_by(FeedInventoryTransaction.feed_item_id)
            .subquery()
        )

        total = self.scalar_decimal(
            select(
                func.coalesce(
                    func.sum(balance_subquery.c.balance_kg),
                    0,
                )
            )
        )

        low_stock = self.scalar_int(
            select(func.count(FeedItem.id))
            .outerjoin(
                balance_subquery,
                balance_subquery.c.feed_item_id == FeedItem.id,
            )
            .where(
                FeedItem.farm_id == farm_id,
                FeedItem.is_active.is_(True),
                func.coalesce(
                    balance_subquery.c.balance_kg,
                    0,
                )
                <= FeedItem.reorder_level_kg,
            )
        )

        return total, low_stock

    def flock_summary(
        self,
        farm_id: UUID,
        *,
        date_from: date,
        date_to: date,
    ) -> dict[str, Decimal | int]:
        active_flocks = self.scalar_int(
            select(func.count(Flock.id)).where(
                Flock.farm_id == farm_id,
                Flock.status == "ACTIVE",
            )
        )

        population = self.scalar_int(
            select(
                func.coalesce(
                    func.sum(FlockPopulationTransaction.signed_quantity),
                    0,
                )
            ).where(FlockPopulationTransaction.farm_id == farm_id)
        )

        losses = self.scalar_int(
            select(
                func.coalesce(
                    func.sum(BirdLossRecord.quantity),
                    0,
                )
            ).where(
                BirdLossRecord.farm_id == farm_id,
                BirdLossRecord.loss_date >= date_from,
                BirdLossRecord.loss_date <= date_to,
                BirdLossRecord.status == "ACTIVE",
            )
        )

        population_before_losses = population + losses
        mortality_rate = (
            Decimal(losses) * Decimal("100") / Decimal(population_before_losses)
            if population_before_losses > 0
            else ZERO
        )

        return {
            "active_flocks": active_flocks,
            "current_population": population,
            "losses": losses,
            "mortality_rate": mortality_rate,
        }

    def health_summary(
        self,
        farm_id: UUID,
        *,
        today: date,
        due_until: date,
    ) -> dict[str, int]:
        open_statuses = (
            "OPEN",
            "UNDER_TREATMENT",
            "MONITORING",
        )

        open_incidents = self.scalar_int(
            select(func.count(HealthIncident.id)).where(
                HealthIncident.farm_id == farm_id,
                HealthIncident.status.in_(open_statuses),
            )
        )

        critical_incidents = self.scalar_int(
            select(func.count(HealthIncident.id)).where(
                HealthIncident.farm_id == farm_id,
                HealthIncident.status.in_(open_statuses),
                HealthIncident.severity == "CRITICAL",
            )
        )

        incomplete_statuses = (
            "COMPLETED",
            "CANCELLED",
        )

        due_soon = self.scalar_int(
            select(func.count(VaccinationSchedule.id)).where(
                VaccinationSchedule.farm_id == farm_id,
                VaccinationSchedule.scheduled_date >= today,
                VaccinationSchedule.scheduled_date <= due_until,
                ~VaccinationSchedule.status.in_(incomplete_statuses),
            )
        )

        overdue = self.scalar_int(
            select(func.count(VaccinationSchedule.id)).where(
                VaccinationSchedule.farm_id == farm_id,
                VaccinationSchedule.scheduled_date < today,
                ~VaccinationSchedule.status.in_(incomplete_statuses),
            )
        )

        return {
            "open_incidents": open_incidents,
            "critical_incidents": critical_incidents,
            "due_soon": due_soon,
            "overdue": overdue,
        }

    def sales_summary(
        self,
        farm_id: UUID,
        *,
        date_from: date,
        date_to: date,
    ) -> dict[str, Decimal | int]:
        excluded_statuses = ("DRAFT", "CANCELLED")

        revenue = self.scalar_decimal(
            select(
                func.coalesce(
                    func.sum(Sale.total_amount),
                    0,
                )
            ).where(
                Sale.farm_id == farm_id,
                Sale.sale_date >= date_from,
                Sale.sale_date <= date_to,
                ~Sale.status.in_(excluded_statuses),
            )
        )

        amount_received = self.scalar_decimal(
            select(
                func.coalesce(
                    func.sum(SalePayment.amount),
                    0,
                )
            ).where(
                SalePayment.farm_id == farm_id,
                SalePayment.payment_date >= date_from,
                SalePayment.payment_date <= date_to,
                SalePayment.status == "POSTED",
            )
        )

        outstanding = self.scalar_decimal(
            select(
                func.coalesce(
                    func.sum(Customer.current_balance),
                    0,
                )
            ).where(Customer.farm_id == farm_id)
        )

        over_limit = self.scalar_int(
            select(func.count(Customer.id)).where(
                Customer.farm_id == farm_id,
                Customer.credit_limit > 0,
                Customer.current_balance > Customer.credit_limit,
            )
        )

        return {
            "revenue": revenue,
            "amount_received": amount_received,
            "outstanding": outstanding,
            "over_limit": over_limit,
        }

    def finance_summary(
        self,
        farm_id: UUID,
        *,
        date_from: date,
        date_to: date,
        today: date,
    ) -> dict[str, Decimal | int]:
        signed_cash = case(
            (
                CashLedgerEntry.direction == "INFLOW",
                CashLedgerEntry.amount,
            ),
            else_=-CashLedgerEntry.amount,
        )

        current_cash = self.scalar_decimal(
            select(
                func.coalesce(
                    func.sum(signed_cash),
                    0,
                )
            ).where(CashLedgerEntry.farm_id == farm_id)
        )

        month_net_cash = self.scalar_decimal(
            select(
                func.coalesce(
                    func.sum(signed_cash),
                    0,
                )
            ).where(
                CashLedgerEntry.farm_id == farm_id,
                CashLedgerEntry.entry_date >= date_from,
                CashLedgerEntry.entry_date <= date_to,
            )
        )

        expenses = self.scalar_decimal(
            select(
                func.coalesce(
                    func.sum(Expense.amount),
                    0,
                )
            ).where(
                Expense.farm_id == farm_id,
                Expense.expense_date >= date_from,
                Expense.expense_date <= date_to,
                Expense.status == "POSTED",
            )
        )

        supplier_payables = self.scalar_decimal(
            select(
                func.coalesce(
                    func.sum(SupplierBill.balance_due),
                    0,
                )
            ).where(
                SupplierBill.farm_id == farm_id,
                SupplierBill.status != "VOIDED",
            )
        )

        overdue_bills = self.scalar_int(
            select(func.count(SupplierBill.id)).where(
                SupplierBill.farm_id == farm_id,
                SupplierBill.due_date < today,
                SupplierBill.balance_due > 0,
                SupplierBill.status != "VOIDED",
            )
        )

        return {
            "current_cash": current_cash,
            "expenses": expenses,
            "supplier_payables": supplier_payables,
            "overdue_bills": overdue_bills,
            "net_cash": month_net_cash,
        }

    def low_feed_stock_alerts(
        self,
        farm_id: UUID,
    ) -> list[tuple[FeedItem, Decimal]]:
        balance_subquery = (
            select(
                FeedInventoryTransaction.feed_item_id.label("feed_item_id"),
                func.coalesce(
                    func.sum(FeedInventoryTransaction.signed_quantity_kg),
                    0,
                ).label("balance_kg"),
            )
            .where(FeedInventoryTransaction.farm_id == farm_id)
            .group_by(FeedInventoryTransaction.feed_item_id)
            .subquery()
        )

        rows = self.database_session.execute(
            select(
                FeedItem,
                func.coalesce(
                    balance_subquery.c.balance_kg,
                    0,
                ),
            )
            .outerjoin(
                balance_subquery,
                balance_subquery.c.feed_item_id == FeedItem.id,
            )
            .where(
                FeedItem.farm_id == farm_id,
                FeedItem.is_active.is_(True),
                func.coalesce(
                    balance_subquery.c.balance_kg,
                    0,
                )
                <= FeedItem.reorder_level_kg,
            )
            .order_by(FeedItem.name.asc())
        ).all()

        return [(item, Decimal(balance or 0)) for item, balance in rows]

    def overdue_vaccination_alerts(
        self,
        farm_id: UUID,
        *,
        today: date,
    ) -> list[VaccinationSchedule]:
        return list(
            self.database_session.scalars(
                select(VaccinationSchedule)
                .where(
                    VaccinationSchedule.farm_id == farm_id,
                    VaccinationSchedule.scheduled_date < today,
                    ~VaccinationSchedule.status.in_(("COMPLETED", "CANCELLED")),
                )
                .order_by(VaccinationSchedule.scheduled_date.asc())
            ).all()
        )

    def active_health_alerts(
        self,
        farm_id: UUID,
    ) -> list[HealthIncident]:
        return list(
            self.database_session.scalars(
                select(HealthIncident)
                .where(
                    HealthIncident.farm_id == farm_id,
                    HealthIncident.status.in_(
                        (
                            "OPEN",
                            "UNDER_TREATMENT",
                            "MONITORING",
                        )
                    ),
                )
                .order_by(HealthIncident.incident_date.asc())
            ).all()
        )

    def overdue_supplier_bill_alerts(
        self,
        farm_id: UUID,
        *,
        today: date,
    ) -> list[SupplierBill]:
        return list(
            self.database_session.scalars(
                select(SupplierBill)
                .where(
                    SupplierBill.farm_id == farm_id,
                    SupplierBill.due_date < today,
                    SupplierBill.balance_due > 0,
                    SupplierBill.status != "VOIDED",
                )
                .order_by(SupplierBill.due_date.asc())
            ).all()
        )

    def customer_credit_alerts(
        self,
        farm_id: UUID,
    ) -> list[Customer]:
        return list(
            self.database_session.scalars(
                select(Customer)
                .where(
                    Customer.farm_id == farm_id,
                    Customer.credit_limit > 0,
                    Customer.current_balance > Customer.credit_limit,
                )
                .order_by(Customer.current_balance.desc())
            ).all()
        )

    def feed_usage_total(
        self,
        farm_id: UUID,
        *,
        date_from: date,
        date_to: date,
    ) -> Decimal:
        return self.scalar_decimal(
            select(
                func.coalesce(
                    func.sum(FeedUsage.quantity_kg),
                    0,
                )
            ).where(
                FeedUsage.farm_id == farm_id,
                FeedUsage.usage_date >= date_from,
                FeedUsage.usage_date <= date_to,
            )
        )

    def supplier_bill_costs(
        self,
        farm_id: UUID,
        *,
        date_from: date,
        date_to: date,
    ) -> Decimal:
        return self.scalar_decimal(
            select(
                func.coalesce(
                    func.sum(SupplierBill.total_amount),
                    0,
                )
            ).where(
                SupplierBill.farm_id == farm_id,
                SupplierBill.bill_date >= date_from,
                SupplierBill.bill_date <= date_to,
                SupplierBill.status != "VOIDED",
            )
        )

    def trend_rows(
        self,
        farm_id: UUID,
        *,
        date_from: date,
        date_to: date,
    ) -> dict[str, list[tuple[date, Decimal]]]:
        production_expression = (
            DailyEggProduction.morning_eggs
            + DailyEggProduction.afternoon_eggs
            + DailyEggProduction.evening_eggs
        )

        production = [
            (record_date, Decimal(value or 0))
            for record_date, value in self.database_session.execute(
                select(
                    DailyEggProduction.production_date,
                    func.coalesce(
                        func.sum(production_expression),
                        0,
                    ),
                )
                .where(
                    DailyEggProduction.farm_id == farm_id,
                    DailyEggProduction.production_date >= date_from,
                    DailyEggProduction.production_date <= date_to,
                    DailyEggProduction.status == "CONFIRMED",
                )
                .group_by(DailyEggProduction.production_date)
                .order_by(DailyEggProduction.production_date)
            ).all()
        ]

        sales = [
            (record_date, Decimal(value or 0))
            for record_date, value in self.database_session.execute(
                select(
                    Sale.sale_date,
                    func.coalesce(
                        func.sum(Sale.total_amount),
                        0,
                    ),
                )
                .where(
                    Sale.farm_id == farm_id,
                    Sale.sale_date >= date_from,
                    Sale.sale_date <= date_to,
                    ~Sale.status.in_(("DRAFT", "CANCELLED")),
                )
                .group_by(Sale.sale_date)
                .order_by(Sale.sale_date)
            ).all()
        ]

        expenses = [
            (record_date, Decimal(value or 0))
            for record_date, value in self.database_session.execute(
                select(
                    Expense.expense_date,
                    func.coalesce(
                        func.sum(Expense.amount),
                        0,
                    ),
                )
                .where(
                    Expense.farm_id == farm_id,
                    Expense.expense_date >= date_from,
                    Expense.expense_date <= date_to,
                    Expense.status == "POSTED",
                )
                .group_by(Expense.expense_date)
                .order_by(Expense.expense_date)
            ).all()
        ]

        feed_usage = [
            (record_date, Decimal(value or 0))
            for record_date, value in self.database_session.execute(
                select(
                    FeedUsage.usage_date,
                    func.coalesce(
                        func.sum(FeedUsage.quantity_kg),
                        0,
                    ),
                )
                .where(
                    FeedUsage.farm_id == farm_id,
                    FeedUsage.usage_date >= date_from,
                    FeedUsage.usage_date <= date_to,
                )
                .group_by(FeedUsage.usage_date)
                .order_by(FeedUsage.usage_date)
            ).all()
        ]

        losses = [
            (record_date, Decimal(value or 0))
            for record_date, value in self.database_session.execute(
                select(
                    BirdLossRecord.loss_date,
                    func.coalesce(
                        func.sum(BirdLossRecord.quantity),
                        0,
                    ),
                )
                .where(
                    BirdLossRecord.farm_id == farm_id,
                    BirdLossRecord.loss_date >= date_from,
                    BirdLossRecord.loss_date <= date_to,
                    BirdLossRecord.status == "ACTIVE",
                )
                .group_by(BirdLossRecord.loss_date)
                .order_by(BirdLossRecord.loss_date)
            ).all()
        ]

        return {
            "EGG_PRODUCTION": production,
            "SALES_REVENUE": sales,
            "OPERATING_EXPENSES": expenses,
            "FEED_USAGE": feed_usage,
            "BIRD_LOSSES": losses,
        }
