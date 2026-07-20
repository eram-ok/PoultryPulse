from datetime import date, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient


def create_house(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/houses",
        json={
            "house_code": (f"HEALTH-H-{uuid4().hex[:8].upper()}"),
            "name": "Health Test House",
            "capacity": 1500,
            "status": "ACTIVE",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_supplier(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/suppliers",
        json={
            "supplier_code": (f"HEALTH-S-{uuid4().hex[:8].upper()}"),
            "name": "Health Test Bird Supplier",
            "supplier_type": "BIRD_SUPPLIER",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_flock(client: TestClient) -> dict:
    house = create_house(client)
    supplier = create_supplier(client)
    response = client.post(
        "/api/v1/flocks",
        json={
            "house_id": house["id"],
            "supplier_id": supplier["id"],
            "flock_code": (f"HEALTH-F-{uuid4().hex[:8].upper()}"),
            "name": "Health Test Layers",
            "breed": "Lohmann Brown",
            "arrival_date": date.today().isoformat(),
            "age_at_arrival_days": 126,
            "initial_population": 1000,
            "purchase_cost": 25000000,
            "production_stage": "LAYING",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_product(
    client: TestClient,
    *,
    product_type: str,
    egg_days: int = 0,
    meat_days: int = 0,
) -> dict:
    response = client.post(
        "/api/v1/health/products",
        json={
            "product_code": (f"HP-{uuid4().hex[:8].upper()}"),
            "name": (
                "Newcastle Vaccine"
                if product_type == "VACCINE"
                else "Poultry Antibiotic"
            ),
            "product_type": product_type,
            "default_egg_withdrawal_days": egg_days,
            "default_meat_withdrawal_days": meat_days,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_health_routes_require_authentication(
    client: TestClient,
) -> None:
    assert client.get("/api/v1/health/products").status_code == 401


def test_create_health_product(
    authenticated_client: TestClient,
) -> None:
    product = create_product(
        authenticated_client,
        product_type="VACCINE",
    )
    assert product["is_vaccine"] is True
    assert product["is_active"] is True


def test_schedule_and_complete_vaccination(
    authenticated_client: TestClient,
) -> None:
    flock = create_flock(authenticated_client)
    vaccine = create_product(
        authenticated_client,
        product_type="VACCINE",
    )
    schedule_response = authenticated_client.post(
        "/api/v1/health/vaccinations",
        json={
            "flock_id": flock["id"],
            "product_id": vaccine["id"],
            "vaccine_name": vaccine["name"],
            "scheduled_date": date.today().isoformat(),
            "route": "DRINKING_WATER",
        },
    )
    assert schedule_response.status_code == 201
    assert schedule_response.json()["status"] == "DUE"

    completion = authenticated_client.post(
        (f"/api/v1/health/vaccinations/{schedule_response.json()['id']}/complete"),
        json={
            "birds_vaccinated": 1000,
            "batch_number": "BATCH-001",
            "expiry_date": (date.today() + timedelta(days=30)).isoformat(),
        },
    )
    assert completion.status_code == 200
    assert completion.json()["status"] == "COMPLETED"
    assert completion.json()["administration"] is not None


def test_missed_vaccination_is_detected(
    authenticated_client: TestClient,
) -> None:
    house = create_house(authenticated_client)
    supplier = create_supplier(authenticated_client)

    flock_response = authenticated_client.post(
        "/api/v1/flocks",
        json={
            "house_id": house["id"],
            "supplier_id": supplier["id"],
            "flock_code": (f"HEALTH-F-{uuid4().hex[:8].upper()}"),
            "name": "Missed Vaccination Test Layers",
            "breed": "Lohmann Brown",
            "arrival_date": (date.today() - timedelta(days=2)).isoformat(),
            "age_at_arrival_days": 126,
            "initial_population": 1000,
            "purchase_cost": 25000000,
            "production_stage": "LAYING",
        },
    )

    assert flock_response.status_code == 201
    flock = flock_response.json()

    vaccine = create_product(
        authenticated_client,
        product_type="VACCINE",
    )

    response = authenticated_client.post(
        "/api/v1/health/vaccinations",
        json={
            "flock_id": flock["id"],
            "product_id": vaccine["id"],
            "vaccine_name": vaccine["name"],
            "scheduled_date": (date.today() - timedelta(days=1)).isoformat(),
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "MISSED"
    assert response.json()["is_overdue"] is True


def test_incident_treatment_and_resolution(
    authenticated_client: TestClient,
) -> None:
    flock = create_flock(authenticated_client)
    medicine = create_product(
        authenticated_client,
        product_type="ANTIBIOTIC",
        egg_days=7,
        meat_days=14,
    )
    incident = authenticated_client.post(
        "/api/v1/health/incidents",
        json={
            "flock_id": flock["id"],
            "incident_code": (f"HI-{uuid4().hex[:8].upper()}"),
            "affected_birds": 20,
            "symptoms": "Coughing and low appetite.",
            "severity": "HIGH",
        },
    )
    assert incident.status_code == 201
    assert incident.json()["status"] == "OPEN"

    treatment = authenticated_client.post(
        "/api/v1/health/treatments",
        json={
            "flock_id": flock["id"],
            "health_incident_id": incident.json()["id"],
            "product_id": medicine["id"],
            "birds_treated": 20,
            "dose": "1 gram per litre",
        },
    )
    assert treatment.status_code == 201
    assert treatment.json()["egg_withdrawal_days"] == 7
    assert treatment.json()["meat_withdrawal_days"] == 14
    assert treatment.json()["is_egg_withdrawal_active"]

    incident_after = authenticated_client.get(
        (f"/api/v1/health/incidents/{incident.json()['id']}")
    )
    assert incident_after.json()["status"] == "UNDER_TREATMENT"

    completed = authenticated_client.post(
        (f"/api/v1/health/treatments/{treatment.json()['id']}/complete"),
        json={
            "end_date": date.today().isoformat(),
            "notes": "Course completed.",
        },
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "COMPLETED"

    resolved = authenticated_client.post(
        (f"/api/v1/health/incidents/{incident.json()['id']}/resolve"),
        json={
            "resolution_notes": ("Birds recovered after treatment."),
        },
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "RESOLVED"


def test_active_withdrawal_and_history(
    authenticated_client: TestClient,
) -> None:
    flock = create_flock(authenticated_client)
    medicine = create_product(
        authenticated_client,
        product_type="ANTIBIOTIC",
        egg_days=7,
        meat_days=14,
    )
    treatment = authenticated_client.post(
        "/api/v1/health/treatments",
        json={
            "flock_id": flock["id"],
            "product_id": medicine["id"],
            "birds_treated": 100,
        },
    )
    assert treatment.status_code == 201

    withdrawals = authenticated_client.get(
        "/api/v1/health/withdrawals",
        params={"flock_id": flock["id"]},
    )
    assert withdrawals.status_code == 200
    assert treatment.json()["id"] in {
        item["id"] for item in withdrawals.json()["items"]
    }

    history = authenticated_client.get((f"/api/v1/health/flocks/{flock['id']}/history"))
    assert history.status_code == 200
    assert history.json()["flock_id"] == flock["id"]
    assert len(history.json()["treatment_records"]) == 1


def test_health_summary(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get("/api/v1/health/summary")
    assert response.status_code == 200
    assert "open_incidents" in response.json()
