from __future__ import annotations

from uuid import uuid4

from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response

from app.modules.audit.context import (
    AuditRequestContext,
    reset_audit_context,
    set_audit_context,
)


def client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    if request.client is None:
        return None

    return request.client.host


class AuditRequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get("x-request-id") or uuid4().hex

        token = set_audit_context(
            AuditRequestContext(
                request_id=request_id,
                request_method=request.method,
                request_path=request.url.path,
                ip_address=client_ip(request),
                user_agent=request.headers.get("user-agent"),
            )
        )

        request.state.request_id = request_id

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            reset_audit_context(token)
