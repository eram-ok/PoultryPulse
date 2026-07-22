from enum import StrEnum


class FarmLifecycleStatus(StrEnum):
    """Platform-controlled lifecycle states for a customer farm."""

    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DEACTIVATED = "DEACTIVATED"
