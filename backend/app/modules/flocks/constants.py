from enum import Enum


class FlockProductionStage(str, Enum):
    """Current production stage of a poultry flock."""

    BROODING = "BROODING"
    GROWING = "GROWING"
    POINT_OF_LAY = "POINT_OF_LAY"
    LAYING = "LAYING"
    MOLTING = "MOLTING"
    DEPLETED = "DEPLETED"
    SOLD = "SOLD"


class FlockStatus(str, Enum):
    """Operational status of a flock."""

    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DEPLETED = "DEPLETED"
    SOLD = "SOLD"
    ARCHIVED = "ARCHIVED"


class PopulationTransactionType(str, Enum):
    """Types of bird-population movements."""

    INITIAL_PLACEMENT = "INITIAL_PLACEMENT"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    MORTALITY = "MORTALITY"
    CULLING = "CULLING"
    BIRD_SALE = "BIRD_SALE"
    ADJUSTMENT_IN = "ADJUSTMENT_IN"
    ADJUSTMENT_OUT = "ADJUSTMENT_OUT"
    REVERSAL = "REVERSAL"
