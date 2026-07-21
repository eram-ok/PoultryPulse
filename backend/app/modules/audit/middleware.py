from __future__ import annotations

from uuid import uuid4

from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings
from app.core.network import resolve_client_ip
from app.modules.audit.context import (
    AuditRequestContext,
    reset_audit_context,
    set_audit_context,
)


settings = get_settings()


def client_ip(request: Request) -> str | None:
    return resolve_client_ip(
        request,
        trusted_proxy_entries=(settings.trusted_proxy_list),
    )


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
