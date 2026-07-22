from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_database_session
from app.modules.onboarding.schemas import (
    FarmInvitationAcceptRequest,
    FarmInvitationAcceptResponse,
    FarmInvitationPublicResponse,
    FarmInvitationTokenRequest,
)
from app.modules.onboarding.service import FarmOnboardingService


router = APIRouter(
    prefix="/onboarding/invitations",
    tags=["Farm Onboarding"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Pragma"] = "no-cache"


@router.post(
    "/validate",
    response_model=FarmInvitationPublicResponse,
    summary="Validate a farm administrator invitation",
)
def validate_invitation(
    payload: FarmInvitationTokenRequest,
    response: Response,
    database_session: DatabaseSession,
) -> FarmInvitationPublicResponse:
    _no_store(response)
    return FarmOnboardingService(
        database_session
    ).validate_invitation(payload.token)


@router.post(
    "/accept",
    response_model=FarmInvitationAcceptResponse,
    summary="Accept a farm administrator invitation",
)
def accept_invitation(
    payload: FarmInvitationAcceptRequest,
    response: Response,
    database_session: DatabaseSession,
) -> FarmInvitationAcceptResponse:
    _no_store(response)
    return FarmOnboardingService(
        database_session
    ).accept_invitation(
        token=payload.token,
        new_password=payload.new_password,
    )
