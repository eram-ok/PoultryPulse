from datetime import date, datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.modules.alerts.constants import (
    AlertDeliveryChannel,
    AlertStatus,
)
from app.modules.alerts.delivery_constants import (
    AlertEventType,
    NotificationDeliveryStatus,
)
from app.modules.reports.constants import (
    AlertSeverity,
    AlertType,
)


def clean_optional(
    value: str | None,
) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


class AlertRefreshRequest(BaseModel):
    as_of_date: date | None = None
    send_now: bool = True


class AlertRefreshResponse(BaseModel):
    run_id: UUID
    detected_count: int
    created_count: int
    updated_count: int
    resolved_count: int
    deliveries_queued: int
    deliveries_sent: int
    deliveries_failed: int


class AlertAssignmentRequest(BaseModel):
    assigned_to: UUID | None = None
    notes: str | None = Field(
        default=None,
        max_length=1000,
    )

    @field_validator("notes")
    @classmethod
    def normalize_notes(
        cls,
        value: str | None,
    ) -> str | None:
        return clean_optional(value)


class AlertActionRequest(BaseModel):
    notes: str | None = Field(
        default=None,
        max_length=2000,
    )

    @field_validator("notes")
    @classmethod
    def normalize_notes(
        cls,
        value: str | None,
    ) -> str | None:
        return clean_optional(value)


class PersistentAlertResponse(BaseModel):
    id: UUID
    farm_id: UUID
    fingerprint: str
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus
    title: str
    message: str
    source_module: str
    source_id: UUID | None
    action_path: str | None
    assigned_to: UUID | None
    first_detected_at: datetime
    last_detected_at: datetime
    occurrence_count: int
    acknowledged_by: UUID | None
    acknowledged_at: datetime | None
    resolved_by: UUID | None
    resolved_at: datetime | None
    resolution_notes: str | None
    is_read: bool
    is_dismissed: bool
    created_at: datetime
    updated_at: datetime


class PersistentAlertListResponse(BaseModel):
    items: list[PersistentAlertResponse]
    total: int
    offset: int
    limit: int


class AlertCountsResponse(BaseModel):
    total_active: int
    unread: int
    open: int
    acknowledged: int
    critical: int
    assigned_to_me: int


class AlertEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    alert_id: UUID
    actor_user_id: UUID | None
    event_type: AlertEventType
    from_status: AlertStatus | None
    to_status: AlertStatus | None
    notes: str | None
    created_at: datetime


class AlertEventListResponse(BaseModel):
    items: list[AlertEventResponse]
    total: int


class NotificationPreferenceUpsert(BaseModel):
    alert_type: AlertType
    channel: AlertDeliveryChannel
    minimum_severity: AlertSeverity = AlertSeverity.INFO
    is_enabled: bool = True


class NotificationPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    user_id: UUID
    alert_type: AlertType
    channel: AlertDeliveryChannel
    minimum_severity: AlertSeverity
    is_enabled: bool
    created_at: datetime
    updated_at: datetime


class NotificationPreferenceListResponse(BaseModel):
    items: list[NotificationPreferenceResponse]


class NotificationDeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    alert_id: UUID
    user_id: UUID
    channel: AlertDeliveryChannel
    destination: str | None
    status: NotificationDeliveryStatus
    subject: str
    attempt_count: int
    max_attempts: int
    provider_name: str | None
    provider_message_id: str | None
    last_error: str | None
    next_attempt_at: datetime | None
    sent_at: datetime | None
    created_at: datetime
    updated_at: datetime


class NotificationDeliveryListResponse(BaseModel):
    items: list[NotificationDeliveryResponse]
    total: int
    offset: int
    limit: int


class DeliveryProcessResponse(BaseModel):
    processed: int
    sent: int
    failed: int
    skipped: int


class TestNotificationRequest(BaseModel):
    channel: AlertDeliveryChannel
    destination: str | None = Field(
        default=None,
        max_length=255,
    )

    @field_validator("destination")
    @classmethod
    def normalize_destination(
        cls,
        value: str | None,
    ) -> str | None:
        return clean_optional(value)


class NotificationChannelStatusResponse(BaseModel):
    in_app_enabled: bool
    email_enabled: bool
    email_ready: bool
    sms_enabled: bool
    sms_ready: bool
    sms_provider: str
