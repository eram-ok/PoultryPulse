from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.modules.auth.models import RefreshToken
from app.modules.farms.models import Farm
from app.modules.onboarding.constants import FarmInvitationStatus
from app.modules.onboarding.models import PlatformFarmInvitation
from app.modules.users.models import Role, User, user_roles


class FarmOnboardingRepository:
    """Database operations for platform-controlled farm invitations."""

    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session

    def add(
        self,
        invitation: PlatformFarmInvitation,
    ) -> PlatformFarmInvitation:
        self.database_session.add(invitation)
        return invitation

    def get_farm(self, farm_id: UUID) -> Farm | None:
        return self.database_session.get(Farm, farm_id)

    def get_user(self, user_id: UUID) -> User | None:
        return self.database_session.get(User, user_id)

    def get_by_token_hash(
        self,
        token_hash: str,
        *,
        for_update: bool = False,
    ) -> PlatformFarmInvitation | None:
        statement = select(PlatformFarmInvitation).where(
            PlatformFarmInvitation.token_hash == token_hash
        )
        if for_update:
            statement = statement.with_for_update()
        return self.database_session.scalar(statement)

    def get_latest_for_farm(
        self,
        farm_id: UUID,
        *,
        for_update: bool = False,
    ) -> PlatformFarmInvitation | None:
        statement = (
            select(PlatformFarmInvitation)
            .where(PlatformFarmInvitation.farm_id == farm_id)
            .order_by(
                PlatformFarmInvitation.created_at.desc(),
                PlatformFarmInvitation.id.desc(),
            )
            .limit(1)
        )
        if for_update:
            statement = statement.with_for_update()
        return self.database_session.scalar(statement)

    def get_pending_for_farm(
        self,
        farm_id: UUID,
        *,
        for_update: bool = False,
    ) -> PlatformFarmInvitation | None:
        statement = (
            select(PlatformFarmInvitation)
            .where(
                PlatformFarmInvitation.farm_id == farm_id,
                PlatformFarmInvitation.status
                == FarmInvitationStatus.PENDING.value,
            )
            .order_by(
                PlatformFarmInvitation.created_at.desc(),
                PlatformFarmInvitation.id.desc(),
            )
            .limit(1)
        )
        if for_update:
            statement = statement.with_for_update()
        return self.database_session.scalar(statement)

    def get_by_idempotency(
        self,
        *,
        platform_user_id: UUID,
        idempotency_key: str,
    ) -> PlatformFarmInvitation | None:
        statement = select(PlatformFarmInvitation).where(
            PlatformFarmInvitation.issued_by_platform_user_id
            == platform_user_id,
            PlatformFarmInvitation.idempotency_key
            == idempotency_key,
        )
        return self.database_session.scalar(statement)

    def find_administrator(
        self,
        farm_id: UUID,
    ) -> User | None:
        statement = (
            select(User)
            .join(
                user_roles,
                user_roles.c.user_id == User.id,
            )
            .join(
                Role,
                Role.id == user_roles.c.role_id,
            )
            .where(
                User.farm_id == farm_id,
                Role.farm_id == farm_id,
                Role.name == "Administrator",
            )
            .order_by(User.created_at.asc(), User.id.asc())
            .limit(1)
        )
        return self.database_session.scalar(statement)

    def revoke_user_refresh_tokens(
        self,
        user_id: UUID,
        *,
        revoked_at: datetime,
    ) -> int:
        statement = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        result = self.database_session.execute(statement)
        return int(result.rowcount or 0)
