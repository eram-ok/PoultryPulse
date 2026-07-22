from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.modules.onboarding.constants import (
    FarmInvitationDeliveryStatus,
    FarmInvitationStatus,
)
from app.modules.users.schemas import validate_password_strength


class PlatformFarmInvitationResponse(BaseModel):
    """Platform-safe invitation metadata without its secret token."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    administrator_user_id: UUID
    issued_by_platform_user_id: UUID | None
    status: FarmInvitationStatus
    expires_at: datetime
    accepted_at: datetime | None
    revoked_at: datetime | None
    delivery_status: FarmInvitationDeliveryStatus
    delivery_attempt_count: int
    last_delivery_attempt_at: datetime | None
    last_delivery_error: str | None
    sent_at: datetime | None
    idempotency_key: str | None
    created_at: datetime
    updated_at: datetime


class PlatformFarmOnboardingStatusResponse(BaseModel):
    """Current platform view of one farm's administrator onboarding."""

    farm_id: UUID
    administrator_user_id: UUID | None
    administrator_username: str | None
    administrator_email: str | None
    administrator_is_active: bool | None
    administrator_is_verified: bool | None
    completed: bool
    legacy_completed: bool
    invitation: PlatformFarmInvitationResponse | None


class PlatformFarmInvitationIssueResponse(BaseModel):
    """One-time result for an invitation issue or reissue."""

    invitation: PlatformFarmInvitationResponse
    setup_url: str | None
    setup_url_returned_once: bool


class PlatformFarmInvitationRevokeRequest(BaseModel):
    """Reason supplied when revoking a pending invitation."""

    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=5, max_length=1000)

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 5:
            raise ValueError(
                "The revocation reason must contain at least five characters."
            )
        return normalized


class FarmInvitationTokenRequest(BaseModel):
    """Secret invitation token supplied in a request body."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=32, max_length=512)


class FarmInvitationAcceptRequest(FarmInvitationTokenRequest):
    """Invitation token and the administrator's chosen password."""

    new_password: str = Field(min_length=12, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return validate_password_strength(value)


class FarmInvitationPublicResponse(BaseModel):
    """Safe invitation information shown before account activation."""

    farm_name: str
    farm_code: str
    administrator_name: str
    administrator_username: str
    status: FarmInvitationStatus
    expires_at: datetime


class FarmInvitationAcceptResponse(BaseModel):
    """Confirmation returned after a successful one-time activation."""

    farm_code: str
    administrator_username: str
    accepted_at: datetime
    message: str
