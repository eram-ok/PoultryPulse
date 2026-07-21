from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.reports.constants import (
    AlertSeverity,
    AlertType,
    TrendMetric,
)


class DashboardProductionSummary(BaseModel):
    today_total_eggs: int
    today_saleable_eggs: int
    today_damaged_or_rejected: int
    today_birds_present: int
    today_laying_percentage: Decimal
    month_total_eggs: int
    month_average_laying_percentage: Decimal


class DashboardInventorySummary(BaseModel):
    total_eggs_in_stock: int
    saleable_eggs_in_stock: int
    total_feed_kg: Decimal
    low_stock_feed_items: int


class DashboardFlockSummary(BaseModel):
    active_flocks: int
    current_bird_population: int
    losses_last_7_days: int
    mortality_rate_last_7_days: Decimal


class DashboardHealthSummary(BaseModel):
    open_health_incidents: int
    critical_health_incidents: int
    vaccinations_due_next_7_days: int
    overdue_vaccinations: int


class DashboardSalesSummary(BaseModel):
    month_sales_revenue: Decimal
    month_amount_received: Decimal
    outstanding_customer_balance: Decimal
    customers_over_credit_limit: int


class DashboardFinanceSummary(BaseModel):
    current_cash_balance: Decimal
    month_operating_expenses: Decimal
    outstanding_supplier_payables: Decimal
    overdue_supplier_bills: int
    month_net_cash_flow: Decimal


class DashboardResponse(BaseModel):
    as_of_date: date
    production: DashboardProductionSummary
    inventory: DashboardInventorySummary
    flocks: DashboardFlockSummary
    health: DashboardHealthSummary
    sales: DashboardSalesSummary
    finance: DashboardFinanceSummary
    active_alert_count: int
    critical_alert_count: int


class OperationalAlertResponse(BaseModel):
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    source_module: str
    source_id: UUID | None
    action_path: str | None
    detected_on: date


class OperationalAlertListResponse(BaseModel):
    items: list[OperationalAlertResponse]
    total: int
    critical: int
    warning: int
    info: int


class PerformanceSummaryResponse(BaseModel):
    date_from: date
    date_to: date
    total_eggs_produced: int
    saleable_eggs_produced: int
    damaged_or_rejected_eggs: int
    average_laying_percentage: Decimal
    total_feed_used_kg: Decimal
    feed_kg_per_100_birds: Decimal
    total_bird_losses: int
    mortality_rate_percent: Decimal
    sales_revenue: Decimal
    operating_expenses: Decimal
    supplier_bill_costs: Decimal
    estimated_profit: Decimal
    profit_margin_percent: Decimal


class TrendPoint(BaseModel):
    metric_date: date
    value: Decimal


class TrendSeries(BaseModel):
    metric: TrendMetric
    points: list[TrendPoint]


class TrendReportResponse(BaseModel):
    date_from: date
    date_to: date
    series: list[TrendSeries]


class FarmReportFilters(BaseModel):
    date_from: date
    date_to: date
    include_zero_days: bool = True
    metrics: list[TrendMetric] = Field(default_factory=lambda: list(TrendMetric))
