from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_database_session
from app.modules.alerts.config import NotificationSettings
from app.modules.alerts.constants import (
    AlertDeliveryChannel,
    AlertStatus,
)
from app.modules.alerts.delivery_constants import (
    NotificationDeliveryStatus,
)
from app.modules.alerts.models import OperationalAlert
from app.modules.alerts.repository import AlertsRepository
from app.modules.alerts.schemas import (
    AlertActionRequest,
    AlertAssignmentRequest,
    AlertCountsResponse,
    AlertEventListResponse,
    AlertEventResponse,
    AlertRefreshRequest,
    AlertRefreshResponse,
    DeliveryProcessResponse,
    NotificationChannelStatusResponse,
    NotificationDeliveryListResponse,
    NotificationDeliveryResponse,
    NotificationPreferenceListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpsert,
    PersistentAlertListResponse,
    PersistentAlertResponse,
    TestNotificationRequest,
)
from app.modules.alerts.service import AlertsService
from app.modules.auth.dependencies import require_permissions
from app.modules.reports.constants import (
    AlertSeverity,
    AlertType,
)
from app.modules.users.models import User


router = APIRouter(
    prefix="/alerts",
    tags=["Notification Center and Alert Delivery"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


def alert_response(
    alert: OperationalAlert,
    *,
    is_read: bool,
    is_dismissed: bool,
) -> PersistentAlertResponse:
    return PersistentAlertResponse(
        id=alert.id,
        farm_id=alert.farm_id,
        fingerprint=alert.fingerprint,
        alert_type=alert.alert_type,
        severity=alert.severity,
        status=alert.status,
        title=alert.title,
        message=alert.message,
        source_module=alert.source_module,
        source_id=alert.source_id,
        action_path=alert.action_path,
        assigned_to=alert.assigned_to,
        first_detected_at=alert.first_detected_at,
        last_detected_at=alert.last_detected_at,
        occurrence_count=alert.occurrence_count,
        acknowledged_by=alert.acknowledged_by,
        acknowledged_at=alert.acknowledged_at,
        resolved_by=alert.resolved_by,
        resolved_at=alert.resolved_at,
        resolution_notes=alert.resolution_notes,
        is_read=is_read,
        is_dismissed=is_dismissed,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )


def current_alert_response(
    repository: AlertsRepository,
    alert: OperationalAlert,
    user_id: UUID,
) -> PersistentAlertResponse:
    state = repository.get_state(
        alert.farm_id,
        alert.id,
        user_id,
    )
    return alert_response(
        alert,
        is_read=(state.is_read if state is not None else False),
        is_dismissed=(state.is_dismissed if state is not None else False),
    )


@router.get(
    "/channel-status",
    response_model=NotificationChannelStatusResponse,
)
def channel_status(
    current_user: Annotated[
        User,
        Depends(require_permissions("alerts.view")),
    ],
) -> NotificationChannelStatusResponse:
    del current_user
    settings = NotificationSettings.from_environment()
    return NotificationChannelStatusResponse(
        in_app_enabled=True,
        email_enabled=settings.email_enabled,
        email_ready=settings.email_ready,
        sms_enabled=settings.sms_enabled,
        sms_ready=settings.sms_ready,
        sms_provider=settings.sms_provider,
    )


@router.get(
    "/counts",
    response_model=AlertCountsResponse,
)
def alert_counts(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("alerts.view")),
    ],
) -> AlertCountsResponse:
    values = AlertsRepository(database_session).alert_counts(
        current_user.farm_id,
        current_user.id,
    )
    return AlertCountsResponse(**values)


@router.get(
    "/preferences",
    response_model=NotificationPreferenceListResponse,
)
def list_preferences(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("notifications.manage")),
    ],
) -> NotificationPreferenceListResponse:
    items = AlertsRepository(database_session).list_preferences(
        current_user.farm_id,
        current_user.id,
    )
    return NotificationPreferenceListResponse(
        items=[NotificationPreferenceResponse.model_validate(item) for item in items]
    )


@router.put(
    "/preferences",
    response_model=NotificationPreferenceResponse,
)
def save_preference(
    payload: NotificationPreferenceUpsert,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("notifications.manage")),
    ],
) -> NotificationPreferenceResponse:
    preference = AlertsService(database_session).upsert_preference(
        current_user.farm_id,
        current_user.id,
        alert_type=payload.alert_type.value,
        channel=payload.channel.value,
        minimum_severity=(payload.minimum_severity.value),
        is_enabled=payload.is_enabled,
    )
    return NotificationPreferenceResponse.model_validate(preference)


