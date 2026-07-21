from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.modules.audit.constants import (
    AuditAction,
    AuditOutcome,
    AuditSeverity,
)
from app.modules.audit.models import AuditLog
from app.modules.audit.service import AuditService


if TYPE_CHECKING:
    from app.modules.farms.models import Farm, FarmSettings
    from app.modules.users.models import Role, User


logger = logging.getLogger(__name__)


def exception_error_code(error: Exception) -> str:
    value = getattr(error, "error_code", None)
    if isinstance(value, str) and value:
        return value

    return type(error).__name__


def exception_message(error: Exception) -> str:
    module_name = type(error).__module__

    if module_name.startswith("app."):
        return str(error)[:500]

    return "An unexpected application error occurred."


def audit_severity_for_error(
    error: Exception,
) -> AuditSeverity:
    error_code = exception_error_code(error)

    if error_code in {
        "account_temporarily_locked",
        "inactive_account",
        "required_permission_missing",
    }:
        return AuditSeverity.WARNING

    return AuditSeverity.INFO


def record_audit_safely(
    database_session: Session,
    *,
    module: str,
    action: AuditAction | str,
    description: str,
    outcome: AuditOutcome | str = AuditOutcome.SUCCESS,
    severity: AuditSeverity | str = AuditSeverity.INFO,
    farm_id: UUID | None = None,
    actor_user_id: UUID | None = None,
    actor_username: str | None = None,
    resource_type: str | None = None,
    resource_id: UUID | str | None = None,
    before_values: dict[str, Any] | None = None,
    after_values: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
) -> AuditLog | None:
    try:
        return AuditService(database_session).record(
            module=module,
            action=action,
            description=description,
            outcome=outcome,
            severity=severity,
            farm_id=farm_id,
            actor_user_id=actor_user_id,
            actor_username=actor_username,
            resource_type=resource_type,
            resource_id=resource_id,
            before_values=before_values,
            after_values=after_values,
            metadata=metadata,
            error_code=error_code,
            error_message=error_message,
            commit=True,
        )
    except Exception:
        database_session.rollback()
        logger.exception("PoultryPulse could not persist an audit event.")
        return None


def record_failure_safely(
    database_session: Session,
    *,
    module: str,
    action: AuditAction | str,
    description: str,
    error: Exception,
    farm_id: UUID | None = None,
    actor_user_id: UUID | None = None,
    actor_username: str | None = None,
    resource_type: str | None = None,
    resource_id: UUID | str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog | None:
    return record_audit_safely(
        database_session,
        module=module,
        action=action,
        description=description,
        outcome=AuditOutcome.FAILURE,
        severity=audit_severity_for_error(error),
        farm_id=farm_id,
        actor_user_id=actor_user_id,
        actor_username=actor_username,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata=metadata,
        error_code=exception_error_code(error),
        error_message=exception_message(error),
    )


def token_identity(
    token: str,
) -> dict[str, Any]:
    try:
        payload = decode_token(token)
    except (TypeError, ValueError):
        return {
            "decoded": False,
            "user_id": None,
            "farm_id": None,
            "username": None,
            "token_type": None,
        }

    def parse_uuid(value: object) -> UUID | None:
        try:
            return UUID(str(value))
        except (TypeError, ValueError):
            return None

    return {
        "decoded": True,
        "user_id": parse_uuid(payload.get("sub")),
        "farm_id": parse_uuid(payload.get("farm_id")),
        "username": (
            str(payload["username"]) if payload.get("username") is not None else None
        ),
        "token_type": payload.get("type"),
    }


def user_snapshot(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "farm_id": user.farm_id,
        "username": user.username,
        "email": user.email,
        "telephone": user.telephone,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "must_change_password": user.must_change_password,
        "failed_login_attempts": (user.failed_login_attempts),
        "locked_until": user.locked_until,
        "last_login_at": user.last_login_at,
        "role_ids": sorted(str(role.id) for role in user.roles),
        "role_names": sorted(role.name for role in user.roles),
    }


def role_snapshot(role: Role) -> dict[str, Any]:
    return {
        "id": role.id,
        "farm_id": role.farm_id,
        "name": role.name,
        "description": role.description,
        "is_system_role": role.is_system_role,
        "is_active": role.is_active,
        "permission_codes": sorted(permission.code for permission in role.permissions),
    }


def farm_snapshot(farm: Farm) -> dict[str, Any]:
    return {
        "id": farm.id,
        "farm_code": farm.farm_code,
        "name": farm.name,
        "owner_name": farm.owner_name,
        "telephone": farm.telephone,
        "email": farm.email,
        "district": farm.district,
        "address": farm.address,
        "logo_url": farm.logo_url,
        "timezone": farm.timezone,
        "currency_code": farm.currency_code,
        "is_active": farm.is_active,
    }


def farm_settings_snapshot(
    settings: FarmSettings,
) -> dict[str, Any]:
    return {
        "id": settings.id,
        "farm_id": settings.farm_id,
        "eggs_per_tray": settings.eggs_per_tray,
        "low_production_threshold": (settings.low_production_threshold),
        "mortality_alert_threshold": (settings.mortality_alert_threshold),
        "vaccination_reminder_days": (settings.vaccination_reminder_days),
        "session_timeout_minutes": (settings.session_timeout_minutes),
        "allow_negative_stock": (settings.allow_negative_stock),
        "allow_customer_credit": (settings.allow_customer_credit),
        "maximum_discount_percentage": (settings.maximum_discount_percentage),
    }
