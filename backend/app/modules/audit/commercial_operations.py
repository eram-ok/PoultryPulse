from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import wraps
import inspect as python_inspect
from typing import Any

from sqlalchemy.orm import Session

from app.modules.audit.integration import (
    record_audit_safely,
    record_failure_safely,
)
from app.modules.audit.operations import (
    BeforeLoader,
    bound_metadata,
    load_before_value,
    model_snapshot,
    resolve_action,
    resolve_actor_user_id,
    resolve_farm_id,
    resource_id,
)
from app.modules.audit.sanitizer import sanitize_mapping


@dataclass(frozen=True)
class CommercialAuditSpec:
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
    result_labels: tuple[str, ...] | None = None
    snapshot_result: bool = True
    excluded_metadata_arguments: tuple[str, ...] = ()


def service_database_session(service: Any) -> Session | None:
    for attribute_name in (
        "database_session",
        "db",
    ):
        candidate = getattr(
            service,
            attribute_name,
            None,
        )
        if isinstance(candidate, Session):
            return candidate

    return None


def commercial_result_snapshot(
    result: Any,
    spec: CommercialAuditSpec,
) -> dict[str, Any] | None:
    if not spec.snapshot_result:
        return None

    snapshot = model_snapshot(result)
    if snapshot is not None:
        return snapshot

    if spec.result_labels is not None and isinstance(result, (tuple, list)):
        labelled_values = {
            label: value
            for label, value in zip(
                spec.result_labels,
                result,
                strict=False,
            )
        }
        return sanitize_mapping(labelled_values)

    return None


def commercial_metadata(
    arguments: Mapping[str, Any],
    spec: CommercialAuditSpec,
) -> dict[str, Any] | None:
    metadata = (
        bound_metadata(
            arguments,
            static_metadata=spec.static_metadata,
        )
        or {}
    )

    for argument_name in spec.excluded_metadata_arguments:
        metadata.pop(argument_name, None)

    return metadata or None


def commercial_audit_operation(
    spec: CommercialAuditSpec,
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
            database_session = service_database_session(service)

            if database_session is None:
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

            metadata = commercial_metadata(
                arguments,
                spec,
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
                    actor_user_id=(resolved_actor_user_id),
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

            after_values = commercial_result_snapshot(
                result,
                spec,
            )
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
