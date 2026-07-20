from datetime import date
from uuid import uuid4

import pytest

from app.modules.eggs.constants import (
    EggInventoryTransactionType,
    NEGATIVE_EGG_TRANSACTION_TYPES,
    POSITIVE_EGG_TRANSACTION_TYPES,
    SALEABLE_EGG_GRADES,
)
from app.modules.eggs.models import (
    EggInventoryTransaction,
    get_signed_egg_quantity,
    validate_egg_grade,
)


def test_positive_inventory_transaction_quantity() -> None:
    signed_quantity = get_signed_egg_quantity(
        EggInventoryTransactionType.PRODUCTION_IN.value,
        500,
    )

    assert signed_quantity == 500


def test_negative_inventory_transaction_quantity() -> None:
    signed_quantity = get_signed_egg_quantity(
        EggInventoryTransactionType.INTERNAL_USE_OUT.value,
        20,
    )

    assert signed_quantity == -20


def test_reversal_requires_explicit_quantity() -> None:
    with pytest.raises(ValueError):
        get_signed_egg_quantity(
            EggInventoryTransactionType.REVERSAL.value,
            100,
        )


def test_saleable_egg_grades() -> None:
    assert SALEABLE_EGG_GRADES == {
        "LARGE",
        "MEDIUM",
        "SMALL",
    }


def test_positive_transaction_types() -> None:
    assert "PRODUCTION_IN" in (POSITIVE_EGG_TRANSACTION_TYPES)

    assert "ADJUSTMENT_IN" in (POSITIVE_EGG_TRANSACTION_TYPES)


def test_negative_transaction_types() -> None:
    assert "SALE_OUT" in (NEGATIVE_EGG_TRANSACTION_TYPES)

    assert "DAMAGE_OUT" in (NEGATIVE_EGG_TRANSACTION_TYPES)


def test_validate_supported_egg_grade() -> None:
    assert validate_egg_grade("LARGE") == "LARGE"


def test_invalid_egg_grade_is_rejected() -> None:
    with pytest.raises(ValueError):
        validate_egg_grade("EXTRA_LARGE")


def test_inventory_transaction_direction() -> None:
    transaction = EggInventoryTransaction(
        farm_id=uuid4(),
        transaction_group_id=uuid4(),
        inventory_date=date.today(),
        egg_grade="MEDIUM",
        transaction_type="ADJUSTMENT_OUT",
        quantity=25,
        signed_quantity=-25,
        source_type="MANUAL_ADJUSTMENT",
        source_id=None,
        created_by=uuid4(),
    )

    assert transaction.direction == "OUT"
    assert transaction.is_reversal is False
