from datetime import date, datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.modules.eggs.constants import (
    EggGrade,
    EggInventoryTransactionType,
)


ALLOWED_ADJUSTMENT_TYPES = {
    EggInventoryTransactionType.ADJUSTMENT_IN,
    EggInventoryTransactionType.ADJUSTMENT_OUT,
}

ALLOWED_ISSUE_TYPES = {
    EggInventoryTransactionType.INTERNAL_USE_OUT,
    EggInventoryTransactionType.DONATION_OUT,
    EggInventoryTransactionType.DAMAGE_OUT,
}


class EggInventoryAdjustmentCreate(BaseModel):
    """Manual increase or reduction of egg stock."""

    inventory_date: date = Field(default_factory=date.today)
    egg_grade: EggGrade
    transaction_type: EggInventoryTransactionType
    quantity: int = Field(gt=0, le=100_000_000)
    reference: str | None = Field(
        default=None,
        max_length=100,
    )
    description: str = Field(
        min_length=5,
        max_length=1000,
    )

    @field_validator("inventory_date")
    @classmethod
    def validate_inventory_date(
        cls,
        value: date,
    ) -> date:
        if value > date.today():
            raise ValueError("Inventory date cannot be in the future.")

        return value

    @field_validator("transaction_type")
    @classmethod
    def validate_transaction_type(
        cls,
        value: EggInventoryTransactionType,
    ) -> EggInventoryTransactionType:
        if value not in ALLOWED_ADJUSTMENT_TYPES:
            raise ValueError(
                "Only ADJUSTMENT_IN or ADJUSTMENT_OUT "
                "may be used for an inventory adjustment."
            )

        return value

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        normalized = value.strip()

        if len(normalized) < 5:
            raise ValueError("Description must contain at least five characters.")

        return normalized


class EggInventoryIssueCreate(BaseModel):
    """Egg stock issued for use, donation or disposal."""

    inventory_date: date = Field(default_factory=date.today)
    egg_grade: EggGrade
    transaction_type: EggInventoryTransactionType
    quantity: int = Field(gt=0, le=100_000_000)
    reference: str | None = Field(
        default=None,
        max_length=100,
    )
    description: str = Field(
        min_length=5,
        max_length=1000,
    )

    @field_validator("inventory_date")
    @classmethod
    def validate_inventory_date(
        cls,
        value: date,
    ) -> date:
        if value > date.today():
            raise ValueError("Inventory date cannot be in the future.")

        return value

    @field_validator("transaction_type")
    @classmethod
    def validate_transaction_type(
        cls,
        value: EggInventoryTransactionType,
    ) -> EggInventoryTransactionType:
        if value not in ALLOWED_ISSUE_TYPES:
            raise ValueError(
                "Only INTERNAL_USE_OUT, DONATION_OUT or DAMAGE_OUT may be used here."
            )

        return value

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        normalized = value.strip()

        if len(normalized) < 5:
            raise ValueError("Description must contain at least five characters.")

        return normalized


class EggInventoryReversalCreate(BaseModel):
    """Information required to reverse a transaction."""

    inventory_date: date = Field(default_factory=date.today)
    reason: str = Field(
        min_length=5,
        max_length=1000,
    )

    @field_validator("inventory_date")
    @classmethod
    def validate_inventory_date(
        cls,
        value: date,
    ) -> date:
        if value > date.today():
            raise ValueError("Reversal date cannot be in the future.")

        return value

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        normalized = value.strip()

        if len(normalized) < 5:
            raise ValueError("Reversal reason must contain at least five characters.")

        return normalized


class EggInventoryTransactionResponse(BaseModel):
    """One egg-inventory ledger transaction."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    transaction_group_id: UUID
    inventory_date: date
    egg_grade: EggGrade
    transaction_type: EggInventoryTransactionType
    quantity: int
    signed_quantity: int
    direction: str
    source_type: str
    source_id: UUID | None
    reference: str | None
    description: str | None
    created_by: UUID
    reversed_transaction_id: UUID | None
    is_reversal: bool
    created_at: datetime


class EggInventoryTransactionListResponse(BaseModel):
    """Paginated egg-inventory transaction listing."""

    items: list[EggInventoryTransactionResponse]
    total: int
    offset: int
    limit: int


class EggInventoryBalanceItem(BaseModel):
    """Current egg-stock balance for one grade."""

    egg_grade: EggGrade
    balance_eggs: int
    trays: int
    loose_eggs: int
    eggs_per_tray: int
    is_saleable: bool


class EggInventorySummaryResponse(BaseModel):
    """Current egg inventory across all grades."""

    eggs_per_tray: int
    balances: list[EggInventoryBalanceItem]

    total_saleable_eggs: int
    total_saleable_trays: int
    total_saleable_loose_eggs: int

    total_non_saleable_eggs: int
    total_all_eggs: int
