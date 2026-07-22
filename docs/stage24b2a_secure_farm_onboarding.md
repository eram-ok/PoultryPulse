# Stage 24B2A — Secure Farm Invitation Backend

Stage 24B2A replaces manually shared temporary farm-administrator passwords
with persisted, hashed, expiring account-setup invitations.

## Security boundary

- Farm creation remains platform-super-administrator only.
- Tenant users cannot create farms or manage onboarding.
- Invitation secrets are generated with `secrets.token_urlsafe`.
- Only SHA-256 token hashes are stored.
- Setup URLs are returned once and are never placed in audit metadata.
- Public validation and acceptance submit the token in a JSON request body,
  rather than embedding it in an API path that could be logged.
- Invitation validation and acceptance responses use `Cache-Control: no-store`.
- Public invitation endpoints share authentication rate limiting.

## Farm creation

`POST /api/v1/platform/farms`

The operation atomically creates:

1. the farm and settings;
2. five default system roles;
3. an inactive and unverified first administrator;
4. one pending invitation;
5. platform audit events.

The response contains a one-time `setup_url` instead of a temporary password.
An optional `Idempotency-Key` request header prevents duplicate farms. Replaying
an identical request returns the existing farm without returning the setup URL
again. Reusing the key with different data returns
`onboarding_idempotency_conflict`.

## Public activation

- `POST /api/v1/onboarding/invitations/validate`
- `POST /api/v1/onboarding/invitations/accept`

Acceptance validates password strength, activates and verifies the first
administrator, clears the forced-password-change flag, revokes existing refresh
sessions, marks the invitation accepted, and writes a sanitized platform audit
event.

## Platform management

- `GET /api/v1/platform/farms/{farm_id}/onboarding`
- `POST /api/v1/platform/farms/{farm_id}/onboarding/resend`
- `POST /api/v1/platform/farms/{farm_id}/onboarding/revoke`

Reissue always invalidates the old pending token and returns a newly generated
setup URL once. Completed administrators cannot be re-invited through this
workflow.

## Delivery

The existing SMTP `NotificationSettings` and `EmailTransport` are reused
without creating tenant operational alerts. Delivery status is stored directly
on the invitation as `NOT_CONFIGURED`, `PENDING`, `SENT`, or `FAILED`.

Email delivery failure does not roll back a successfully created farm.

## Configuration

```dotenv
FARM_INVITATION_EXPIRY_HOURS=72
FARM_ONBOARDING_SETUP_BASE_URL=http://localhost:3000/setup-account
```

Existing farms and users are not modified by the migration.

## Migration

- Revision: `d13f7b9c4e21`
- Parent: `a84f1d2c9b73`
- New table: `platform_farm_invitations`

Stage 24B2B will add the public Next.js setup-account interface. Stage 24B3
remains responsible for the platform administration dashboard.
