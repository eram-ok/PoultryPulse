from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.users.models import Role, User


class UserRepository:
    """Database operations for PoultryPulse users and roles."""

    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session

    def get_by_id(self, user_id: UUID) -> User | None:
        statement = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.id == user_id)
        )

        return self.database_session.scalar(statement)

    def get_by_username(
        self,
        farm_id: UUID,
        username: str,
    ) -> User | None:
        statement = select(User).where(
            User.farm_id == farm_id,
            func.lower(User.username) == username.lower(),
        )

        return self.database_session.scalar(statement)

    def get_by_email(
        self,
        farm_id: UUID,
        email: str,
    ) -> User | None:
        statement = select(User).where(
            User.farm_id == farm_id,
            func.lower(User.email) == email.lower(),
        )

        return self.database_session.scalar(statement)

    def get_by_telephone(
        self,
        farm_id: UUID,
        telephone: str,
    ) -> User | None:
        statement = select(User).where(
            User.farm_id == farm_id,
            User.telephone == telephone,
        )

        return self.database_session.scalar(statement)

    def list_users(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[User], int]:
        users_statement = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.farm_id == farm_id)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        total_statement = select(func.count(User.id)).where(User.farm_id == farm_id)

        users = list(self.database_session.scalars(users_statement).all())

        total = self.database_session.scalar(total_statement) or 0

        return users, total

    def get_roles_by_ids(
        self,
        farm_id: UUID,
        role_ids: list[UUID],
    ) -> list[Role]:
        statement = (
            select(Role)
            .options(selectinload(Role.permissions))
            .where(
                Role.farm_id == farm_id,
                Role.id.in_(role_ids),
                Role.is_active.is_(True),
            )
        )

        return list(self.database_session.scalars(statement).all())

    def get_role(
        self,
        farm_id: UUID,
        role_id: UUID,
    ) -> Role | None:
        statement = (
            select(Role)
            .options(selectinload(Role.permissions))
            .where(
                Role.farm_id == farm_id,
                Role.id == role_id,
            )
        )

        return self.database_session.scalar(statement)

    def list_roles(self, farm_id: UUID) -> list[Role]:
        statement = (
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.farm_id == farm_id)
            .order_by(Role.name)
        )

        return list(self.database_session.scalars(statement).all())

    def update_user(
        self,
        user: User,
        changes: dict[str, Any],
    ) -> User:
        for field_name, field_value in changes.items():
            setattr(user, field_name, field_value)

        self.database_session.add(user)
        return user

    def find_login_candidates(
        self,
        identifier: str,
        *,
        farm_code: str | None = None,
    ) -> list[User]:
        from app.modules.farms.models import Farm

        normalized = identifier.strip().lower()

        statement = (
            select(User)
            .join(Farm, Farm.id == User.farm_id)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(
                or_(
                    func.lower(User.username) == normalized,
                    func.lower(User.email) == normalized,
                    User.telephone == identifier.strip(),
                )
            )
        )

        if farm_code is not None:
            statement = statement.where(
                func.upper(Farm.farm_code) == farm_code.strip().upper()
            )

        return list(self.database_session.scalars(statement).all())
