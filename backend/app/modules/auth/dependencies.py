from app.modules.audit.context import bind_audit_actor
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
from app.modules.auth.repository import AuthRepository
from app.modules.users.models import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    database_session: DatabaseSession,
) -> User:
    """Load the active user represented by an access token."""

    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise AuthenticationError(
            "The access token is invalid or expired.",
            error_code="invalid_access_token",
        ) from exc

    if payload.get("type") != "access":
        raise AuthenticationError(
            "A refresh token cannot access this resource.",
            error_code="incorrect_token_type",
        )

    principal_type = payload.get("principal_type")
    if principal_type not in {None, "farm_user"}:
        raise AuthenticationError(
            "A platform token cannot access farm resources.",
            error_code="invalid_farm_principal",
        )

    if principal_type is None and payload.get("farm_id") is None:
        raise AuthenticationError(
            "The token does not represent a farm user.",
            error_code="invalid_farm_principal",
        )

    try:
        user_id = UUID(str(payload["sub"]))
    except (TypeError, ValueError) as exc:
        raise AuthenticationError(
            "The token contains an invalid user identifier.",
            error_code="invalid_token_subject",
        ) from exc

    user = AuthRepository(database_session).get_user_by_id(user_id)

    if user is None:
        raise AuthenticationError(
            "The user represented by this token no longer exists.",
            error_code="token_user_not_found",
        )

    if not user.is_active:
        raise AuthenticationError(
            "This user account is inactive.",
            error_code="inactive_account",
        )

    farm = AuthRepository(
        database_session
    ).get_farm_by_id(user.farm_id)

    if farm is None or not farm.is_active:
        raise AuthenticationError(
            "This farm account is inactive.",
            error_code="inactive_farm",
        )

    if str(user.farm_id) != str(payload.get("farm_id")):
        raise AuthenticationError(
            "The token does not belong to this farm.",
            error_code="token_farm_mismatch",
        )

    bind_audit_actor(
        user_id=user.id,
        farm_id=user.farm_id,
        username=user.username,
    )
    return user


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]


def require_permissions(
    *permission_codes: str,
) -> Callable[..., User]:
    """Create a dependency requiring all supplied permissions."""

    def permission_dependency(
        current_user: CurrentUser,
    ) -> User:
        missing_permissions = [
            permission_code
            for permission_code in permission_codes
            if not current_user.has_permission(permission_code)
        ]

        if missing_permissions:
            raise AuthorizationError(
                "You do not have permission to perform this action.",
                error_code="required_permission_missing",
            )

        return current_user

    return permission_dependency
