from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.modules.auth.models import RefreshToken
from app.modules.farms.models import Farm
from app.modules.users.models import Role, User
from app.modules.users.repository import UserRepository


class AuthRepository:
    """Database operations required by authentication."""

    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session
        self.users = UserRepository(database_session)

    def find_login_candidates(
        self,
        identifier: str,
        *,
        farm_code: str | None,
    ) -> list[User]:
        return self.users.find_login_candidates(
            identifier,
            farm_code=farm_code,
        )

    def get_user_by_id(self, user_id: UUID) -> User | None:
        return self.users.get_by_id(user_id)

    def get_farm_by_id(
        self,
        farm_id: UUID,
    ) -> Farm | None:
        return self.database_session.get(Farm, farm_id)

    def get_refresh_token(
        self,
        jti: str,
    ) -> RefreshToken | None:
        statement = (
            select(RefreshToken)
            .options(
                selectinload(RefreshToken.user)
                .selectinload(User.roles)
                .selectinload(Role.permissions)
            )
            .where(RefreshToken.jti == jti)
        )

        return self.database_session.scalar(statement)

    def revoke_all_refresh_tokens(
        self,
        user_id: UUID,
        revoked_at: datetime,
    ) -> None:
        statement = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )

        self.database_session.execute(statement)
