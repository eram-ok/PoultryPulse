from uuid import uuid4

from app.modules.alerts.constants import (
    AlertDeliveryChannel,
    AlertRefreshStatus,
    AlertStatus,
)
from app.modules.alerts.models import (
    AlertRefreshRun,
    AlertUserState,
    NotificationPreference,
    OperationalAlert,
)
from app.modules.reports.constants import (
    AlertSeverity,
    AlertType,
)


def test_open_operational_alert_properties() -> None:
    alert = OperationalAlert(
        farm_id=uuid4(),
        fingerprint="LOW_FEED_STOCK:item-1",
        alert_type=AlertType.LOW_FEED_STOCK.value,
        severity=AlertSeverity.CRITICAL.value,
        status=AlertStatus.OPEN.value,
        title="Low feed stock",
        message="Feed stock is below reorder level.",
        source_module="feed",
    )

    assert alert.is_open is True
    assert alert.is_acknowledged is False
    assert alert.is_resolved is False
    assert alert.is_critical is True


def test_acknowledged_alert_property() -> None:
    alert = OperationalAlert(
        farm_id=uuid4(),
        fingerprint="HEALTH_INCIDENT:item-1",
        alert_type=AlertType.HEALTH_INCIDENT.value,
        severity=AlertSeverity.WARNING.value,
        status=AlertStatus.ACKNOWLEDGED.value,
        title="Health incident",
        message="A health incident needs review.",
        source_module="health",
    )

    assert alert.is_acknowledged is True


def test_resolved_alert_property() -> None:
    alert = OperationalAlert(
        farm_id=uuid4(),
        fingerprint="OVERDUE_VACCINATION:item-1",
        alert_type=AlertType.OVERDUE_VACCINATION.value,
        severity=AlertSeverity.CRITICAL.value,
        status=AlertStatus.RESOLVED.value,
        title="Overdue vaccination",
        message="The vaccination was completed.",
        source_module="health",
    )

    assert alert.is_resolved is True


def test_alert_user_state_values() -> None:
    state = AlertUserState(
        farm_id=uuid4(),
        alert_id=uuid4(),
        user_id=uuid4(),
        is_read=False,
        is_dismissed=False,
    )

    assert state.is_read is False
    assert state.is_dismissed is False


def test_notification_preference_values() -> None:
    preference = NotificationPreference(
        farm_id=uuid4(),
        user_id=uuid4(),
        alert_type=AlertType.LOW_FEED_STOCK.value,
        channel=AlertDeliveryChannel.IN_APP.value,
        minimum_severity=AlertSeverity.WARNING.value,
        is_enabled=True,
    )

    assert preference.channel == "IN_APP"
    assert preference.is_enabled is True


def test_completed_refresh_run_property() -> None:
    refresh = AlertRefreshRun(
        farm_id=uuid4(),
        status=AlertRefreshStatus.COMPLETED.value,
        detected_count=4,
        created_count=2,
        updated_count=2,
        resolved_count=0,
    )

    assert refresh.is_completed is True
    assert refresh.is_failed is False


def test_failed_refresh_run_property() -> None:
    refresh = AlertRefreshRun(
        farm_id=uuid4(),
        status=AlertRefreshStatus.FAILED.value,
        error_message="Refresh failed.",
    )

    assert refresh.is_failed is True
