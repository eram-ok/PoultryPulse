from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.modules.reports.constants import AlertSeverity
from app.modules.reports.schemas import (
    OperationalAlertListResponse,
    PerformanceSummaryResponse,
)


class ComparisonMetric(BaseModel):
    metric: str
    label: str
    unit: str
    current_value: Decimal
    previous_value: Decimal
    absolute_change: Decimal
    percent_change: Decimal | None
    direction: str


class ComparativeReportResponse(BaseModel):
    current_date_from: date
    current_date_to: date
    previous_date_from: date
    previous_date_to: date
    metrics: list[ComparisonMetric]


class ExecutiveHighlight(BaseModel):
    severity: AlertSeverity
    title: str
    message: str


class ExecutiveSummaryResponse(BaseModel):
    date_from: date
    date_to: date
    performance: PerformanceSummaryResponse
    alerts: OperationalAlertListResponse
    highlights: list[ExecutiveHighlight]
