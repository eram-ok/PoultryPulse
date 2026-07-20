from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.health.models import (
    HealthIncident,
    HealthProduct,
    TreatmentRecord,
    VaccinationSchedule,
    calculate_withdrawal_until,
)


def test_health_product_vaccine_property() -> None:
    product = HealthProduct(
        farm_id=uuid4(),
        product_code="VAC-001",
        name="Newcastle Vaccine",
        product_type="VACCINE",
        default_egg_withdrawal_days=0,
        default_meat_withdrawal_days=0,
    )

    assert product.is_vaccine is True


def test_non_vaccine_product_property() -> None:
    product = HealthProduct(
        farm_id=uuid4(),
        product_code="MED-001",
        name="Poultry Antibiotic",
        product_type="ANTIBIOTIC",
        default_egg_withdrawal_days=7,
        default_meat_withdrawal_days=14,
    )

    assert product.is_vaccine is False


def test_vaccination_schedule_completed_property() -> None:
    schedule = VaccinationSchedule(
        farm_id=uuid4(),
        flock_id=uuid4(),
        vaccine_name="Newcastle Vaccine",
        scheduled_date=date.today(),
        route="DRINKING_WATER",
        status="COMPLETED",
        created_by=uuid4(),
    )

    assert schedule.is_completed is True
    assert schedule.is_cancelled is False


def test_vaccination_schedule_overdue_property() -> None:
    schedule = VaccinationSchedule(
        farm_id=uuid4(),
        flock_id=uuid4(),
        vaccine_name="Gumboro Vaccine",
        scheduled_date=(date.today() - timedelta(days=2)),
        route="DRINKING_WATER",
        status="SCHEDULED",
        created_by=uuid4(),
    )

    assert schedule.is_overdue is True


def test_cancelled_schedule_is_not_overdue() -> None:
    schedule = VaccinationSchedule(
        farm_id=uuid4(),
        flock_id=uuid4(),
        vaccine_name="Fowl Pox Vaccine",
        scheduled_date=(date.today() - timedelta(days=2)),
        route="WING_WEB",
        status="CANCELLED",
        created_by=uuid4(),
    )

    assert schedule.is_overdue is False
    assert schedule.is_cancelled is True


def test_health_incident_resolved_property() -> None:
    incident = HealthIncident(
        farm_id=uuid4(),
        flock_id=uuid4(),
        incident_code="HI-001",
        incident_date=date.today(),
        severity="HIGH",
        status="RESOLVED",
        affected_birds=20,
        symptoms="Coughing and reduced appetite.",
        isolation_required=True,
        recorded_by=uuid4(),
        resolved_by=uuid4(),
        resolution_date=date.today(),
    )

    assert incident.is_resolved is True


def test_open_health_incident_property() -> None:
    incident = HealthIncident(
        farm_id=uuid4(),
        flock_id=uuid4(),
        incident_code="HI-002",
        incident_date=date.today(),
        severity="MODERATE",
        status="OPEN",
        affected_birds=10,
        symptoms="Reduced feed consumption.",
        isolation_required=False,
        recorded_by=uuid4(),
    )

    assert incident.is_resolved is False


def test_calculate_egg_withdrawal_date() -> None:
    treatment_date = date(2026, 7, 20)

    withdrawal_until = calculate_withdrawal_until(
        treatment_date,
        7,
    )

    assert withdrawal_until == date(2026, 7, 27)


def test_zero_withdrawal_days_returns_none() -> None:
    withdrawal_until = calculate_withdrawal_until(
        date.today(),
        0,
    )

    assert withdrawal_until is None


def test_negative_withdrawal_days_are_rejected() -> None:
    with pytest.raises(ValueError):
        calculate_withdrawal_until(
            date.today(),
            -1,
        )


def test_treatment_withdrawal_properties() -> None:
    treatment = TreatmentRecord(
        farm_id=uuid4(),
        flock_id=uuid4(),
        product_name="Poultry Antibiotic",
        treatment_date=date.today(),
        birds_treated=100,
        route="DRINKING_WATER",
        treatment_cost=Decimal("50000.00"),
        egg_withdrawal_days=7,
        meat_withdrawal_days=14,
        egg_withdrawal_until=(date.today() + timedelta(days=7)),
        meat_withdrawal_until=(date.today() + timedelta(days=14)),
        status="ACTIVE",
        recorded_by=uuid4(),
    )

    assert treatment.is_egg_withdrawal_active is True
    assert treatment.is_meat_withdrawal_active is True
    assert treatment.is_completed is False


def test_cancelled_treatment_has_no_active_withdrawal() -> None:
    treatment = TreatmentRecord(
        farm_id=uuid4(),
        flock_id=uuid4(),
        product_name="Poultry Antibiotic",
        treatment_date=date.today(),
        birds_treated=100,
        route="DRINKING_WATER",
        treatment_cost=Decimal("50000.00"),
        egg_withdrawal_days=7,
        meat_withdrawal_days=14,
        egg_withdrawal_until=(date.today() + timedelta(days=7)),
        meat_withdrawal_until=(date.today() + timedelta(days=14)),
        status="CANCELLED",
        recorded_by=uuid4(),
    )

    assert treatment.is_egg_withdrawal_active is False
    assert treatment.is_meat_withdrawal_active is False
