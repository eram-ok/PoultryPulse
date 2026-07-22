
import re
from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from app.modules.users.schemas import validate_password_strength


class PlatformUserResponse(BaseModel):
    """Platform user returned by the platform authentication API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    is_active: bool
    is_super_admin: bool
    must_change_password: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PlatformTokenResponse(BaseModel):
    """Access and refresh tokens for a platform identity."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: PlatformUserResponse


class PlatformRefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class PlatformLogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class PlatformChangePasswordRequest(BaseModel):
    current_password: str = Field(
        min_length=1,
        max_length=128,
    )
    new_password: str = Field(
        min_length=12,
        max_length=128,
    )

    @field_validator("new_password")
    @classmethod
    def check_new_password(cls, value: str) -> str:
        return validate_password_strength(value)


def normalize_platform_username(value: str) -> str:
    normalized = value.strip().lower()

    if not re.fullmatch(r"[a-z0-9._-]+", normalized):
        raise ValueError(
            "Username may only contain letters, numbers, "
            "dots, underscores and hyphens."
        )

    return normalized


class PlatformBootstrapIdentity(BaseModel):
    """Validated fields used by the secure bootstrap script."""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return normalize_platform_username(value)

    @field_validator("first_name", "last_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name cannot be empty.")
        return normalized

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return validate_password_strength(value)
