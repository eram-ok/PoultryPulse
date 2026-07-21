# Stage 17C2 — Sales, Finance, Alerts and Notification Auditing

Stage 17C2 extends the system audit trail to commercial and administrative
operations without rewriting the existing routers or business services.

## Audited areas

- customer creation and updates;
- sale creation, updates, confirmation and cancellation;
- customer payments and payment reversals;
- sale returns and return reversals;
- expense categories, expenses and expense voiding;
- supplier bills, supplier payments and payment reversals;
- cash-ledger adjustments and sales-receipt synchronization;
- alert refresh and notification-delivery processing;
- alert read, dismissal, assignment, acknowledgement, resolution and reopening;
- notification preferences and test notifications.

## Implementation

The commercial registry installs idempotent wrappers around 31 service-layer
mutation methods. The wrappers preserve each service's existing commit,
rollback and validation behavior.

The wrapper supports both service session conventions used in PoultryPulse:
`database_session` and the finance module's `db` alias.

## Audit contents

Audit events contain the farm, actor, request ID, request path, IP address,
user agent, action, result, resource identifier and safe operation metadata.
Update, cancellation, voiding, reversal and status-change operations include
before-and-after snapshots where the service exposes the affected model.

Notification destinations are intentionally excluded from audit metadata.
Passwords and authentication tokens continue to be protected by the Stage 17A
sanitizer.

## Database

Stage 17C2 uses the existing `audit_logs` table. No Alembic migration is
required.
