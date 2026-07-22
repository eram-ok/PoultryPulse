
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
from app.modules.platform.dependencies import (
    CurrentPlatformUser,
)
from app.modules.platform.schemas import (
    PlatformChangePasswordRequest,
    PlatformLogoutRequest,
    PlatformRefreshTokenRequest,
    PlatformTokenResponse,
    PlatformUserResponse,
)
from app.modules.platform.service import PlatformAuthService


settings = get_settings()

router = APIRouter(
    prefix="/platform/auth",
    tags=["Platform Authentication"],
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
    response_model=PlatformTokenResponse,
    summary="Log in to PoultryPulse platform administration",
)
def login(
    request: Request,
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    database_session: DatabaseSession,
) -> PlatformTokenResponse:
    service = PlatformAuthService(database_session)
    candidate = service.repository.find_user(
        form_data.username
    )

    try:
        response = service.login(
            form_data.username,
            form_data.password,
            created_ip=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except Exception as error:
        service.record_event(
            action="LOGIN_FAILED",
            outcome="FAILURE",
            description="A platform login attempt failed.",
            user=candidate,
            resource_type="PlatformUser",
            resource_id=(
                candidate.id
                if candidate is not None
                else None
            ),
            metadata={
                "identifier": form_data.username.strip(),
            },
            error=error,
        )
        raise

    service.record_event(
        action="LOGIN",
        outcome="SUCCESS",
        description="A platform user logged in.",
        user=candidate,
        resource_type="PlatformUser",
        resource_id=response.user.id,
        metadata={
            "authentication_method": "password",
        },
    )

    return response


@router.post(
    "/refresh",
    response_model=PlatformTokenResponse,
    summary="Refresh a platform authentication session",
)
def refresh(
    request: Request,
    payload: PlatformRefreshTokenRequest,
    database_session: DatabaseSession,
) -> PlatformTokenResponse:
    service = PlatformAuthService(database_session)

    try:
        response = service.refresh(
            payload.refresh_token,
            created_ip=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except Exception as error:
        service.record_event(
            action="TOKEN_REFRESH",
            outcome="FAILURE",
            description="A platform token refresh failed.",
            error=error,
        )
        raise

    user = service.repository.get_user_by_id(
        response.user.id
    )
    service.record_event(
        action="TOKEN_REFRESH",
        outcome="SUCCESS",
        description="Platform tokens were rotated.",
        user=user,
        resource_type="PlatformUser",
        resource_id=response.user.id,
    )

    return response


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out from platform administration",
)
def logout(
    payload: PlatformLogoutRequest,
    database_session: DatabaseSession,
) -> Response:
    PlatformAuthService(database_session).logout(
        payload.refresh_token
    )
    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.get(
    "/me",
    response_model=PlatformUserResponse,
    summary="Get the current platform user",
)
def get_me(
    current_user: CurrentPlatformUser,
) -> PlatformUserResponse:
    return PlatformUserResponse.model_validate(
        current_user
    )


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change the current platform password",
)
def change_password(
    payload: PlatformChangePasswordRequest,
    current_user: CurrentPlatformUser,
    database_session: DatabaseSession,
) -> Response:
    service = PlatformAuthService(database_session)

    try:
        service.change_password(
            current_user,
            payload.current_password,
            payload.new_password,
        )
    except Exception as error:
        service.record_event(
            action="PASSWORD_CHANGE",
            outcome="FAILURE",
            description="A platform password change failed.",
            user=current_user,
            resource_type="PlatformUser",
            resource_id=current_user.id,
            error=error,
        )
        raise

    service.record_event(
        action="PASSWORD_CHANGE",
        outcome="SUCCESS",
        description="A platform user changed their password.",
        user=current_user,
        resource_type="PlatformUser",
        resource_id=current_user.id,
        metadata={
            "existing_sessions_revoked": True,
        },
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
