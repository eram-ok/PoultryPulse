from __future__ import annotations

import hashlib
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import (
    BusinessRuleError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.core.security import hash_password
from app.modules.alerts.config import NotificationSettings
from app.modules.alerts.transports import EmailTransport
from app.modules.audit.context import get_audit_context
from app.modules.farms.constants import FarmLifecycleStatus
from app.modules.farms.models import Farm
from app.modules.onboarding.constants import (
    FarmInvitationDeliveryStatus,
    FarmInvitationStatus,
)
from app.modules.onboarding.models import PlatformFarmInvitation
from app.modules.onboarding.repository import FarmOnboardingRepository
from app.modules.onboarding.schemas import (
    FarmInvitationAcceptResponse,
    FarmInvitationPublicResponse,
    PlatformFarmInvitationIssueResponse,
    PlatformFarmInvitationResponse,
    PlatformFarmOnboardingStatusResponse,
)
from app.modules.platform.models import PlatformAuditLog, PlatformUser
from app.modules.users.models import User


class FarmOnboardingService:
    """Create, deliver, validate, reissue and accept farm invitations."""

    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session
        self.repository = FarmOnboardingRepository(database_session)
        self.settings = get_settings()

    @staticmethod
    def request_fingerprint(payload: dict[str, Any]) -> str:
        serialized = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    @staticmethod
    def token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _new_token() -> tuple[str, str]:
        token = secrets.token_urlsafe(48)
        return token, FarmOnboardingService.token_hash(token)

    def _setup_url(self, token: str) -> str:
        base_url = self.settings.farm_onboarding_setup_base_url.strip()
        parts = urlsplit(base_url)
        fragment = dict(
            parse_qsl(
                parts.fragment,
                keep_blank_values=True,
            )
        )
        fragment["token"] = token
        return urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                parts.path,
                parts.query,
                urlencode(fragment),
            )
        )

    @staticmethod
    def _invitation_response(
        invitation: PlatformFarmInvitation,
    ) -> PlatformFarmInvitationResponse:
        return PlatformFarmInvitationResponse.model_validate(invitation)

    @staticmethod
    def _audit(
        *,
        action: str,
        description: str,
        farm_id: UUID,
        invitation_id: UUID,
        actor: PlatformUser | None = None,
        actor_username: str | None = None,
        outcome: str = "SUCCESS",
        severity: str = "INFO",
        metadata: dict[str, Any] | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        public_path: str | None = None,
    ) -> PlatformAuditLog:
        context = get_audit_context()
        return PlatformAuditLog(
            platform_user_id=(actor.id if actor is not None else None),
            target_farm_id=farm_id,
            actor_username=(
                actor.username
                if actor is not None
                else actor_username
            ),
            action=action,
            outcome=outcome,
            severity=severity,
            description=description,
            resource_type="FarmInvitation",
            resource_id=str(invitation_id),
            request_id=context.request_id,
            request_method=context.request_method,
            request_path=(
                public_path
                if public_path is not None
                else context.request_path
            ),
            ip_address=context.ip_address,
            user_agent=context.user_agent,
            metadata_json=metadata,
            error_code=error_code,
            error_message=error_message,
        )

    def find_idempotent_replay(
        self,
        *,
        actor: PlatformUser,
        idempotency_key: str | None,
        request_fingerprint: str,
    ) -> PlatformFarmInvitation | None:
        if idempotency_key is None:
            return None

        normalized_key = idempotency_key.strip()
        invitation = self.repository.get_by_idempotency(
            platform_user_id=actor.id,
            idempotency_key=normalized_key,
        )
        if invitation is None:
            return None

        if invitation.request_fingerprint != request_fingerprint:
            raise ResourceConflictError(
                "The idempotency key was already used with different onboarding data.",
                error_code="onboarding_idempotency_conflict",
            )

        return invitation

    def prepare_invitation(
        self,
        *,
        farm: Farm,
        administrator: User,
        actor: PlatformUser,
        idempotency_key: str | None,
        request_fingerprint: str,
        issued_at: datetime | None = None,
    ) -> tuple[PlatformFarmInvitation, str, str]:
        current_time = issued_at or datetime.now(UTC)
        token, token_hash = self._new_token()
        notification_settings = NotificationSettings.from_environment()
        delivery_status = (
            FarmInvitationDeliveryStatus.PENDING
            if notification_settings.email_ready
            else FarmInvitationDeliveryStatus.NOT_CONFIGURED
        )

        invitation = PlatformFarmInvitation(
            farm_id=farm.id,
            administrator_user_id=administrator.id,
            issued_by_platform_user_id=actor.id,
            token_hash=token_hash,
            status=FarmInvitationStatus.PENDING.value,
            expires_at=current_time
            + timedelta(
                hours=self.settings.farm_invitation_expiry_hours
            ),
            delivery_status=delivery_status.value,
            idempotency_key=(
                idempotency_key.strip()
                if idempotency_key is not None
                else None
            ),
            request_fingerprint=request_fingerprint,
        )
        self.repository.add(invitation)
        self.database_session.flush()

        return invitation, token, self._setup_url(token)

    def administrator_for_invitation(
        self,
        invitation: PlatformFarmInvitation,
    ) -> User:
        administrator = self.repository.get_user(
            invitation.administrator_user_id
        )
        if administrator is None:
            raise ResourceNotFoundError(
                "The invited farm administrator no longer exists.",
                error_code="invited_administrator_not_found",
            )
        return administrator

    def deliver_invitation(
        self,
        invitation_id: UUID,
        *,
        setup_url: str,
        actor: PlatformUser,
    ) -> PlatformFarmInvitation:
        invitation = self.database_session.get(
            PlatformFarmInvitation,
            invitation_id,
        )
        if invitation is None:
            raise ResourceNotFoundError(
                "The farm invitation could not be retrieved.",
                error_code="farm_invitation_not_found",
            )

        if invitation.status != FarmInvitationStatus.PENDING.value:
            return invitation

        administrator = self.administrator_for_invitation(invitation)
        farm = self.repository.get_farm(invitation.farm_id)
        if farm is None:
            raise ResourceNotFoundError(
                "The invited farm no longer exists.",
                error_code="platform_farm_not_found",
            )

        notification_settings = NotificationSettings.from_environment()
        if not notification_settings.email_ready:
            invitation.delivery_status = (
                FarmInvitationDeliveryStatus.NOT_CONFIGURED.value
            )
            invitation.last_delivery_error = None
            self.database_session.commit()
            return invitation

        invitation.delivery_attempt_count += 1
        invitation.last_delivery_attempt_at = datetime.now(UTC)

        body = (
            f"Hello {administrator.first_name},\n\n"
            f"You have been invited to administer {farm.name} "
            f"({farm.farm_code}) in PoultryPulse.\n\n"
            f"Set up your account using this one-time link:\n"
            f"{setup_url}\n\n"
            f"This link expires at {invitation.expires_at.isoformat()}.\n"
            "If you were not expecting this invitation, contact the "
            "PoultryPulse platform administrator."
        )
        result = EmailTransport(notification_settings).send(
            destination=administrator.email or "",
            subject=f"Set up your PoultryPulse account for {farm.name}",
            body=body,
        )

        if result.success:
            invitation.delivery_status = (
                FarmInvitationDeliveryStatus.SENT.value
            )
            invitation.sent_at = datetime.now(UTC)
            invitation.last_delivery_error = None
            action = "FARM_INVITATION_SENT"
            outcome = "SUCCESS"
            severity = "INFO"
            description = "Sent a farm administrator setup invitation."
            error_code = None
        else:
            invitation.delivery_status = (
                FarmInvitationDeliveryStatus.FAILED.value
            )
            invitation.last_delivery_error = (
                (result.error or "Email delivery failed.")[:2000]
            )
            action = "FARM_INVITATION_SEND_FAILED"
            outcome = "FAILURE"
            severity = "WARNING"
            description = "Failed to send a farm administrator setup invitation."
            error_code = "farm_invitation_email_delivery_failed"

        self.database_session.add(
            self._audit(
                action=action,
                outcome=outcome,
                severity=severity,
                description=description,
                farm_id=invitation.farm_id,
                invitation_id=invitation.id,
                actor=actor,
                metadata={
                    "delivery_status": invitation.delivery_status,
                    "delivery_attempt_count": (
                        invitation.delivery_attempt_count
                    ),
                },
                error_code=error_code,
                error_message=(
                    "Invitation email delivery failed."
                    if not result.success
                    else None
                ),
            )
        )

        try:
            self.database_session.commit()
        except Exception:
            self.database_session.rollback()
            raise

        return invitation

    def platform_status(
        self,
        farm_id: UUID,
    ) -> PlatformFarmOnboardingStatusResponse:
        farm = self.repository.get_farm(farm_id)
        if farm is None:
            raise ResourceNotFoundError(
                "The requested farm does not exist.",
                error_code="platform_farm_not_found",
            )

        invitation = self.repository.get_latest_for_farm(farm_id)
        administrator = (
            self.administrator_for_invitation(invitation)
            if invitation is not None
            else self.repository.find_administrator(farm_id)
        )
        completed = bool(
            administrator is not None
            and administrator.is_active
            and administrator.is_verified
        )

        return PlatformFarmOnboardingStatusResponse(
            farm_id=farm.id,
            administrator_user_id=(
                administrator.id if administrator is not None else None
            ),
            administrator_username=(
                administrator.username
                if administrator is not None
                else None
            ),
            administrator_email=(
                administrator.email
                if administrator is not None
                else None
            ),
            administrator_is_active=(
                administrator.is_active
                if administrator is not None
                else None
            ),
            administrator_is_verified=(
                administrator.is_verified
                if administrator is not None
                else None
            ),
            completed=completed,
            legacy_completed=(invitation is None and completed),
            invitation=(
                self._invitation_response(invitation)
                if invitation is not None
                else None
            ),
        )

    def reissue_invitation(
        self,
        farm_id: UUID,
        *,
        actor: PlatformUser,
    ) -> PlatformFarmInvitationIssueResponse:
        farm = self.repository.get_farm(farm_id)
        if farm is None:
            raise ResourceNotFoundError(
                "The requested farm does not exist.",
                error_code="platform_farm_not_found",
            )
        if (
            not farm.is_active
            or farm.lifecycle_status
            != FarmLifecycleStatus.ACTIVE.value
        ):
            raise BusinessRuleError(
                "Invitations cannot be issued while the farm is not active.",
                error_code="inactive_farm_invitation",
            )

        latest = self.repository.get_latest_for_farm(
            farm_id,
            for_update=True,
        )
        administrator = (
            self.administrator_for_invitation(latest)
            if latest is not None
            else self.repository.find_administrator(farm_id)
        )
        if administrator is None:
            raise ResourceNotFoundError(
                "The farm does not have an administrator account to invite.",
                error_code="farm_administrator_not_found",
            )
        if administrator.is_active and administrator.is_verified:
            raise BusinessRuleError(
                "The farm administrator has already completed onboarding.",
                error_code="farm_onboarding_already_completed",
            )

        current_time = datetime.now(UTC)
        if (
            latest is not None
            and latest.status == FarmInvitationStatus.PENDING.value
        ):
            latest.status = FarmInvitationStatus.REVOKED.value
            latest.revoked_at = current_time

        token, token_hash = self._new_token()
        notification_settings = NotificationSettings.from_environment()
        invitation = PlatformFarmInvitation(
            farm_id=farm.id,
            administrator_user_id=administrator.id,
            issued_by_platform_user_id=actor.id,
            token_hash=token_hash,
            status=FarmInvitationStatus.PENDING.value,
            expires_at=current_time
            + timedelta(
                hours=self.settings.farm_invitation_expiry_hours
            ),
            delivery_status=(
                FarmInvitationDeliveryStatus.PENDING.value
                if notification_settings.email_ready
                else FarmInvitationDeliveryStatus.NOT_CONFIGURED.value
            ),
        )
        self.repository.add(invitation)
        self.database_session.flush()
        setup_url = self._setup_url(token)

        self.database_session.add(
            self._audit(
                action="FARM_INVITATION_REISSUED",
                description="Reissued a farm administrator setup invitation.",
                farm_id=farm.id,
                invitation_id=invitation.id,
                actor=actor,
                metadata={
                    "administrator_user_id": str(administrator.id),
                    "previous_invitation_id": (
                        str(latest.id) if latest is not None else None
                    ),
                    "expires_at": invitation.expires_at.isoformat(),
                },
            )
        )

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()
            raise ResourceConflictError(
                "The farm invitation could not be reissued.",
                error_code="farm_invitation_reissue_conflict",
            ) from exc
        except Exception:
            self.database_session.rollback()
            raise

        invitation = self.deliver_invitation(
            invitation.id,
            setup_url=setup_url,
            actor=actor,
        )
        return PlatformFarmInvitationIssueResponse(
            invitation=self._invitation_response(invitation),
            setup_url=setup_url,
            setup_url_returned_once=True,
        )

    def revoke_invitation(
        self,
        farm_id: UUID,
        *,
        actor: PlatformUser,
        reason: str,
    ) -> PlatformFarmOnboardingStatusResponse:
        farm = self.repository.get_farm(farm_id)
        if farm is None:
            raise ResourceNotFoundError(
                "The requested farm does not exist.",
                error_code="platform_farm_not_found",
            )

        invitation = self.repository.get_pending_for_farm(
            farm_id,
            for_update=True,
        )
        if invitation is None:
            raise BusinessRuleError(
                "The farm does not have a pending invitation to revoke.",
                error_code="pending_farm_invitation_not_found",
            )

        current_time = datetime.now(UTC)
        invitation.status = FarmInvitationStatus.REVOKED.value
        invitation.revoked_at = current_time

        self.database_session.add(
            self._audit(
                action="FARM_INVITATION_REVOKED",
                description="Revoked a farm administrator setup invitation.",
                farm_id=farm.id,
                invitation_id=invitation.id,
                actor=actor,
                severity="WARNING",
                metadata={
                    "reason": reason,
                    "administrator_user_id": (
                        str(invitation.administrator_user_id)
                    ),
                },
            )
        )

        try:
            self.database_session.commit()
        except Exception:
            self.database_session.rollback()
            raise

        return self.platform_status(farm_id)

    def _load_public_invitation(
        self,
        token: str,
        *,
        for_update: bool = False,
    ) -> tuple[PlatformFarmInvitation, Farm, User]:
        invitation = self.repository.get_by_token_hash(
            self.token_hash(token),
            for_update=for_update,
        )
        if invitation is None:
            raise ResourceNotFoundError(
                "The invitation is invalid or no longer available.",
                error_code="farm_invitation_invalid",
            )

        farm = self.repository.get_farm(invitation.farm_id)
        administrator = self.repository.get_user(
            invitation.administrator_user_id
        )
        if farm is None or administrator is None:
            raise ResourceNotFoundError(
                "The invitation is invalid or no longer available.",
                error_code="farm_invitation_invalid",
            )

        current_time = datetime.now(UTC)
        if (
            invitation.status == FarmInvitationStatus.PENDING.value
            and invitation.expires_at <= current_time
        ):
            invitation.status = FarmInvitationStatus.EXPIRED.value
            self.database_session.add(
                self._audit(
                    action="FARM_INVITATION_EXPIRED",
                    description="A farm administrator invitation expired.",
                    farm_id=farm.id,
                    invitation_id=invitation.id,
                    actor_username=administrator.username,
                    severity="WARNING",
                    public_path=(
                        "/api/v1/onboarding/invitations/[redacted]"
                    ),
                )
            )
            self.database_session.commit()
            raise BusinessRuleError(
                "The invitation has expired.",
                error_code="farm_invitation_expired",
            )

        status_error = {
            FarmInvitationStatus.ACCEPTED.value: (
                "The invitation has already been accepted.",
                "farm_invitation_already_accepted",
            ),
            FarmInvitationStatus.REVOKED.value: (
                "The invitation has been revoked.",
                "farm_invitation_revoked",
            ),
            FarmInvitationStatus.EXPIRED.value: (
                "The invitation has expired.",
                "farm_invitation_expired",
            ),
        }.get(invitation.status)
        if status_error is not None:
            message, error_code = status_error
            raise BusinessRuleError(
                message,
                error_code=error_code,
            )

        if (
            not farm.is_active
            or farm.lifecycle_status
            != FarmLifecycleStatus.ACTIVE.value
        ):
            raise BusinessRuleError(
                "The farm is not active, so this invitation cannot be used.",
                error_code="inactive_farm_invitation",
            )

        return invitation, farm, administrator

    def validate_invitation(
        self,
        token: str,
    ) -> FarmInvitationPublicResponse:
        invitation, farm, administrator = (
            self._load_public_invitation(token)
        )
        return FarmInvitationPublicResponse(
            farm_name=farm.name,
            farm_code=farm.farm_code,
            administrator_name=administrator.full_name,
            administrator_username=administrator.username,
            status=FarmInvitationStatus(invitation.status),
            expires_at=invitation.expires_at,
        )

    def accept_invitation(
        self,
        *,
        token: str,
        new_password: str,
    ) -> FarmInvitationAcceptResponse:
        invitation, farm, administrator = (
            self._load_public_invitation(
                token,
                for_update=True,
            )
        )
        current_time = datetime.now(UTC)

        administrator.password_hash = hash_password(new_password)
        administrator.is_active = True
        administrator.is_verified = True
        administrator.must_change_password = False
        administrator.failed_login_attempts = 0
        administrator.locked_until = None

        invitation.status = FarmInvitationStatus.ACCEPTED.value
        invitation.accepted_at = current_time

        revoked_sessions = self.repository.revoke_user_refresh_tokens(
            administrator.id,
            revoked_at=current_time,
        )

        self.database_session.add(
            self._audit(
                action="FARM_INVITATION_ACCEPTED",
                description="Accepted a farm administrator setup invitation.",
                farm_id=farm.id,
                invitation_id=invitation.id,
                actor_username=administrator.username,
                metadata={
                    "administrator_user_id": str(administrator.id),
                    "revoked_refresh_sessions": revoked_sessions,
                },
                public_path=(
                    "/api/v1/onboarding/invitations/accept"
                ),
            )
        )

        try:
            self.database_session.commit()
        except Exception:
            self.database_session.rollback()
            raise

        return FarmInvitationAcceptResponse(
            farm_code=farm.farm_code,
            administrator_username=administrator.username,
            accepted_at=current_time,
            message=(
                "The administrator account is active. "
                "Sign in with the password you just created."
            ),
        )
