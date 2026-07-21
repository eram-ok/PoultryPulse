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
    """Create a secure one-way password hash."""

    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    password_hash: str,
) -> bool:
    """Check whether a plain password matches a stored hash."""

    return password_hasher.verify(
        plain_password,
        password_hash,
    )


def _base_token_claims(
    *,
    subject: str,
    token_type: str,
    expires_at: datetime,
) -> dict[str, Any]:
    issued_at = datetime.now(UTC)

    return {
        "sub": subject,
        "type": token_type,
        "iat": issued_at,
        "nbf": issued_at,
        "exp": expires_at,
        "jti": str(uuid4()),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }


def create_access_token(
    subject: str,
    *,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed short-lived access token."""

    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(minutes=settings.access_token_expire_minutes)
    claims = _base_token_claims(
        subject=subject,
        token_type="access",
        expires_at=expires_at,
    )

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
    """Create a signed long-lived refresh token."""

    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(days=settings.refresh_token_expire_days)
    claims = _base_token_claims(
        subject=subject,
        token_type="refresh",
        expires_at=expires_at,
    )

    if additional_claims:
        claims.update(additional_claims)

    return jwt.encode(
        claims,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a signed PoultryPulse token."""

    required_claims = [
        "sub",
        "type",
        "iat",
        "exp",
        "jti",
    ]
    options: dict[str, Any] = {
        "require": required_claims,
        "verify_aud": (settings.jwt_validate_issuer_audience),
        "verify_iss": (settings.jwt_validate_issuer_audience),
    }
    decode_kwargs: dict[str, Any] = {
        "algorithms": [settings.jwt_algorithm],
        "options": options,
        "leeway": settings.jwt_leeway_seconds,
    }

    if settings.jwt_validate_issuer_audience:
        required_claims.extend(["iss", "aud"])
        decode_kwargs.update(
            {
                "issuer": settings.jwt_issuer,
                "audience": settings.jwt_audience,
            }
        )

    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            **decode_kwargs,
        )
    except InvalidTokenError as exc:
        raise ValueError("The authentication token is invalid or expired.") from exc
