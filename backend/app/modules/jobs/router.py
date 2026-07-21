from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.orm import Session

from app.core.database import get_database_session
from app.core.exceptions import (
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.modules.auth.dependencies import require_permissions
from app.modules.jobs.constants import (
    BackgroundJobStatus,
    BackgroundJobTrigger,
)
from app.modules.jobs.schemas import (
    BackgroundJobDefinitionListResponse,
    BackgroundJobDefinitionResponse,
    BackgroundJobRunListResponse,
    BackgroundJobRunResponse,
)
from app.modules.jobs.service import BackgroundJobsService
from app.modules.users.models import User


router = APIRouter(
    prefix="/jobs",
    tags=["Background Jobs"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


@router.get(
    "/definitions",
    response_model=BackgroundJobDefinitionListResponse,
)
def list_job_definitions(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("audit.view")),
    ],
) -> BackgroundJobDefinitionListResponse:
    del current_user
    service = BackgroundJobsService(database_session)
    return BackgroundJobDefinitionListResponse(
        items=[
            BackgroundJobDefinitionResponse(
                name=item.name,
                enabled=item.enabled,
                per_farm=item.per_farm,
                interval_seconds=item.interval_seconds,
            )
            for item in service.definitions
        ]
    )


@router.get(
    "/runs",
    response_model=BackgroundJobRunListResponse,
)
def list_job_runs(
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("audit.view")),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    job_name: str | None = None,
    job_status: Annotated[
        BackgroundJobStatus | None,
        Query(alias="status"),
    ] = None,
) -> BackgroundJobRunListResponse:
    service = BackgroundJobsService(database_session)
    items, total = service.repository.list_runs(
        offset=offset,
        limit=limit,
        job_name=job_name,
        status=(job_status.value if job_status is not None else None),
        farm_id=current_user.farm_id,
    )
    return BackgroundJobRunListResponse(
        items=[BackgroundJobRunResponse.model_validate(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/runs/{run_id}",
    response_model=BackgroundJobRunResponse,
)
def get_job_run(
    run_id: UUID,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("audit.view")),
    ],
) -> BackgroundJobRunResponse:
    service = BackgroundJobsService(database_session)
    item = service.repository.get_run(run_id)
    if item is None or item.farm_id != current_user.farm_id:
        raise ResourceNotFoundError(
            "The selected background job run does not exist.",
            error_code="background_job_run_not_found",
        )
    return BackgroundJobRunResponse.model_validate(item)


@router.post(
    "/{job_name}/run",
    response_model=BackgroundJobRunResponse,
)
def run_job_now(
    job_name: str,
    database_session: DatabaseSession,
    current_user: Annotated[
        User,
        Depends(require_permissions("audit.manage")),
    ],
) -> BackgroundJobRunResponse:
    service = BackgroundJobsService(database_session)
    definition = service.definition(job_name)
    if not definition.per_farm:
        raise ResourceConflictError(
            "Global maintenance jobs can only be run "
            "from the administrative command line.",
            error_code="global_job_cli_only",
        )

    run = service.run(
        job_name=job_name,
        farm_id=current_user.farm_id,
        trigger=BackgroundJobTrigger.MANUAL.value,
        force=True,
    )
    if run is None:
        raise RuntimeError("A forced job run did not return a record.")
    return BackgroundJobRunResponse.model_validate(run)
