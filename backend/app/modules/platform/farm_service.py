from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BusinessRuleError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.core.security import hash_password
from app.modules.audit.context import get_audit_context
from app.modules.farms.constants import FarmLifecycleStatus
from app.modules.farms.models import Farm, FarmSettings
from app.modules.farms.schemas import FarmSettingsResponse
from app.modules.onboarding.schemas import (
    PlatformFarmInvitationResponse,
)
from app.modules.onboarding.service import (
    FarmOnboardingService,
)
from app.modules.platform.farm_repository import (
    RECENT_LOGIN_WINDOW_DAYS,
    PlatformFarmRecord,
    PlatformFarmRepository,
)
from app.modules.platform.farm_schemas import (
    PlatformActivationRequest,
    PlatformFarmAdministratorResponse,
    PlatformFarmCreateRequest,
    PlatformFarmDetailResponse,
    PlatformFarmListResponse,
    PlatformFarmOnboardingResponse,
    PlatformFarmSummaryResponse,
    PlatformFarmUpdateRequest,
    PlatformLifecycleReasonRequest,
)
from app.modules.platform.models import (
    PlatformAuditLog,
    PlatformUser,
)
from app.modules.users.models import Permission, Role, User


DEFAULT_ROLE_DESCRIPTIONS = {
    "Administrator": (
        "Full tenant administration and operational access."
    ),
    "Owner": (
        "Farm ownership, administration and reporting access."
    ),
    "Manager": (
        "Day-to-day operational poultry farm management."
    ),
    "Attendant": (
        "Daily poultry, production, feed and health data entry."
    ),
    "Sales Officer": (
        "Customer, sales, payment and commercial operations."
    ),
}


