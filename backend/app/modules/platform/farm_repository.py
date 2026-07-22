from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import (
    func,
    or_,
    select,
    update,
)
from sqlalchemy.orm import Session, selectinload

from app.modules.auth.models import RefreshToken
from app.modules.farms.constants import FarmLifecycleStatus
from app.modules.farms.models import Farm
from app.modules.users.models import (
    Permission,
    User,
)


RECENT_LOGIN_WINDOW_DAYS = 30


@dataclass(frozen=True)
class PlatformFarmRecord:
    """One farm and its platform-safe usage statistics."""

    farm: Farm
    total_users: int
    active_users: int
    recent_login_users: int
    active_refresh_sessions: int
    last_login_at: datetime | None


class PlatformFarmRepository:
    """Cross-farm queries reserved for the platform boundary."""

    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session

    @staticmethod
    def _statistics_subqueries(
        *,
        current_time: datetime,
    ):
        recent_cutoff = current_time - timedelta(
            days=RECENT_LOGIN_WINDOW_DAYS
        )

        user_statistics = (
            select(
                User.farm_id.label("farm_id"),
                func.count(User.id).label("total_users"),
                func.count(User.id)
                .filter(User.is_active.is_(True))
                .label("active_users"),
                func.count(User.id)
                .filter(User.last_login_at >= recent_cutoff)
                .label("recent_login_users"),
                func.max(User.last_login_at).label(
                    "last_login_at"
                ),
            )
            .group_by(User.farm_id)
            .subquery()
        )

        session_statistics = (
            select(
                User.farm_id.label("farm_id"),
                func.count(RefreshToken.id)
                .filter(
                    RefreshToken.revoked_at.is_(None),
                    RefreshToken.expires_at > current_time,
                )
                .label("active_refresh_sessions"),
            )
            .join(
                RefreshToken,
                RefreshToken.user_id == User.id,
            )
            .group_by(User.farm_id)
            .subquery()
        )

        return user_statistics, session_statistics

    @classmethod
    def _aggregate_statement(
        cls,
        *,
        current_time: datetime,
    ):
        user_statistics, session_statistics = (
            cls._statistics_subqueries(
                current_time=current_time
            )
        )

        return (
            select(
                Farm,
                func.coalesce(
                    user_statistics.c.total_users,
                    0,
                ).label("total_users"),
                func.coalesce(
                    user_statistics.c.active_users,
                    0,
                ).label("active_users"),
                func.coalesce(
                    user_statistics.c.recent_login_users,
                    0,
                ).label("recent_login_users"),
                func.coalesce(
                    session_statistics.c.active_refresh_sessions,
                    0,
                ).label("active_refresh_sessions"),
                user_statistics.c.last_login_at,
            )
            .outerjoin(
                user_statistics,
                user_statistics.c.farm_id == Farm.id,
            )
            .outerjoin(
                session_statistics,
                session_statistics.c.farm_id == Farm.id,
            )
        )

    @staticmethod
    def _record_from_row(row) -> PlatformFarmRecord:
        values = row._mapping

        return PlatformFarmRecord(
            farm=row[0],
            total_users=int(values["total_users"]),
            active_users=int(values["active_users"]),
            recent_login_users=int(
                values["recent_login_users"]
            ),
            active_refresh_sessions=int(
                values["active_refresh_sessions"]
            ),
            last_login_at=values["last_login_at"],
        )

    def list_farms(
        self,
        *,
        offset: int,
        limit: int,
        search: str | None,
        lifecycle_status: FarmLifecycleStatus | None,
    ) -> tuple[list[PlatformFarmRecord], int]:
        current_time = datetime.now(UTC)
        statement = self._aggregate_statement(
            current_time=current_time
        )
        count_statement = select(func.count(Farm.id))

        conditions = []

        if search:
            normalized_search = search.strip()
            if normalized_search:
                search_pattern = f"%{normalized_search}%"
                conditions.append(
                    or_(
                        Farm.farm_code.ilike(search_pattern),
                        Farm.name.ilike(search_pattern),
                        Farm.owner_name.ilike(search_pattern),
                        Farm.email.ilike(search_pattern),
                        Farm.telephone.ilike(search_pattern),
                        Farm.district.ilike(search_pattern),
                    )
                )

        if lifecycle_status is not None:
            conditions.append(
                Farm.lifecycle_status
                == lifecycle_status.value
            )

        if conditions:
            statement = statement.where(*conditions)
            count_statement = count_statement.where(
                *conditions
            )

        statement = (
            statement.order_by(
                Farm.created_at.desc(),
                Farm.name.asc(),
            )
            .offset(offset)
            .limit(limit)
        )

        rows = self.database_session.execute(
            statement
        ).all()
        total = (
            self.database_session.scalar(count_statement)
            or 0
        )

        return (
            [
                self._record_from_row(row)
                for row in rows
            ],
            int(total),
        )

    def get_farm(
        self,
        farm_id: UUID,
    ) -> PlatformFarmRecord | None:
        statement = (
            self._aggregate_statement(
                current_time=datetime.now(UTC)
            )
            .options(selectinload(Farm.settings))
            .where(Farm.id == farm_id)
        )
        row = self.database_session.execute(
            statement
        ).one_or_none()

        if row is None:
            return None

        return self._record_from_row(row)

    def get_farm_by_code(
        self,
        farm_code: str,
    ) -> Farm | None:
        statement = select(Farm).where(
            func.upper(Farm.farm_code)
            == farm_code.strip().upper()
        )
        return self.database_session.scalar(statement)

    def list_permissions(self) -> list[Permission]:
        statement = select(Permission).order_by(
            Permission.code
        )
        return list(
            self.database_session.scalars(
                statement
            ).all()
        )

    def revoke_farm_refresh_tokens(
        self,
        farm_id: UUID,
        *,
        revoked_at: datetime,
    ) -> int:
        user_ids = select(User.id).where(
            User.farm_id == farm_id
        )
        statement = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id.in_(user_ids),
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        result = self.database_session.execute(
            statement
        )
        return int(result.rowcount or 0)

    def add_all(
        self,
        *items: object,
    ) -> None:
        self.database_session.add_all(list(items))
