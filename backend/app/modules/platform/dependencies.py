
from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_database_session
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
)
from app.core.security import decode_token
from app.modules.platform.models import PlatformUser
from app.modules.platform.repository import (
    PlatformAuthRepository,
)
from app.modules.platform.service import (
    PLATFORM_PRINCIPAL_TYPE,
)


platform_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/platform/auth/login"
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


def get_current_platform_user(
    token: Annotated[
        str,
        Depends(platform_oauth2_scheme),
    ],
    database_session: DatabaseSession,
) -> PlatformUser:
    """Load an active platform user from a platform access token."""

    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise AuthenticationError(
            "The platform access token is invalid or expired.",
            error_code="invalid_platform_access_token",
        ) from exc

    if payload.get("type") != "access":
        raise AuthenticationError(
            "A refresh token cannot access this resource.",
            error_code="incorrect_token_type",
        )

    if (
        payload.get("principal_type")
        != PLATFORM_PRINCIPAL_TYPE
    ):
        raise AuthenticationError(
            "A farm token cannot access platform resources.",
            error_code="invalid_platform_principal",
        )

    try:
        platform_user_id = UUID(str(payload["sub"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise AuthenticationError(
            "The token contains an invalid platform user.",
            error_code="invalid_platform_token_subject",
        ) from exc

    user = PlatformAuthRepository(
        database_session
    ).get_user_by_id(platform_user_id)

    if user is None:
        raise AuthenticationError(
            "The platform user no longer exists.",
            error_code="platform_token_user_not_found",
        )

    if not user.is_active:
        raise AuthenticationError(
            "This platform account is inactive.",
            error_code="inactive_platform_account",
        )

    return user


CurrentPlatformUser = Annotated[
    PlatformUser,
    Depends(get_current_platform_user),
]


def require_platform_super_admin() -> Callable[
    ...,
    PlatformUser,
]:
    """Require an active platform super administrator."""

    def dependency(
        current_user: CurrentPlatformUser,
    ) -> PlatformUser:
        if not current_user.is_super_admin:
            raise AuthorizationError(
                "Platform super-administrator access is required.",
                error_code="platform_super_admin_required",
            )

        return current_user

    return dependency


CurrentPlatformSuperAdmin = Annotated[
    PlatformUser,
    Depends(require_platform_super_admin()),
]
