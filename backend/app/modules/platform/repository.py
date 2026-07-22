
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session, selectinload

from app.modules.platform.models import (
    PlatformAuditLog,
    PlatformRefreshToken,
    PlatformUser,
)


class PlatformAuthRepository:
    """Database operations for platform identities and sessions."""

    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session

    def get_user_by_id(
        self,
        platform_user_id: UUID,
    ) -> PlatformUser | None:
        return self.database_session.get(
            PlatformUser,
            platform_user_id,
        )

    def find_user(
        self,
        identifier: str,
    ) -> PlatformUser | None:
        normalized = identifier.strip().lower()
        statement = select(PlatformUser).where(
            or_(
                func.lower(PlatformUser.username) == normalized,
                func.lower(PlatformUser.email) == normalized,
            )
        )
        return self.database_session.scalar(statement)

    def get_user_by_username(
        self,
        username: str,
    ) -> PlatformUser | None:
        statement = select(PlatformUser).where(
            func.lower(PlatformUser.username)
            == username.strip().lower()
        )
        return self.database_session.scalar(statement)

    def get_user_by_email(
        self,
        email: str,
    ) -> PlatformUser | None:
        statement = select(PlatformUser).where(
            func.lower(PlatformUser.email)
            == email.strip().lower()
        )
        return self.database_session.scalar(statement)

    def get_refresh_token(
        self,
        jti: str,
    ) -> PlatformRefreshToken | None:
        statement = (
            select(PlatformRefreshToken)
            .options(
                selectinload(
                    PlatformRefreshToken.platform_user
                )
            )
            .where(PlatformRefreshToken.jti == jti)
        )
        return self.database_session.scalar(statement)

    def revoke_all_refresh_tokens(
        self,
        platform_user_id: UUID,
        revoked_at: datetime,
    ) -> None:
        statement = (
            update(PlatformRefreshToken)
            .where(
                PlatformRefreshToken.platform_user_id
                == platform_user_id,
                PlatformRefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        self.database_session.execute(statement)

    def add_audit_log(
        self,
        item: PlatformAuditLog,
    ) -> PlatformAuditLog:
        self.database_session.add(item)
        return item
