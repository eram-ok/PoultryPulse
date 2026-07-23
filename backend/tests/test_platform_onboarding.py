import hashlib
import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.modules.alerts.config import NotificationSettings
from app.modules.alerts.transports import DeliveryResult, EmailTransport
from app.modules.onboarding.constants import (
    FarmInvitationDeliveryStatus,
    FarmInvitationStatus,
)
from app.modules.onboarding.models import PlatformFarmInvitation
from app.modules.platform.models import PlatformAuditLog, PlatformUser
from app.modules.users.models import User


PLATFORM_PASSWORD = "SecurePlatformPassword123!"
ACCEPTED_PASSWORD = "AcceptedFarmPassword123!"


def create_platform_context(
    database_session: Session,
) -> tuple[dict[str, str], PlatformUser]:
    unique_value = uuid4().hex[:10]
    user = PlatformUser(
        username=f"onboarding-{unique_value}",
        email=f"onboarding-{unique_value}@example.com",
        password_hash=hash_password(PLATFORM_PASSWORD),
        first_name="Platform",
        last_name="Onboarding",
        is_active=True,
        is_super_admin=True,
        must_change_password=False,
    )
    database_session.add(user)
    database_session.commit()

    token = create_access_token(
        str(user.id),
        additional_claims={
            "principal_type": "platform_user",
            "username": user.username,
            "is_super_admin": True,
        },
    )
    return {"Authorization": f"Bearer {token}"}, user


def onboarding_payload(
    *,
    farm_code: str | None = None,
) -> dict[str, object]:
    unique_value = uuid4().hex[:10]
    return {
        "farm_code": (
            farm_code
            or f"ONB-{unique_value.upper()}"
        ),
        "name": "Secure Onboarding Farm",
        "owner_name": "Onboarding Owner",
        "telephone": "+256700123456",
        "email": f"farm-{unique_value}@example.com",
        "district": "Mukono",
        "address": "Mukono, Uganda",
        "timezone": "Africa/Kampala",
        "currency_code": "UGX",
        "settings": {
            "eggs_per_tray": 30,
            "low_production_threshold": 70,
            "mortality_alert_threshold": 1,
            "vaccination_reminder_days": 3,
            "session_timeout_minutes": 60,
            "allow_negative_stock": False,
            "allow_customer_credit": True,
            "maximum_discount_percentage": 5,
        },
        "first_administrator": {
            "username": f"admin-{unique_value}",
            "email": f"admin-{unique_value}@example.com",
            "telephone": "+256701123456",
            "first_name": "First",
            "last_name": "Administrator",
        },
    }


def setup_token(response_body: dict[str, object]) -> str:
    setup_url = response_body["setup_url"]
    assert isinstance(setup_url, str)
    parsed = urlparse(setup_url)
    assert "token=" not in parsed.query
    fragment = parse_qs(parsed.fragment)
    return fragment["token"][0]


def create_onboarding(
    client: TestClient,
    database_session: Session,
    monkeypatch,
    *,
    payload: dict[str, object] | None = None,
    idempotency_key: str | None = None,
) -> tuple[dict[str, object], dict[str, str], PlatformUser]:
    monkeypatch.setenv("ALERT_EMAIL_ENABLED", "false")
    headers, actor = create_platform_context(database_session)
    if idempotency_key is not None:
        headers = {
            **headers,
            "Idempotency-Key": idempotency_key,
        }
    response = client.post(
        "/api/v1/platform/farms",
        headers=headers,
        json=(payload or onboarding_payload()),
    )
    assert response.status_code == 201, response.text
    return response.json(), headers, actor


