from __future__ import annotations

import csv
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from io import StringIO
from uuid import UUID

from app.core.exceptions import BusinessRuleError
from app.modules.reports.advanced_schemas import (
    ComparisonMetric,
    ComparativeReportResponse,
    ExecutiveHighlight,
    ExecutiveSummaryResponse,
)
from app.modules.reports.constants import (
    AlertSeverity,
    TrendMetric,
)
from app.modules.reports.schemas import (
    OperationalAlertListResponse,
    PerformanceSummaryResponse,
    TrendReportResponse,
)
from app.modules.reports.service import ReportsService


TWO_PLACES = Decimal("0.01")


def rounded(value: Decimal | int | str) -> Decimal:
    return Decimal(str(value)).quantize(
        TWO_PLACES,
        rounding=ROUND_HALF_UP,
    )


class AdvancedReportsService:
    def __init__(self, database_session) -> None:
        self.reports = ReportsService(database_session)

    @staticmethod
    def _comparison_metric(
        *,
        metric: str,
        label: str,
        unit: str,
        current_value: Decimal | int,
        previous_value: Decimal | int,
    ) -> ComparisonMetric:
        current = rounded(current_value)
        previous = rounded(previous_value)
        difference = rounded(current - previous)

        if difference > 0:
            direction = "INCREASE"
        elif difference < 0:
            direction = "DECREASE"
        else:
            direction = "UNCHANGED"

        if previous == Decimal("0.00"):
            percent_change = Decimal("0.00") if current == Decimal("0.00") else None
        else:
            percent_change = rounded(difference / abs(previous) * Decimal("100"))

        return ComparisonMetric(
            metric=metric,
            label=label,
            unit=unit,
            current_value=current,
            previous_value=previous,
            absolute_change=difference,
            percent_change=percent_change,
            direction=direction,
        )

    @staticmethod
    def _resolve_comparison_period(
        *,
        date_from: date,
        date_to: date,
        compare_from: date | None,
        compare_to: date | None,
    ) -> tuple[date, date]:
        ReportsService.validate_range(
            date_from,
            date_to,
        )

        if (compare_from is None) != (compare_to is None):
            raise BusinessRuleError(
                (
                    "Both comparison dates are required when "
                    "using a custom comparison period."
                ),
                error_code=("incomplete_comparison_period"),
            )

        if compare_from is not None and compare_to is not None:
            ReportsService.validate_range(
                compare_from,
                compare_to,
            )
            return compare_from, compare_to

        period_days = (date_to - date_from).days + 1
        previous_to = date_from - timedelta(days=1)
        previous_from = previous_to - timedelta(days=period_days - 1)
        return previous_from, previous_to

    def comparison(
        self,
        farm_id: UUID,
        *,
        date_from: date,
        date_to: date,
        compare_from: date | None,
        compare_to: date | None,
    ) -> ComparativeReportResponse:
        (
            previous_from,
            previous_to,
        ) = self._resolve_comparison_period(
            date_from=date_from,
            date_to=date_to,
            compare_from=compare_from,
            compare_to=compare_to,
        )

        current = self.reports.performance(
            farm_id,
            date_from=date_from,
            date_to=date_to,
        )
        previous = self.reports.performance(
            farm_id,
            date_from=previous_from,
            date_to=previous_to,
        )

        metrics = [
            self._comparison_metric(
                metric="TOTAL_EGGS",
                label="Total eggs produced",
                unit="eggs",
                current_value=current.total_eggs_produced,
                previous_value=(previous.total_eggs_produced),
            ),
            self._comparison_metric(
                metric="LAYING_PERCENTAGE",
                label="Average laying percentage",
                unit="percent",
                current_value=(current.average_laying_percentage),
                previous_value=(previous.average_laying_percentage),
            ),
            self._comparison_metric(
                metric="FEED_USED",
                label="Feed used",
                unit="kg",
                current_value=current.total_feed_used_kg,
                previous_value=(previous.total_feed_used_kg),
            ),
            self._comparison_metric(
                metric="BIRD_LOSSES",
                label="Bird losses",
                unit="birds",
                current_value=current.total_bird_losses,
                previous_value=(previous.total_bird_losses),
            ),
            self._comparison_metric(
                metric="SALES_REVENUE",
                label="Sales revenue",
                unit="currency",
                current_value=current.sales_revenue,
                previous_value=previous.sales_revenue,
            ),
            self._comparison_metric(
                metric="TOTAL_COSTS",
                label="Total operating costs",
                unit="currency",
                current_value=(
                    current.operating_expenses + current.supplier_bill_costs
                ),
                previous_value=(
                    previous.operating_expenses + previous.supplier_bill_costs
                ),
            ),
            self._comparison_metric(
                metric="ESTIMATED_PROFIT",
                label="Estimated profit",
                unit="currency",
                current_value=current.estimated_profit,
                previous_value=(previous.estimated_profit),
            ),
        ]

        return ComparativeReportResponse(
            current_date_from=date_from,
            current_date_to=date_to,
            previous_date_from=previous_from,
            previous_date_to=previous_to,
            metrics=metrics,
        )

    @staticmethod
    def _executive_highlights(
        performance: PerformanceSummaryResponse,
        alerts: OperationalAlertListResponse,
    ) -> list[ExecutiveHighlight]:
        highlights: list[ExecutiveHighlight] = []

        if performance.estimated_profit < 0:
            highlights.append(
                ExecutiveHighlight(
                    severity=AlertSeverity.CRITICAL,
                    title="Estimated loss recorded",
                    message=(
                        "Estimated costs exceeded sales revenue during this period."
                    ),
                )
            )
        elif performance.estimated_profit > 0:
            highlights.append(
                ExecutiveHighlight(
                    severity=AlertSeverity.INFO,
                    title="Positive estimated profit",
                    message=(
                        "Sales revenue exceeded the recorded costs for this period."
                    ),
                )
            )
        else:
            highlights.append(
                ExecutiveHighlight(
                    severity=AlertSeverity.WARNING,
                    title="Break-even performance",
                    message=(
                        "Estimated sales revenue and costs were equal for this period."
                    ),
                )
            )

        if alerts.critical > 0:
            highlights.append(
                ExecutiveHighlight(
                    severity=AlertSeverity.CRITICAL,
                    title="Critical alerts require action",
                    message=(
                        f"{alerts.critical} critical operational alert(s) are active."
                    ),
                )
            )
        elif alerts.total > 0:
            highlights.append(
                ExecutiveHighlight(
                    severity=AlertSeverity.WARNING,
                    title="Operational alerts are active",
                    message=(
                        f"{alerts.total} operational alert(s) should be reviewed."
                    ),
                )
            )
        else:
            highlights.append(
                ExecutiveHighlight(
                    severity=AlertSeverity.INFO,
                    title="No active alerts",
                    message=("No operational alerts were detected."),
                )
            )

        if performance.total_eggs_produced == 0:
            highlights.append(
                ExecutiveHighlight(
                    severity=AlertSeverity.WARNING,
                    title="No confirmed egg production",
                    message=(
                        "No confirmed egg production was "
                        "recorded in the selected period."
                    ),
                )
            )
        else:
            highlights.append(
                ExecutiveHighlight(
                    severity=AlertSeverity.INFO,
                    title="Production recorded",
                    message=(
                        f"{performance.total_eggs_produced} "
                        "eggs were produced during the "
                        "selected period."
                    ),
                )
            )

        if performance.mortality_rate_percent >= Decimal("2.00"):
            highlights.append(
                ExecutiveHighlight(
                    severity=AlertSeverity.CRITICAL,
                    title="Elevated mortality rate",
                    message=(
                        "The mortality rate reached "
                        f"{performance.mortality_rate_percent}%."
                    ),
                )
            )
        elif performance.total_bird_losses > 0:
            highlights.append(
                ExecutiveHighlight(
                    severity=AlertSeverity.WARNING,
                    title="Bird losses recorded",
                    message=(
                        f"{performance.total_bird_losses} bird loss(es) were recorded."
                    ),
                )
            )

        return highlights

    def executive_summary(
        self,
        farm_id: UUID,
        *,
        date_from: date,
        date_to: date,
        as_of_date: date | None,
    ) -> ExecutiveSummaryResponse:
        ReportsService.validate_range(
            date_from,
            date_to,
        )

        performance = self.reports.performance(
            farm_id,
            date_from=date_from,
            date_to=date_to,
        )
        alerts = self.reports.alerts(
            farm_id,
            today=as_of_date or date_to,
        )

        return ExecutiveSummaryResponse(
            date_from=date_from,
            date_to=date_to,
            performance=performance,
            alerts=alerts,
            highlights=self._executive_highlights(
                performance,
                alerts,
            ),
        )

    @staticmethod
    def _csv_response_text(
        headers: list[str],
        rows: list[list[object]],
    ) -> str:
        output = StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)
        return output.getvalue()

    def performance_csv(
        self,
        farm_id: UUID,
        *,
        date_from: date,
        date_to: date,
    ) -> str:
        performance = self.reports.performance(
            farm_id,
            date_from=date_from,
            date_to=date_to,
        )

        rows = [
            ["date_from", performance.date_from],
            ["date_to", performance.date_to],
            [
                "total_eggs_produced",
                performance.total_eggs_produced,
            ],
            [
                "saleable_eggs_produced",
                performance.saleable_eggs_produced,
            ],
            [
                "damaged_or_rejected_eggs",
                performance.damaged_or_rejected_eggs,
            ],
            [
                "average_laying_percentage",
                performance.average_laying_percentage,
            ],
            [
                "total_feed_used_kg",
                performance.total_feed_used_kg,
            ],
            [
                "feed_kg_per_100_birds",
                performance.feed_kg_per_100_birds,
            ],
            [
                "total_bird_losses",
                performance.total_bird_losses,
            ],
            [
                "mortality_rate_percent",
                performance.mortality_rate_percent,
            ],
            [
                "sales_revenue",
                performance.sales_revenue,
            ],
            [
                "operating_expenses",
                performance.operating_expenses,
            ],
            [
                "supplier_bill_costs",
                performance.supplier_bill_costs,
            ],
            [
                "estimated_profit",
                performance.estimated_profit,
            ],
            [
                "profit_margin_percent",
                performance.profit_margin_percent,
            ],
        ]

        return self._csv_response_text(
            ["metric", "value"],
            rows,
        )

    def trends_csv(
        self,
        farm_id: UUID,
        *,
        date_from: date,
        date_to: date,
        metrics: list[TrendMetric],
        include_zero_days: bool,
    ) -> str:
        report: TrendReportResponse = self.reports.trends(
            farm_id,
            date_from=date_from,
            date_to=date_to,
            metrics=metrics,
            include_zero_days=include_zero_days,
        )

        rows: list[list[object]] = []

        for series in report.series:
            for point in series.points:
                rows.append(
                    [
                        series.metric.value,
                        point.metric_date,
                        point.value,
                    ]
                )

        return self._csv_response_text(
            ["metric", "date", "value"],
            rows,
        )

    def alerts_csv(
        self,
        farm_id: UUID,
        *,
        as_of_date: date | None,
    ) -> str:
        alerts = self.reports.alerts(
            farm_id,
            today=as_of_date,
        )

        rows = [
            [
                item.severity.value,
                item.alert_type.value,
                item.title,
                item.message,
                item.source_module,
                item.source_id or "",
                item.action_path or "",
                item.detected_on,
            ]
            for item in alerts.items
        ]

        return self._csv_response_text(
            [
                "severity",
                "alert_type",
                "title",
                "message",
                "source_module",
                "source_id",
                "action_path",
                "detected_on",
            ],
            rows,
        )
