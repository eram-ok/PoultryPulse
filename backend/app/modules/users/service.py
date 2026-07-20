from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BusinessRuleError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.core.security import hash_password
from app.modules.users.models import Role, User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserUpdate


class UserService:
    """Business operations for user management."""

    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session
        self.repository = UserRepository(database_session)

    def create_user(
        self,
        farm_id: UUID,
        payload: UserCreate,
    ) -> User:
        if self.repository.get_by_username(
            farm_id,
            payload.username,
        ):
            raise ResourceConflictError(
                "A user with this username already exists.",
                error_code="username_already_exists",
            )

        if payload.email and self.repository.get_by_email(
            farm_id,
            str(payload.email),
        ):
            raise ResourceConflictError(
                "A user with this email address already exists.",
                error_code="email_already_exists",
            )

        if payload.telephone and self.repository.get_by_telephone(
            farm_id,
            payload.telephone,
        ):
            raise ResourceConflictError(
                "A user with this telephone number already exists.",
                error_code="telephone_already_exists",
            )

        unique_role_ids = list(set(payload.role_ids))
        roles = self.repository.get_roles_by_ids(
            farm_id,
            unique_role_ids,
        )

        if len(roles) != len(unique_role_ids):
            raise BusinessRuleError(
                "One or more selected roles are invalid.",
                error_code="invalid_role_assignment",
            )

        user = User(
            farm_id=farm_id,
            username=payload.username,
            email=(str(payload.email).lower() if payload.email else None),
            telephone=payload.telephone,
            password_hash=hash_password(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            is_active=True,
            is_verified=True,
            must_change_password=payload.must_change_password,
        )

        user.roles = roles
        self.database_session.add(user)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The user could not be created because "
                "one of the values already exists.",
                error_code="user_creation_conflict",
            ) from exc

        created_user = self.repository.get_by_id(user.id)

        if created_user is None:
            raise ResourceNotFoundError(
                "The created user could not be retrieved.",
                error_code="created_user_not_found",
            )

        return created_user

    def list_users(
        self,
        farm_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[User], int]:
        return self.repository.list_users(
            farm_id,
            offset=offset,
            limit=limit,
        )

    def get_user(
        self,
        farm_id: UUID,
        user_id: UUID,
    ) -> User:
        user = self.repository.get_by_id(user_id)

        if user is None or user.farm_id != farm_id:
            raise ResourceNotFoundError(
                "The requested user does not exist.",
                error_code="user_not_found",
            )

        return user

    def update_user(
        self,
        farm_id: UUID,
        user_id: UUID,
        payload: UserUpdate,
    ) -> User:
        user = self.get_user(farm_id, user_id)
        changes = payload.model_dump(exclude_unset=True)

        requested_email = changes.get("email")

        if requested_email is not None:
            requested_email = str(requested_email).lower()
            changes["email"] = requested_email

            conflicting_user = self.repository.get_by_email(
                farm_id,
                requested_email,
            )

            if conflicting_user is not None and conflicting_user.id != user.id:
                raise ResourceConflictError(
                    "Another user already uses this email.",
                    error_code="email_already_exists",
                )

        requested_telephone = changes.get("telephone")

        if requested_telephone:
            conflicting_user = self.repository.get_by_telephone(
                farm_id,
                requested_telephone,
            )

            if conflicting_user is not None and conflicting_user.id != user.id:
                raise ResourceConflictError(
                    "Another user already uses this telephone.",
                    error_code="telephone_already_exists",
                )

        self.repository.update_user(user, changes)

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()

            raise ResourceConflictError(
                "The user could not be updated.",
                error_code="user_update_conflict",
            ) from exc

        updated_user = self.repository.get_by_id(user_id)

        if updated_user is None:
            raise ResourceNotFoundError(
                "The updated user could not be retrieved.",
                error_code="updated_user_not_found",
            )

        return updated_user

    def activate_user(
        self,
        farm_id: UUID,
        user_id: UUID,
    ) -> User:
        user = self.get_user(farm_id, user_id)
        user.is_active = True

        self.database_session.commit()

        return self.get_user(farm_id, user_id)

    def deactivate_user(
        self,
        farm_id: UUID,
        user_id: UUID,
        *,
        acting_user_id: UUID,
    ) -> User:
        if user_id == acting_user_id:
            raise BusinessRuleError(
                "You cannot deactivate your own account.",
                error_code="cannot_deactivate_self",
            )

        user = self.get_user(farm_id, user_id)
        user.is_active = False

        self.database_session.commit()

        return self.get_user(farm_id, user_id)

    def assign_role(
        self,
        farm_id: UUID,
        user_id: UUID,
        role_id: UUID,
    ) -> User:
        user = self.get_user(farm_id, user_id)
        role = self.repository.get_role(farm_id, role_id)

        if role is None or not role.is_active:
            raise ResourceNotFoundError(
                "The requested role does not exist.",
                error_code="role_not_found",
            )

        if role not in user.roles:
            user.roles.append(role)
            self.database_session.commit()

        return self.get_user(farm_id, user_id)

    def remove_role(
        self,
        farm_id: UUID,
        user_id: UUID,
        role_id: UUID,
    ) -> User:
        user = self.get_user(farm_id, user_id)
        role = self.repository.get_role(farm_id, role_id)

        if role is None:
            raise ResourceNotFoundError(
                "The requested role does not exist.",
                error_code="role_not_found",
            )

        remaining_roles = [
            assigned_role for assigned_role in user.roles if assigned_role.id != role_id
        ]

        if not remaining_roles:
            raise BusinessRuleError(
                "A user must have at least one role.",
                error_code="user_requires_role",
            )

        user.roles = remaining_roles
        self.database_session.commit()

        return self.get_user(farm_id, user_id)

    def list_roles(self, farm_id: UUID) -> list[Role]:
        return self.repository.list_roles(farm_id)