def test_onboarding_stores_only_hashed_token_and_accepts_once(
    client: TestClient,
    auth_context: dict[str, object],
    database_session: Session,
    monkeypatch,
) -> None:
    _ = auth_context
    body, _, _ = create_onboarding(
        client,
        database_session,
        monkeypatch,
    )
    token = setup_token(body)
    farm_id = UUID(body["farm"]["id"])
    invitation_id = UUID(body["invitation"]["id"])

    assert "temporary_password" not in body
    assert body["setup_url_returned_once"] is True
    assert body["idempotent_replay"] is False
    assert body["administrator"]["is_active"] is False
    assert body["administrator"]["is_verified"] is False
    assert body["invitation"]["status"] == "PENDING"

    invitation = database_session.get(
        PlatformFarmInvitation,
        invitation_id,
    )
    assert invitation is not None
    assert invitation.token_hash != token
    assert invitation.token_hash == hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    validation = client.post(
        "/api/v1/onboarding/invitations/validate",
        json={"token": token},
    )
    assert validation.status_code == 200
    assert validation.headers["cache-control"] == (
        "no-store, max-age=0"
    )
    assert validation.json()["farm_code"] == (
        body["farm"]["farm_code"]
    )

    accepted = client.post(
        "/api/v1/onboarding/invitations/accept",
        json={
            "token": token,
            "new_password": ACCEPTED_PASSWORD,
        },
    )
    assert accepted.status_code == 200, accepted.text

    administrator = database_session.get(
        User,
        UUID(body["administrator"]["id"]),
    )
    assert administrator is not None
    assert administrator.is_active is True
    assert administrator.is_verified is True
    assert administrator.must_change_password is False
    assert verify_password(
        ACCEPTED_PASSWORD,
        administrator.password_hash,
    )

    repeated = client.post(
        "/api/v1/onboarding/invitations/accept",
        json={
            "token": token,
            "new_password": ACCEPTED_PASSWORD,
        },
    )
    assert repeated.status_code == 422
    assert repeated.json()["error"]["code"] == (
        "farm_invitation_already_accepted"
    )

    login = client.post(
        "/api/v1/auth/login",
        data={
            "username": (
                f"{body['farm']['farm_code']}:"
                f"{body['administrator']['username']}"
            ),
            "password": ACCEPTED_PASSWORD,
        },
    )
    assert login.status_code == 200, login.text

    audits = list(
        database_session.scalars(
            select(PlatformAuditLog).where(
                PlatformAuditLog.target_farm_id == farm_id
            )
        ).all()
    )
    serialized_audits = json.dumps(
        [
            {
                "action": audit.action,
                "metadata": audit.metadata_json,
                "path": audit.request_path,
            }
            for audit in audits
        ]
    )
    assert token not in serialized_audits
    assert body["setup_url"] not in serialized_audits


