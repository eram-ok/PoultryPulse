# Stage 17B — Authentication and Administration Auditing

Stage 17B records mutation and authentication activity for:

- successful and failed login attempts;
- refresh-token rotation;
- logout;
- password changes;
- user creation and updates;
- account activation and deactivation;
- role assignment and removal;
- farm registration and profile changes;
- farm-settings changes.

## Security guarantees

Passwords, password hashes, access tokens and refresh tokens are never
written to the audit trail.

Authentication failures capture only safe identifier metadata, the error
code, request ID, IP address and user agent.

## Transaction behavior

Business operations continue to use their existing transaction boundaries.
Audit writes happen immediately afterward using a best-effort recorder.
An audit storage failure is logged and rolled back without undoing a business
operation that has already committed.

## No migration

Stage 17B uses the `audit_logs` table introduced in Stage 17A and does not
change the database schema.
