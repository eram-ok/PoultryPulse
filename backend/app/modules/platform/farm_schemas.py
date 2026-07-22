from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from app.modules.farms.constants import FarmLifecycleStatus
from app.modules.farms.schemas import (
    FarmCreate,
    FarmSettingsResponse,
    FarmUpdate,
)

class PlatformFirstFarmAdministratorCreate(BaseModel):
    """Identity details for the first administrator of a farm."""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    telephone: str | None = Field(
        default=None,
        max_length=30,
    )
    first_name: str = Field(
        min_length=1,
        max_length=100,
    )
    last_name: str = Field(
        min_length=1,
        max_length=100,
    )

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        normalized = value.strip().lower()

        import re

        if not re.fullmatch(
            r"[a-z0-9._-]+",
            normalized,
        ):
            raise ValueError(
                "Username may only contain letters, numbers, "
                "dots, underscores and hyphens."
            )

        return normalized

    @field_validator("first_name", "last_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name cannot be empty.")
        return normalized

    @field_validator("telephone")
    @classmethod
    def normalize_telephone(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None


class PlatformFarmCreateRequest(FarmCreate):
    """Create a farm and its first farm administrator."""

    first_administrator: PlatformFirstFarmAdministratorCreate


class PlatformFarmUpdateRequest(FarmUpdate):
    """Platform-safe farm profile fields."""

    model_config = ConfigDict(extra="forbid")


class PlatformLifecycleReasonRequest(BaseModel):
    """Required reason for a restrictive lifecycle action."""

    model_config = ConfigDict(extra="forbid")

    reason: str = Field(
        min_length=5,
        max_length=1000,
    )

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 5:
            raise ValueError(
                "The lifecycle reason must contain "
                "at least five characters."
            )
        return normalized


class PlatformActivationRequest(BaseModel):
    """Optional note supplied when activating a farm."""

    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(
        default=None,
        max_length=1000,
    )

    @field_validator("reason")
    @classmethod
    def normalize_reason(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None


class PlatformFarmAdministratorResponse(BaseModel):
    """First farm administrator returned without a password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    username: str
    email: str | None
    telephone: str | None
    first_name: str
    last_name: str
    is_active: bool
    is_verified: bool
    must_change_password: bool


class PlatformFarmSummaryResponse(BaseModel):
    """Farm profile, lifecycle state and platform-safe usage totals."""

    id: UUID
    farm_code: str
    name: str
    owner_name: str | None
    telephone: str | None
    email: str | None
    district: str | None
    address: str | None
    logo_url: str | None
    timezone: str
    currency_code: str
    is_active: bool
    lifecycle_status: FarmLifecycleStatus
    lifecycle_reason: str | None
    lifecycle_changed_at: datetime
    lifecycle_changed_by_platform_user_id: UUID | None
    suspended_at: datetime | None
    deactivated_at: datetime | None
    created_at: datetime
    updated_at: datetime
    total_users: int
    active_users: int
    recent_login_users: int
    active_refresh_sessions: int
    last_login_at: datetime | None


class PlatformFarmDetailResponse(
    PlatformFarmSummaryResponse
):
    """Complete platform view of a registered farm."""

    settings: FarmSettingsResponse | None


class PlatformFarmListResponse(BaseModel):
    """Paginated platform-level farm listing."""

    items: list[PlatformFarmSummaryResponse]
    total: int
    offset: int
    limit: int
    recent_login_window_days: int


class PlatformFarmOnboardingResponse(BaseModel):
    """One-time farm onboarding result."""

    farm: PlatformFarmDetailResponse
    administrator: PlatformFarmAdministratorResponse
    temporary_password: str = Field(
        min_length=12,
        max_length=128,
        description=(
            "Generated temporary password returned once. "
            "It is never stored in plain text."
        ),
    )
