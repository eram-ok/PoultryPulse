from __future__ import annotations

import logging

from fastapi import Request
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)


async def unexpected_exception_handler(
    request: Request,
    error: Exception,
) -> JSONResponse:
    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    logger.exception(
        "Unhandled PoultryPulse request failure.",
        extra={
            "request_id": request_id,
            "request_method": request.method,
            "request_path": request.url.path,
            "error_type": type(error).__name__,
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_server_error",
                "message": ("An unexpected server error occurred."),
                "request_id": request_id,
            }
        },
    )
