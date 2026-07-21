from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from app.core.exceptions import BusinessRuleError
from app.modules.reports.constants import (
    AlertSeverity,
    AlertType,
    TrendMetric,
)
from app.modules.reports.repository import ReportsRepository
from app.modules.reports.schemas import (
    DashboardFinanceSummary,
    DashboardFlockSummary,
    DashboardHealthSummary,
    DashboardInventorySummary,
    DashboardProductionSummary,
    DashboardResponse,
    DashboardSalesSummary,
    OperationalAlertListResponse,
    OperationalAlertResponse,
    PerformanceSummaryResponse,
    TrendPoint,
    TrendReportResponse,
    TrendSeries,
)


MONEY_QUANTUM = Decimal("0.01")
QUANTITY_QUANTUM = Decimal("0.001")


def money(value: Decimal | int) -> Decimal:
    return Decimal(value).quantize(
        MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def quantity(value: Decimal | int) -> Decimal:
    return Decimal(value).quantize(
        QUANTITY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


class ReportsService:
    def __init__(self, database_session) -> None:
        self.repository = ReportsRepository(database_session)

    @staticmethod
    def validate_range(
        date_from: date,
        date_to: date,
        *,
        maximum_days: int = 366,
    ) -> None:
        if date_from > date_to:
            raise BusinessRuleError(
                "The start date cannot be after the end date.",
                error_code="invalid_report_date_range",
            )

        if (date_to - date_from).days > maximum_days:
            raise BusinessRuleError(
                (f"The selected period cannot exceed {maximum_days} days."),
                error_code="report_period_too_large",
            )

    def alerts(
        self,
        farm_id: UUID,
        *,
        today: date | None = None,
    ) -> OperationalAlertListResponse:
        current_date = today or date.today()
        items: list[OperationalAlertResponse] = []

        for feed_item, balance in self.repository.low_feed_stock_alerts(farm_id):
            severity = (
                AlertSeverity.CRITICAL
                if balance <= Decimal("0")
                else AlertSeverity.WARNING
            )
            items.append(
                OperationalAlertResponse(
                    alert_type=AlertType.LOW_FEED_STOCK,
                    severity=severity,
                    title=f"Low feed stock: {feed_item.name}",
                    message=(
                        f"{quantity(balance)} kg remains; "
                        f"reorder level is "
                        f"{quantity(feed_item.reorder_level_kg)} kg."
                    ),
                    source_module="feed",
                    source_id=feed_item.id,
                    action_path=(f"/feed/items/{feed_item.id}"),
                    detected_on=current_date,
                )
            )

        for schedule in self.repository.overdue_vaccination_alerts(
            farm_id,
            today=current_date,
        ):
            items.append(
                OperationalAlertResponse(
                    alert_type=(AlertType.OVERDUE_VACCINATION),
                    severity=AlertSeverity.CRITICAL,
                    title=(f"Overdue vaccination: {schedule.vaccine_name}"),
                    message=(f"Scheduled for {schedule.scheduled_date.isoformat()}."),
                    source_module="health",
                    source_id=schedule.id,
                    action_path=(f"/health/vaccination-schedules/{schedule.id}"),
                    detected_on=current_date,
                )
            )

        for incident in self.repository.active_health_alerts(farm_id):
            severity = (
                AlertSeverity.CRITICAL
                if incident.severity in ("HIGH", "CRITICAL")
                else AlertSeverity.WARNING
            )
            items.append(
                OperationalAlertResponse(
                    alert_type=AlertType.HEALTH_INCIDENT,
                    severity=severity,
                    title=(f"Health incident {incident.incident_code}"),
                    message=(
                        f"{incident.affected_birds} birds "
                        f"affected; status is "
                        f"{incident.status}."
                    ),
                    source_module="health",
                    source_id=incident.id,
                    action_path=(f"/health/incidents/{incident.id}"),
                    detected_on=current_date,
                )
            )

        for bill in self.repository.overdue_supplier_bill_alerts(
            farm_id,
            today=current_date,
        ):
            items.append(
                OperationalAlertResponse(
                    alert_type=(AlertType.OVERDUE_SUPPLIER_BILL),
                    severity=AlertSeverity.WARNING,
                    title=(f"Overdue supplier bill {bill.bill_number}"),
                    message=(f"Outstanding balance is {money(bill.balance_due)}."),
                    source_module="finance",
                    source_id=bill.id,
                    action_path=(f"/finance/supplier-bills/{bill.id}"),
                    detected_on=current_date,
                )
            )

        for customer in self.repository.customer_credit_alerts(farm_id):
            items.append(
                OperationalAlertResponse(
                    alert_type=(AlertType.CUSTOMER_CREDIT_LIMIT),
                    severity=AlertSeverity.WARNING,
                    title=(f"Credit limit exceeded: {customer.name}"),
                    message=(
                        f"Balance is "
                        f"{money(customer.current_balance)}; "
                        f"limit is "
                        f"{money(customer.credit_limit)}."
                    ),
                    source_module="sales",
                    source_id=customer.id,
                    action_path=(f"/sales/customers/{customer.id}"),
                    detected_on=current_date,
                )
            )

        current_cash = self.repository.finance_summary(
            farm_id,
            date_from=current_date,
            date_to=current_date,
            today=current_date,
        )["current_cash"]
        if current_cash < Decimal("0"):
            items.append(
                OperationalAlertResponse(
                    alert_type=(AlertType.NEGATIVE_CASH_BALANCE),
                    severity=AlertSeverity.CRITICAL,
                    title="Negative cash balance",
                    message=(f"Current cash balance is {money(current_cash)}."),
                    source_module="finance",
                    source_id=None,
                    action_path="/finance/cash-ledger",
                    detected_on=current_date,
                )
            )

        severity_rank = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.WARNING: 1,
            AlertSeverity.INFO: 2,
        }
        items.sort(
            key=lambda item: (
                severity_rank[item.severity],
                item.title,
            )
        )

        return OperationalAlertListResponse(
            items=items,
            total=len(items),
            critical=sum(item.severity == AlertSeverity.CRITICAL for item in items),
            warning=sum(item.severity == AlertSeverity.WARNING for item in items),
            info=sum(item.severity == AlertSeverity.INFO for item in items),
        )

    def dashboard(
        self,
        farm_id: UUID,
        *,
        as_of_date: date | None = None,
    ) -> DashboardResponse:
        current_date = as_of_date or date.today()
        month_start = current_date.replace(day=1)
        week_start = current_date - timedelta(days=6)

        today_production = self.repository.production_totals(
            farm_id,
            date_from=current_date,
            date_to=current_date,
        )
        month_production = self.repository.production_totals(
            farm_id,
            date_from=month_start,
            date_to=current_date,
        )
        egg_inventory = self.repository.egg_inventory(farm_id)
        feed_total, low_stock = self.repository.feed_inventory(farm_id)
        flock_data = self.repository.flock_summary(
            farm_id,
            date_from=week_start,
            date_to=current_date,
        )
        health_data = self.repository.health_summary(
            farm_id,
            today=current_date,
            due_until=current_date + timedelta(days=7),
        )
        sales_data = self.repository.sales_summary(
            farm_id,
            date_from=month_start,
            date_to=current_date,
        )
        finance_data = self.repository.finance_summary(
            farm_id,
            date_from=month_start,
            date_to=current_date,
            today=current_date,
        )
        alerts = self.alerts(
            farm_id,
            today=current_date,
        )

        return DashboardResponse(
            as_of_date=current_date,
            production=DashboardProductionSummary(
                today_total_eggs=(today_production["total_eggs"]),
                today_saleable_eggs=(today_production["saleable_eggs"]),
                today_damaged_or_rejected=(today_production["damaged_or_rejected"]),
                today_birds_present=(today_production["birds_present"]),
                today_laying_percentage=money(
                    today_production["average_laying_percentage"]
                ),
                month_total_eggs=(month_production["total_eggs"]),
                month_average_laying_percentage=money(
                    month_production["average_laying_percentage"]
                ),
            ),
            inventory=DashboardInventorySummary(
                total_eggs_in_stock=(egg_inventory["total"]),
                saleable_eggs_in_stock=(egg_inventory["saleable"]),
                total_feed_kg=quantity(feed_total),
                low_stock_feed_items=low_stock,
            ),
            flocks=DashboardFlockSummary(
                active_flocks=flock_data["active_flocks"],
                current_bird_population=flock_data["current_population"],
                losses_last_7_days=flock_data["losses"],
                mortality_rate_last_7_days=money(flock_data["mortality_rate"]),
            ),
            health=DashboardHealthSummary(
                open_health_incidents=health_data["open_incidents"],
                critical_health_incidents=health_data["critical_incidents"],
                vaccinations_due_next_7_days=(health_data["due_soon"]),
                overdue_vaccinations=health_data["overdue"],
            ),
            sales=DashboardSalesSummary(
                month_sales_revenue=money(sales_data["revenue"]),
                month_amount_received=money(sales_data["amount_received"]),
                outstanding_customer_balance=money(sales_data["outstanding"]),
                customers_over_credit_limit=(sales_data["over_limit"]),
            ),
            finance=DashboardFinanceSummary(
                current_cash_balance=money(finance_data["current_cash"]),
                month_operating_expenses=money(finance_data["expenses"]),
                outstanding_supplier_payables=money(finance_data["supplier_payables"]),
                overdue_supplier_bills=finance_data["overdue_bills"],
                month_net_cash_flow=money(finance_data["net_cash"]),
            ),
            active_alert_count=alerts.total,
            critical_alert_count=alerts.critical,
        )

    def performance(
        self,
        farm_id: UUID,
        *,
        date_from: date,
        date_to: date,
    ) -> PerformanceSummaryResponse:
        self.validate_range(date_from, date_to)

        production = self.repository.production_totals(
            farm_id,
            date_from=date_from,
            date_to=date_to,
        )
        flock_data = self.repository.flock_summary(
            farm_id,
            date_from=date_from,
            date_to=date_to,
        )
        feed_used = self.repository.feed_usage_total(
            farm_id,
            date_from=date_from,
            date_to=date_to,
        )
        sales = self.repository.sales_summary(
            farm_id,
            date_from=date_from,
            date_to=date_to,
        )
        finance = self.repository.finance_summary(
            farm_id,
            date_from=date_from,
            date_to=date_to,
            today=date_to,
        )
        supplier_costs = self.repository.supplier_bill_costs(
            farm_id,
            date_from=date_from,
            date_to=date_to,
        )

        total_costs = Decimal(finance["expenses"]) + supplier_costs
        estimated_profit = Decimal(sales["revenue"]) - total_costs
        revenue = Decimal(sales["revenue"])

        margin = (
            estimated_profit * Decimal("100") / revenue if revenue > 0 else Decimal("0")
        )

        population = int(flock_data["current_population"])
        feed_per_100 = (
            feed_used * Decimal("100") / Decimal(population)
            if population > 0
            else Decimal("0")
        )

        return PerformanceSummaryResponse(
            date_from=date_from,
            date_to=date_to,
            total_eggs_produced=production["total_eggs"],
            saleable_eggs_produced=production["saleable_eggs"],
            damaged_or_rejected_eggs=production["damaged_or_rejected"],
            average_laying_percentage=money(production["average_laying_percentage"]),
            total_feed_used_kg=quantity(feed_used),
            feed_kg_per_100_birds=quantity(feed_per_100),
            total_bird_losses=flock_data["losses"],
            mortality_rate_percent=money(flock_data["mortality_rate"]),
            sales_revenue=money(revenue),
            operating_expenses=money(finance["expenses"]),
            supplier_bill_costs=money(supplier_costs),
            estimated_profit=money(estimated_profit),
            profit_margin_percent=money(margin),
        )

    def trends(
        self,
        farm_id: UUID,
        *,
        date_from: date,
        date_to: date,
        metrics: list[TrendMetric],
        include_zero_days: bool,
    ) -> TrendReportResponse:
        self.validate_range(
            date_from,
            date_to,
            maximum_days=93,
        )

        raw = self.repository.trend_rows(
            farm_id,
            date_from=date_from,
            date_to=date_to,
        )

        dates: list[date] = []
        cursor = date_from
        while cursor <= date_to:
            dates.append(cursor)
            cursor += timedelta(days=1)

        series: list[TrendSeries] = []

        for metric in metrics:
            point_map = {
                point_date: Decimal(value) for point_date, value in raw[metric.value]
            }

            if include_zero_days:
                points = [
                    TrendPoint(
                        metric_date=point_date,
                        value=money(
                            point_map.get(
                                point_date,
                                Decimal("0"),
                            )
                        ),
                    )
                    for point_date in dates
                ]
            else:
                points = [
                    TrendPoint(
                        metric_date=point_date,
                        value=money(value),
                    )
                    for point_date, value in raw[metric.value]
                ]

            series.append(
                TrendSeries(
                    metric=metric,
                    points=points,
                )
            )

        return TrendReportResponse(
            date_from=date_from,
            date_to=date_to,
            series=series,
        )
