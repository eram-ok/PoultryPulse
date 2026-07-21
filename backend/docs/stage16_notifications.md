# PoultryPulse Stage 16 notification configuration

Stage 16 supports three delivery channels:

- In-app notification center
- SMTP email
- SMS through Africa's Talking, Twilio, or a generic HTTP gateway

## Email

```env
ALERT_EMAIL_ENABLED=true
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=notifications@example.com
SMTP_PASSWORD=replace-with-secret
SMTP_FROM_EMAIL=notifications@example.com
SMTP_FROM_NAME=PoultryPulse
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_TIMEOUT_SECONDS=20
```

Use either STARTTLS (`SMTP_USE_TLS=true`) or implicit SSL
(`SMTP_USE_SSL=true`), according to the mail provider.

## Africa's Talking SMS

```env
ALERT_SMS_ENABLED=true
SMS_PROVIDER=africastalking
AFRICASTALKING_USERNAME=replace-with-username
AFRICASTALKING_API_KEY=replace-with-api-key
AFRICASTALKING_SENDER_ID=
AFRICASTALKING_API_URL=https://api.africastalking.com/version1/messaging
```

For the Africa's Talking sandbox, set the URL to:

```env
AFRICASTALKING_API_URL=https://api.sandbox.africastalking.com/version1/messaging
```

## Twilio SMS

```env
ALERT_SMS_ENABLED=true
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=replace-with-account-sid
TWILIO_AUTH_TOKEN=replace-with-auth-token
TWILIO_FROM_NUMBER=+10000000000
TWILIO_MESSAGING_SERVICE_SID=
```

Use either `TWILIO_FROM_NUMBER` or
`TWILIO_MESSAGING_SERVICE_SID`.

## Generic HTTP SMS gateway

```env
ALERT_SMS_ENABLED=true
SMS_PROVIDER=generic
GENERIC_SMS_URL=https://sms-provider.example/api/messages
GENERIC_SMS_API_KEY=replace-with-api-key
GENERIC_SMS_AUTH_HEADER=Authorization
GENERIC_SMS_AUTH_PREFIX=Bearer 
GENERIC_SMS_TO_FIELD=to
GENERIC_SMS_MESSAGE_FIELD=message
GENERIC_SMS_SENDER_FIELD=sender
GENERIC_SMS_SENDER_ID=PoultryPulse
```

The generic adapter sends a JSON POST request.

## Retry settings

```env
ALERT_MAX_DELIVERY_ATTEMPTS=3
ALERT_RETRY_DELAY_MINUTES=15
```

## Manual alert refresh

```powershell
python -m scripts.refresh_operational_alerts `
  --farm-code PP-FARM-001
```

Queue without immediately sending email or SMS:

```powershell
python -m scripts.refresh_operational_alerts `
  --farm-code PP-FARM-001 `
  --queue-only
```

## Windows Task Scheduler

Create a scheduled task that runs from the backend directory:

```powershell
.\.venv\Scripts\python.exe `
  -m scripts.refresh_operational_alerts `
  --farm-code PP-FARM-001
```

A practical starting cadence is every 15 minutes. The refresh is
idempotent: active conditions update existing alert records rather than
creating duplicate alerts.
