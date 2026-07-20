from enum import Enum


class ProductionRecordStatus(str, Enum):
    """Workflow status of a daily egg-production record."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    VOIDED = "VOIDED"