class PlatformFarmService:
    """Platform-only customer-farm onboarding and lifecycle operations."""

    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session
        self.repository = PlatformFarmRepository(
            database_session
        )

    @staticmethod
    def _unusable_password() -> str:
        # This random value is hashed but never shared.
        return secrets.token_urlsafe(64)

    @staticmethod
    def _farm_snapshot(
        farm: Farm,
    ) -> dict[str, Any]:
        return {
            "id": str(farm.id),
            "farm_code": farm.farm_code,
            "name": farm.name,
            "owner_name": farm.owner_name,
            "telephone": farm.telephone,
            "email": farm.email,
            "district": farm.district,
            "timezone": farm.timezone,
            "currency_code": farm.currency_code,
            "is_active": farm.is_active,
            "lifecycle_status": farm.lifecycle_status,
            "lifecycle_reason": farm.lifecycle_reason,
        }

    @staticmethod
    def _summary(
        record: PlatformFarmRecord,
    ) -> PlatformFarmSummaryResponse:
        farm = record.farm

        return PlatformFarmSummaryResponse(
            id=farm.id,
            farm_code=farm.farm_code,
            name=farm.name,
            owner_name=farm.owner_name,
            telephone=farm.telephone,
            email=farm.email,
            district=farm.district,
            address=farm.address,
            logo_url=farm.logo_url,
            timezone=farm.timezone,
            currency_code=farm.currency_code,
            is_active=farm.is_active,
            lifecycle_status=FarmLifecycleStatus(
                farm.lifecycle_status
            ),
            lifecycle_reason=farm.lifecycle_reason,
            lifecycle_changed_at=(
                farm.lifecycle_changed_at
            ),
            lifecycle_changed_by_platform_user_id=(
                farm.lifecycle_changed_by_platform_user_id
            ),
            suspended_at=farm.suspended_at,
            deactivated_at=farm.deactivated_at,
            created_at=farm.created_at,
            updated_at=farm.updated_at,
            total_users=record.total_users,
            active_users=record.active_users,
            recent_login_users=record.recent_login_users,
            active_refresh_sessions=(
                record.active_refresh_sessions
            ),
            last_login_at=record.last_login_at,
        )

    @classmethod
    def _detail(
        cls,
        record: PlatformFarmRecord,
    ) -> PlatformFarmDetailResponse:
        summary = cls._summary(record)
        settings = (
            FarmSettingsResponse.model_validate(
                record.farm.settings
            )
            if record.farm.settings is not None
            else None
        )

        return PlatformFarmDetailResponse(
            **summary.model_dump(),
            settings=settings,
        )

    @staticmethod
    def _permission_codes_for_role(
        role_name: str,
        permissions: list[Permission],
    ) -> set[str]:
        allowed_permissions = [
            permission
            for permission in permissions
            if permission.code != "farms.create"
        ]

        if role_name in {"Administrator", "Owner"}:
            return {
                permission.code
                for permission in allowed_permissions
            }

        if role_name == "Manager":
            excluded_modules = {
                "users",
                "roles",
                "audit",
            }
            excluded_codes = {
                "farms.settings.update",
            }
            return {
                permission.code
                for permission in allowed_permissions
                if (
                    permission.module not in excluded_modules
                    and permission.code not in excluded_codes
                )
            }

        if role_name == "Attendant":
            allowed_modules = {
                "houses",
                "flocks",
                "production",
                "eggs",
                "feed",
                "health",
                "bird_losses",
                "alerts",
                "notifications",
            }
            blocked_fragments = {
                ".reverse",
                ".adjust",
                ".approve",
                ".cancel",
                ".manage",
                ".resolve",
            }
            return {
                permission.code
                for permission in allowed_permissions
                if (
                    permission.module in allowed_modules
                    and not any(
                        fragment in permission.code
                        for fragment in blocked_fragments
                    )
                )
            }

        if role_name == "Sales Officer":
            allowed_modules = {
                "customers",
                "sales",
                "payments",
                "expenses",
                "finance",
                "reports",
            }
            extra_codes = {
                "farms.view",
                "eggs.view",
            }
            return {
                permission.code
                for permission in allowed_permissions
                if (
                    permission.module in allowed_modules
                    or permission.code in extra_codes
                )
            }

        return set()

    @staticmethod
    def _success_audit(
        *,
        actor: PlatformUser,
        farm: Farm,
        action: str,
        description: str,
        severity: str = "INFO",
        metadata: dict[str, Any] | None = None,
    ) -> PlatformAuditLog:
        context = get_audit_context()

        return PlatformAuditLog(
            platform_user_id=actor.id,
            target_farm_id=farm.id,
            actor_username=actor.username,
            action=action,
            outcome="SUCCESS",
            severity=severity,
            description=description,
            resource_type="Farm",
            resource_id=str(farm.id),
            request_id=context.request_id,
            request_method=context.request_method,
            request_path=context.request_path,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
            metadata_json=metadata,
        )

    def list_farms(
        self,
        *,
        offset: int,
        limit: int,
        search: str | None,
        lifecycle_status: FarmLifecycleStatus | None,
    ) -> PlatformFarmListResponse:
        records, total = self.repository.list_farms(
            offset=offset,
            limit=limit,
            search=search,
            lifecycle_status=lifecycle_status,
        )

        return PlatformFarmListResponse(
            items=[
                self._summary(record)
                for record in records
            ],
            total=total,
            offset=offset,
            limit=limit,
            recent_login_window_days=(
                RECENT_LOGIN_WINDOW_DAYS
            ),
        )

    def get_farm(
        self,
        farm_id: UUID,
    ) -> PlatformFarmDetailResponse:
        record = self.repository.get_farm(farm_id)

        if record is None:
            raise ResourceNotFoundError(
                "The requested farm does not exist.",
                error_code="platform_farm_not_found",
            )

        return self._detail(record)

    def create_farm(
        self,
        payload: PlatformFarmCreateRequest,
        *,
        actor: PlatformUser,
        idempotency_key: str | None = None,
    ) -> PlatformFarmOnboardingResponse:
        onboarding = FarmOnboardingService(
            self.database_session
        )
        request_fingerprint = onboarding.request_fingerprint(
            payload.model_dump(mode="json")
        )
        existing_invitation = (
            onboarding.find_idempotent_replay(
                actor=actor,
                idempotency_key=idempotency_key,
                request_fingerprint=request_fingerprint,
            )
        )

        if existing_invitation is not None:
            record = self.repository.get_farm(
                existing_invitation.farm_id
            )
            if record is None:
                raise ResourceNotFoundError(
                    "The idempotent farm onboarding record is incomplete.",
                    error_code="onboarding_replay_farm_not_found",
                )
            administrator = (
                onboarding.administrator_for_invitation(
                    existing_invitation
                )
            )
            return PlatformFarmOnboardingResponse(
                farm=self._detail(record),
                administrator=(
                    PlatformFarmAdministratorResponse.model_validate(
                        administrator
                    )
                ),
                invitation=(
                    PlatformFarmInvitationResponse.model_validate(
                        existing_invitation
                    )
                ),
                setup_url=None,
                setup_url_returned_once=False,
                idempotent_replay=True,
            )

        if (
            self.repository.get_farm_by_code(
                payload.farm_code
            )
            is not None
        ):
            raise ResourceConflictError(
                "A farm with this farm code already exists.",
                error_code="farm_code_already_exists",
            )

        permissions = self.repository.list_permissions()
        if not permissions:
            raise BusinessRuleError(
                "The global permission catalog is empty.",
                error_code="permission_catalog_empty",
            )

        farm_data = payload.model_dump(
            exclude={
                "settings",
                "first_administrator",
            }
        )
        settings_data = payload.settings.model_dump()
        administrator_data = (
            payload.first_administrator.model_dump()
        )
        now = datetime.now(UTC)

        farm = Farm(
            **farm_data,
            is_active=True,
            lifecycle_status=(
                FarmLifecycleStatus.ACTIVE.value
            ),
            lifecycle_reason=(
                "Created by a platform administrator."
            ),
            lifecycle_changed_at=now,
            lifecycle_changed_by_platform_user_id=(
                actor.id
            ),
        )
        farm.settings = FarmSettings(**settings_data)
        self.database_session.add(farm)

        try:
            self.database_session.flush()

            permission_by_code = {
                permission.code: permission
                for permission in permissions
            }
            role_map: dict[str, Role] = {}

            for role_name, description in (
                DEFAULT_ROLE_DESCRIPTIONS.items()
            ):
                requested_codes = (
                    self._permission_codes_for_role(
                        role_name,
                        permissions,
                    )
                )
                role = Role(
                    farm_id=farm.id,
                    name=role_name,
                    description=description,
                    is_system_role=True,
                    is_active=True,
                )
                role.permissions = [
                    permission_by_code[code]
                    for code in sorted(requested_codes)
                ]
                self.database_session.add(role)
                role_map[role_name] = role

            administrator = User(
                farm_id=farm.id,
                username=administrator_data[
                    "username"
                ],
                email=str(
                    administrator_data["email"]
                ).lower(),
                telephone=administrator_data[
                    "telephone"
                ],
                password_hash=hash_password(
                    self._unusable_password()
                ),
                first_name=administrator_data[
                    "first_name"
                ],
                last_name=administrator_data[
                    "last_name"
                ],
                is_active=False,
                is_verified=False,
                must_change_password=True,
            )
            administrator.roles = [
                role_map["Administrator"]
            ]
            self.database_session.add(administrator)
            self.database_session.flush()

            invitation, _, setup_url = (
                onboarding.prepare_invitation(
                    farm=farm,
                    administrator=administrator,
                    actor=actor,
                    idempotency_key=idempotency_key,
                    request_fingerprint=request_fingerprint,
                    issued_at=now,
                )
            )

            self.database_session.add(
                self._success_audit(
                    actor=actor,
                    farm=farm,
                    action="FARM_CREATE",
                    description=(
                        "Created a customer farm and "
                        "its first administrator."
                    ),
                    metadata={
                        "farm_code": farm.farm_code,
                        "initial_administrator_username": (
                            administrator.username
                        ),
                        "default_roles": sorted(
                            role_map
                        ),
                        "administrator_activation_required": (
                            True
                        ),
                        "invitation_id": str(
                            invitation.id
                        ),
                    },
                )
            )
            self.database_session.add(
                self._success_audit(
                    actor=actor,
                    farm=farm,
                    action="FARM_ONBOARDING_CREATED",
                    description=(
                        "Created a secure farm administrator "
                        "onboarding invitation."
                    ),
                    metadata={
                        "invitation_id": str(
                            invitation.id
                        ),
                        "administrator_user_id": str(
                            administrator.id
                        ),
                        "expires_at": (
                            invitation.expires_at.isoformat()
                        ),
                        "idempotency_key_supplied": (
                            idempotency_key is not None
                        ),
                    },
                )
            )
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()
            raise ResourceConflictError(
                "The farm could not be created because "
                "a unique value already exists.",
                error_code="platform_farm_creation_conflict",
            ) from exc
        except Exception:
            self.database_session.rollback()
            raise

        invitation = onboarding.deliver_invitation(
            invitation.id,
            setup_url=setup_url,
            actor=actor,
        )

        record = self.repository.get_farm(farm.id)
        if record is None:
            raise ResourceNotFoundError(
                "The farm was created but could not be retrieved.",
                error_code="created_platform_farm_not_found",
            )

        return PlatformFarmOnboardingResponse(
            farm=self._detail(record),
            administrator=(
                PlatformFarmAdministratorResponse.model_validate(
                    administrator
                )
            ),
            invitation=(
                PlatformFarmInvitationResponse.model_validate(
                    invitation
                )
            ),
            setup_url=setup_url,
            setup_url_returned_once=True,
            idempotent_replay=False,
        )

    def update_farm(
        self,
        farm_id: UUID,
        payload: PlatformFarmUpdateRequest,
        *,
        actor: PlatformUser,
    ) -> PlatformFarmDetailResponse:
        record = self.repository.get_farm(farm_id)
        if record is None:
            raise ResourceNotFoundError(
                "The requested farm does not exist.",
                error_code="platform_farm_not_found",
            )

        changes = payload.model_dump(
            exclude_unset=True
        )
        if not changes:
            raise BusinessRuleError(
                "At least one farm field must be supplied.",
                error_code="no_farm_changes_supplied",
            )

        requested_code = changes.get("farm_code")
        if (
            requested_code is not None
            and requested_code != record.farm.farm_code
        ):
            conflicting = (
                self.repository.get_farm_by_code(
                    requested_code
                )
            )
            if (
                conflicting is not None
                and conflicting.id != farm_id
            ):
                raise ResourceConflictError(
                    "Another farm already uses this farm code.",
                    error_code="farm_code_already_exists",
                )

        before_values = self._farm_snapshot(
            record.farm
        )

        for field_name, field_value in changes.items():
            setattr(
                record.farm,
                field_name,
                field_value,
            )

        self.database_session.add(
            self._success_audit(
                actor=actor,
                farm=record.farm,
                action="FARM_UPDATE",
                description=(
                    "Updated a customer farm profile."
                ),
                metadata={
                    "requested_fields": sorted(changes),
                    "before": before_values,
                    "after": self._farm_snapshot(
                        record.farm
                    ),
                },
            )
        )

        try:
            self.database_session.commit()
        except IntegrityError as exc:
            self.database_session.rollback()
            raise ResourceConflictError(
                "The farm could not be updated because "
                "a unique value already exists.",
                error_code="platform_farm_update_conflict",
            ) from exc
        except Exception:
            self.database_session.rollback()
            raise

        return self.get_farm(farm_id)

    def _transition(
        self,
        farm_id: UUID,
        *,
        target_status: FarmLifecycleStatus,
        reason: str,
        actor: PlatformUser,
    ) -> PlatformFarmDetailResponse:
        record = self.repository.get_farm(farm_id)
        if record is None:
            raise ResourceNotFoundError(
                "The requested farm does not exist.",
                error_code="platform_farm_not_found",
            )

        farm = record.farm
        current_status = FarmLifecycleStatus(
            farm.lifecycle_status
        )

        if current_status == target_status:
            raise BusinessRuleError(
                "The farm is already in the requested lifecycle state.",
                error_code="farm_lifecycle_state_unchanged",
            )

        now = datetime.now(UTC)
        before_values = self._farm_snapshot(farm)
        revoked_sessions = 0

        farm.lifecycle_status = target_status.value
        farm.lifecycle_reason = reason
        farm.lifecycle_changed_at = now
        farm.lifecycle_changed_by_platform_user_id = (
            actor.id
        )
        farm.is_active = (
            target_status == FarmLifecycleStatus.ACTIVE
        )

        if target_status == FarmLifecycleStatus.SUSPENDED:
            farm.suspended_at = now
        elif (
            target_status
            == FarmLifecycleStatus.DEACTIVATED
        ):
            farm.deactivated_at = now

        if target_status != FarmLifecycleStatus.ACTIVE:
            revoked_sessions = (
                self.repository.revoke_farm_refresh_tokens(
                    farm.id,
                    revoked_at=now,
                )
            )

        action = {
            FarmLifecycleStatus.ACTIVE: "FARM_ACTIVATE",
            FarmLifecycleStatus.SUSPENDED: "FARM_SUSPEND",
            FarmLifecycleStatus.DEACTIVATED: (
                "FARM_DEACTIVATE"
            ),
        }[target_status]
        severity = (
            "INFO"
            if target_status == FarmLifecycleStatus.ACTIVE
            else "WARNING"
        )

        self.database_session.add(
            self._success_audit(
                actor=actor,
                farm=farm,
                action=action,
                description=(
                    "Changed a customer farm lifecycle state "
                    f"to {target_status.value}."
                ),
                severity=severity,
                metadata={
                    "reason": reason,
                    "previous_status": (
                        current_status.value
                    ),
                    "new_status": target_status.value,
                    "revoked_refresh_sessions": (
                        revoked_sessions
                    ),
                    "before": before_values,
                    "after": self._farm_snapshot(farm),
                },
            )
        )

        try:
            self.database_session.commit()
        except Exception:
            self.database_session.rollback()
            raise

        return self.get_farm(farm_id)

    def activate_farm(
        self,
        farm_id: UUID,
        payload: PlatformActivationRequest,
        *,
        actor: PlatformUser,
    ) -> PlatformFarmDetailResponse:
        reason = (
            payload.reason
            or "Activated by a platform administrator."
        )
        return self._transition(
            farm_id,
            target_status=FarmLifecycleStatus.ACTIVE,
            reason=reason,
            actor=actor,
        )

    def suspend_farm(
        self,
        farm_id: UUID,
        payload: PlatformLifecycleReasonRequest,
        *,
        actor: PlatformUser,
    ) -> PlatformFarmDetailResponse:
        return self._transition(
            farm_id,
            target_status=(
                FarmLifecycleStatus.SUSPENDED
            ),
            reason=payload.reason,
            actor=actor,
        )

    def deactivate_farm(
        self,
        farm_id: UUID,
        payload: PlatformLifecycleReasonRequest,
        *,
        actor: PlatformUser,
    ) -> PlatformFarmDetailResponse:
        return self._transition(
            farm_id,
            target_status=(
                FarmLifecycleStatus.DEACTIVATED
            ),
            reason=payload.reason,
            actor=actor,
        )