def test_onboarding_idempotency_replays_without_secret(
    client: TestClient,
    auth_context: dict[str, object],
    database_session: Session,
    monkeypatch,
) -> None:
    _ = auth_context
    monkeypatch.setenv("ALERT_EMAIL_ENABLED", "false")
    headers, _ = create_platform_context(database_session)
    payload = onboarding_payload()
    headers["Idempotency-Key"] = (
        f"onboarding-{uuid4().hex}"
    )

    first = client.post(
        "/api/v1/platform/farms",
        headers=headers,
        json=payload,
    )
    second = client.post(
        "/api/v1/platform/farms",
        headers=headers,
        json=payload,
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["farm"]["id"] == first.json()["farm"]["id"]
    assert second.json()["setup_url"] is None
    assert second.json()["setup_url_returned_once"] is False
    assert second.json()["idempotent_replay"] is True

    count = database_session.scalar(
        select(func.count()).select_from(
            PlatformFarmInvitation
        ).where(
            PlatformFarmInvitation.farm_id
            == UUID(first.json()["farm"]["id"])
        )
    )
    assert count == 1

    changed_payload = dict(payload)
    changed_payload["name"] = "Different Farm Name"
    conflict = client.post(
        "/api/v1/platform/farms",
        headers=headers,
        json=changed_payload,
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == (
        "onboarding_idempotency_conflict"
    )


def test_reissue_invalidates_old_token_and_revoke_blocks_new_token(
    client: TestClient,
    auth_context: dict[str, object],
    database_session: Session,
    monkeypatch,
) -> None:
    _ = auth_context
    body, headers, _ = create_onboarding(
        client,
        database_session,
        monkeypatch,
    )
    farm_id = body["farm"]["id"]
    old_token = setup_token(body)

    reissued = client.post(
        f"/api/v1/platform/farms/{farm_id}/onboarding/resend",
        headers=headers,
    )
    assert reissued.status_code == 200, reissued.text
    new_token = setup_token(reissued.json())
    assert new_token != old_token

    old_validation = client.post(
        "/api/v1/onboarding/invitations/validate",
        json={"token": old_token},
    )
    assert old_validation.status_code == 422
    assert old_validation.json()["error"]["code"] == (
        "farm_invitation_revoked"
    )

    new_validation = client.post(
        "/api/v1/onboarding/invitations/validate",
        json={"token": new_token},
    )
    assert new_validation.status_code == 200

    revoked = client.post(
        f"/api/v1/platform/farms/{farm_id}/onboarding/revoke",
        headers=headers,
        json={"reason": "Customer requested a new contact."},
    )
    assert revoked.status_code == 200
    assert revoked.json()["invitation"]["status"] == "REVOKED"

    revoked_validation = client.post(
        "/api/v1/onboarding/invitations/validate",
        json={"token": new_token},
    )
    assert revoked_validation.status_code == 422
    assert revoked_validation.json()["error"]["code"] == (
        "farm_invitation_revoked"
    )


def test_expired_and_inactive_farm_invitations_are_rejected(
    client: TestClient,
    auth_context: dict[str, object],
    database_session: Session,
    monkeypatch,
) -> None:
    _ = auth_context
    body, headers, _ = create_onboarding(
        client,
        database_session,
        monkeypatch,
    )
    token = setup_token(body)
    invitation = database_session.get(
        PlatformFarmInvitation,
        UUID(body["invitation"]["id"]),
    )
    assert invitation is not None
    invitation.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    database_session.commit()

    expired = client.post(
        "/api/v1/onboarding/invitations/validate",
        json={"token": token},
    )
    assert expired.status_code == 422
    assert expired.json()["error"]["code"] == (
        "farm_invitation_expired"
    )
    assert invitation.status == FarmInvitationStatus.EXPIRED.value

    active_body, active_headers, _ = create_onboarding(
        client,
        database_session,
        monkeypatch,
    )
    active_token = setup_token(active_body)
    farm_id = active_body["farm"]["id"]

    suspended = client.post(
        f"/api/v1/platform/farms/{farm_id}/suspend",
        headers=active_headers,
        json={"reason": "Billing review is currently required."},
    )
    assert suspended.status_code == 200

    inactive = client.post(
        "/api/v1/onboarding/invitations/validate",
        json={"token": active_token},
    )
    assert inactive.status_code == 422
    assert inactive.json()["error"]["code"] == (
        "inactive_farm_invitation"
    )


def test_configured_email_delivery_updates_invitation_state(
    client: TestClient,
    auth_context: dict[str, object],
    database_session: Session,
    monkeypatch,
) -> None:
    _ = auth_context
    monkeypatch.setattr(
        NotificationSettings,
        "from_environment",
        classmethod(
            lambda cls: SimpleNamespace(email_ready=True)
        ),
    )
    monkeypatch.setattr(
        EmailTransport,
        "send",
        lambda self, **kwargs: DeliveryResult(
            success=True,
            provider_message_id="test-message",
        ),
    )

    headers, _ = create_platform_context(database_session)
    response = client.post(
        "/api/v1/platform/farms",
        headers=headers,
        json=onboarding_payload(),
    )
    assert response.status_code == 201, response.text
    invitation = database_session.get(
        PlatformFarmInvitation,
        UUID(response.json()["invitation"]["id"]),
    )
    assert invitation is not None
    assert invitation.delivery_status == (
        FarmInvitationDeliveryStatus.SENT.value
    )
    assert invitation.delivery_attempt_count == 1
    assert invitation.sent_at is not None


def test_farm_token_cannot_manage_platform_onboarding(
    authenticated_client: TestClient,
    auth_context: dict[str, object],
) -> None:
    farm = auth_context["farm"]
    response = authenticated_client.get(
        f"/api/v1/platform/farms/{farm.id}/onboarding"
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == (
        "invalid_platform_principal"
    )
