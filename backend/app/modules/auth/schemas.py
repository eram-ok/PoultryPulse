from pydantic import BaseModel, Field, field_validator

from app.modules.users.schemas import (
    UserResponse,
    validate_password_strength,
)


class TokenResponse(BaseModel):
    """Access and refresh tokens returned after authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Refresh-token rotation request."""

    refresh_token: str = Field(min_length=20)


class LogoutRequest(BaseModel):
    """Refresh token that should be revoked during logout."""

    refresh_token: str = Field(min_length=20)


class ChangePasswordRequest(BaseModel):
    """Current and new passwords for an authenticated user."""

    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)

    @field_validator("new_password")
    @classmethod
    def check_new_password(cls, value: str) -> str:
        return validate_password_strength(value)