@router.get(
    "/deliveries",
    response_model=NotificationDeliveryListResponse,
)
def list_deliveries(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("notifications.view_deliveries")),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    delivery_status: Annotated[
        NotificationDeliveryStatus | None,
        Query(alias="status"),
    ] = None,
    channel: AlertDeliveryChannel | None = None,
    alert_id: UUID | None = None,
    user_id: UUID | None = None,
) -> NotificationDeliveryListResponse:
    items, total = AlertsRepository(database_session).list_deliveries(
        current_user.farm_id,
        offset=offset,
        limit=limit,
        status=(delivery_status.value if delivery_status is not None else None),
        channel=(channel.value if channel is not None else None),
        alert_id=alert_id,
        user_id=user_id,
    )
    return NotificationDeliveryListResponse(
        items=[NotificationDeliveryResponse.model_validate(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post(
    "/deliveries/process",
    response_model=DeliveryProcessResponse,
)
def process_deliveries(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("notifications.send")),
    ],
    limit: Annotated[int, Query(ge=1, le=1000)] = 200,
) -> DeliveryProcessResponse:
    return AlertsService(database_session).process_deliveries(
        current_user.farm_id,
        actor_user_id=current_user.id,
        limit=limit,
    )


@router.post(
    "/deliveries/{delivery_id}/retry",
    response_model=NotificationDeliveryResponse,
)
def retry_delivery(
    delivery_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("notifications.send")),
    ],
) -> NotificationDeliveryResponse:
    delivery = AlertsService(database_session).retry_delivery(
        current_user.farm_id,
        delivery_id,
        current_user.id,
    )
    return NotificationDeliveryResponse.model_validate(delivery)


@router.post(
    "/test-notification",
    response_model=NotificationDeliveryResponse,
    status_code=status.HTTP_201_CREATED,
)
def test_notification(
    payload: TestNotificationRequest,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("notifications.send")),
    ],
) -> NotificationDeliveryResponse:
    delivery = AlertsService(database_session).send_test_notification(
        current_user.farm_id,
        current_user,
        channel=payload.channel.value,
        destination=payload.destination,
    )
    return NotificationDeliveryResponse.model_validate(delivery)


@router.post(
    "/refresh",
    response_model=AlertRefreshResponse,
)
def refresh_alerts(
    payload: AlertRefreshRequest,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("alerts.refresh")),
    ],
) -> AlertRefreshResponse:
    return AlertsService(database_session).refresh(
        current_user.farm_id,
        current_user.id,
        as_of_date=payload.as_of_date,
        send_now=payload.send_now,
    )


@router.get(
    "",
    response_model=PersistentAlertListResponse,
)
def list_alerts(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("alerts.view")),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    alert_status: Annotated[
        AlertStatus | None,
        Query(alias="status"),
    ] = None,
    severity: AlertSeverity | None = None,
    alert_type: AlertType | None = None,
    assigned_to: UUID | None = None,
    assigned_to_me: bool = False,
    unread_only: bool = False,
    include_dismissed: bool = False,
    search: Annotated[
        str | None,
        Query(min_length=1, max_length=150),
    ] = None,
) -> PersistentAlertListResponse:
    repository = AlertsRepository(database_session)
    rows, total = repository.list_alerts(
        current_user.farm_id,
        current_user.id,
        offset=offset,
        limit=limit,
        status=(alert_status.value if alert_status is not None else None),
        severity=(severity.value if severity is not None else None),
        alert_type=(alert_type.value if alert_type is not None else None),
        assigned_to=assigned_to,
        assigned_to_me=assigned_to_me,
        unread_only=unread_only,
        include_dismissed=include_dismissed,
        search=search,
    )
    return PersistentAlertListResponse(
        items=[
            alert_response(
                alert,
                is_read=(state.is_read if state is not None else False),
                is_dismissed=(state.is_dismissed if state is not None else False),
            )
            for alert, state in rows
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{alert_id}",
    response_model=PersistentAlertResponse,
)
def get_alert(
    alert_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("alerts.view")),
    ],
) -> PersistentAlertResponse:
    service = AlertsService(database_session)
    alert = service._alert(
        current_user.farm_id,
        alert_id,
    )
    return current_alert_response(
        service.repository,
        alert,
        current_user.id,
    )


