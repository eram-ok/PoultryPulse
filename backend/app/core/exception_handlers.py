from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import ApplicationError


async def application_error_handler(
    request: Request,
    exception: ApplicationError,
) -> JSONResponse:
    """Convert expected application errors into consistent API responses."""

    return JSONResponse(
        status_code=exception.status_code,
        content={
            "error": {
                "code": exception.error_code,
                "message": exception.message,
                "path": request.url.path,
            }
        },
    )
