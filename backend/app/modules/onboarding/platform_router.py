from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_database_session
from app.modules.onboarding.schemas import (
    PlatformFarmInvitationIssueResponse,
    PlatformFarmInvitationRevokeRequest,
    PlatformFarmOnboardingStatusResponse,
)
from app.modules.onboarding.service import FarmOnboardingService
from app.modules.platform.dependencies import CurrentPlatformSuperAdmin


router = APIRouter(
    prefix="/platform/farms",
    tags=["Platform Farm Onboarding"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


@router.get(
    "/{farm_id}/onboarding",
    response_model=PlatformFarmOnboardingStatusResponse,
    summary="Get a farm's onboarding status",
)
def get_onboarding_status(
    farm_id: UUID,
    database_session: DatabaseSession,
    current_user: CurrentPlatformSuperAdmin,
) -> PlatformFarmOnboardingStatusResponse:
    return FarmOnboardingService(
        database_session
    ).platform_status(farm_id)


@router.post(
    "/{farm_id}/onboarding/resend",
    response_model=PlatformFarmInvitationIssueResponse,
    summary="Reissue a farm administrator invitation",
)
def resend_invitation(
    farm_id: UUID,
    response: Response,
    database_session: DatabaseSession,
    current_user: CurrentPlatformSuperAdmin,
) -> PlatformFarmInvitationIssueResponse:
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return FarmOnboardingService(
        database_session
    ).reissue_invitation(
        farm_id,
        actor=current_user,
    )


@router.post(
    "/{farm_id}/onboarding/revoke",
    response_model=PlatformFarmOnboardingStatusResponse,
    summary="Revoke a pending farm administrator invitation",
)
def revoke_invitation(
    farm_id: UUID,
    payload: PlatformFarmInvitationRevokeRequest,
    database_session: DatabaseSession,
    current_user: CurrentPlatformSuperAdmin,
) -> PlatformFarmOnboardingStatusResponse:
    return FarmOnboardingService(
        database_session
    ).revoke_invitation(
        farm_id,
        actor=current_user,
        reason=payload.reason,
    )
