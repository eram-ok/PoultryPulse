from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditLog


class AuditRepository:
    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session

    def get(
        self,
        farm_id: UUID,
        audit_id: UUID,
    ) -> AuditLog | None:
        return self.database_session.scalar(
            select(AuditLog).where(
                AuditLog.farm_id == farm_id,
                AuditLog.id == audit_id,
            )
        )

    def list(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        date_from: datetime | None,
        date_to: datetime | None,
        action: str | None,
        outcome: str | None,
        severity: str | None,
        module: str | None,
        actor_user_id: UUID | None,
        resource_type: str | None,
        resource_id: str | None,
        request_id: str | None,
        search: str | None,
    ) -> tuple[list[AuditLog], int]:
        conditions = [AuditLog.farm_id == farm_id]

        if date_from is not None:
            conditions.append(AuditLog.occurred_at >= date_from)
        if date_to is not None:
            conditions.append(AuditLog.occurred_at <= date_to)
        if action is not None:
            conditions.append(AuditLog.action == action)
        if outcome is not None:
            conditions.append(AuditLog.outcome == outcome)
        if severity is not None:
            conditions.append(AuditLog.severity == severity)
        if module is not None:
            conditions.append(AuditLog.module == module)
        if actor_user_id is not None:
            conditions.append(AuditLog.actor_user_id == actor_user_id)
        if resource_type is not None:
            conditions.append(AuditLog.resource_type == resource_type)
        if resource_id is not None:
            conditions.append(AuditLog.resource_id == resource_id)
        if request_id is not None:
            conditions.append(AuditLog.request_id == request_id)
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(
                or_(
                    AuditLog.description.ilike(pattern),
                    AuditLog.actor_username.ilike(pattern),
                    AuditLog.module.ilike(pattern),
                    AuditLog.resource_type.ilike(pattern),
                    AuditLog.resource_id.ilike(pattern),
                    AuditLog.error_code.ilike(pattern),
                    AuditLog.error_message.ilike(pattern),
                )
            )

        statement = (
            select(AuditLog)
            .where(*conditions)
            .order_by(
                AuditLog.occurred_at.desc(),
                AuditLog.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        count_statement = select(func.count(AuditLog.id)).where(*conditions)

        items = list(self.database_session.scalars(statement).all())
        total = int(self.database_session.scalar(count_statement) or 0)
        return items, total

    def summary(
        self,
        farm_id: UUID,
        *,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> dict[str, int]:
        conditions = [AuditLog.farm_id == farm_id]
        if date_from is not None:
            conditions.append(AuditLog.occurred_at >= date_from)
        if date_to is not None:
            conditions.append(AuditLog.occurred_at <= date_to)

        total = int(
            self.database_session.scalar(
                select(func.count(AuditLog.id)).where(*conditions)
            )
            or 0
        )
        successful = int(
            self.database_session.scalar(
                select(func.count(AuditLog.id)).where(
                    *conditions,
                    AuditLog.outcome == "SUCCESS",
                )
            )
            or 0
        )
        failed = int(
            self.database_session.scalar(
                select(func.count(AuditLog.id)).where(
                    *conditions,
                    AuditLog.outcome.in_(("FAILURE", "DENIED")),
                )
            )
            or 0
        )
        critical = int(
            self.database_session.scalar(
                select(func.count(AuditLog.id)).where(
                    *conditions,
                    AuditLog.severity == "CRITICAL",
                )
            )
            or 0
        )
        unique_actors = int(
            self.database_session.scalar(
                select(func.count(func.distinct(AuditLog.actor_user_id))).where(
                    *conditions,
                    AuditLog.actor_user_id.is_not(None),
                )
            )
            or 0
        )

        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "critical": critical,
            "unique_actors": unique_actors,
        }
