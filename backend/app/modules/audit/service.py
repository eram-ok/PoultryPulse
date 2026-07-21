from __future__ import annotations

import csv
from io import StringIO
from typing import Any, Mapping
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError
from app.modules.audit.constants import (
    AuditAction,
    AuditOutcome,
    AuditSeverity,
)
from app.modules.audit.context import get_audit_context
from app.modules.audit.models import AuditLog
from app.modules.audit.repository import AuditRepository
from app.modules.audit.sanitizer import (
    calculate_changes,
    sanitize_mapping,
)


class AuditService:
    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session
        self.repository = AuditRepository(database_session)

    def record(
        self,
        *,
        module: str,
        action: AuditAction | str,
        description: str,
        outcome: AuditOutcome | str = (AuditOutcome.SUCCESS),
        severity: AuditSeverity | str = (AuditSeverity.INFO),
        farm_id: UUID | None = None,
        actor_user_id: UUID | None = None,
        actor_username: str | None = None,
        resource_type: str | None = None,
        resource_id: UUID | str | None = None,
        before_values: Mapping[str, Any] | None = None,
        after_values: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        commit: bool = False,
    ) -> AuditLog:
        context = get_audit_context()

        resolved_farm_id = farm_id if farm_id is not None else context.actor_farm_id
        resolved_actor_user_id = (
            actor_user_id if actor_user_id is not None else context.actor_user_id
        )
        resolved_actor_username = (
            actor_username if actor_username is not None else context.actor_username
        )

        sanitized_before = sanitize_mapping(before_values)
        sanitized_after = sanitize_mapping(after_values)

        item = AuditLog(
            farm_id=resolved_farm_id,
            actor_user_id=resolved_actor_user_id,
            actor_username=resolved_actor_username,
            action=(action.value if isinstance(action, AuditAction) else action),
            outcome=(outcome.value if isinstance(outcome, AuditOutcome) else outcome),
            severity=(
                severity.value if isinstance(severity, AuditSeverity) else severity
            ),
            module=module,
            resource_type=resource_type,
            resource_id=(str(resource_id) if resource_id is not None else None),
            description=description,
            request_id=context.request_id,
            request_method=context.request_method,
            request_path=context.request_path,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
            before_values=sanitized_before,
            after_values=sanitized_after,
            changes=calculate_changes(
                sanitized_before,
                sanitized_after,
            ),
            metadata_json=sanitize_mapping(metadata),
            error_code=error_code,
            error_message=error_message,
        )
        self.database_session.add(item)
        self.database_session.flush()

        if commit:
            self.database_session.commit()
            self.database_session.refresh(item)

        return item

    def get(
        self,
        farm_id: UUID,
        audit_id: UUID,
    ) -> AuditLog:
        item = self.repository.get(
            farm_id,
            audit_id,
        )
        if item is None:
            raise ResourceNotFoundError(
                "The selected audit record does not exist.",
                error_code="audit_log_not_found",
            )
        return item

    def export_csv(
        self,
        farm_id: UUID,
        **filters: Any,
    ) -> str:
        items, _ = self.repository.list(
            farm_id,
            offset=0,
            limit=10000,
            **filters,
        )

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "occurred_at",
                "actor_username",
                "actor_user_id",
                "action",
                "outcome",
                "severity",
                "module",
                "resource_type",
                "resource_id",
                "description",
                "request_id",
                "request_method",
                "request_path",
                "ip_address",
                "error_code",
                "error_message",
            ]
        )

        for item in items:
            writer.writerow(
                [
                    item.occurred_at.isoformat(),
                    item.actor_username,
                    item.actor_user_id,
                    item.action,
                    item.outcome,
                    item.severity,
                    item.module,
                    item.resource_type,
                    item.resource_id,
                    item.description,
                    item.request_id,
                    item.request_method,
                    item.request_path,
                    item.ip_address,
                    item.error_code,
                    item.error_message,
                ]
            )

        return output.getvalue()
