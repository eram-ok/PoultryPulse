from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.audit.constants import (
    AuditAction,
    AuditOutcome,
    AuditSeverity,
)


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID | None
    actor_user_id: UUID | None
    actor_username: str | None
    action: AuditAction
    outcome: AuditOutcome
    severity: AuditSeverity
    module: str
    resource_type: str | None
    resource_id: str | None
    description: str
    request_id: str | None
    request_method: str | None
    request_path: str | None
    ip_address: str | None
    user_agent: str | None
    before_values: dict[str, Any] | None
    after_values: dict[str, Any] | None
    changes: dict[str, Any] | None
    metadata_json: dict[str, Any] | None
    error_code: str | None
    error_message: str | None
    occurred_at: datetime
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    offset: int
    limit: int


class AuditSummaryResponse(BaseModel):
    total: int
    successful: int
    failed: int
    critical: int
    unique_actors: int
