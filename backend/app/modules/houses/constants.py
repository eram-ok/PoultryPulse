from enum import Enum


class PoultryHouseStatus(str, Enum):
    """Operational status of a poultry house."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    UNDER_MAINTENANCE = "UNDER_MAINTENANCE"
    CLOSED = "CLOSED"
