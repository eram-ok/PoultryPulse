
# Stage 24B1A — Platform Identity Foundation

PoultryPulse now has two deliberately separate identity boundaries.

## Farm identities

Farm users continue to authenticate through `/api/v1/auth/*`. Their access
tokens carry a `principal_type` of `farm_user` and a `farm_id`. Existing
legacy farm sessions without the new principal claim remain valid until they
expire, provided they still contain a valid farm ID.

Farm authentication now verifies that the related farm exists and is active
during:

- password login;
- refresh-token rotation;
- every protected API request.

An inactive farm therefore cannot continue using old access or refresh
tokens.

## Platform identities

Platform users authenticate through `/api/v1/platform/auth/*`. They are stored
outside the farm `users` table and never receive a farm ID.

The foundation includes:

- `platform_users`;
- `platform_refresh_tokens`;
- `platform_audit_logs`;
- independent access-token validation;
- refresh-token rotation and revocation;
- login lockout;
- password changes;
- platform security auditing;
- a secure first-super-administrator bootstrap command.

Farm tokens are rejected by platform dependencies. Platform tokens are
rejected by farm dependencies.

## Bootstrap

After applying the migration, create the first platform super administrator
with `scripts/bootstrap_platform_admin.py`. The password is collected twice
through `getpass`; it is never accepted as a command-line argument or printed.

## Deliberate exclusions

Stage 24B1A does not yet add:

- the platform frontend;
- farm creation from the platform dashboard;
- farm suspension controls;
- platform farm listings;
- support-mode access to a farm.

Those features build on this identity foundation in later Stage 24B parts.
