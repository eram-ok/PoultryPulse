from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.orm import Session

from app.core.database import get_database_session
from app.modules.audit.constants import AuditAction
from app.modules.audit.integration import (
    record_audit_safely,
    record_failure_safely,
    role_snapshot,
    user_snapshot,
)
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
    service = UserService(database_session)

    try:
        user = service.create_user(
            current_user.farm_id,
            payload,
        )
    except Exception as error:
        record_failure_safely(
            database_session,
            module="users",
            action=AuditAction.CREATE,
            description="A farm-user creation attempt failed.",
            error=error,
            farm_id=current_user.farm_id,
            actor_user_id=current_user.id,
            actor_username=current_user.username,
            resource_type="User",
            metadata={
                "requested_username": payload.username,
                "requested_role_ids": payload.role_ids,
            },
        )
        raise

    record_audit_safely(
        database_session,
        module="users",
        action=AuditAction.CREATE,
        description="Created a farm user.",
        farm_id=current_user.farm_id,
        actor_user_id=current_user.id,
        actor_username=current_user.username,
        resource_type="User",
        resource_id=user.id,
        after_values=user_snapshot(user),
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
    service = UserService(database_session)
    existing = service.get_user(
        current_user.farm_id,
        user_id,
    )
    before_values = user_snapshot(existing)

    try:
        user = service.update_user(
            current_user.farm_id,
            user_id,
            payload,
        )
    except Exception as error:
        record_failure_safely(
            database_session,
            module="users",
            action=AuditAction.UPDATE,
            description="A farm-user update failed.",
            error=error,
            farm_id=current_user.farm_id,
            actor_user_id=current_user.id,
            actor_username=current_user.username,
            resource_type="User",
            resource_id=user_id,
            metadata={
                "requested_fields": sorted(payload.model_dump(exclude_unset=True)),
            },
        )
        raise

    record_audit_safely(
        database_session,
        module="users",
        action=AuditAction.UPDATE,
        description="Updated a farm user.",
        farm_id=current_user.farm_id,
        actor_user_id=current_user.id,
        actor_username=current_user.username,
        resource_type="User",
        resource_id=user.id,
        before_values=before_values,
        after_values=user_snapshot(user),
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
    service = UserService(database_session)
    before_values = user_snapshot(
        service.get_user(
            current_user.farm_id,
            user_id,
        )
    )

    try:
        user = service.activate_user(
            current_user.farm_id,
            user_id,
        )
    except Exception as error:
        record_failure_safely(
            database_session,
            module="users",
            action=AuditAction.ACTIVATE,
            description="A farm-user activation failed.",
            error=error,
            farm_id=current_user.farm_id,
            actor_user_id=current_user.id,
            actor_username=current_user.username,
            resource_type="User",
            resource_id=user_id,
        )
        raise

    record_audit_safely(
        database_session,
        module="users",
        action=AuditAction.ACTIVATE,
        description="Activated a farm user.",
        farm_id=current_user.farm_id,
        actor_user_id=current_user.id,
        actor_username=current_user.username,
        resource_type="User",
        resource_id=user.id,
        before_values=before_values,
        after_values=user_snapshot(user),
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
    service = UserService(database_session)
    before_values = user_snapshot(
        service.get_user(
            current_user.farm_id,
            user_id,
        )
    )

    try:
        user = service.deactivate_user(
            current_user.farm_id,
            user_id,
            acting_user_id=current_user.id,
        )
    except Exception as error:
        record_failure_safely(
            database_session,
            module="users",
            action=AuditAction.DEACTIVATE,
            description="A farm-user deactivation failed.",
            error=error,
            farm_id=current_user.farm_id,
            actor_user_id=current_user.id,
            actor_username=current_user.username,
            resource_type="User",
            resource_id=user_id,
        )
        raise

    record_audit_safely(
        database_session,
        module="users",
        action=AuditAction.DEACTIVATE,
        description="Deactivated a farm user.",
        farm_id=current_user.farm_id,
        actor_user_id=current_user.id,
        actor_username=current_user.username,
        resource_type="User",
        resource_id=user.id,
        before_values=before_values,
        after_values=user_snapshot(user),
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
    service = UserService(database_session)
    existing = service.get_user(
        current_user.farm_id,
        user_id,
    )
    role = service.repository.get_role(
        current_user.farm_id,
        role_id,
    )
    before_values = user_snapshot(existing)

    try:
        user = service.assign_role(
            current_user.farm_id,
            user_id,
            role_id,
        )
    except Exception as error:
        record_failure_safely(
            database_session,
            module="roles",
            action=AuditAction.ASSIGN,
            description="A role assignment failed.",
            error=error,
            farm_id=current_user.farm_id,
            actor_user_id=current_user.id,
            actor_username=current_user.username,
            resource_type="User",
            resource_id=user_id,
            metadata={
                "role_id": role_id,
                "role": (role_snapshot(role) if role is not None else None),
            },
        )
        raise

    record_audit_safely(
        database_session,
        module="roles",
        action=AuditAction.ASSIGN,
        description="Assigned a role to a farm user.",
        farm_id=current_user.farm_id,
        actor_user_id=current_user.id,
        actor_username=current_user.username,
        resource_type="User",
        resource_id=user.id,
        before_values=before_values,
        after_values=user_snapshot(user),
        metadata={
            "role_id": role_id,
            "role": (role_snapshot(role) if role is not None else None),
        },
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
    service = UserService(database_session)
    existing = service.get_user(
        current_user.farm_id,
        user_id,
    )
    role = service.repository.get_role(
        current_user.farm_id,
        role_id,
    )
    before_values = user_snapshot(existing)

    try:
        user = service.remove_role(
            current_user.farm_id,
            user_id,
            role_id,
        )
    except Exception as error:
        record_failure_safely(
            database_session,
            module="roles",
            action=AuditAction.REMOVE,
            description="A role-removal operation failed.",
            error=error,
            farm_id=current_user.farm_id,
            actor_user_id=current_user.id,
            actor_username=current_user.username,
            resource_type="User",
            resource_id=user_id,
            metadata={
                "role_id": role_id,
                "role": (role_snapshot(role) if role is not None else None),
            },
        )
        raise

    record_audit_safely(
        database_session,
        module="roles",
        action=AuditAction.REMOVE,
        description="Removed a role from a farm user.",
        farm_id=current_user.farm_id,
        actor_user_id=current_user.id,
        actor_username=current_user.username,
        resource_type="User",
        resource_id=user.id,
        before_values=before_values,
        after_values=user_snapshot(user),
        metadata={
            "role_id": role_id,
            "role": (role_snapshot(role) if role is not None else None),
        },
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