@router.get(
    "/{alert_id}/events",
    response_model=AlertEventListResponse,
)
def alert_events(
    alert_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("alerts.view")),
    ],
) -> AlertEventListResponse:
    service = AlertsService(database_session)
    service._alert(
        current_user.farm_id,
        alert_id,
    )
    items = service.repository.list_events(
        current_user.farm_id,
        alert_id,
    )
    return AlertEventListResponse(
        items=[AlertEventResponse.model_validate(item) for item in items],
        total=len(items),
    )


def state_action_response(
    *,
    service: AlertsService,
    alert: OperationalAlert,
    user_id: UUID,
) -> PersistentAlertResponse:
    return current_alert_response(
        service.repository,
        alert,
        user_id,
    )


@router.post(
    "/{alert_id}/read",
    response_model=PersistentAlertResponse,
)
def mark_read(
    alert_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("alerts.view")),
    ],
) -> PersistentAlertResponse:
    service = AlertsService(database_session)
    alert = service.mark_read(
        current_user.farm_id,
        alert_id,
        current_user.id,
        is_read=True,
    )
    return state_action_response(
        service=service,
        alert=alert,
        user_id=current_user.id,
    )


@router.post(
    "/{alert_id}/unread",
    response_model=PersistentAlertResponse,
)
def mark_unread(
    alert_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("alerts.view")),
    ],
) -> PersistentAlertResponse:
    service = AlertsService(database_session)
    alert = service.mark_read(
        current_user.farm_id,
        alert_id,
        current_user.id,
        is_read=False,
    )
    return state_action_response(
        service=service,
        alert=alert,
        user_id=current_user.id,
    )


@router.post(
    "/{alert_id}/dismiss",
    response_model=PersistentAlertResponse,
)
def dismiss_alert(
    alert_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("alerts.view")),
    ],
) -> PersistentAlertResponse:
    service = AlertsService(database_session)
    alert = service.dismiss(
        current_user.farm_id,
        alert_id,
        current_user.id,
        dismissed=True,
    )
    return state_action_response(
        service=service,
        alert=alert,
        user_id=current_user.id,
    )


@router.post(
    "/{alert_id}/restore",
    response_model=PersistentAlertResponse,
)
def restore_alert(
    alert_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("alerts.view")),
    ],
) -> PersistentAlertResponse:
    service = AlertsService(database_session)
    alert = service.dismiss(
        current_user.farm_id,
        alert_id,
        current_user.id,
        dismissed=False,
    )
    return state_action_response(
        service=service,
        alert=alert,
        user_id=current_user.id,
    )


@router.post(
    "/{alert_id}/assign",
    response_model=PersistentAlertResponse,
)
def assign_alert(
    alert_id: UUID,
    payload: AlertAssignmentRequest,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("alerts.assign")),
    ],
) -> PersistentAlertResponse:
    service = AlertsService(database_session)
    alert = service.assign(
        current_user.farm_id,
        alert_id,
        current_user.id,
        payload.assigned_to,
        payload.notes,
    )
    return state_action_response(
        service=service,
        alert=alert,
        user_id=current_user.id,
    )


@router.post(
    "/{alert_id}/acknowledge",
    response_model=PersistentAlertResponse,
)
def acknowledge_alert(
    alert_id: UUID,
    payload: AlertActionRequest,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("alerts.acknowledge")),
    ],
) -> PersistentAlertResponse:
    service = AlertsService(database_session)
    alert = service.acknowledge(
        current_user.farm_id,
        alert_id,
        current_user.id,
        payload.notes,
    )
    return state_action_response(
        service=service,
        alert=alert,
        user_id=current_user.id,
    )


@router.post(
    "/{alert_id}/resolve",
    response_model=PersistentAlertResponse,
)
def resolve_alert(
    alert_id: UUID,
    payload: AlertActionRequest,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("alerts.resolve")),
    ],
) -> PersistentAlertResponse:
    service = AlertsService(database_session)
    alert = service.resolve(
        current_user.farm_id,
        alert_id,
        current_user.id,
        payload.notes,
    )
    return state_action_response(
        service=service,
        alert=alert,
        user_id=current_user.id,
    )


@router.post(
    "/{alert_id}/reopen",
    response_model=PersistentAlertResponse,
)
def reopen_alert(
    alert_id: UUID,
    payload: AlertActionRequest,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("alerts.resolve")),
    ],
) -> PersistentAlertResponse:
    service = AlertsService(database_session)
    alert = service.reopen(
        current_user.farm_id,
        alert_id,
        current_user.id,
        payload.notes,
    )
    return state_action_response(
        service=service,
        alert=alert,
        user_id=current_user.id,
    )
