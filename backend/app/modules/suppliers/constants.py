from enum import Enum


class SupplierType(str, Enum):
    """Categories of suppliers used by PoultryPulse."""

    BIRD_SUPPLIER = "BIRD_SUPPLIER"
    FEED_SUPPLIER = "FEED_SUPPLIER"
    MEDICINE_SUPPLIER = "MEDICINE_SUPPLIER"
    EQUIPMENT_SUPPLIER = "EQUIPMENT_SUPPLIER"
    GENERAL_SUPPLIER = "GENERAL_SUPPLIER"
