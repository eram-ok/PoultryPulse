from enum import StrEnum


class CustomerStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLOCKED = "BLOCKED"


class SaleStatus(StrEnum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    PARTIALLY_RETURNED = "PARTIALLY_RETURNED"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"


class SalePaymentTerms(StrEnum):
    CASH = "CASH"
    CREDIT = "CREDIT"


class EggSaleUnit(StrEnum):
    PIECE = "PIECE"
    TRAY = "TRAY"
    CRATE = "CRATE"


class PaymentMethod(StrEnum):
    CASH = "CASH"
    MOBILE_MONEY = "MOBILE_MONEY"
    BANK_TRANSFER = "BANK_TRANSFER"
    CHEQUE = "CHEQUE"
    OTHER = "OTHER"


class PaymentStatus(StrEnum):
    POSTED = "POSTED"
    REVERSED = "REVERSED"


class SaleReturnStatus(StrEnum):
    POSTED = "POSTED"
    REVERSED = "REVERSED"


class CustomerLedgerEntryType(StrEnum):
    OPENING_BALANCE = "OPENING_BALANCE"
    SALE = "SALE"
    PAYMENT = "PAYMENT"
    SALE_RETURN = "SALE_RETURN"
    ADJUSTMENT = "ADJUSTMENT"
    REVERSAL = "REVERSAL"
