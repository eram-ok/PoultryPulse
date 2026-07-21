from datetime import date

from fastapi.testclient import TestClient

from app.modules.reports.constants import (
    AlertSeverity,
    AlertType,
)
from app.modules.reports.schemas import (
    OperationalAlertListResponse,
    OperationalAlertResponse,
)


def fake_dynamic_alerts(
    *args,
    **kwargs,
) -> OperationalAlertListResponse:
    del args, kwargs
    item = OperationalAlertResponse(
        alert_type=AlertType.LOW_FEED_STOCK,
        severity=AlertSeverity.CRITICAL,
        title="Low feed stock: Layers Mash",
        message="0.000 kg remains.",
        source_module="feed",
        source_id=None,
        action_path="/feed/items/test",
        detected_on=date.today(),
    )
    return OperationalAlertListResponse(
        items=[item],
        total=1,
        critical=1,
        warning=0,
        info=0,
    )


def test_alert_routes_require_authentication(
    client: TestClient,
) -> None:
    assert client.get("/api/v1/alerts").status_code == 401


def test_refresh_creates_persistent_alert(
    authenticated_client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        ("app.modules.alerts.service.ReportsService.alerts"),
        fake_dynamic_alerts,
    )

    refresh = authenticated_client.post(
        "/api/v1/alerts/refresh",
        json={"send_now": False},
    )
    assert refresh.status_code == 200
    assert refresh.json()["created_count"] == 1

    listing = authenticated_client.get("/api/v1/alerts")
    assert listing.status_code == 200
    payload = listing.json()
    assert payload["total"] >= 1
    assert payload["items"][0]["status"] == "OPEN"


def test_alert_lifecycle_and_user_state(
    authenticated_client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        ("app.modules.alerts.service.ReportsService.alerts"),
        fake_dynamic_alerts,
    )
    authenticated_client.post(
        "/api/v1/alerts/refresh",
        json={"send_now": False},
    )

    alert = authenticated_client.get("/api/v1/alerts").json()["items"][0]
    alert_id = alert["id"]

    read = authenticated_client.post(f"/api/v1/alerts/{alert_id}/read")
    assert read.status_code == 200
    assert read.json()["is_read"] is True

    acknowledged = authenticated_client.post(
        f"/api/v1/alerts/{alert_id}/acknowledge",
        json={"notes": "Investigating feed delivery."},
    )
    assert acknowledged.status_code == 200
    assert acknowledged.json()["status"] == "ACKNOWLEDGED"

    resolved = authenticated_client.post(
        f"/api/v1/alerts/{alert_id}/resolve",
        json={"notes": "Feed stock replenished."},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "RESOLVED"

    reopened = authenticated_client.post(
        f"/api/v1/alerts/{alert_id}/reopen",
        json={"notes": "Issue returned."},
    )
    assert reopened.status_code == 200
    assert reopened.json()["status"] == "OPEN"

    events = authenticated_client.get(f"/api/v1/alerts/{alert_id}/events")
    assert events.status_code == 200
    assert events.json()["total"] >= 4


def test_notification_preferences(
    authenticated_client: TestClient,
) -> None:
    saved = authenticated_client.put(
        "/api/v1/alerts/preferences",
        json={
            "alert_type": "LOW_FEED_STOCK",
            "channel": "EMAIL",
            "minimum_severity": "WARNING",
            "is_enabled": True,
        },
    )
    assert saved.status_code == 200
    assert saved.json()["channel"] == "EMAIL"

    listing = authenticated_client.get("/api/v1/alerts/preferences")
    assert listing.status_code == 200
    assert any(item["channel"] == "EMAIL" for item in listing.json()["items"])


def test_channel_status(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get("/api/v1/alerts/channel-status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["in_app_enabled"] is True
    assert "email_ready" in payload
    assert "sms_ready" in payload
