from enum import Enum


class HealthProductType(str, Enum):
    """Types of veterinary products used by a farm."""

    VACCINE = "VACCINE"
    ANTIBIOTIC = "ANTIBIOTIC"
    ANTIPARASITIC = "ANTIPARASITIC"
    ANTIFUNGAL = "ANTIFUNGAL"
    VITAMIN = "VITAMIN"
    MINERAL = "MINERAL"
    ELECTROLYTE = "ELECTROLYTE"
    DISINFECTANT = "DISINFECTANT"
    PROBIOTIC = "PROBIOTIC"
    OTHER = "OTHER"


class VaccinationRoute(str, Enum):
    """Methods used to administer poultry vaccines."""

    DRINKING_WATER = "DRINKING_WATER"
    EYE_DROP = "EYE_DROP"
    SPRAY = "SPRAY"
    INJECTION = "INJECTION"
    FEED = "FEED"
    WING_WEB = "WING_WEB"
    NASAL_DROP = "NASAL_DROP"
    OTHER = "OTHER"


class VaccinationScheduleStatus(str, Enum):
    """Current workflow status of a vaccination schedule."""

    SCHEDULED = "SCHEDULED"
    DUE = "DUE"
    COMPLETED = "COMPLETED"
    MISSED = "MISSED"
    CANCELLED = "CANCELLED"


class HealthIncidentSeverity(str, Enum):
    """Severity assigned to a poultry health incident."""

    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class HealthIncidentStatus(str, Enum):
    """Current workflow status of a health incident."""

    OPEN = "OPEN"
    UNDER_TREATMENT = "UNDER_TREATMENT"
    MONITORING = "MONITORING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class TreatmentStatus(str, Enum):
    """Current status of a flock treatment."""

    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
