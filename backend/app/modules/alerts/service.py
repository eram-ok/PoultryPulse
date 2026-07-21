from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
import hashlib
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BusinessRuleError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.modules.alerts.config import NotificationSettings
from app.modules.alerts.constants import (
    AlertDeliveryChannel,
    AlertRefreshStatus,
    AlertStatus,
)
from app.modules.alerts.delivery_constants import (
    AlertEventType,
    NotificationDeliveryStatus,
)
from app.modules.alerts.delivery_models import (
    NotificationDelivery,
)
from app.modules.alerts.models import (
    AlertRefreshRun,
    NotificationPreference,
    OperationalAlert,
)
from app.modules.alerts.repository import AlertsRepository
from app.modules.alerts.schemas import (
    AlertRefreshResponse,
    DeliveryProcessResponse,
)
from app.modules.alerts.transports import (
    EmailTransport,
    SmsTransport,
)
from app.modules.reports.constants import AlertSeverity
from app.modules.reports.schemas import (
    OperationalAlertResponse,
)
from app.modules.reports.service import ReportsService
from app.modules.users.models import User


SEVERITY_RANK = {
    AlertSeverity.INFO.value: 1,
    AlertSeverity.WARNING.value: 2,
    AlertSeverity.CRITICAL.value: 3,
}


