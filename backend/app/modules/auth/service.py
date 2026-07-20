from datetime import UTC, datetime, timedelta

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
from app.modules.auth.models import RefreshToken
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import TokenResponse
from app.modules.users.models import User
from app.modules.users.schemas import UserResponse


settings = get_settings()


class AuthService:
    """Authentication and token-management operations."""

    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session
        self.repository = AuthRepository(database_session)

    @staticmethod
    def parse_login_identifier(
        supplied_identifier: str,
    ) -> tuple[str | None, str]:
        cleaned = supplied_identifier.strip()

        if ":" not in cleaned:
            return None, cleaned

        farm_code, identifier = cleaned.split(":", 1)

        return farm_code.strip(), identifier.strip()

    def _issue_token_pair(
        self,
        user: User,
        *,
        created_ip: str | None,
        user_agent: str | None,
    ) -> tuple[str, str, RefreshToken]:
        claims = {
            "farm_id": str(user.farm_id),
            "username": user.username,
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

        refresh_record = RefreshToken(
            user_id=user.id,
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

        return access_token, refresh_token, refresh_record

    def _token_response(
        self,
        user: User,
        access_token: str,
        refresh_token: str,
    ) -> TokenResponse:
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=(settings.access_token_expire_minutes * 60),
            user=UserResponse.model_validate(user),
        )

    def login(
        self,
        supplied_identifier: str,
        password: str,
        *,
        created_ip: str | None,
        user_agent: str | None,
    ) -> TokenResponse:
        farm_code, identifier = self.parse_login_identifier(supplied_identifier)

        candidates = self.repository.find_login_candidates(
            identifier,
            farm_code=farm_code,
        )

        if not candidates:
            raise AuthenticationError(
                "The username or password is incorrect.",
                error_code="invalid_credentials",
            )

        if len(candidates) > 1:
            raise AuthenticationError(
                "This identifier belongs to more than one farm. "
                "Log in using FARM-CODE:username.",
                error_code="ambiguous_login_identifier",
            )

        user = candidates[0]
        current_time = datetime.now(UTC)

        if not user.is_active:
            raise AuthenticationError(
                "This user account is inactive.",
                error_code="inactive_account",
            )

        if user.locked_until is not None and user.locked_until > current_time:
            raise AuthenticationError(
                "This account is temporarily locked. Try again later.",
                error_code="account_temporarily_locked",
            )

        if not verify_password(
            password,
            user.password_hash,
        ):
            user.failed_login_attempts += 1

            if user.failed_login_attempts >= settings.login_max_failed_attempts:
                user.locked_until = current_time + timedelta(
                    minutes=settings.login_lock_minutes
                )

            self.database_session.commit()

            raise AuthenticationError(
                "The username or password is incorrect.",
                error_code="invalid_credentials",
            )

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = current_time

        access_token, refresh_token, _ = self._issue_token_pair(
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
    ) -> TokenResponse:
        try:
            payload = decode_token(supplied_refresh_token)
        except ValueError as exc:
            raise AuthenticationError(
                "The refresh token is invalid or expired.",
                error_code="invalid_refresh_token",
            ) from exc

        if payload.get("type") != "refresh":
            raise AuthenticationError(
                "An access token cannot be used for refresh.",
                error_code="incorrect_token_type",
            )

        jti = str(payload["jti"])
        refresh_record = self.repository.get_refresh_token(jti)

        if refresh_record is None:
            raise AuthenticationError(
                "The refresh token is not recognized.",
                error_code="refresh_token_not_found",
            )

        current_time = datetime.now(UTC)

        if refresh_record.revoked_at is not None:
            raise AuthenticationError(
                "This refresh token has already been revoked.",
                error_code="refresh_token_revoked",
            )

        if refresh_record.expires_at <= current_time:
            raise AuthenticationError(
                "The refresh token has expired.",
                error_code="refresh_token_expired",
            )

        user = refresh_record.user

        if not user.is_active:
            raise AuthenticationError(
                "This user account is inactive.",
                error_code="inactive_account",
            )

        if str(user.id) != str(payload["sub"]):
            raise AuthenticationError(
                "The refresh token is invalid.",
                error_code="refresh_token_user_mismatch",
            )

        if str(user.farm_id) != str(payload["farm_id"]):
            raise AuthenticationError(
                "The refresh token farm is invalid.",
                error_code="refresh_token_farm_mismatch",
            )

        refresh_record.revoked_at = current_time

        access_token, new_refresh_token, new_record = self._issue_token_pair(
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

    def logout(self, supplied_refresh_token: str) -> None:
        try:
            payload = decode_token(supplied_refresh_token)
        except ValueError:
            return

        if payload.get("type") != "refresh":
            return

        refresh_record = self.repository.get_refresh_token(str(payload["jti"]))

        if refresh_record is not None and refresh_record.revoked_at is None:
            refresh_record.revoked_at = datetime.now(UTC)
            self.database_session.commit()

    def change_password(
        self,
        user: User,
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
