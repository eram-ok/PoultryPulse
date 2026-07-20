from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.modules.feed.constants import (
    FeedCategory,
    FeedInventoryTransactionType,
    FeedPurchaseStatus,
    FeedUsagePeriod,
)


ALLOWED_FEED_ADJUSTMENT_TYPES = {
    FeedInventoryTransactionType.RETURN_IN,
    FeedInventoryTransactionType.SUPPLIER_RETURN_OUT,
    FeedInventoryTransactionType.ADJUSTMENT_IN,
    FeedInventoryTransactionType.ADJUSTMENT_OUT,
}


class FeedItemCreate(BaseModel):
    """Information required to register a feed item."""

    feed_code: str = Field(
        min_length=2,
        max_length=30,
    )
    name: str = Field(
        min_length=2,
        max_length=150,
    )
    category: FeedCategory = FeedCategory.OTHER
    brand: str | None = Field(
        default=None,
        max_length=120,
    )
    manufacturer: str | None = Field(
        default=None,
        max_length=150,
    )
    description: str | None = None
    reorder_level_kg: Decimal = Field(
        default=Decimal("0.000"),
        ge=0,
        max_digits=14,
        decimal_places=3,
    )

    @field_validator("feed_code")
    @classmethod
    def normalize_feed_code(cls, value: str) -> str:
        normalized = value.strip().upper().replace(" ", "-")

        if not normalized:
            raise ValueError("Feed code cannot be empty.")

        return normalized

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()

        if len(normalized) < 2:
            raise ValueError("Feed name must contain at least two characters.")

        return normalized

    @field_validator(
        "brand",
        "manufacturer",
        "description",
    )
    @classmethod
    def normalize_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None


