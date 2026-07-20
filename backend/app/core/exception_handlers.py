from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ApplicationError,
    AuthenticationError,
)


async def application_error_handler(
    request: Request,
    exception: ApplicationError,
) -> JSONResponse:
    """Convert application errors into consistent API responses."""

    headers = None

    if isinstance(exception, AuthenticationError):
        headers = {"WWW-Authenticate": "Bearer"}

    return JSONResponse(
        status_code=exception.status_code,
        headers=headers,
        content={
            "error": {
                "code": exception.error_code,
                "message": exception.message,
                "path": request.url.path,
            }
        },
    )
