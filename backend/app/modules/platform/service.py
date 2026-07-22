
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import (
    AuthenticationError,
    BusinessRuleError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.modules.audit.context import get_audit_context
from app.modules.platform.models import (
    PlatformAuditLog,
    PlatformRefreshToken,
    PlatformUser,
)
from app.modules.platform.repository import (
    PlatformAuthRepository,
)
from app.modules.platform.schemas import (
    PlatformTokenResponse,
    PlatformUserResponse,
)


settings = get_settings()
logger = logging.getLogger(__name__)
PLATFORM_PRINCIPAL_TYPE = "platform_user"


class PlatformAuthService:
    """Authentication and session operations for platform users."""

    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session
        self.repository = PlatformAuthRepository(
            database_session
        )

    def _issue_token_pair(
        self,
        user: PlatformUser,
        *,
        created_ip: str | None,
        user_agent: str | None,
    ) -> tuple[
        str,
        str,
        PlatformRefreshToken,
    ]:
        claims = {
            "principal_type": PLATFORM_PRINCIPAL_TYPE,
            "username": user.username,
            "is_super_admin": user.is_super_admin,
        }
        access_token = create_access_token(
            str(user.id),
            additional_claims=claims,
        )
        refresh_token = create_refresh_token(
            str(user.id),
            additional_claims=claims,
        )
        refresh_payload = decode_token(refresh_token)
        refresh_record = PlatformRefreshToken(
            platform_user_id=user.id,
            jti=str(refresh_payload["jti"]),
            expires_at=datetime.fromtimestamp(
                int(refresh_payload["exp"]),
                tz=UTC,
            ),
            created_ip=created_ip,
            user_agent=user_agent,
        )
        self.database_session.add(refresh_record)
        self.database_session.flush()

        return (
            access_token,
            refresh_token,
            refresh_record,
        )

    @staticmethod
    def _token_response(
        user: PlatformUser,
        access_token: str,
        refresh_token: str,
    ) -> PlatformTokenResponse:
        return PlatformTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=(
                settings.access_token_expire_minutes * 60
            ),
            user=PlatformUserResponse.model_validate(user),
        )

    def login(
        self,
        identifier: str,
        password: str,
        *,
        created_ip: str | None,
        user_agent: str | None,
    ) -> PlatformTokenResponse:
        user = self.repository.find_user(identifier)

        if user is None:
            raise AuthenticationError(
                "The username or password is incorrect.",
                error_code="invalid_platform_credentials",
            )

        current_time = datetime.now(UTC)

        if not user.is_active:
            raise AuthenticationError(
                "This platform account is inactive.",
                error_code="inactive_platform_account",
            )

        if (
            user.locked_until is not None
            and user.locked_until > current_time
        ):
            raise AuthenticationError(
                "This platform account is temporarily locked.",
                error_code="platform_account_temporarily_locked",
            )

        if not verify_password(
            password,
            user.password_hash,
        ):
            user.failed_login_attempts += 1

            if (
                user.failed_login_attempts
                >= settings.login_max_failed_attempts
            ):
                user.locked_until = current_time + timedelta(
                    minutes=settings.login_lock_minutes
                )

            self.database_session.commit()

            raise AuthenticationError(
                "The username or password is incorrect.",
                error_code="invalid_platform_credentials",
            )

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = current_time

        (
            access_token,
            refresh_token,
            _,
        ) = self._issue_token_pair(
            user,
            created_ip=created_ip,
            user_agent=user_agent,
        )

        self.database_session.commit()

        return self._token_response(
            user,
            access_token,
            refresh_token,
        )

    def refresh(
        self,
        supplied_refresh_token: str,
        *,
        created_ip: str | None,
        user_agent: str | None,
    ) -> PlatformTokenResponse:
        try:
            payload = decode_token(
                supplied_refresh_token
            )
        except ValueError as exc:
            raise AuthenticationError(
                "The platform refresh token is invalid or expired.",
                error_code="invalid_platform_refresh_token",
            ) from exc

        if payload.get("type") != "refresh":
            raise AuthenticationError(
                "An access token cannot be used for refresh.",
                error_code="incorrect_token_type",
            )

        if (
            payload.get("principal_type")
            != PLATFORM_PRINCIPAL_TYPE
        ):
            raise AuthenticationError(
                "A farm token cannot access platform authentication.",
                error_code="invalid_platform_principal",
            )

        refresh_record = self.repository.get_refresh_token(
            str(payload["jti"])
        )

        if refresh_record is None:
            raise AuthenticationError(
                "The platform refresh token is not recognized.",
                error_code="platform_refresh_token_not_found",
            )

        current_time = datetime.now(UTC)

        if refresh_record.revoked_at is not None:
            raise AuthenticationError(
                "This platform refresh token was revoked.",
                error_code="platform_refresh_token_revoked",
            )

        if refresh_record.expires_at <= current_time:
            raise AuthenticationError(
                "The platform refresh token has expired.",
                error_code="platform_refresh_token_expired",
            )

        user = refresh_record.platform_user

        if not user.is_active:
            raise AuthenticationError(
                "This platform account is inactive.",
                error_code="inactive_platform_account",
            )

        if str(user.id) != str(payload["sub"]):
            raise AuthenticationError(
                "The platform refresh token is invalid.",
                error_code="platform_refresh_user_mismatch",
            )

        refresh_record.revoked_at = current_time

        (
            access_token,
            new_refresh_token,
            new_record,
        ) = self._issue_token_pair(
            user,
            created_ip=created_ip,
            user_agent=user_agent,
        )

        refresh_record.replaced_by_jti = new_record.jti
        self.database_session.commit()

        return self._token_response(
            user,
            access_token,
            new_refresh_token,
        )

    def logout(
        self,
        supplied_refresh_token: str,
    ) -> None:
        try:
            payload = decode_token(
                supplied_refresh_token
            )
        except ValueError:
            return

        if payload.get("type") != "refresh":
            return

        if (
            payload.get("principal_type")
            != PLATFORM_PRINCIPAL_TYPE
        ):
            raise AuthenticationError(
                "A farm token cannot access platform authentication.",
                error_code="invalid_platform_principal",
            )

        refresh_record = self.repository.get_refresh_token(
            str(payload["jti"])
        )

        if (
            refresh_record is not None
            and refresh_record.revoked_at is None
        ):
            refresh_record.revoked_at = datetime.now(UTC)
            self.database_session.commit()

    def change_password(
        self,
        user: PlatformUser,
        current_password: str,
        new_password: str,
    ) -> None:
        if not verify_password(
            current_password,
            user.password_hash,
        ):
            raise AuthenticationError(
                "The current password is incorrect.",
                error_code="incorrect_current_password",
            )

        if verify_password(
            new_password,
            user.password_hash,
        ):
            raise BusinessRuleError(
                "The new password must differ from the current password.",
                error_code="password_unchanged",
            )

        user.password_hash = hash_password(new_password)
        user.must_change_password = False

        self.repository.revoke_all_refresh_tokens(
            user.id,
            datetime.now(UTC),
        )
        self.database_session.commit()

    def record_event(
        self,
        *,
        action: str,
        outcome: str,
        description: str,
        user: PlatformUser | None = None,
        target_farm_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: UUID | str | None = None,
        metadata: dict[str, Any] | None = None,
        error: Exception | None = None,
    ) -> None:
        context = get_audit_context()
        error_code = None
        error_message = None

        if error is not None:
            value = getattr(error, "error_code", None)
            error_code = (
                value
                if isinstance(value, str)
                else type(error).__name__
            )
            error_message = (
                str(error)[:500]
                if type(error).__module__.startswith("app.")
                else "An unexpected application error occurred."
            )

        item = PlatformAuditLog(
            platform_user_id=(
                user.id if user is not None else None
            ),
            target_farm_id=target_farm_id,
            actor_username=(
                user.username if user is not None else None
            ),
            action=action,
            outcome=outcome,
            severity=(
                "WARNING"
                if outcome in {"FAILURE", "DENIED"}
                else "INFO"
            ),
            description=description,
            resource_type=resource_type,
            resource_id=(
                str(resource_id)
                if resource_id is not None
                else None
            ),
            request_id=context.request_id,
            request_method=context.request_method,
            request_path=context.request_path,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
            metadata_json=metadata,
            error_code=error_code,
            error_message=error_message,
        )

        try:
            self.repository.add_audit_log(item)
            self.database_session.commit()
        except Exception:
            self.database_session.rollback()
            logger.exception(
                "PoultryPulse could not persist a platform audit event."
            )
