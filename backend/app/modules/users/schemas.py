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


def validate_password_strength(password: str) -> str:
    """Validate a user password against PoultryPulse rules."""

    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters.")

    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain an uppercase letter.")

    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain a lowercase letter.")

    if not re.search(r"\d", password):
        raise ValueError("Password must contain a number.")

    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValueError("Password must contain a special character.")

    return password


class PermissionResponse(BaseModel):
    """Permission information returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    module: str
    name: str
    description: str | None


class RoleResponse(BaseModel):
    """Role information returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    name: str
    description: str | None
    is_system_role: bool
    is_active: bool
    permissions: list[PermissionResponse]


class UserCreate(BaseModel):
    """Information required to create a user."""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr | None = None
    telephone: str | None = Field(default=None, max_length=30)
    password: str = Field(min_length=12, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role_ids: list[UUID] = Field(min_length=1)
    must_change_password: bool = True

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        normalized = value.strip().lower()

        if not re.fullmatch(r"[a-z0-9._-]+", normalized):
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

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return validate_password_strength(value)


class UserUpdate(BaseModel):
    """User profile fields that administrators may update."""

    email: EmailStr | None = None
    telephone: str | None = Field(default=None, max_length=30)
    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    last_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    is_verified: bool | None = None
    must_change_password: bool | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def normalize_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        if not normalized:
            raise ValueError("Name cannot be empty.")

        return normalized


class UserResponse(BaseModel):
    """Complete user information returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    username: str
    email: str | None
    telephone: str | None
    first_name: str
    last_name: str
    full_name: str
    is_active: bool
    is_verified: bool
    must_change_password: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
    roles: list[RoleResponse]


class UserListResponse(BaseModel):
    """Paginated user listing."""

    items: list[UserResponse]
    total: int
    offset: int
    limit: int
