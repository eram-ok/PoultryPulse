from enum import Enum


class EggGrade(str, Enum):
    """Egg grades tracked in PoultryPulse inventory."""

    LARGE = "LARGE"
    MEDIUM = "MEDIUM"
    SMALL = "SMALL"
    DAMAGED = "DAMAGED"
    REJECTED = "REJECTED"


class EggInventoryTransactionType(str, Enum):
    """Types of egg-stock movements."""

    PRODUCTION_IN = "PRODUCTION_IN"
    SALE_OUT = "SALE_OUT"
    SALE_RETURN_IN = "SALE_RETURN_IN"
    INTERNAL_USE_OUT = "INTERNAL_USE_OUT"
    DONATION_OUT = "DONATION_OUT"
    DAMAGE_OUT = "DAMAGE_OUT"
    ADJUSTMENT_IN = "ADJUSTMENT_IN"
    ADJUSTMENT_OUT = "ADJUSTMENT_OUT"
    REVERSAL = "REVERSAL"


SALEABLE_EGG_GRADES = {
    EggGrade.LARGE.value,
    EggGrade.MEDIUM.value,
    EggGrade.SMALL.value,
}


POSITIVE_EGG_TRANSACTION_TYPES = {
    EggInventoryTransactionType.PRODUCTION_IN.value,
    EggInventoryTransactionType.SALE_RETURN_IN.value,
    EggInventoryTransactionType.ADJUSTMENT_IN.value,
}


NEGATIVE_EGG_TRANSACTION_TYPES = {
    EggInventoryTransactionType.SALE_OUT.value,
    EggInventoryTransactionType.INTERNAL_USE_OUT.value,
    EggInventoryTransactionType.DONATION_OUT.value,
    EggInventoryTransactionType.DAMAGE_OUT.value,
    EggInventoryTransactionType.ADJUSTMENT_OUT.value,
}
