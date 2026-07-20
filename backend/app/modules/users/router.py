from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.orm import Session

from app.core.database import get_database_session
from app.modules.auth.dependencies import require_permissions
from app.modules.users.models import User
from app.modules.users.schemas import (
    RoleResponse,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.modules.users.service import UserService


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

roles_router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


@router.get(
    "",
    response_model=UserListResponse,
    summary="List farm users",
)
def list_users(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("users.view")),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> UserListResponse:
    users, total = UserService(database_session).list_users(
        current_user.farm_id,
        offset=offset,
        limit=limit,
    )

    return UserListResponse(
        items=[UserResponse.model_validate(user) for user in users],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post(
    "",
    response_model=UserResponse,
    status_code=201,
    summary="Create a farm user",
)
def create_user(
    payload: UserCreate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("users.create")),
    ],
) -> UserResponse:
    user = UserService(database_session).create_user(
        current_user.farm_id,
        payload,
    )

    return UserResponse.model_validate(user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get one farm user",
)
def get_user(
    user_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("users.view")),
    ],
) -> UserResponse:
    user = UserService(database_session).get_user(
        current_user.farm_id,
        user_id,
    )

    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update a farm user",
)
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("users.update")),
    ],
) -> UserResponse:
    user = UserService(database_session).update_user(
        current_user.farm_id,
        user_id,
        payload,
    )

    return UserResponse.model_validate(user)


@router.post(
    "/{user_id}/activate",
    response_model=UserResponse,
    summary="Activate a farm user",
)
def activate_user(
    user_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("users.update")),
    ],
) -> UserResponse:
    user = UserService(database_session).activate_user(
        current_user.farm_id,
        user_id,
    )

    return UserResponse.model_validate(user)


@router.post(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    summary="Deactivate a farm user",
)
def deactivate_user(
    user_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("users.deactivate")),
    ],
) -> UserResponse:
    user = UserService(database_session).deactivate_user(
        current_user.farm_id,
        user_id,
        acting_user_id=current_user.id,
    )

    return UserResponse.model_validate(user)


@router.post(
    "/{user_id}/roles/{role_id}",
    response_model=UserResponse,
    summary="Assign a role to a user",
)
def assign_role(
    user_id: UUID,
    role_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("roles.assign")),
    ],
) -> UserResponse:
    user = UserService(database_session).assign_role(
        current_user.farm_id,
        user_id,
        role_id,
    )

    return UserResponse.model_validate(user)


@router.delete(
    "/{user_id}/roles/{role_id}",
    response_model=UserResponse,
    summary="Remove a role from a user",
)
def remove_role(
    user_id: UUID,
    role_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("roles.assign")),
    ],
) -> UserResponse:
    user = UserService(database_session).remove_role(
        current_user.farm_id,
        user_id,
        role_id,
    )

    return UserResponse.model_validate(user)


@roles_router.get(
    "",
    response_model=list[RoleResponse],
    summary="List farm roles and permissions",
)
def list_roles(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("roles.view")),
    ],
) -> list[RoleResponse]:
    roles = UserService(database_session).list_roles(current_user.farm_id)

    return [RoleResponse.model_validate(role) for role in roles]
