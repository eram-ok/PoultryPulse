from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass, replace
from uuid import UUID


@dataclass(frozen=True)
class AuditRequestContext:
    request_id: str | None = None
    request_method: str | None = None
    request_path: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    actor_user_id: UUID | None = None
    actor_farm_id: UUID | None = None
    actor_username: str | None = None


_audit_context: ContextVar[AuditRequestContext] = ContextVar(
    "poultrypulse_audit_context",
    default=AuditRequestContext(),
)


def get_audit_context() -> AuditRequestContext:
    return _audit_context.get()


def set_audit_context(
    context: AuditRequestContext,
) -> Token[AuditRequestContext]:
    return _audit_context.set(context)


def reset_audit_context(
    token: Token[AuditRequestContext],
) -> None:
    _audit_context.reset(token)


def bind_audit_actor(
    *,
    user_id: UUID,
    farm_id: UUID,
    username: str,
) -> None:
    current = get_audit_context()
    _audit_context.set(
        replace(
            current,
            actor_user_id=user_id,
            actor_farm_id=farm_id,
            actor_username=username,
        )
    )
