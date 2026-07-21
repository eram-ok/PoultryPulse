from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BackgroundJobDefinitionResponse(BaseModel):
    name: str
    enabled: bool
    per_farm: bool
    interval_seconds: int


class BackgroundJobDefinitionListResponse(BaseModel):
    items: list[BackgroundJobDefinitionResponse]


class BackgroundJobRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID | None
    job_name: str
    status: str
    trigger: str
    scheduled_for: datetime | None
    started_at: datetime
    completed_at: datetime | None
    duration_ms: int | None
    result_json: dict[str, Any] | None
    error_type: str | None
    error_message: str | None
    worker_id: str
    created_at: datetime


class BackgroundJobRunListResponse(BaseModel):
    items: list[BackgroundJobRunResponse]
    total: int
    offset: int
    limit: int
