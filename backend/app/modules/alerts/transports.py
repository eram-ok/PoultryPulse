from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr
import base64
import json
import smtplib
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.modules.alerts.config import NotificationSettings


@dataclass(frozen=True)
class DeliveryResult:
    success: bool
    provider_message_id: str | None = None
    error: str | None = None


class EmailTransport:
    provider_name = "smtp"

    def __init__(
        self,
        settings: NotificationSettings,
    ) -> None:
        self.settings = settings

    def send(
        self,
        *,
        destination: str,
        subject: str,
        body: str,
    ) -> DeliveryResult:
        if not self.settings.email_ready:
            return DeliveryResult(
                success=False,
                error=("SMTP email delivery is disabled or not fully configured."),
            )

        message = EmailMessage()
        message["From"] = formataddr(
            (
                self.settings.smtp_from_name,
                self.settings.smtp_from_email,
            )
        )
        message["To"] = destination
        message["Subject"] = subject
        message.set_content(body)

        try:
            if self.settings.smtp_use_ssl:
                client = smtplib.SMTP_SSL(
                    self.settings.smtp_host,
                    self.settings.smtp_port,
                    timeout=(self.settings.smtp_timeout_seconds),
                )
            else:
                client = smtplib.SMTP(
                    self.settings.smtp_host,
                    self.settings.smtp_port,
                    timeout=(self.settings.smtp_timeout_seconds),
                )

            with client:
                if self.settings.smtp_use_tls and not self.settings.smtp_use_ssl:
                    client.starttls()

                if self.settings.smtp_username:
                    client.login(
                        self.settings.smtp_username,
                        self.settings.smtp_password,
                    )

                response = client.send_message(message)

            if response:
                return DeliveryResult(
                    success=False,
                    error=(f"SMTP server rejected one or more recipients: {response}"),
                )

            return DeliveryResult(
                success=True,
                provider_message_id=(message.get("Message-ID")),
            )
        except (
            OSError,
            smtplib.SMTPException,
        ) as exc:
            return DeliveryResult(
                success=False,
                error=str(exc),
            )


class SmsTransport:
    def __init__(
        self,
        settings: NotificationSettings,
    ) -> None:
        self.settings = settings

    @property
    def provider_name(self) -> str:
        return self.settings.sms_provider

    def send(
        self,
        *,
        destination: str,
        body: str,
    ) -> DeliveryResult:
        if not self.settings.sms_ready:
            return DeliveryResult(
                success=False,
                error=("SMS delivery is disabled or not fully configured."),
            )

        if self.settings.sms_provider == "africastalking":
            return self._send_africastalking(
                destination=destination,
                body=body,
            )

        if self.settings.sms_provider == "twilio":
            return self._send_twilio(
                destination=destination,
                body=body,
            )

        return self._send_generic(
            destination=destination,
            body=body,
        )

    @staticmethod
    def _response_error(
        exc: HTTPError,
    ) -> str:
        try:
            content = exc.read().decode(
                "utf-8",
                errors="replace",
            )
        except OSError:
            content = ""
        return f"HTTP {exc.code}: {content or exc.reason}"

    def _send_africastalking(
        self,
        *,
        destination: str,
        body: str,
    ) -> DeliveryResult:
        payload = {
            "username": (self.settings.africastalking_username),
            "to": destination,
            "message": body,
        }
        if self.settings.africastalking_sender_id:
            payload["from"] = self.settings.africastalking_sender_id

        request = Request(
            self.settings.africastalking_api_url,
            data=urlencode(payload).encode("utf-8"),
            method="POST",
            headers={
                "Accept": "application/json",
                "Content-Type": ("application/x-www-form-urlencoded"),
                "apiKey": (self.settings.africastalking_api_key),
            },
        )

        try:
            with urlopen(
                request,
                timeout=20,
            ) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            return DeliveryResult(
                success=False,
                error=self._response_error(exc),
            )
        except (URLError, OSError, ValueError) as exc:
            return DeliveryResult(
                success=False,
                error=str(exc),
            )

        recipients = data.get("SMSMessageData", {}).get("Recipients", [])
        recipient = recipients[0] if recipients else {}
        status = str(recipient.get("status", "")).lower()

        success = status in {
            "success",
            "sent",
            "queued",
        }
        return DeliveryResult(
            success=success,
            provider_message_id=recipient.get("messageId"),
            error=(None if success else json.dumps(data)),
        )

    def _send_twilio(
        self,
        *,
        destination: str,
        body: str,
    ) -> DeliveryResult:
        url = (
            "https://api.twilio.com/2010-04-01/"
            f"Accounts/{self.settings.twilio_account_sid}/"
            "Messages.json"
        )
        payload = {
            "To": destination,
            "Body": body,
        }

        if self.settings.twilio_messaging_service_sid:
            payload["MessagingServiceSid"] = self.settings.twilio_messaging_service_sid
        else:
            payload["From"] = self.settings.twilio_from_number

        credentials = (
            f"{self.settings.twilio_account_sid}:{self.settings.twilio_auth_token}"
        )
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode(
            "ascii"
        )

        request = Request(
            url,
            data=urlencode(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": (f"Basic {encoded_credentials}"),
                "Content-Type": ("application/x-www-form-urlencoded"),
                "Accept": "application/json",
            },
        )

        try:
            with urlopen(
                request,
                timeout=20,
            ) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            return DeliveryResult(
                success=False,
                error=self._response_error(exc),
            )
        except (URLError, OSError, ValueError) as exc:
            return DeliveryResult(
                success=False,
                error=str(exc),
            )

        message_id = data.get("sid")
        success = bool(message_id)
        return DeliveryResult(
            success=success,
            provider_message_id=message_id,
            error=(None if success else json.dumps(data)),
        )

    def _send_generic(
        self,
        *,
        destination: str,
        body: str,
    ) -> DeliveryResult:
        payload = {
            self.settings.generic_sms_to_field: (destination),
            self.settings.generic_sms_message_field: (body),
        }

        if self.settings.generic_sms_sender_field:
            payload[self.settings.generic_sms_sender_field] = (
                self.settings.generic_sms_sender_id
            )

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.settings.generic_sms_api_key:
            headers[self.settings.generic_sms_auth_header] = (
                self.settings.generic_sms_auth_prefix
                + self.settings.generic_sms_api_key
            )

        request = Request(
            self.settings.generic_sms_url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers=headers,
        )

        try:
            with urlopen(
                request,
                timeout=20,
            ) as response:
                raw = response.read().decode("utf-8")
                data = json.loads(raw) if raw else {}
        except HTTPError as exc:
            return DeliveryResult(
                success=False,
                error=self._response_error(exc),
            )
        except (URLError, OSError, ValueError) as exc:
            return DeliveryResult(
                success=False,
                error=str(exc),
            )

        message_id = (
            data.get("message_id")
            or data.get("messageId")
            or data.get("id")
            or data.get("sid")
        )
        return DeliveryResult(
            success=True,
            provider_message_id=(str(message_id) if message_id is not None else None),
        )
