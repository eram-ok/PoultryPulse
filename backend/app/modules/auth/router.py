from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_database_session
from app.core.network import resolve_client_ip
from app.modules.audit.constants import (
    AuditAction,
    AuditOutcome,
    AuditSeverity,
)
from app.modules.audit.integration import (
    record_audit_safely,
    record_failure_safely,
    token_identity,
    user_snapshot,
)
from app.modules.auth.dependencies import CurrentUser
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    LogoutRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from app.modules.auth.service import AuthService
from app.modules.users.schemas import UserResponse


settings = get_settings()


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


def get_client_ip(request: Request) -> str | None:
    return resolve_client_ip(
        request,
        trusted_proxy_entries=settings.trusted_proxy_list,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in to PoultryPulse",
)
def login(
    request: Request,
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    database_session: DatabaseSession,
) -> TokenResponse:
    """Authenticate a user and return access and refresh tokens."""

    service = AuthService(database_session)
    farm_code, identifier = service.parse_login_identifier(form_data.username)
    candidates = service.repository.find_login_candidates(
        identifier,
        farm_code=farm_code,
    )
    candidate = candidates[0] if len(candidates) == 1 else None
    metadata = {
        "identifier": identifier,
        "farm_code": farm_code,
        "candidate_count": len(candidates),
    }

    try:
        response = service.login(
            supplied_identifier=form_data.username,
            password=form_data.password,
            created_ip=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except Exception as error:
        record_failure_safely(
            database_session,
            module="auth",
            action=AuditAction.LOGIN_FAILED,
            description="A PoultryPulse login attempt failed.",
            error=error,
            farm_id=(candidate.farm_id if candidate is not None else None),
            actor_user_id=(candidate.id if candidate is not None else None),
            actor_username=(
                candidate.username if candidate is not None else identifier
            ),
            resource_type="User",
            resource_id=(candidate.id if candidate is not None else None),
            metadata=metadata,
        )
        raise

    record_audit_safely(
        database_session,
        module="auth",
        action=AuditAction.LOGIN,
        description="User logged in to PoultryPulse.",
        outcome=AuditOutcome.SUCCESS,
        severity=AuditSeverity.INFO,
        farm_id=response.user.farm_id,
        actor_user_id=response.user.id,
        actor_username=response.user.username,
        resource_type="User",
        resource_id=response.user.id,
        after_values=(
            user_snapshot(candidate)
            if candidate is not None
            else {
                "id": response.user.id,
                "farm_id": response.user.farm_id,
                "username": response.user.username,
            }
        ),
        metadata={
            "authentication_method": "password",
            "farm_code": farm_code,
        },
    )
    return response


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh an authentication session",
)
def refresh_token(
    request: Request,
    payload: RefreshTokenRequest,
    database_session: DatabaseSession,
) -> TokenResponse:
    """Rotate a valid refresh token and issue new tokens."""

    identity = token_identity(payload.refresh_token)

    try:
        response = AuthService(database_session).refresh(
            payload.refresh_token,
            created_ip=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except Exception as error:
        record_failure_safely(
            database_session,
            module="auth",
            action=AuditAction.TOKEN_REFRESH,
            description="A session-token refresh failed.",
            error=error,
            farm_id=identity["farm_id"],
            actor_user_id=identity["user_id"],
            actor_username=identity["username"],
            resource_type="RefreshToken",
            metadata={
                "token_decoded": identity["decoded"],
                "token_type": identity["token_type"],
            },
        )
        raise

    record_audit_safely(
        database_session,
        module="auth",
        action=AuditAction.TOKEN_REFRESH,
        description="Authentication tokens were rotated.",
        farm_id=response.user.farm_id,
        actor_user_id=response.user.id,
        actor_username=response.user.username,
        resource_type="User",
        resource_id=response.user.id,
        metadata={
            "token_decoded": identity["decoded"],
            "token_type": identity["token_type"],
        },
    )
    return response


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out and revoke a refresh token",
)
def logout(
    payload: LogoutRequest,
    database_session: DatabaseSession,
) -> Response:
    """Revoke a refresh token."""

    identity = token_identity(payload.refresh_token)

    try:
        AuthService(database_session).logout(payload.refresh_token)
    except Exception as error:
        record_failure_safely(
            database_session,
            module="auth",
            action=AuditAction.LOGOUT,
            description="A logout operation failed.",
            error=error,
            farm_id=identity["farm_id"],
            actor_user_id=identity["user_id"],
            actor_username=identity["username"],
            resource_type="RefreshToken",
            metadata={
                "token_decoded": identity["decoded"],
                "token_type": identity["token_type"],
            },
        )
        raise

    record_audit_safely(
        database_session,
        module="auth",
        action=AuditAction.LOGOUT,
        description="User logged out of PoultryPulse.",
        farm_id=identity["farm_id"],
        actor_user_id=identity["user_id"],
        actor_username=identity["username"],
        resource_type="User",
        resource_id=identity["user_id"],
        metadata={
            "token_decoded": identity["decoded"],
            "token_type": identity["token_type"],
        },
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current user",
)
def get_me(
    current_user: CurrentUser,
) -> UserResponse:
    """Return the authenticated user's profile and roles."""

    return UserResponse.model_validate(current_user)


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change the current user's password",
)
def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUser,
    database_session: DatabaseSession,
) -> Response:
    """Change a password and revoke existing refresh tokens."""

    try:
        AuthService(database_session).change_password(
            current_user,
            payload.current_password,
            payload.new_password,
        )
    except Exception as error:
        record_failure_safely(
            database_session,
            module="auth",
            action=AuditAction.PASSWORD_CHANGE,
            description="A password-change attempt failed.",
            error=error,
            farm_id=current_user.farm_id,
            actor_user_id=current_user.id,
            actor_username=current_user.username,
            resource_type="User",
            resource_id=current_user.id,
        )
        raise

    record_audit_safely(
        database_session,
        module="auth",
        action=AuditAction.PASSWORD_CHANGE,
        description="User changed their PoultryPulse password.",
        farm_id=current_user.farm_id,
        actor_user_id=current_user.id,
        actor_username=current_user.username,
        resource_type="User",
        resource_id=current_user.id,
        metadata={
            "existing_sessions_revoked": True,
        },
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
