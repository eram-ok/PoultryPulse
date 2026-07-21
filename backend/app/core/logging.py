from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar, Token
from datetime import UTC, datetime
from typing import Any


_request_id_context: ContextVar[str | None] = ContextVar(
    "poultrypulse_log_request_id",
    default=None,
)

_EXTRA_FIELDS = (
    "application",
    "client_ip",
    "database_status",
    "duration_ms",
    "environment",
    "error_type",
    "event",
    "request_method",
    "request_path",
    "response_size_bytes",
    "status_code",
    "version",
)

_configured_signature: tuple[str, str, bool] | None = None


def bind_log_request_id(
    request_id: str | None,
) -> Token[str | None]:
    """Bind a request identifier to logs emitted in this context."""

    return _request_id_context.set(request_id)


def reset_log_request_id(
    token: Token[str | None],
) -> None:
    """Restore the previous request identifier."""

    _request_id_context.reset(token)


def current_log_request_id() -> str | None:
    """Return the request identifier bound to the current context."""

    return _request_id_context.get()


class JsonLogFormatter(logging.Formatter):
    """Render one structured JSON object per log record."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = (
            getattr(
                record,
                "request_id",
                None,
            )
            or current_log_request_id()
        )
        if request_id:
            payload["request_id"] = request_id

        for field_name in _EXTRA_FIELDS:
            value = getattr(
                record,
                field_name,
                None,
            )
            if value is not None:
                payload[field_name] = value

        if record.exc_info:
            payload["exception"] = self.formatException(
                record.exc_info,
            )

        return json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )


class TextLogFormatter(logging.Formatter):
    """Render concise human-readable logs for local development."""

    def format(self, record: logging.LogRecord) -> str:
        request_id = (
            getattr(
                record,
                "request_id",
                None,
            )
            or current_log_request_id()
        )
        suffix = f" request_id={request_id}" if request_id else ""
        original_message = record.msg
        original_args = record.args
        try:
            record.msg = f"{record.getMessage()}{suffix}"
            record.args = ()
            return super().format(record)
        finally:
            record.msg = original_message
            record.args = original_args


def configure_logging(
    *,
    level: str,
    log_format: str,
    include_uvicorn_access_logs: bool,
) -> None:
    """Configure deterministic application and server logging."""

    global _configured_signature

    normalized_level = level.upper()
    normalized_format = log_format.lower()
    signature = (
        normalized_level,
        normalized_format,
        include_uvicorn_access_logs,
    )

    if _configured_signature == signature:
        return

    handler = logging.StreamHandler(sys.stdout)

    if normalized_format == "json":
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(
            TextLogFormatter(
                "%(asctime)s %(levelname)s [%(name)s] %(message)s",
            )
        )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(normalized_level)

    for logger_name in (
        "uvicorn",
        "uvicorn.error",
    ):
        server_logger = logging.getLogger(logger_name)
        server_logger.handlers.clear()
        server_logger.propagate = True
        server_logger.setLevel(normalized_level)

    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers.clear()
    access_logger.propagate = True
    access_logger.setLevel(
        normalized_level if include_uvicorn_access_logs else logging.WARNING
    )

    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.WARNING,
    )

    _configured_signature = signature
