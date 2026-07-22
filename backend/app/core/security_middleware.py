from __future__ import annotations

import json
import threading
import time
from collections import defaultdict, deque
from collections.abc import Iterable
from typing import Any
from uuid import uuid4

from starlette.types import (
    ASGIApp,
    Message,
    Receive,
    Scope,
    Send,
)

from app.core.network import resolve_client_ip_from_scope


class _BodyTooLargeError(Exception):
    pass


class SecurityHardeningMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        max_request_body_bytes: int,
        security_headers_enabled: bool,
        hsts_enabled: bool,
        hsts_max_age_seconds: int,
        auth_rate_limit_enabled: bool,
        auth_rate_limit_requests: int,
        auth_rate_limit_window_seconds: int,
        trusted_proxy_entries: tuple[str, ...] = (),
        api_v1_prefix: str = "/api/v1",
    ) -> None:
        self.app = app
        self.max_request_body_bytes = max_request_body_bytes
        self.security_headers_enabled = security_headers_enabled
        self.hsts_enabled = hsts_enabled
        self.hsts_max_age_seconds = hsts_max_age_seconds
        self.auth_rate_limit_enabled = auth_rate_limit_enabled
        self.auth_rate_limit_requests = auth_rate_limit_requests
        self.auth_rate_limit_window_seconds = auth_rate_limit_window_seconds
        self.trusted_proxy_entries = trusted_proxy_entries
        prefix = api_v1_prefix.rstrip("/")
        self.rate_limited_paths = {
            f"{prefix}/auth/login",
            f"{prefix}/auth/refresh",
            f"{prefix}/platform/auth/login",
            f"{prefix}/platform/auth/refresh",
        }
        self._rate_limit_events: dict[
            tuple[str, str],
            deque[float],
        ] = defaultdict(deque)
        self._rate_limit_lock = threading.Lock()

    @staticmethod
    def _header_map(
        headers: Iterable[tuple[bytes, bytes]],
    ) -> dict[bytes, bytes]:
        return {key.lower(): value for key, value in headers}

    @staticmethod
    def _json_response(
        status_code: int,
        payload: dict[str, Any],
        *,
        extra_headers: dict[str, str] | None = None,
    ) -> tuple[int, list[tuple[bytes, bytes]], bytes]:
        body = json.dumps(
            payload,
            separators=(",", ":"),
        ).encode("utf-8")
        headers = [
            (b"content-type", b"application/json"),
            (
                b"content-length",
                str(len(body)).encode("ascii"),
            ),
        ]

        if extra_headers:
            headers.extend(
                (
                    key.lower().encode("latin-1"),
                    value.encode("latin-1"),
                )
                for key, value in extra_headers.items()
            )

        return status_code, headers, body

    def _security_headers(
        self,
        *,
        path: str,
    ) -> dict[bytes, bytes]:
        if not self.security_headers_enabled:
            return {}

        headers = {
            b"x-content-type-options": b"nosniff",
            b"x-frame-options": b"DENY",
            b"referrer-policy": b"no-referrer",
            b"permissions-policy": (b"camera=(), microphone=(), geolocation=()"),
            b"x-permitted-cross-domain-policies": b"none",
            b"cross-origin-resource-policy": b"same-site",
            b"content-security-policy": (
                b"frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
            ),
        }

        if "/auth/" in path:
            headers[b"cache-control"] = b"no-store, max-age=0"
            headers[b"pragma"] = b"no-cache"

        if self.hsts_enabled:
            headers[b"strict-transport-security"] = (
                f"max-age={self.hsts_max_age_seconds}; includeSubDomains"
            ).encode("ascii")

        return headers

    def _rate_limit_key(
        self,
        scope: Scope,
    ) -> tuple[str, str]:
        client_ip = resolve_client_ip_from_scope(
            headers=scope.get("headers", ()),
            client=scope.get("client"),
            trusted_proxy_entries=(self.trusted_proxy_entries),
        )
        return (
            client_ip or "unknown",
            str(scope.get("path", "")),
        )

    def _check_rate_limit(
        self,
        scope: Scope,
    ) -> int | None:
        if (
            not self.auth_rate_limit_enabled
            or scope.get("method") != "POST"
            or scope.get("path") not in self.rate_limited_paths
        ):
            return None

        key = self._rate_limit_key(scope)
        now = time.monotonic()
        cutoff = now - self.auth_rate_limit_window_seconds

        with self._rate_limit_lock:
            events = self._rate_limit_events[key]

            while events and events[0] <= cutoff:
                events.popleft()

            if len(events) >= self.auth_rate_limit_requests:
                retry_after = max(
                    1,
                    int(self.auth_rate_limit_window_seconds - (now - events[0])),
                )
                return retry_after

            events.append(now)

        return None

    async def _send_direct_response(
        self,
        *,
        send: Send,
        path: str,
        status_code: int,
        payload: dict[str, Any],
        request_id: str,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        response_status, headers, body = self._json_response(
            status_code,
            payload,
            extra_headers=extra_headers,
        )
        additions = self._security_headers(path=path)
        additions.setdefault(
            b"x-request-id",
            request_id.encode("latin-1"),
        )
        addition_names = set(additions)
        merged_headers = [
            (key, value) for key, value in headers if key.lower() not in addition_names
        ]
        merged_headers.extend(additions.items())

        await send(
            {
                "type": "http.response.start",
                "status": response_status,
                "headers": merged_headers,
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body,
            }
        )

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = str(scope.get("path", ""))
        incoming_headers = self._header_map(scope.get("headers", ()))
        request_id = (
            incoming_headers.get(b"x-request-id") or uuid4().hex.encode("ascii")
        ).decode("latin-1")

        content_length = incoming_headers.get(b"content-length")
        if content_length is not None:
            try:
                declared_length = int(content_length)
            except ValueError:
                await self._send_direct_response(
                    send=send,
                    path=path,
                    status_code=400,
                    request_id=request_id,
                    payload={
                        "error": {
                            "code": "invalid_content_length",
                            "message": ("The Content-Length header is invalid."),
                        }
                    },
                )
                return

            if declared_length > self.max_request_body_bytes:
                await self._send_direct_response(
                    send=send,
                    path=path,
                    status_code=413,
                    request_id=request_id,
                    payload={
                        "error": {
                            "code": "request_body_too_large",
                            "message": (
                                "The request body exceeds the configured size limit."
                            ),
                        }
                    },
                )
                return

        retry_after = self._check_rate_limit(scope)
        if retry_after is not None:
            await self._send_direct_response(
                send=send,
                path=path,
                status_code=429,
                request_id=request_id,
                extra_headers={
                    "Retry-After": str(retry_after),
                },
                payload={
                    "error": {
                        "code": "authentication_rate_limited",
                        "message": (
                            "Too many authentication requests. Try again later."
                        ),
                    }
                },
            )
            return

        bytes_received = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal bytes_received

            message = await receive()

            if message["type"] == "http.request":
                bytes_received += len(message.get("body", b""))
                if bytes_received > self.max_request_body_bytes:
                    raise _BodyTooLargeError

            return message

        async def hardened_send(message: Message) -> None:
            nonlocal response_started

            if message["type"] == "http.response.start":
                response_started = True
                additions = self._security_headers(path=path)
                addition_names = set(additions)
                response_headers = [
                    (key, value)
                    for key, value in message.get(
                        "headers",
                        (),
                    )
                    if key.lower() not in addition_names
                ]
                response_headers.extend(additions.items())
                message = {
                    **message,
                    "headers": response_headers,
                }

            await send(message)

        try:
            await self.app(
                scope,
                limited_receive,
                hardened_send,
            )
        except _BodyTooLargeError:
            if response_started:
                raise

            await self._send_direct_response(
                send=send,
                path=path,
                status_code=413,
                request_id=request_id,
                payload={
                    "error": {
                        "code": "request_body_too_large",
                        "message": (
                            "The request body exceeds the configured size limit."
                        ),
                    }
                },
            )
