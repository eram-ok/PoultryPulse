from dataclasses import replace

from app.modules.alerts.config import NotificationSettings
from app.modules.alerts.transports import (
    EmailTransport,
    SmsTransport,
)


def disabled_settings() -> NotificationSettings:
    return NotificationSettings.from_environment()


def test_disabled_email_transport_fails_cleanly() -> None:
    settings = replace(
        disabled_settings(),
        email_enabled=False,
    )
    result = EmailTransport(settings).send(
        destination="person@example.com",
        subject="Test",
        body="Hello",
    )

    assert result.success is False
    assert "disabled" in (result.error or "").lower()


def test_disabled_sms_transport_fails_cleanly() -> None:
    settings = replace(
        disabled_settings(),
        sms_enabled=False,
    )
    result = SmsTransport(settings).send(
        destination="+256700000000",
        body="Hello",
    )

    assert result.success is False
    assert "disabled" in (result.error or "").lower()


def test_generic_sms_readiness() -> None:
    settings = replace(
        disabled_settings(),
        sms_enabled=True,
        sms_provider="generic",
        generic_sms_url=("https://example.invalid/sms"),
    )

    assert settings.sms_ready is True
