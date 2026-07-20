from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.feed.constants import (
    FeedInventoryTransactionType,
    NEGATIVE_FEED_TRANSACTION_TYPES,
    POSITIVE_FEED_TRANSACTION_TYPES,
)
from app.modules.feed.models import (
    FeedInventoryTransaction,
    FeedPurchase,
    get_signed_feed_quantity,
)


def test_feed_purchase_total_cost() -> None:
    purchase = FeedPurchase(
        farm_id=uuid4(),
        feed_item_id=uuid4(),
        supplier_id=uuid4(),
        purchase_date=date.today(),
        quantity_kg=Decimal("1000.000"),
        unit_cost=Decimal("2000.00"),
        created_by=uuid4(),
    )

    assert purchase.total_cost == Decimal("2000000.00")


def test_positive_feed_transaction_quantity() -> None:
    signed_quantity = get_signed_feed_quantity(
        FeedInventoryTransactionType.PURCHASE_IN.value,
        Decimal("500.000"),
    )

    assert signed_quantity == Decimal("500.000")


def test_negative_feed_transaction_quantity() -> None:
    signed_quantity = get_signed_feed_quantity(
        FeedInventoryTransactionType.USAGE_OUT.value,
        Decimal("55.500"),
    )

    assert signed_quantity == Decimal("-55.500")


def test_reversal_requires_explicit_quantity() -> None:
    with pytest.raises(ValueError):
        get_signed_feed_quantity(
            FeedInventoryTransactionType.REVERSAL.value,
            Decimal("100.000"),
        )


def test_positive_feed_transaction_types() -> None:
    assert "PURCHASE_IN" in (POSITIVE_FEED_TRANSACTION_TYPES)

    assert "ADJUSTMENT_IN" in (POSITIVE_FEED_TRANSACTION_TYPES)


def test_negative_feed_transaction_types() -> None:
    assert "USAGE_OUT" in (NEGATIVE_FEED_TRANSACTION_TYPES)

    assert "WASTAGE_OUT" in (NEGATIVE_FEED_TRANSACTION_TYPES)


def test_feed_inventory_direction() -> None:
    transaction = FeedInventoryTransaction(
        farm_id=uuid4(),
        transaction_group_id=uuid4(),
        feed_item_id=uuid4(),
        inventory_date=date.today(),
        transaction_type="USAGE_OUT",
        quantity_kg=Decimal("25.000"),
        signed_quantity_kg=Decimal("-25.000"),
        source_type="FLOCK_FEED_USAGE",
        source_id=uuid4(),
        created_by=uuid4(),
    )

    assert transaction.direction == "OUT"
    assert transaction.is_reversal is False


def test_feed_inventory_reversal_flag() -> None:
    transaction = FeedInventoryTransaction(
        farm_id=uuid4(),
        transaction_group_id=uuid4(),
        feed_item_id=uuid4(),
        inventory_date=date.today(),
        transaction_type="REVERSAL",
        quantity_kg=Decimal("25.000"),
        signed_quantity_kg=Decimal("25.000"),
        source_type="FEED_TRANSACTION_REVERSAL",
        source_id=uuid4(),
        created_by=uuid4(),
    )

    assert transaction.is_reversal is True
