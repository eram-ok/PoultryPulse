from __future__ import annotations

import logging
import time
from collections.abc import Iterable
from uuid import uuid4

from starlette.types import (
    ASGIApp,
    Message,
    Receive,
    Scope,
    Send,
)

from app.core.logging import (
    bind_log_request_id,
    reset_log_request_id,
)
from app.core.network import resolve_client_ip_from_scope


logger = logging.getLogger("poultrypulse.requests")


def _headers_to_mapping(
    headers: Iterable[tuple[bytes, bytes]],
) -> dict[bytes, bytes]:
    return {key.lower(): value for key, value in headers}


def _request_id_from_scope(scope: Scope) -> str:
    state = scope.get("state")

    if isinstance(state, dict):
        state_request_id = state.get("request_id")
        if state_request_id:
            return str(state_request_id)

    headers = _headers_to_mapping(
        scope.get("headers", ()),
    )
    supplied = headers.get(b"x-request-id")

    if supplied:
        return supplied.decode(
            "latin-1",
            errors="replace",
        )

    return uuid4().hex


class OperationalRequestLoggingMiddleware:
    """Log completed requests without recording request bodies."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        enabled: bool,
        trusted_proxy_entries: tuple[str, ...] = (),
        excluded_paths: tuple[str, ...] = (),
        health_paths: tuple[str, ...] = (),
    ) -> None:
        self.app = app
        self.enabled = enabled
        self.trusted_proxy_entries = trusted_proxy_entries
        self.excluded_paths = set(excluded_paths)
        self.health_paths = set(health_paths)

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started_at = time.perf_counter()
        path = str(scope.get("path", ""))
        method = str(scope.get("method", ""))
        request_id = _request_id_from_scope(scope)
        status_code = 500
        response_size_bytes: int | None = None
        token = bind_log_request_id(request_id)

        async def observed_send(
            message: Message,
        ) -> None:
            nonlocal status_code
            nonlocal response_size_bytes

            if message["type"] == "http.response.start":
                status_code = int(
                    message.get("status", 500),
                )
                headers = list(
                    message.get("headers", ()),
                )

                if path in self.health_paths:
                    header_names = {key.lower() for key, _ in headers}
                    if b"cache-control" not in header_names:
                        headers.append(
                            (
                                b"cache-control",
                                b"no-store, max-age=0",
                            )
                        )
                    if b"pragma" not in header_names:
                        headers.append((b"pragma", b"no-cache"))

                for key, value in headers:
                    if key.lower() == b"content-length":
                        try:
                            response_size_bytes = int(value)
                        except ValueError:
                            response_size_bytes = None
                        break

                message = {
                    **message,
                    "headers": headers,
                }

            await send(message)

        error_type: str | None = None

        try:
            await self.app(
                scope,
                receive,
                observed_send,
            )
        except Exception as error:
            status_code = 500
            error_type = type(error).__name__
            raise
        finally:
            duration_ms = round(
                (time.perf_counter() - started_at) * 1000,
                3,
            )

            if self.enabled and path not in self.excluded_paths:
                client_ip = resolve_client_ip_from_scope(
                    headers=scope.get("headers", ()),
                    client=scope.get("client"),
                    trusted_proxy_entries=(self.trusted_proxy_entries),
                )
                level = (
                    logging.ERROR
                    if status_code >= 500
                    else (logging.WARNING if status_code >= 400 else logging.INFO)
                )
                logger.log(
                    level,
                    "HTTP request completed.",
                    extra={
                        "request_id": request_id,
                        "request_method": method,
                        "request_path": path,
                        "status_code": status_code,
                        "duration_ms": duration_ms,
                        "client_ip": client_ip,
                        "response_size_bytes": (response_size_bytes),
                        "error_type": error_type,
                        "event": "http_request_completed",
                    },
                )

            reset_log_request_id(token)
