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

from app.core.database import get_database_session
from app.modules.auth.dependencies import CurrentUser
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    LogoutRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from app.modules.auth.service import AuthService
from app.modules.users.schemas import UserResponse


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


def get_client_ip(request: Request) -> str | None:
    if request.client is None:
        return None

    return request.client.host


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

    return AuthService(database_session).login(
        supplied_identifier=form_data.username,
        password=form_data.password,
        created_ip=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


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

    return AuthService(database_session).refresh(
        payload.refresh_token,
        created_ip=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


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

    AuthService(database_session).logout(payload.refresh_token)

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

    AuthService(database_session).change_password(
        current_user,
        payload.current_password,
        payload.new_password,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
