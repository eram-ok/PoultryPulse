from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from functools import wraps
import inspect as python_inspect
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy.exc import NoInspectionAvailable
from sqlalchemy.orm import Session

from app.modules.audit.constants import AuditAction
from app.modules.audit.context import get_audit_context
from app.modules.audit.integration import (
    record_audit_safely,
    record_failure_safely,
)
from app.modules.audit.sanitizer import (
    json_safe,
    sanitize_mapping,
)


ActorArgumentNames = (
    "created_by",
    "recorded_by",
    "updated_by",
    "submitted_by",
    "confirmed_by",
    "rejected_by",
    "voided_by",
    "reversed_by",
    "cancelled_by",
    "resolved_by",
    "completed_by",
    "received_by",
    "paid_by",
    "requested_by",
    "actor_user_id",
    "user_id",
)


@dataclass(frozen=True)
class BeforeLoader:
    method_path: str
    argument_names: tuple[str, ...]


@dataclass(frozen=True)
class OperationAuditSpec:
    module_path: str
    class_name: str
    method_name: str
    module: str
    action: str
    description: str
    resource_type: str
    resource_id_argument: str | None = None
    before_loader: BeforeLoader | None = None
    static_metadata: Mapping[str, Any] | None = None


def model_snapshot(value: Any) -> dict[str, Any] | None:
    primary = primary_result(value)
    if primary is None:
        return None

    if isinstance(primary, BaseModel):
        return sanitize_mapping(primary.model_dump(mode="json"))

    if isinstance(primary, Mapping):
        return sanitize_mapping(primary)

    try:
        mapper = sqlalchemy_inspect(primary).mapper
    except (NoInspectionAvailable, AttributeError):
        return None

    values = {
        attribute.key: getattr(primary, attribute.key)
        for attribute in mapper.column_attrs
    }
    return sanitize_mapping(values)


def primary_result(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, (BaseModel, Mapping)):
        return value

    try:
        sqlalchemy_inspect(value).mapper
    except (NoInspectionAvailable, AttributeError):
        pass
    else:
        return value

    if isinstance(value, (tuple, list)):
        for item in value:
            selected = primary_result(item)
            if selected is not None:
                return selected

    return None


def bound_metadata(
    arguments: Mapping[str, Any],
    *,
    static_metadata: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    metadata: dict[str, Any] = {}

    if static_metadata:
        metadata.update(static_metadata)

    for name, value in arguments.items():
        if name in {
            "self",
            "farm_id",
            *ActorArgumentNames,
        }:
            continue

        if isinstance(value, BaseModel):
            metadata[name] = value.model_dump(
                mode="json",
                exclude_none=False,
            )
            continue

        if isinstance(value, Mapping):
            metadata[name] = dict(value)
            continue

        if value is None or isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
                UUID,
                date,
                datetime,
                Decimal,
                Enum,
            ),
        ):
            metadata[name] = json_safe(value)

    return sanitize_mapping(metadata) or None


def resolve_actor_user_id(
    arguments: Mapping[str, Any],
) -> UUID | None:
    context_actor = get_audit_context().actor_user_id
    if context_actor is not None:
        return context_actor

    for name in ActorArgumentNames:
        value = arguments.get(name)
        if isinstance(value, UUID):
            return value

    return None


def resolve_farm_id(
    arguments: Mapping[str, Any],
) -> UUID | None:
    value = arguments.get("farm_id")
    if isinstance(value, UUID):
        return value

    return get_audit_context().actor_farm_id


def resolve_action(
    spec: OperationAuditSpec,
    arguments: Mapping[str, Any],
) -> str:
    if spec.action == "ACTIVE_STATUS":
        return (
            AuditAction.ACTIVATE.value
            if bool(arguments.get("is_active"))
            else AuditAction.DEACTIVATE.value
        )

    return spec.action


def load_before_value(
    service: Any,
    loader: BeforeLoader | None,
    arguments: Mapping[str, Any],
) -> Any:
    if loader is None:
        return None

    target = service
    for part in loader.method_path.split("."):
        target = getattr(target, part)

    values = [arguments[name] for name in loader.argument_names]
    return target(*values)


def resource_id(
    spec: OperationAuditSpec,
    arguments: Mapping[str, Any],
    after_values: Mapping[str, Any] | None,
    before_values: Mapping[str, Any] | None,
) -> UUID | str | None:
    if after_values and after_values.get("id") is not None:
        return str(after_values["id"])

    if before_values and before_values.get("id") is not None:
        return str(before_values["id"])

    if spec.resource_id_argument is None:
        return None

    value = arguments.get(spec.resource_id_argument)
    if isinstance(value, (UUID, str)):
        return value

    return None


def audit_operation(
    spec: OperationAuditSpec,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(
        operation: Callable[..., Any],
    ) -> Callable[..., Any]:
        if getattr(
            operation,
            "__poultrypulse_audit_wrapped__",
            False,
        ):
            return operation

        signature = python_inspect.signature(operation)

        @wraps(operation)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            bound = signature.bind(*args, **kwargs)
            bound.apply_defaults()
            arguments = bound.arguments
            service = arguments["self"]
            database_session = service.database_session

            if not isinstance(database_session, Session):
                return operation(*args, **kwargs)

            before_values: dict[str, Any] | None = None
            if spec.before_loader is not None:
                try:
                    before_values = model_snapshot(
                        load_before_value(
                            service,
                            spec.before_loader,
                            arguments,
                        )
                    )
                except Exception:
                    before_values = None

            metadata = bound_metadata(
                arguments,
                static_metadata=spec.static_metadata,
            )
            resolved_action = resolve_action(
                spec,
                arguments,
            )
            resolved_farm_id = resolve_farm_id(arguments)
            resolved_actor_user_id = resolve_actor_user_id(arguments)

            try:
                result = operation(*args, **kwargs)
            except Exception as error:
                database_session.rollback()
                record_failure_safely(
                    database_session,
                    module=spec.module,
                    action=resolved_action,
                    description=(f"{spec.description} failed."),
                    error=error,
                    farm_id=resolved_farm_id,
                    actor_user_id=resolved_actor_user_id,
                    resource_type=spec.resource_type,
                    resource_id=resource_id(
                        spec,
                        arguments,
                        None,
                        before_values,
                    ),
                    metadata=metadata,
                )
                raise

            after_values = model_snapshot(result)
            record_audit_safely(
                database_session,
                module=spec.module,
                action=resolved_action,
                description=spec.description,
                farm_id=resolved_farm_id,
                actor_user_id=resolved_actor_user_id,
                resource_type=spec.resource_type,
                resource_id=resource_id(
                    spec,
                    arguments,
                    after_values,
                    before_values,
                ),
                before_values=before_values,
                after_values=after_values,
                metadata=metadata,
            )
            return result

        setattr(
            wrapped,
            "__poultrypulse_audit_wrapped__",
            True,
        )
        setattr(
            wrapped,
            "__poultrypulse_audit_spec__",
            spec,
        )
        return wrapped

    return decorator
