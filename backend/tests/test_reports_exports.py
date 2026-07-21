from datetime import date, timedelta

from fastapi.testclient import TestClient


def test_advanced_reports_require_authentication(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/reports/comparison")
    assert response.status_code == 401


def test_comparison_uses_previous_equal_period(
    authenticated_client: TestClient,
) -> None:
    current_to = date.today()
    current_from = current_to - timedelta(days=6)

    response = authenticated_client.get(
        "/api/v1/reports/comparison",
        params={
            "date_from": current_from.isoformat(),
            "date_to": current_to.isoformat(),
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["current_date_from"] == (current_from.isoformat())
    assert payload["current_date_to"] == (current_to.isoformat())
    assert payload["previous_date_to"] == (current_from - timedelta(days=1)).isoformat()
    assert len(payload["metrics"]) == 7


def test_incomplete_comparison_period_is_rejected(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get(
        "/api/v1/reports/comparison",
        params={
            "compare_from": (date.today() - timedelta(days=10)).isoformat(),
        },
    )

    assert response.status_code == 422


def test_executive_summary_returns_highlights(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get("/api/v1/reports/executive-summary")

    assert response.status_code == 200
    payload = response.json()

    assert "performance" in payload
    assert "alerts" in payload
    assert len(payload["highlights"]) >= 3


def test_performance_csv_export(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get("/api/v1/reports/exports/performance.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert "metric,value" in response.text
    assert "estimated_profit" in response.text


def test_trends_csv_export(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get(
        "/api/v1/reports/exports/trends.csv",
        params=[
            ("metrics", "EGG_PRODUCTION"),
            ("metrics", "SALES_REVENUE"),
        ],
    )

    assert response.status_code == 200
    assert "metric,date,value" in response.text
    assert "EGG_PRODUCTION" in response.text
    assert "SALES_REVENUE" in response.text


def test_alerts_csv_export(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get("/api/v1/reports/exports/alerts.csv")

    assert response.status_code == 200
    assert "severity,alert_type,title,message" in response.text
