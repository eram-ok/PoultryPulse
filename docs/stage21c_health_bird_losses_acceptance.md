# Stage 21C — Health, Bird Losses, and Operational Acceptance

Stage 21C completes the PoultryPulse operational frontend.

## Health management

The `/health` workspace provides:

- live health summary metrics
- health-product registration and activation state
- vaccination schedule creation, completion, and cancellation
- health-incident creation and resolution
- treatment creation and completion
- egg and meat withdrawal visibility
- permission-aware actions
- responsive operational tables and empty/error/loading states

The `/health/incidents/new` route opens the health workspace directly in the incident-creation flow.

## Bird losses

The `/bird-losses` workspace provides:

- mortality and culling summaries
- date, type, status, and search filtering
- loss creation with cause and disposal information
- automatic flock-population reduction through the backend service
- mortality-threshold visibility
- record details and audited reversal
- automatic population restoration when a record is reversed

## Operational acceptance

Validate every Stage 21 module using an Administrator and a restricted user:

1. Alerts: list, filters, read/dismiss, acknowledge/resolve, refresh.
2. Houses: create, edit, deactivate, reactivate.
3. Flocks: create, edit, population summary, allowed adjustment.
4. Production: draft, edit, submit, reject or confirm.
5. Egg inventory: balances, adjustments, issues, reversal.
6. Feed: item, purchase, usage, adjustment, wastage.
7. Health: product, vaccination, incident, treatment, withdrawal.
8. Bird losses: mortality/culling, threshold, population effect, reversal.
9. Authentication: login, logout, expiry, protected routes.
10. Permissions: hidden actions and backend 403 responses remain consistent.
11. Responsive layout: phone, tablet, laptop, desktop.
12. Offline and backend-unavailable states.

Stage 21C does not change FastAPI source, database schema, Alembic migrations, npm dependencies, or environment values.
