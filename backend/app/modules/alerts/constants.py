from enum import StrEnum


class AlertStatus(StrEnum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class AlertDeliveryChannel(StrEnum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"


class AlertRefreshStatus(StrEnum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
