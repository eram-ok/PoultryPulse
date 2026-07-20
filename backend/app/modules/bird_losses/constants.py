from enum import Enum


class BirdLossType(str, Enum):
    """Types of bird-population losses."""

    MORTALITY = "MORTALITY"
    CULLING = "CULLING"


class BirdLossReason(str, Enum):
    """Reasons associated with mortality or culling."""

    DISEASE = "DISEASE"
    INJURY = "INJURY"
    PREDATION = "PREDATION"
    HEAT_STRESS = "HEAT_STRESS"
    COLD_STRESS = "COLD_STRESS"
    SUFFOCATION = "SUFFOCATION"
    STARVATION = "STARVATION"
    DEHYDRATION = "DEHYDRATION"
    POISONING = "POISONING"
    LOW_PRODUCTION = "LOW_PRODUCTION"
    DEFORMITY = "DEFORMITY"
    OLD_AGE = "OLD_AGE"
    AGGRESSION = "AGGRESSION"
    VETERINARY_RECOMMENDATION = "VETERINARY_RECOMMENDATION"
    UNKNOWN = "UNKNOWN"
    OTHER = "OTHER"


class BirdDisposalMethod(str, Enum):
    """Methods used to dispose of dead or culled birds."""

    BURIAL = "BURIAL"
    INCINERATION = "INCINERATION"
    COMPOSTING = "COMPOSTING"
    RENDERING = "RENDERING"
    VETERINARY_DISPOSAL = "VETERINARY_DISPOSAL"
    SOLD_FOR_SLAUGHTER = "SOLD_FOR_SLAUGHTER"
    HOME_CONSUMPTION = "HOME_CONSUMPTION"
    OTHER = "OTHER"
    NOT_RECORDED = "NOT_RECORDED"


class BirdLossRecordStatus(str, Enum):
    """Audit status of a mortality or culling record."""

    ACTIVE = "ACTIVE"
    REVERSED = "REVERSED"
