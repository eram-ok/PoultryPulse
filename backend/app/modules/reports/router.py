from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_database_session
from app.modules.auth.dependencies import require_permissions
from app.modules.reports.constants import TrendMetric
from app.modules.reports.schemas import (
    DashboardResponse,
    OperationalAlertListResponse,
    PerformanceSummaryResponse,
    TrendReportResponse,
)
from app.modules.reports.service import ReportsService
from app.modules.users.models import User


router = APIRouter(
    prefix="/reports",
    tags=["Dashboard, Analytics and Alerts"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
)
def dashboard(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("dashboard.view")),
    ],
    as_of_date: date | None = None,
) -> DashboardResponse:
    return ReportsService(database_session).dashboard(
        current_user.farm_id,
        as_of_date=as_of_date,
    )


@router.get(
    "/alerts",
    response_model=OperationalAlertListResponse,
)
def operational_alerts(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("alerts.view")),
    ],
    as_of_date: date | None = None,
) -> OperationalAlertListResponse:
    return ReportsService(database_session).alerts(
        current_user.farm_id,
        today=as_of_date,
    )


@router.get(
    "/performance",
    response_model=PerformanceSummaryResponse,
)
def performance(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("reports.view")),
    ],
    date_from: date | None = None,
    date_to: date | None = None,
) -> PerformanceSummaryResponse:
    resolved_to = date_to or date.today()
    resolved_from = date_from or (resolved_to - timedelta(days=29))

    return ReportsService(database_session).performance(
        current_user.farm_id,
        date_from=resolved_from,
        date_to=resolved_to,
    )


@router.get(
    "/trends",
    response_model=TrendReportResponse,
)
def trends(
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
) -> TrendReportResponse:
    resolved_to = date_to or date.today()
    resolved_from = date_from or (resolved_to - timedelta(days=29))
    resolved_metrics = metrics or list(TrendMetric)

    return ReportsService(database_session).trends(
        current_user.farm_id,
        date_from=resolved_from,
        date_to=resolved_to,
        metrics=resolved_metrics,
        include_zero_days=include_zero_days,
    )
