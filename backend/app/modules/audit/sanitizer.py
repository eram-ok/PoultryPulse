from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping
from uuid import UUID


REDACTED = "[REDACTED]"

SENSITIVE_PARTS = (
    "password",
    "passcode",
    "secret",
    "token",
    "authorization",
    "cookie",
    "api_key",
    "apikey",
    "private_key",
    "refresh_token",
    "access_token",
)


def is_sensitive_key(key: str) -> bool:
    normalized = key.strip().lower()
    return any(part in normalized for part in SENSITIVE_PARTS)


def json_safe(value: Any) -> Any:
    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, Mapping):
        return sanitize_mapping(value)

    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]

    return str(value)


def sanitize_mapping(
    values: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if values is None:
        return None

    sanitized: dict[str, Any] = {}

    for key, value in values.items():
        normalized_key = str(key)

        if is_sensitive_key(normalized_key):
            sanitized[normalized_key] = REDACTED
        else:
            sanitized[normalized_key] = json_safe(value)

    return sanitized


def calculate_changes(
    before_values: Mapping[str, Any] | None,
    after_values: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    before = sanitize_mapping(before_values) or {}
    after = sanitize_mapping(after_values) or {}

    changes: dict[str, Any] = {}

    for key in sorted(set(before) | set(after)):
        old_value = before.get(key)
        new_value = after.get(key)

        if old_value != new_value:
            changes[key] = {
                "before": old_value,
                "after": new_value,
            }

    return changes or None