class FeedItemUpdate(BaseModel):
    """Feed-item fields that may be updated."""

    feed_code: str | None = Field(
        default=None,
        min_length=2,
        max_length=30,
    )
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    category: FeedCategory | None = None
    brand: str | None = Field(
        default=None,
        max_length=120,
    )
    manufacturer: str | None = Field(
        default=None,
        max_length=150,
    )
    description: str | None = None
    reorder_level_kg: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=14,
        decimal_places=3,
    )

    @field_validator("feed_code")
    @classmethod
    def normalize_feed_code(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip().upper().replace(" ", "-")

        if not normalized:
            raise ValueError("Feed code cannot be empty.")

        return normalized

    @field_validator("name")
    @classmethod
    def normalize_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        if len(normalized) < 2:
            raise ValueError("Feed name must contain at least two characters.")

        return normalized


class FeedItemResponse(BaseModel):
    """Feed-item information returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    feed_code: str
    name: str
    category: FeedCategory
    brand: str | None
    manufacturer: str | None
    description: str | None
    reorder_level_kg: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


class FeedItemListResponse(BaseModel):
    """Paginated feed-item listing."""

    items: list[FeedItemResponse]
    total: int
    offset: int
    limit: int


class FeedPurchaseCreate(BaseModel):
    """Information required to receive purchased feed."""

    feed_item_id: UUID
    supplier_id: UUID | None = None
    purchase_date: date = Field(default_factory=date.today)
    invoice_number: str | None = Field(
        default=None,
        max_length=100,
    )
    quantity_kg: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=3,
    )
    unit_cost: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=14,
        decimal_places=2,
    )
    notes: str | None = None

    @field_validator("purchase_date")
    @classmethod
    def validate_purchase_date(
        cls,
        value: date,
    ) -> date:
        if value > date.today():
            raise ValueError("Purchase date cannot be in the future.")

        return value

    @field_validator("invoice_number")
    @classmethod
    def normalize_invoice_number(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip().upper()
        return normalized or None


class FeedPurchaseVoidRequest(BaseModel):
    """Reason supplied when voiding a feed purchase."""

    reason: str = Field(
        min_length=5,
        max_length=1000,
    )

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        normalized = value.strip()

        if len(normalized) < 5:
            raise ValueError("Void reason must contain at least five characters.")

        return normalized


class FeedPurchaseResponse(BaseModel):
    """Feed-purchase information returned by the API."""

    id: UUID
    farm_id: UUID
    feed_item_id: UUID
    feed_code: str
    feed_name: str
    supplier_id: UUID | None
    supplier_code: str | None
    supplier_name: str | None
    purchase_date: date
    invoice_number: str | None
    quantity_kg: Decimal
    unit_cost: Decimal
    total_cost: Decimal
    status: FeedPurchaseStatus
    notes: str | None
    created_by: UUID
    voided_by: UUID | None
    voided_at: datetime | None
    created_at: datetime
    updated_at: datetime


class FeedPurchaseListResponse(BaseModel):
    """Paginated feed-purchase listing."""

    items: list[FeedPurchaseResponse]
    total: int
    offset: int
    limit: int


class FeedUsageCreate(BaseModel):
    """Feed issued to a flock."""

    flock_id: UUID
    feed_item_id: UUID
    usage_date: date = Field(default_factory=date.today)
    feeding_period: FeedUsagePeriod = FeedUsagePeriod.OTHER
    quantity_kg: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=3,
    )
    notes: str | None = None

    @field_validator("usage_date")
    @classmethod
    def validate_usage_date(
        cls,
        value: date,
    ) -> date:
        if value > date.today():
            raise ValueError("Usage date cannot be in the future.")

        return value


class FeedUsageResponse(BaseModel):
    """Flock feed-usage information."""

    id: UUID
    farm_id: UUID
    flock_id: UUID
    flock_code: str
    flock_name: str
    feed_item_id: UUID
    feed_code: str
    feed_name: str
    usage_date: date
    feeding_period: FeedUsagePeriod
    quantity_kg: Decimal
    birds_present: int
    grams_per_bird: Decimal
    notes: str | None
    created_by: UUID
    created_at: datetime


class FeedUsageListResponse(BaseModel):
    """Paginated flock feed-usage listing."""

    items: list[FeedUsageResponse]
    total: int
    offset: int
    limit: int


class FeedInventoryAdjustmentCreate(BaseModel):
    """Manual feed-stock adjustment or return."""

    feed_item_id: UUID
    inventory_date: date = Field(default_factory=date.today)
    transaction_type: FeedInventoryTransactionType
    quantity_kg: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=3,
    )
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
        value: FeedInventoryTransactionType,
    ) -> FeedInventoryTransactionType:
        if value not in ALLOWED_FEED_ADJUSTMENT_TYPES:
            raise ValueError(
                "Use RETURN_IN, SUPPLIER_RETURN_OUT, ADJUSTMENT_IN or ADJUSTMENT_OUT."
            )

        return value


class FeedWastageCreate(BaseModel):
    """Feed lost through spillage, contamination or spoilage."""

    feed_item_id: UUID
    inventory_date: date = Field(default_factory=date.today)
    quantity_kg: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=3,
    )
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
            raise ValueError("Wastage date cannot be in the future.")

        return value


class FeedInventoryReversalCreate(BaseModel):
    """Information required to reverse a feed transaction."""

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


class FeedInventoryTransactionResponse(BaseModel):
    """One feed inventory ledger transaction."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    transaction_group_id: UUID
    feed_item_id: UUID
    feed_code: str
    feed_name: str
    inventory_date: date
    transaction_type: FeedInventoryTransactionType
    quantity_kg: Decimal
    signed_quantity_kg: Decimal
    direction: str
    source_type: str
    source_id: UUID | None
    reference: str | None
    description: str | None
    created_by: UUID
    reversed_transaction_id: UUID | None
    is_reversal: bool
    created_at: datetime


class FeedInventoryTransactionListResponse(BaseModel):
    """Paginated feed inventory ledger."""

    items: list[FeedInventoryTransactionResponse]
    total: int
    offset: int
    limit: int


class FeedInventoryBalanceItem(BaseModel):
    """Current balance and alert status for one feed item."""

    feed_item_id: UUID
    feed_code: str
    feed_name: str
    category: FeedCategory
    balance_kg: Decimal
    reorder_level_kg: Decimal
    is_low_stock: bool
    is_out_of_stock: bool
    is_active: bool


class FeedInventorySummaryResponse(BaseModel):
    """Current feed-stock summary."""

    balances: list[FeedInventoryBalanceItem]
    total_feed_kg: Decimal
    active_feed_items: int
    low_stock_items: int
    out_of_stock_items: int
