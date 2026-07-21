from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_database_session
from app.modules.audit.constants import (
    AuditAction,
    AuditOutcome,
    AuditSeverity,
)
from app.modules.audit.repository import AuditRepository
from app.modules.audit.schemas import (
    AuditLogListResponse,
    AuditLogResponse,
    AuditSummaryResponse,
)
from app.modules.audit.service import AuditService
from app.modules.auth.dependencies import require_permissions
from app.modules.users.models import User


router = APIRouter(
    prefix="/audit",
    tags=["Audit Trail and Activity Monitoring"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


@router.get(
    "/summary",
    response_model=AuditSummaryResponse,
)
def audit_summary(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("audit.view")),
    ],
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> AuditSummaryResponse:
    values = AuditRepository(database_session).summary(
        current_user.farm_id,
        date_from=date_from,
        date_to=date_to,
    )
    return AuditSummaryResponse(**values)


@router.get(
    "/export.csv",
    response_class=Response,
)
def export_audit_csv(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("audit.export")),
    ],
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    action: AuditAction | None = None,
    outcome: AuditOutcome | None = None,
    severity: AuditSeverity | None = None,
    module: str | None = None,
    actor_user_id: UUID | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    request_id: str | None = None,
    search: str | None = None,
) -> Response:
    content = AuditService(database_session).export_csv(
        current_user.farm_id,
        date_from=date_from,
        date_to=date_to,
        action=action.value if action else None,
        outcome=outcome.value if outcome else None,
        severity=severity.value if severity else None,
        module=module,
        actor_user_id=actor_user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        request_id=request_id,
        search=search,
    )
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": ('attachment; filename="poultrypulse-audit.csv"')
        },
    )


@router.get(
    "",
    response_model=AuditLogListResponse,
)
def list_audit_logs(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("audit.view")),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    action: AuditAction | None = None,
    outcome: AuditOutcome | None = None,
    severity: AuditSeverity | None = None,
    module: Annotated[
        str | None,
        Query(max_length=80),
    ] = None,
    actor_user_id: UUID | None = None,
    resource_type: Annotated[
        str | None,
        Query(max_length=120),
    ] = None,
    resource_id: Annotated[
        str | None,
        Query(max_length=120),
    ] = None,
    request_id: Annotated[
        str | None,
        Query(max_length=64),
    ] = None,
    search: Annotated[
        str | None,
        Query(min_length=1, max_length=150),
    ] = None,
) -> AuditLogListResponse:
    items, total = AuditRepository(database_session).list(
        current_user.farm_id,
        offset=offset,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        action=action.value if action else None,
        outcome=outcome.value if outcome else None,
        severity=severity.value if severity else None,
        module=module,
        actor_user_id=actor_user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        request_id=request_id,
        search=search,
    )
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{audit_id}",
    response_model=AuditLogResponse,
)
def get_audit_log(
    audit_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("audit.view")),
    ],
) -> AuditLogResponse:
    item = AuditService(database_session).get(
        current_user.farm_id,
        audit_id,
    )
    return AuditLogResponse.model_validate(item)
