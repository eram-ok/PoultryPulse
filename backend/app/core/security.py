from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import get_settings


settings = get_settings()
password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Create a secure one-way hash from a plain-text password."""

    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    password_hash: str,
) -> bool:
    """Check whether a password matches a stored hash."""

    return password_hasher.verify(
        plain_password,
        password_hash,
    )


def create_access_token(
    subject: str,
    *,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed PoultryPulse access token."""

    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(minutes=settings.access_token_expire_minutes)

    claims: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "iat": issued_at,
        "exp": expires_at,
        "jti": str(uuid4()),
    }

    if additional_claims:
        claims.update(additional_claims)

    return jwt.encode(
        claims,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(
    subject: str,
    *,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed PoultryPulse refresh token."""

    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(days=settings.refresh_token_expire_days)

    claims: dict[str, Any] = {
        "sub": subject,
        "type": "refresh",
        "iat": issued_at,
        "exp": expires_at,
        "jti": str(uuid4()),
    }

    if additional_claims:
        claims.update(additional_claims)

    return jwt.encode(
        claims,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a signed PoultryPulse token."""

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError as exc:
        raise ValueError("The authentication token is invalid or expired.") from exc

    return payload