class AlertsService:
    def __init__(
        self,
        database_session: Session,
        settings: NotificationSettings | None = None,
    ) -> None:
        self.database_session = database_session
        self.repository = AlertsRepository(database_session)
        self.settings = settings or NotificationSettings.from_environment()

    @staticmethod
    def fingerprint(
        item: OperationalAlertResponse,
    ) -> str:
        source_key = (
            str(item.source_id)
            if item.source_id is not None
            else item.title.strip().lower()
        )
        raw = f"{item.alert_type.value}|{item.source_module}|{source_key}"
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]
        return f"{item.alert_type.value}:{item.source_module}:{digest}"

    def _alert(
        self,
        farm_id: UUID,
        alert_id: UUID,
        *,
        for_update: bool = False,
    ) -> OperationalAlert:
        alert = self.repository.get_alert(
            farm_id,
            alert_id,
            for_update=for_update,
        )
        if alert is None:
            raise ResourceNotFoundError(
                "The selected alert does not exist.",
                error_code="alert_not_found",
            )
        return alert

    def _delivery(
        self,
        farm_id: UUID,
        delivery_id: UUID,
        *,
        for_update: bool = False,
    ) -> NotificationDelivery:
        delivery = self.repository.get_delivery(
            farm_id,
            delivery_id,
            for_update=for_update,
        )
        if delivery is None:
            raise ResourceNotFoundError(
                "The selected notification delivery does not exist.",
                error_code="notification_delivery_not_found",
            )
        return delivery

    def _commit(
        self,
        message: str,
        error_code: str,
    ) -> None:
        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()
            raise ResourceConflictError(
                message,
                error_code=error_code,
            ) from exc

    @staticmethod
    def _default_preference(
        user: User,
        *,
        channel: str,
    ) -> tuple[bool, str]:
        if channel == AlertDeliveryChannel.IN_APP.value:
            return True, AlertSeverity.INFO.value
        if channel == AlertDeliveryChannel.EMAIL.value:
            return bool(user.email), AlertSeverity.WARNING.value
        return bool(user.telephone), AlertSeverity.CRITICAL.value

    def _preference(
        self,
        *,
        farm_id: UUID,
        user: User,
        alert_type: str,
        channel: str,
    ) -> NotificationPreference:
        preference = self.repository.preference(
            farm_id,
            user.id,
            alert_type,
            channel,
        )
        if preference is not None:
            return preference

        enabled, minimum_severity = self._default_preference(
            user,
            channel=channel,
        )
        preference = NotificationPreference(
            farm_id=farm_id,
            user_id=user.id,
            alert_type=alert_type,
            channel=channel,
            minimum_severity=minimum_severity,
            is_enabled=enabled,
        )
        self.database_session.add(preference)
        self.database_session.flush()
        return preference

    @staticmethod
    def _severity_allowed(
        alert_severity: str,
        minimum_severity: str,
    ) -> bool:
        return SEVERITY_RANK[alert_severity] >= SEVERITY_RANK[minimum_severity]

    @staticmethod
    def _destination(
        user: User,
        channel: str,
    ) -> str | None:
        if channel == AlertDeliveryChannel.IN_APP.value:
            return str(user.id)
        if channel == AlertDeliveryChannel.EMAIL.value:
            return user.email
        return user.telephone

    @staticmethod
    def _message_body(
        alert: OperationalAlert,
    ) -> str:
        return (
            f"{alert.title}\n\n"
            f"{alert.message}\n\n"
            f"Severity: {alert.severity}\n"
            f"Status: {alert.status}\n"
            f"Source: {alert.source_module}\n"
            "Open PoultryPulse to review and act."
        )

    def _queue_notifications(
        self,
        alert: OperationalAlert,
    ) -> int:
        queued = 0
        users = self.repository.active_users(alert.farm_id)

        for user in users:
            for channel in AlertDeliveryChannel:
                preference = self._preference(
                    farm_id=alert.farm_id,
                    user=user,
                    alert_type=alert.alert_type,
                    channel=channel.value,
                )

                if not preference.is_enabled or not self._severity_allowed(
                    alert.severity,
                    preference.minimum_severity,
                ):
                    continue

                destination = self._destination(
                    user,
                    channel.value,
                )

                if channel == AlertDeliveryChannel.IN_APP:
                    self.repository.get_or_create_state(
                        alert.farm_id,
                        alert.id,
                        user.id,
                    )

                delivery = NotificationDelivery(
                    farm_id=alert.farm_id,
                    alert_id=alert.id,
                    user_id=user.id,
                    channel=channel.value,
                    destination=destination,
                    status=(
                        NotificationDeliveryStatus.SENT.value
                        if channel == AlertDeliveryChannel.IN_APP
                        else NotificationDeliveryStatus.PENDING.value
                    ),
                    subject=(f"[{alert.severity}] {alert.title}"),
                    body=self._message_body(alert),
                    attempt_count=(1 if channel == AlertDeliveryChannel.IN_APP else 0),
                    max_attempts=(self.settings.max_delivery_attempts),
                    provider_name=(
                        "in_app" if channel == AlertDeliveryChannel.IN_APP else None
                    ),
                    sent_at=(
                        datetime.now(UTC)
                        if channel == AlertDeliveryChannel.IN_APP
                        else None
                    ),
                )
                self.repository.add_delivery(delivery)
                queued += 1

                self.repository.add_event(
                    farm_id=alert.farm_id,
                    alert_id=alert.id,
                    event_type=(AlertEventType.DELIVERY_QUEUED.value),
                    notes=(f"{channel.value} notification queued for user {user.id}."),
                )

        return queued

    def refresh(
        self,
        farm_id: UUID,
        requested_by: UUID,
        *,
        as_of_date: date | None,
        send_now: bool,
    ) -> AlertRefreshResponse:
        current_date = as_of_date or date.today()
        now = datetime.now(UTC)
        run = AlertRefreshRun(
            farm_id=farm_id,
            requested_by=requested_by,
            status=AlertRefreshStatus.RUNNING.value,
            started_at=now,
        )
        self.repository.add_refresh_run(run)
        self.database_session.flush()

        detected_count = 0
        created_count = 0
        updated_count = 0
        resolved_count = 0
        deliveries_queued = 0

        try:
            dynamic = ReportsService(self.database_session).alerts(
                farm_id,
                today=current_date,
            )
            active_fingerprints: set[str] = set()

            for item in dynamic.items:
                detected_count += 1
                fingerprint = self.fingerprint(item)
                active_fingerprints.add(fingerprint)

                existing = self.repository.get_alert_by_fingerprint(
                    farm_id,
                    fingerprint,
                    for_update=True,
                )

                if existing is None:
                    alert = OperationalAlert(
                        farm_id=farm_id,
                        fingerprint=fingerprint,
                        alert_type=item.alert_type.value,
                        severity=item.severity.value,
                        status=AlertStatus.OPEN.value,
                        title=item.title,
                        message=item.message,
                        source_module=item.source_module,
                        source_id=item.source_id,
                        action_path=item.action_path,
                        first_detected_at=now,
                        last_detected_at=now,
                        occurrence_count=1,
                    )
                    self.database_session.add(alert)
                    self.database_session.flush()
                    created_count += 1
                    should_notify = True
                    self.repository.add_event(
                        farm_id=farm_id,
                        alert_id=alert.id,
                        event_type=(AlertEventType.CREATED.value),
                        actor_user_id=requested_by,
                        to_status=AlertStatus.OPEN.value,
                        notes=("Alert created by operational refresh."),
                    )
                else:
                    alert = existing
                    previous_status = alert.status
                    previous_severity = alert.severity
                    was_resolved = alert.status == AlertStatus.RESOLVED.value
                    severity_escalated = (
                        SEVERITY_RANK[item.severity.value]
                        > SEVERITY_RANK[previous_severity]
                    )

                    alert.alert_type = item.alert_type.value
                    alert.severity = item.severity.value
                    alert.title = item.title
                    alert.message = item.message
                    alert.source_module = item.source_module
                    alert.source_id = item.source_id
                    alert.action_path = item.action_path
                    alert.last_detected_at = now
                    alert.occurrence_count += 1

                    if was_resolved:
                        alert.status = AlertStatus.OPEN.value
                        alert.resolved_by = None
                        alert.resolved_at = None
                        alert.resolution_notes = None
                        self.repository.add_event(
                            farm_id=farm_id,
                            alert_id=alert.id,
                            event_type=(AlertEventType.REOPENED.value),
                            actor_user_id=requested_by,
                            from_status=previous_status,
                            to_status=(AlertStatus.OPEN.value),
                            notes=("Condition was detected again."),
                        )
                    else:
                        self.repository.add_event(
                            farm_id=farm_id,
                            alert_id=alert.id,
                            event_type=(AlertEventType.UPDATED.value),
                            actor_user_id=requested_by,
                            from_status=previous_status,
                            to_status=alert.status,
                            notes=("Alert refreshed from current operational data."),
                        )

                    updated_count += 1
                    should_notify = was_resolved or severity_escalated

                if should_notify:
                    deliveries_queued += self._queue_notifications(alert)

            for alert in self.repository.active_alerts_not_detected(
                farm_id,
                active_fingerprints,
            ):
                previous_status = alert.status
                alert.status = AlertStatus.RESOLVED.value
                alert.resolved_at = now
                alert.resolution_notes = (
                    "Automatically resolved because the condition is no longer active."
                )
                self.repository.add_event(
                    farm_id=farm_id,
                    alert_id=alert.id,
                    event_type=(AlertEventType.AUTO_RESOLVED.value),
                    actor_user_id=requested_by,
                    from_status=previous_status,
                    to_status=AlertStatus.RESOLVED.value,
                    notes=alert.resolution_notes,
                )
                resolved_count += 1

            run.status = AlertRefreshStatus.COMPLETED.value
            run.completed_at = datetime.now(UTC)
            run.detected_count = detected_count
            run.created_count = created_count
            run.updated_count = updated_count
            run.resolved_count = resolved_count
            self.database_session.commit()
        except Exception as exc:
            self.database_session.rollback()
            self.repository.add_refresh_run(
                AlertRefreshRun(
                    farm_id=farm_id,
                    requested_by=requested_by,
                    status=AlertRefreshStatus.FAILED.value,
                    started_at=now,
                    completed_at=datetime.now(UTC),
                    error_message=str(exc),
                )
            )
            self.database_session.commit()
            raise BusinessRuleError(
                "Operational alert refresh failed.",
                error_code="alert_refresh_failed",
            ) from exc

        process_result = DeliveryProcessResponse(
            processed=0,
            sent=0,
            failed=0,
            skipped=0,
        )
        if send_now:
            process_result = self.process_deliveries(
                farm_id,
                actor_user_id=requested_by,
                limit=500,
            )

        return AlertRefreshResponse(
            run_id=run.id,
            detected_count=detected_count,
            created_count=created_count,
            updated_count=updated_count,
            resolved_count=resolved_count,
            deliveries_queued=deliveries_queued,
            deliveries_sent=process_result.sent,
            deliveries_failed=process_result.failed,
        )

    def _dispatch_delivery(
        self,
        delivery: NotificationDelivery,
        *,
        actor_user_id: UUID | None,
    ) -> str:
        now = datetime.now(UTC)
        delivery.attempt_count += 1

        if not delivery.destination:
            delivery.status = NotificationDeliveryStatus.SKIPPED.value
            delivery.last_error = (
                "The user has no destination configured for this notification channel."
            )
            return "SKIPPED"

        if delivery.channel == AlertDeliveryChannel.IN_APP.value:
            delivery.status = NotificationDeliveryStatus.SENT.value
            delivery.provider_name = "in_app"
            delivery.sent_at = now
            return "SENT"

        if delivery.channel == AlertDeliveryChannel.EMAIL.value:
            transport = EmailTransport(self.settings)
            delivery.provider_name = transport.provider_name
            result = transport.send(
                destination=delivery.destination,
                subject=delivery.subject,
                body=delivery.body,
            )
        else:
            transport = SmsTransport(self.settings)
            delivery.provider_name = transport.provider_name
            result = transport.send(
                destination=delivery.destination,
                body=delivery.body,
            )

        if result.success:
            delivery.status = NotificationDeliveryStatus.SENT.value
            delivery.provider_message_id = result.provider_message_id
            delivery.last_error = None
            delivery.next_attempt_at = None
            delivery.sent_at = now
            self.repository.add_event(
                farm_id=delivery.farm_id,
                alert_id=delivery.alert_id,
                event_type=(AlertEventType.DELIVERY_SENT.value),
                actor_user_id=actor_user_id,
                notes=(
                    f"{delivery.channel} notification sent to {delivery.destination}."
                ),
            )
            return "SENT"

        delivery.status = NotificationDeliveryStatus.FAILED.value
        delivery.last_error = result.error
        if delivery.attempt_count < delivery.max_attempts:
            delivery.next_attempt_at = now + timedelta(
                minutes=(self.settings.retry_delay_minutes)
            )
        else:
            delivery.next_attempt_at = None

        self.repository.add_event(
            farm_id=delivery.farm_id,
            alert_id=delivery.alert_id,
            event_type=(AlertEventType.DELIVERY_FAILED.value),
            actor_user_id=actor_user_id,
            notes=(f"{delivery.channel} delivery failed: {result.error}"),
        )
        return "FAILED"

    def process_deliveries(
        self,
        farm_id: UUID,
        *,
        actor_user_id: UUID | None,
        limit: int,
    ) -> DeliveryProcessResponse:
        deliveries = self.repository.pending_deliveries(
            farm_id,
            now=datetime.now(UTC),
            limit=limit,
        )

        sent = 0
        failed = 0
        skipped = 0

        for delivery in deliveries:
            outcome = self._dispatch_delivery(
                delivery,
                actor_user_id=actor_user_id,
            )
            if outcome == "SENT":
                sent += 1
            elif outcome == "SKIPPED":
                skipped += 1
            else:
                failed += 1

        self.database_session.commit()
        return DeliveryProcessResponse(
            processed=len(deliveries),
            sent=sent,
            failed=failed,
            skipped=skipped,
        )

    def retry_delivery(
        self,
        farm_id: UUID,
        delivery_id: UUID,
        actor_user_id: UUID,
    ) -> NotificationDelivery:
        delivery = self._delivery(
            farm_id,
            delivery_id,
            for_update=True,
        )
        if delivery.status == (NotificationDeliveryStatus.SENT.value):
            raise ResourceConflictError(
                "A sent notification cannot be retried.",
                error_code="notification_already_sent",
            )

        delivery.status = NotificationDeliveryStatus.PENDING.value
        delivery.next_attempt_at = None
        delivery.last_error = None
        if delivery.attempt_count >= delivery.max_attempts:
            delivery.max_attempts = delivery.attempt_count + 1

        self.repository.add_event(
            farm_id=farm_id,
            alert_id=delivery.alert_id,
            event_type=(AlertEventType.DELIVERY_RETRIED.value),
            actor_user_id=actor_user_id,
            notes=(f"{delivery.channel} delivery manually queued for retry."),
        )
        self.database_session.commit()
        return delivery

    def mark_read(
        self,
        farm_id: UUID,
        alert_id: UUID,
        user_id: UUID,
        *,
        is_read: bool,
    ) -> OperationalAlert:
        alert = self._alert(farm_id, alert_id)
        state = self.repository.get_or_create_state(
            farm_id,
            alert_id,
            user_id,
        )
        state.is_read = is_read
        state.read_at = datetime.now(UTC) if is_read else None
        self.repository.add_event(
            farm_id=farm_id,
            alert_id=alert_id,
            event_type=(
                AlertEventType.MARKED_READ.value
                if is_read
                else AlertEventType.MARKED_UNREAD.value
            ),
            actor_user_id=user_id,
        )
        self.database_session.commit()
        return alert

    def dismiss(
        self,
        farm_id: UUID,
        alert_id: UUID,
        user_id: UUID,
        *,
        dismissed: bool,
    ) -> OperationalAlert:
        alert = self._alert(farm_id, alert_id)
        state = self.repository.get_or_create_state(
            farm_id,
            alert_id,
            user_id,
        )
        state.is_dismissed = dismissed
        state.dismissed_at = datetime.now(UTC) if dismissed else None
        self.repository.add_event(
            farm_id=farm_id,
            alert_id=alert_id,
            event_type=(
                AlertEventType.DISMISSED.value
                if dismissed
                else AlertEventType.RESTORED.value
            ),
            actor_user_id=user_id,
        )
        self.database_session.commit()
        return alert

    def assign(
        self,
        farm_id: UUID,
        alert_id: UUID,
        actor_user_id: UUID,
        assigned_to: UUID | None,
        notes: str | None,
    ) -> OperationalAlert:
        alert = self._alert(
            farm_id,
            alert_id,
            for_update=True,
        )
        if assigned_to is not None:
            target = self.repository.get_user(
                farm_id,
                assigned_to,
            )
            if target is None or not target.is_active:
                raise ResourceNotFoundError(
                    "The selected assignee does not exist or is inactive.",
                    error_code="alert_assignee_not_found",
                )

        alert.assigned_to = assigned_to
        self.repository.add_event(
            farm_id=farm_id,
            alert_id=alert_id,
            event_type=(
                AlertEventType.ASSIGNED.value
                if assigned_to is not None
                else AlertEventType.UNASSIGNED.value
            ),
            actor_user_id=actor_user_id,
            notes=notes,
        )
        self.database_session.commit()
        return alert

    def acknowledge(
        self,
        farm_id: UUID,
        alert_id: UUID,
        actor_user_id: UUID,
        notes: str | None,
    ) -> OperationalAlert:
        alert = self._alert(
            farm_id,
            alert_id,
            for_update=True,
        )
        if alert.status == AlertStatus.RESOLVED.value:
            raise ResourceConflictError(
                "A resolved alert cannot be acknowledged.",
                error_code="resolved_alert_cannot_acknowledge",
            )

        previous = alert.status
        alert.status = AlertStatus.ACKNOWLEDGED.value
        alert.acknowledged_by = actor_user_id
        alert.acknowledged_at = datetime.now(UTC)
        self.repository.add_event(
            farm_id=farm_id,
            alert_id=alert_id,
            event_type=(AlertEventType.ACKNOWLEDGED.value),
            actor_user_id=actor_user_id,
            from_status=previous,
            to_status=alert.status,
            notes=notes,
        )
        self.database_session.commit()
        return alert

    def resolve(
        self,
        farm_id: UUID,
        alert_id: UUID,
        actor_user_id: UUID,
        notes: str | None,
    ) -> OperationalAlert:
        alert = self._alert(
            farm_id,
            alert_id,
            for_update=True,
        )
        if alert.status == AlertStatus.RESOLVED.value:
            raise ResourceConflictError(
                "This alert is already resolved.",
                error_code="alert_already_resolved",
            )

        previous = alert.status
        alert.status = AlertStatus.RESOLVED.value
        alert.resolved_by = actor_user_id
        alert.resolved_at = datetime.now(UTC)
        alert.resolution_notes = notes
        self.repository.add_event(
            farm_id=farm_id,
            alert_id=alert_id,
            event_type=AlertEventType.RESOLVED.value,
            actor_user_id=actor_user_id,
            from_status=previous,
            to_status=alert.status,
            notes=notes,
        )
        self.database_session.commit()
        return alert

    def reopen(
        self,
        farm_id: UUID,
        alert_id: UUID,
        actor_user_id: UUID,
        notes: str | None,
    ) -> OperationalAlert:
        alert = self._alert(
            farm_id,
            alert_id,
            for_update=True,
        )
        if alert.status != AlertStatus.RESOLVED.value:
            raise ResourceConflictError(
                "Only resolved alerts can be reopened.",
                error_code="alert_not_resolved",
            )

        previous = alert.status
        alert.status = AlertStatus.OPEN.value
        alert.resolved_by = None
        alert.resolved_at = None
        alert.resolution_notes = None
        self.repository.add_event(
            farm_id=farm_id,
            alert_id=alert_id,
            event_type=(AlertEventType.MANUALLY_REOPENED.value),
            actor_user_id=actor_user_id,
            from_status=previous,
            to_status=alert.status,
            notes=notes,
        )
        self._queue_notifications(alert)
        self.database_session.commit()
        return alert

    def upsert_preference(
        self,
        farm_id: UUID,
        user_id: UUID,
        *,
        alert_type: str,
        channel: str,
        minimum_severity: str,
        is_enabled: bool,
    ) -> NotificationPreference:
        preference = self.repository.preference(
            farm_id,
            user_id,
            alert_type,
            channel,
        )
        if preference is None:
            preference = NotificationPreference(
                farm_id=farm_id,
                user_id=user_id,
                alert_type=alert_type,
                channel=channel,
                minimum_severity=minimum_severity,
                is_enabled=is_enabled,
            )
            self.database_session.add(preference)
        else:
            preference.minimum_severity = minimum_severity
            preference.is_enabled = is_enabled

        self._commit(
            "The notification preference could not be saved.",
            "notification_preference_conflict",
        )
        return preference

    def send_test_notification(
        self,
        farm_id: UUID,
        user: User,
        *,
        channel: str,
        destination: str | None,
    ) -> NotificationDelivery:
        resolved_destination = destination
        if resolved_destination is None:
            resolved_destination = self._destination(
                user,
                channel,
            )

        alert = OperationalAlert(
            farm_id=farm_id,
            fingerprint=(f"TEST_NOTIFICATION:{user.id}:{channel}:{uuid4().hex}"),
            alert_type="LOW_FEED_STOCK",
            severity=AlertSeverity.INFO.value,
            status=AlertStatus.RESOLVED.value,
            title="PoultryPulse test notification",
            message=(
                "Your PoultryPulse notification channel is configured and reachable."
            ),
            source_module="alerts",
            first_detected_at=datetime.now(UTC),
            last_detected_at=datetime.now(UTC),
            occurrence_count=1,
            resolved_by=user.id,
            resolved_at=datetime.now(UTC),
            resolution_notes="Test notification record.",
        )
        self.database_session.add(alert)
        self.database_session.flush()

        delivery = NotificationDelivery(
            farm_id=farm_id,
            alert_id=alert.id,
            user_id=user.id,
            channel=channel,
            destination=resolved_destination,
            status=(NotificationDeliveryStatus.PENDING.value),
            subject="PoultryPulse test notification",
            body=alert.message,
            max_attempts=1,
        )
        self.repository.add_delivery(delivery)
        self.database_session.flush()
        self._dispatch_delivery(
            delivery,
            actor_user_id=user.id,
        )
        self.database_session.commit()
        return delivery
