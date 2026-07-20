from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.modules.production.models import (
    DailyEggProduction,
)


def build_production_model() -> DailyEggProduction:
    """Create an in-memory production model for calculations."""

    return DailyEggProduction(
        farm_id=uuid4(),
        flock_id=uuid4(),
        production_date=date.today(),
        birds_present=1000,
        morning_eggs=400,
        afternoon_eggs=350,
        evening_eggs=200,
        large_eggs=500,
        medium_eggs=300,
        small_eggs=100,
        damaged_eggs=30,
        rejected_eggs=20,
        recorded_by=uuid4(),
        last_updated_by=uuid4(),
    )


def test_total_collected_calculation() -> None:
    production = build_production_model()

    assert production.total_collected == 950


def test_total_graded_calculation() -> None:
    production = build_production_model()

    assert production.total_graded == 950


def test_saleable_eggs_calculation() -> None:
    production = build_production_model()

    assert production.saleable_eggs == 900


def test_ungraded_eggs_calculation() -> None:
    production = build_production_model()

    assert production.ungraded_eggs == 0


def test_laying_percentage_calculation() -> None:
    production = build_production_model()

    assert production.laying_percentage == Decimal("95.00")
