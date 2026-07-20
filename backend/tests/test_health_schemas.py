from datetime import date, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.health.schemas import (
    HealthIncidentCreate,
    HealthProductCreate,
    TreatmentRecordCreate,
    VaccinationAdministrationCreate,
    VaccinationScheduleCreate,
)


def test_health_product_code_is_normalized() -> None:
    payload = HealthProductCreate(
        product_code=" vac nd 001 ",
        name="Newcastle Vaccine",
        product_type="VACCINE",
    )

    assert payload.product_code == "VAC-ND-001"


def test_negative_withdrawal_days_are_rejected() -> None:
    with pytest.raises(ValidationError):
        HealthProductCreate(
            product_code="MED-001",
            name="Antibiotic",
            product_type="ANTIBIOTIC",
            default_egg_withdrawal_days=-1,
        )


def test_reminder_after_schedule_is_rejected() -> None:
    with pytest.raises(ValidationError):
        VaccinationScheduleCreate(
            flock_id=uuid4(),
            vaccine_name="Newcastle Vaccine",
            scheduled_date=date.today(),
            reminder_date=date.today() + timedelta(days=1),
        )


def test_future_administration_is_rejected() -> None:
    with pytest.raises(ValidationError):
        VaccinationAdministrationCreate(
            administration_date=date.today() + timedelta(days=1),
            birds_vaccinated=100,
        )


def test_expired_vaccine_is_rejected() -> None:
    with pytest.raises(ValidationError):
        VaccinationAdministrationCreate(
            administration_date=date.today(),
            expiry_date=date.today() - timedelta(days=1),
            birds_vaccinated=100,
        )


def test_future_incident_is_rejected() -> None:
    with pytest.raises(ValidationError):
        HealthIncidentCreate(
            flock_id=uuid4(),
            incident_code="HI-001",
            incident_date=date.today() + timedelta(days=1),
            affected_birds=10,
            symptoms="Reduced appetite.",
        )


def test_treatment_requires_product_or_name() -> None:
    with pytest.raises(ValidationError):
        TreatmentRecordCreate(
            flock_id=uuid4(),
            birds_treated=10,
        )


def test_treatment_end_before_start_is_rejected() -> None:
    with pytest.raises(ValidationError):
        TreatmentRecordCreate(
            flock_id=uuid4(),
            product_name="Antibiotic",
            treatment_date=date.today(),
            end_date=date.today() - timedelta(days=1),
            birds_treated=10,
        )


def test_valid_manual_treatment_payload() -> None:
    payload = TreatmentRecordCreate(
        flock_id=uuid4(),
        product_name=" Electrolyte ",
        birds_treated=100,
        purpose="Hydration support",
    )

    assert payload.product_name == "Electrolyte"
    assert payload.birds_treated == 100
