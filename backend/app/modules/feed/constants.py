from enum import Enum


class FeedCategory(str, Enum):
    """Feed categories supported by PoultryPulse."""

    CHICK_STARTER = "CHICK_STARTER"
    GROWERS_MASH = "GROWERS_MASH"
    LAYERS_MASH = "LAYERS_MASH"
    BROILER_STARTER = "BROILER_STARTER"
    BROILER_FINISHER = "BROILER_FINISHER"
    CONCENTRATE = "CONCENTRATE"
    SUPPLEMENT = "SUPPLEMENT"
    OTHER = "OTHER"


class FeedPurchaseStatus(str, Enum):
    """Current status of a feed purchase."""

    RECEIVED = "RECEIVED"
    VOIDED = "VOIDED"


class FeedUsagePeriod(str, Enum):
    """Feeding period for a flock feed-usage record."""

    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    EVENING = "EVENING"
    OTHER = "OTHER"


class FeedInventoryTransactionType(str, Enum):
    """Types of feed-stock movements."""

    PURCHASE_IN = "PURCHASE_IN"
    RETURN_IN = "RETURN_IN"
    USAGE_OUT = "USAGE_OUT"
    WASTAGE_OUT = "WASTAGE_OUT"
    SUPPLIER_RETURN_OUT = "SUPPLIER_RETURN_OUT"
    ADJUSTMENT_IN = "ADJUSTMENT_IN"
    ADJUSTMENT_OUT = "ADJUSTMENT_OUT"
    REVERSAL = "REVERSAL"


POSITIVE_FEED_TRANSACTION_TYPES = {
    FeedInventoryTransactionType.PURCHASE_IN.value,
    FeedInventoryTransactionType.RETURN_IN.value,
    FeedInventoryTransactionType.ADJUSTMENT_IN.value,
}


NEGATIVE_FEED_TRANSACTION_TYPES = {
    FeedInventoryTransactionType.USAGE_OUT.value,
    FeedInventoryTransactionType.WASTAGE_OUT.value,
    FeedInventoryTransactionType.SUPPLIER_RETURN_OUT.value,
    FeedInventoryTransactionType.ADJUSTMENT_OUT.value,
}
