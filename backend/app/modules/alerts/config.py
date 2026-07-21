from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


def load_local_environment(
    path: Path = Path(".env"),
) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            continue

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]

        os.environ.setdefault(key, value)


load_local_environment()


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class NotificationSettings:
    email_enabled: bool
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    smtp_from_name: str
    smtp_use_tls: bool
    smtp_use_ssl: bool
    smtp_timeout_seconds: int

    sms_enabled: bool
    sms_provider: str

    africastalking_username: str
    africastalking_api_key: str
    africastalking_sender_id: str
    africastalking_api_url: str

    twilio_account_sid: str
    twilio_auth_token: str
    twilio_from_number: str
    twilio_messaging_service_sid: str

    generic_sms_url: str
    generic_sms_api_key: str
    generic_sms_auth_header: str
    generic_sms_auth_prefix: str
    generic_sms_to_field: str
    generic_sms_message_field: str
    generic_sms_sender_field: str
    generic_sms_sender_id: str

    max_delivery_attempts: int
    retry_delay_minutes: int

    @classmethod
    def from_environment(cls) -> "NotificationSettings":
        load_local_environment()

        return cls(
            email_enabled=env_bool(
                "ALERT_EMAIL_ENABLED",
                False,
            ),
            smtp_host=os.getenv("SMTP_HOST", ""),
            smtp_port=env_int("SMTP_PORT", 587),
            smtp_username=os.getenv(
                "SMTP_USERNAME",
                "",
            ),
            smtp_password=os.getenv(
                "SMTP_PASSWORD",
                "",
            ),
            smtp_from_email=os.getenv(
                "SMTP_FROM_EMAIL",
                "",
            ),
            smtp_from_name=os.getenv(
                "SMTP_FROM_NAME",
                "PoultryPulse",
            ),
            smtp_use_tls=env_bool(
                "SMTP_USE_TLS",
                True,
            ),
            smtp_use_ssl=env_bool(
                "SMTP_USE_SSL",
                False,
            ),
            smtp_timeout_seconds=env_int(
                "SMTP_TIMEOUT_SECONDS",
                20,
            ),
            sms_enabled=env_bool(
                "ALERT_SMS_ENABLED",
                False,
            ),
            sms_provider=os.getenv(
                "SMS_PROVIDER",
                "generic",
            )
            .strip()
            .lower(),
            africastalking_username=os.getenv(
                "AFRICASTALKING_USERNAME",
                "",
            ),
            africastalking_api_key=os.getenv(
                "AFRICASTALKING_API_KEY",
                "",
            ),
            africastalking_sender_id=os.getenv(
                "AFRICASTALKING_SENDER_ID",
                "",
            ),
            africastalking_api_url=os.getenv(
                "AFRICASTALKING_API_URL",
                ("https://api.africastalking.com/version1/messaging"),
            ),
            twilio_account_sid=os.getenv(
                "TWILIO_ACCOUNT_SID",
                "",
            ),
            twilio_auth_token=os.getenv(
                "TWILIO_AUTH_TOKEN",
                "",
            ),
            twilio_from_number=os.getenv(
                "TWILIO_FROM_NUMBER",
                "",
            ),
            twilio_messaging_service_sid=os.getenv(
                "TWILIO_MESSAGING_SERVICE_SID",
                "",
            ),
            generic_sms_url=os.getenv(
                "GENERIC_SMS_URL",
                "",
            ),
            generic_sms_api_key=os.getenv(
                "GENERIC_SMS_API_KEY",
                "",
            ),
            generic_sms_auth_header=os.getenv(
                "GENERIC_SMS_AUTH_HEADER",
                "Authorization",
            ),
            generic_sms_auth_prefix=os.getenv(
                "GENERIC_SMS_AUTH_PREFIX",
                "Bearer ",
            ),
            generic_sms_to_field=os.getenv(
                "GENERIC_SMS_TO_FIELD",
                "to",
            ),
            generic_sms_message_field=os.getenv(
                "GENERIC_SMS_MESSAGE_FIELD",
                "message",
            ),
            generic_sms_sender_field=os.getenv(
                "GENERIC_SMS_SENDER_FIELD",
                "sender",
            ),
            generic_sms_sender_id=os.getenv(
                "GENERIC_SMS_SENDER_ID",
                "PoultryPulse",
            ),
            max_delivery_attempts=max(
                1,
                env_int(
                    "ALERT_MAX_DELIVERY_ATTEMPTS",
                    3,
                ),
            ),
            retry_delay_minutes=max(
                1,
                env_int(
                    "ALERT_RETRY_DELAY_MINUTES",
                    15,
                ),
            ),
        )

    @property
    def email_ready(self) -> bool:
        return bool(self.email_enabled and self.smtp_host and self.smtp_from_email)

    @property
    def sms_ready(self) -> bool:
        if not self.sms_enabled:
            return False

        if self.sms_provider == "africastalking":
            return bool(
                self.africastalking_username
                and self.africastalking_api_key
                and self.africastalking_api_url
            )

        if self.sms_provider == "twilio":
            return bool(
                self.twilio_account_sid
                and self.twilio_auth_token
                and (self.twilio_from_number or self.twilio_messaging_service_sid)
            )

        return bool(self.generic_sms_url)
