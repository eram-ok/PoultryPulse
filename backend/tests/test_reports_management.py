from datetime import date, timedelta

from fastapi.testclient import TestClient


def test_reports_require_authentication(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/reports/dashboard")
    assert response.status_code == 401


def test_dashboard_returns_operational_sections(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get("/api/v1/reports/dashboard")

    assert response.status_code == 200
    payload = response.json()

    assert payload["as_of_date"] == (date.today().isoformat())
    assert "production" in payload
    assert "inventory" in payload
    assert "flocks" in payload
    assert "health" in payload
    assert "sales" in payload
    assert "finance" in payload
    assert "active_alert_count" in payload


def test_operational_alerts_return_counts(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get("/api/v1/reports/alerts")

    assert response.status_code == 200
    payload = response.json()

    assert isinstance(payload["items"], list)
    assert payload["total"] == (
        payload["critical"] + payload["warning"] + payload["info"]
    )


def test_performance_report_defaults_to_30_days(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get("/api/v1/reports/performance")

    assert response.status_code == 200
    payload = response.json()

    assert payload["date_to"] == (date.today().isoformat())
    assert payload["date_from"] == (date.today() - timedelta(days=29)).isoformat()
    assert "estimated_profit" in payload
    assert "average_laying_percentage" in payload


def test_trend_report_returns_daily_points(
    authenticated_client: TestClient,
) -> None:
    date_to = date.today()
    date_from = date_to - timedelta(days=6)

    response = authenticated_client.get(
        "/api/v1/reports/trends",
        params={
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "metrics": [
                "EGG_PRODUCTION",
                "SALES_REVENUE",
            ],
            "include_zero_days": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert len(payload["series"]) == 2
    assert all(len(series["points"]) == 7 for series in payload["series"])


def test_invalid_report_date_range_is_rejected(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get(
        "/api/v1/reports/performance",
        params={
            "date_from": date.today().isoformat(),
            "date_to": (date.today() - timedelta(days=1)).isoformat(),
        },
    )

    assert response.status_code == 422
