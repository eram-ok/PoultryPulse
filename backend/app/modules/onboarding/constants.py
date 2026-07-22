from enum import Enum


class FarmInvitationStatus(str, Enum):
    """Lifecycle states for a farm administrator invitation."""

    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class FarmInvitationDeliveryStatus(str, Enum):
    """Email-delivery states for a farm administrator invitation."""

    NOT_CONFIGURED = "NOT_CONFIGURED"
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
