from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_database_session
from app.modules.auth.dependencies import require_permissions
from app.modules.reports.advanced_schemas import (
    ComparativeReportResponse,
    ExecutiveSummaryResponse,
)
from app.modules.reports.advanced_service import (
    AdvancedReportsService,
)
from app.modules.reports.constants import TrendMetric
from app.modules.users.models import User


router = APIRouter(
    prefix="/reports",
    tags=["Executive Reports and CSV Exports"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


def csv_response(
    content: str,
    filename: str,
) -> Response:
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": (f'attachment; filename="{filename}"')},
    )


@router.get(
    "/comparison",
    response_model=ComparativeReportResponse,
)
def comparison(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("reports.view")),
    ],
    date_from: date | None = None,
    date_to: date | None = None,
    compare_from: date | None = None,
    compare_to: date | None = None,
) -> ComparativeReportResponse:
    resolved_to = date_to or date.today()
    resolved_from = date_from or (resolved_to - timedelta(days=29))

    return AdvancedReportsService(database_session).comparison(
        current_user.farm_id,
        date_from=resolved_from,
        date_to=resolved_to,
        compare_from=compare_from,
        compare_to=compare_to,
    )


@router.get(
    "/executive-summary",
    response_model=ExecutiveSummaryResponse,
)
def executive_summary(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("reports.view")),
    ],
    date_from: date | None = None,
    date_to: date | None = None,
    as_of_date: date | None = None,
) -> ExecutiveSummaryResponse:
    resolved_to = date_to or date.today()
    resolved_from = date_from or (resolved_to - timedelta(days=29))

    return AdvancedReportsService(database_session).executive_summary(
        current_user.farm_id,
        date_from=resolved_from,
        date_to=resolved_to,
        as_of_date=as_of_date,
    )


@router.get("/exports/performance.csv")
def export_performance_csv(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("reports.view")),
    ],
    date_from: date | None = None,
    date_to: date | None = None,
) -> Response:
    resolved_to = date_to or date.today()
    resolved_from = date_from or (resolved_to - timedelta(days=29))

    content = AdvancedReportsService(database_session).performance_csv(
        current_user.farm_id,
        date_from=resolved_from,
        date_to=resolved_to,
    )

    return csv_response(
        content,
        (f"poultrypulse-performance-{resolved_from}-to-{resolved_to}.csv"),
    )


@router.get("/exports/trends.csv")
def export_trends_csv(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("reports.view")),
    ],
    date_from: date | None = None,
    date_to: date | None = None,
    metrics: Annotated[
        list[TrendMetric] | None,
        Query(),
    ] = None,
    include_zero_days: bool = True,
) -> Response:
    resolved_to = date_to or date.today()
    resolved_from = date_from or (resolved_to - timedelta(days=29))
    resolved_metrics = metrics or list(TrendMetric)

    content = AdvancedReportsService(database_session).trends_csv(
        current_user.farm_id,
        date_from=resolved_from,
        date_to=resolved_to,
        metrics=resolved_metrics,
        include_zero_days=include_zero_days,
    )

    return csv_response(
        content,
        (f"poultrypulse-trends-{resolved_from}-to-{resolved_to}.csv"),
    )


@router.get("/exports/alerts.csv")
def export_alerts_csv(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("alerts.view")),
    ],
    as_of_date: date | None = None,
) -> Response:
    resolved_date = as_of_date or date.today()

    content = AdvancedReportsService(database_session).alerts_csv(
        current_user.farm_id,
        as_of_date=resolved_date,
    )

    return csv_response(
        content,
        (f"poultrypulse-alerts-{resolved_date}.csv"),
    )
