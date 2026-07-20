from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.bird_losses.models import (
    BirdLossRecord,
    calculate_bird_loss_percentage,
    calculate_population_after,
)


def test_population_after_mortality() -> None:
    population_after = calculate_population_after(
        population_before=1000,
        quantity=5,
    )

    assert population_after == 995


def test_loss_percentage_calculation() -> None:
    percentage = calculate_bird_loss_percentage(
        quantity=5,
        population_before=1000,
    )

    assert percentage == Decimal("0.5000")


def test_loss_percentage_rounding() -> None:
    percentage = calculate_bird_loss_percentage(
        quantity=5,
        population_before=990,
    )

    assert percentage == Decimal("0.5051")


def test_zero_loss_quantity_is_rejected() -> None:
    with pytest.raises(ValueError):
        calculate_population_after(
            population_before=1000,
            quantity=0,
        )


def test_loss_cannot_exceed_population() -> None:
    with pytest.raises(ValueError):
        calculate_population_after(
            population_before=100,
            quantity=101,
        )


def test_zero_population_is_rejected() -> None:
    with pytest.raises(ValueError):
        calculate_bird_loss_percentage(
            quantity=1,
            population_before=0,
        )


def test_mortality_record_properties() -> None:
    record = BirdLossRecord(
        farm_id=uuid4(),
        flock_id=uuid4(),
        loss_date=date.today(),
        loss_type="MORTALITY",
        quantity=5,
        reason_category="DISEASE",
        disposal_method="BURIAL",
        population_before=1000,
        population_after=995,
        loss_percentage=Decimal("0.5000"),
        status="ACTIVE",
        population_transaction_id=uuid4(),
        recorded_by=uuid4(),
    )

    assert record.is_mortality is True
    assert record.is_culling is False
    assert record.is_reversed is False


def test_culling_record_properties() -> None:
    record = BirdLossRecord(
        farm_id=uuid4(),
        flock_id=uuid4(),
        loss_date=date.today(),
        loss_type="CULLING",
        quantity=10,
        reason_category="LOW_PRODUCTION",
        disposal_method="SOLD_FOR_SLAUGHTER",
        population_before=1000,
        population_after=990,
        loss_percentage=Decimal("1.0000"),
        status="ACTIVE",
        population_transaction_id=uuid4(),
        recorded_by=uuid4(),
    )

    assert record.is_culling is True
    assert record.is_mortality is False
