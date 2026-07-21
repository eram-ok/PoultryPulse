from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.alerts.delivery_models import (
    AlertEvent,
    NotificationDelivery,
)
from app.modules.alerts.models import (
    AlertRefreshRun,
    AlertUserState,
    NotificationPreference,
    OperationalAlert,
)
from app.modules.users.models import User


class AlertsRepository:
    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session

    def get_alert(
        self,
        farm_id: UUID,
        alert_id: UUID,
        *,
        for_update: bool = False,
    ) -> OperationalAlert | None:
        statement = select(OperationalAlert).where(
            OperationalAlert.farm_id == farm_id,
            OperationalAlert.id == alert_id,
        )
        if for_update:
            statement = statement.with_for_update()
        return self.database_session.scalar(statement)

    def get_alert_by_fingerprint(
        self,
        farm_id: UUID,
        fingerprint: str,
        *,
        for_update: bool = False,
    ) -> OperationalAlert | None:
        statement = select(OperationalAlert).where(
            OperationalAlert.farm_id == farm_id,
            OperationalAlert.fingerprint == fingerprint,
        )
        if for_update:
            statement = statement.with_for_update()
        return self.database_session.scalar(statement)

    def list_alerts(
        self,
        farm_id: UUID,
        user_id: UUID,
        *,
        offset: int,
        limit: int,
        status: str | None,
        severity: str | None,
        alert_type: str | None,
        assigned_to: UUID | None,
        assigned_to_me: bool,
        unread_only: bool,
        include_dismissed: bool,
        search: str | None,
    ) -> tuple[
        list[tuple[OperationalAlert, AlertUserState | None]],
        int,
    ]:
        conditions = [OperationalAlert.farm_id == farm_id]

        if status is not None:
            conditions.append(OperationalAlert.status == status)
        if severity is not None:
            conditions.append(OperationalAlert.severity == severity)
        if alert_type is not None:
            conditions.append(OperationalAlert.alert_type == alert_type)
        if assigned_to is not None:
            conditions.append(OperationalAlert.assigned_to == assigned_to)
        if assigned_to_me:
            conditions.append(OperationalAlert.assigned_to == user_id)
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(
                or_(
                    OperationalAlert.title.ilike(pattern),
                    OperationalAlert.message.ilike(pattern),
                    OperationalAlert.source_module.ilike(pattern),
                )
            )

        state_join = (AlertUserState.alert_id == OperationalAlert.id) & (
            AlertUserState.user_id == user_id
        )

        if unread_only:
            conditions.append(
                or_(
                    AlertUserState.id.is_(None),
                    AlertUserState.is_read.is_(False),
                )
            )
        if not include_dismissed:
            conditions.append(
                or_(
                    AlertUserState.id.is_(None),
                    AlertUserState.is_dismissed.is_(False),
                )
            )

        statement = (
            select(OperationalAlert, AlertUserState)
            .outerjoin(AlertUserState, state_join)
            .where(*conditions)
            .order_by(
                OperationalAlert.severity.desc(),
                OperationalAlert.last_detected_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        count_statement = (
            select(func.count(OperationalAlert.id))
            .outerjoin(AlertUserState, state_join)
            .where(*conditions)
        )

        rows = list(self.database_session.execute(statement).all())
        total = int(self.database_session.scalar(count_statement) or 0)
        return rows, total

    def alert_counts(
        self,
        farm_id: UUID,
        user_id: UUID,
    ) -> dict[str, int]:
        active_statuses = ("OPEN", "ACKNOWLEDGED")
        state_join = (AlertUserState.alert_id == OperationalAlert.id) & (
            AlertUserState.user_id == user_id
        )

        total_active = int(
            self.database_session.scalar(
                select(func.count(OperationalAlert.id)).where(
                    OperationalAlert.farm_id == farm_id,
                    OperationalAlert.status.in_(active_statuses),
                )
            )
            or 0
        )
        unread = int(
            self.database_session.scalar(
                select(func.count(OperationalAlert.id))
                .outerjoin(
                    AlertUserState,
                    state_join,
                )
                .where(
                    OperationalAlert.farm_id == farm_id,
                    OperationalAlert.status.in_(active_statuses),
                    or_(
                        AlertUserState.id.is_(None),
                        AlertUserState.is_read.is_(False),
                    ),
                    or_(
                        AlertUserState.id.is_(None),
                        AlertUserState.is_dismissed.is_(False),
                    ),
                )
            )
            or 0
        )
        open_count = int(
            self.database_session.scalar(
                select(func.count(OperationalAlert.id)).where(
                    OperationalAlert.farm_id == farm_id,
                    OperationalAlert.status == "OPEN",
                )
            )
            or 0
        )
        acknowledged = int(
            self.database_session.scalar(
                select(func.count(OperationalAlert.id)).where(
                    OperationalAlert.farm_id == farm_id,
                    OperationalAlert.status == "ACKNOWLEDGED",
                )
            )
            or 0
        )
        critical = int(
            self.database_session.scalar(
                select(func.count(OperationalAlert.id)).where(
                    OperationalAlert.farm_id == farm_id,
                    OperationalAlert.status.in_(active_statuses),
                    OperationalAlert.severity == "CRITICAL",
                )
            )
            or 0
        )
        assigned_to_me = int(
            self.database_session.scalar(
                select(func.count(OperationalAlert.id)).where(
                    OperationalAlert.farm_id == farm_id,
                    OperationalAlert.status.in_(active_statuses),
                    OperationalAlert.assigned_to == user_id,
                )
            )
            or 0
        )

        return {
            "total_active": total_active,
            "unread": unread,
            "open": open_count,
            "acknowledged": acknowledged,
            "critical": critical,
            "assigned_to_me": assigned_to_me,
        }

    def active_users(
        self,
        farm_id: UUID,
    ) -> list[User]:
        return list(
            self.database_session.scalars(
                select(User).where(
                    User.farm_id == farm_id,
                    User.is_active.is_(True),
                )
            ).all()
        )

    def get_user(
        self,
        farm_id: UUID,
        user_id: UUID,
    ) -> User | None:
        return self.database_session.scalar(
            select(User).where(
                User.farm_id == farm_id,
                User.id == user_id,
            )
        )

    def get_state(
        self,
        farm_id: UUID,
        alert_id: UUID,
        user_id: UUID,
    ) -> AlertUserState | None:
        return self.database_session.scalar(
            select(AlertUserState).where(
                AlertUserState.farm_id == farm_id,
                AlertUserState.alert_id == alert_id,
                AlertUserState.user_id == user_id,
            )
        )

    def get_or_create_state(
        self,
        farm_id: UUID,
        alert_id: UUID,
        user_id: UUID,
    ) -> AlertUserState:
        state = self.get_state(
            farm_id,
            alert_id,
            user_id,
        )
        if state is None:
            state = AlertUserState(
                farm_id=farm_id,
                alert_id=alert_id,
                user_id=user_id,
                is_read=False,
                is_dismissed=False,
            )
            self.database_session.add(state)
            self.database_session.flush()
        return state

    def preference(
        self,
        farm_id: UUID,
        user_id: UUID,
        alert_type: str,
        channel: str,
    ) -> NotificationPreference | None:
        return self.database_session.scalar(
            select(NotificationPreference).where(
                NotificationPreference.farm_id == farm_id,
                NotificationPreference.user_id == user_id,
                NotificationPreference.alert_type == alert_type,
                NotificationPreference.channel == channel,
            )
        )

    def list_preferences(
        self,
        farm_id: UUID,
        user_id: UUID,
    ) -> list[NotificationPreference]:
        return list(
            self.database_session.scalars(
                select(NotificationPreference)
                .where(
                    NotificationPreference.farm_id == farm_id,
                    NotificationPreference.user_id == user_id,
                )
                .order_by(
                    NotificationPreference.alert_type,
                    NotificationPreference.channel,
                )
            ).all()
        )

    def active_alerts_not_detected(
        self,
        farm_id: UUID,
        fingerprints: set[str],
    ) -> list[OperationalAlert]:
        conditions = [
            OperationalAlert.farm_id == farm_id,
            OperationalAlert.status.in_(("OPEN", "ACKNOWLEDGED")),
        ]
        if fingerprints:
            conditions.append(~OperationalAlert.fingerprint.in_(fingerprints))

        return list(
            self.database_session.scalars(
                select(OperationalAlert).where(*conditions)
            ).all()
        )

    def add_event(
        self,
        *,
        farm_id: UUID,
        alert_id: UUID,
        event_type: str,
        actor_user_id: UUID | None = None,
        from_status: str | None = None,
        to_status: str | None = None,
        notes: str | None = None,
    ) -> AlertEvent:
        event = AlertEvent(
            farm_id=farm_id,
            alert_id=alert_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            from_status=from_status,
            to_status=to_status,
            notes=notes,
        )
        self.database_session.add(event)
        return event

    def list_events(
        self,
        farm_id: UUID,
        alert_id: UUID,
    ) -> list[AlertEvent]:
        return list(
            self.database_session.scalars(
                select(AlertEvent)
                .where(
                    AlertEvent.farm_id == farm_id,
                    AlertEvent.alert_id == alert_id,
                )
                .order_by(AlertEvent.created_at.asc())
            ).all()
        )

    def add_delivery(
        self,
        delivery: NotificationDelivery,
    ) -> NotificationDelivery:
        self.database_session.add(delivery)
        return delivery

    def get_delivery(
        self,
        farm_id: UUID,
        delivery_id: UUID,
        *,
        for_update: bool = False,
    ) -> NotificationDelivery | None:
        statement = select(NotificationDelivery).where(
            NotificationDelivery.farm_id == farm_id,
            NotificationDelivery.id == delivery_id,
        )
        if for_update:
            statement = statement.with_for_update()
        return self.database_session.scalar(statement)

    def list_deliveries(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
        status: str | None,
        channel: str | None,
        alert_id: UUID | None,
        user_id: UUID | None,
    ) -> tuple[list[NotificationDelivery], int]:
        conditions = [NotificationDelivery.farm_id == farm_id]
        if status is not None:
            conditions.append(NotificationDelivery.status == status)
        if channel is not None:
            conditions.append(NotificationDelivery.channel == channel)
        if alert_id is not None:
            conditions.append(NotificationDelivery.alert_id == alert_id)
        if user_id is not None:
            conditions.append(NotificationDelivery.user_id == user_id)

        records = (
            select(NotificationDelivery)
            .where(*conditions)
            .order_by(NotificationDelivery.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_statement = select(func.count(NotificationDelivery.id)).where(*conditions)

        return (
            list(self.database_session.scalars(records).all()),
            int(self.database_session.scalar(count_statement) or 0),
        )

    def pending_deliveries(
        self,
        farm_id: UUID,
        *,
        now: datetime,
        limit: int,
    ) -> list[NotificationDelivery]:
        return list(
            self.database_session.scalars(
                select(NotificationDelivery)
                .where(
                    NotificationDelivery.farm_id == farm_id,
                    or_(
                        NotificationDelivery.status == "PENDING",
                        (NotificationDelivery.status == "FAILED")
                        & (
                            NotificationDelivery.attempt_count
                            < NotificationDelivery.max_attempts
                        )
                        & (
                            or_(
                                NotificationDelivery.next_attempt_at.is_(None),
                                NotificationDelivery.next_attempt_at <= now,
                            )
                        ),
                    ),
                )
                .order_by(NotificationDelivery.created_at.asc())
                .limit(limit)
                .with_for_update(skip_locked=True)
            ).all()
        )

    def add_refresh_run(
        self,
        run: AlertRefreshRun,
    ) -> AlertRefreshRun:
        self.database_session.add(run)
        return run
