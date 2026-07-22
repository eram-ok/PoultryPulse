# Stage 23C — Audit Trail, Background Jobs, and Administrative Acceptance

Stage 23C completes the remaining PoultryPulse frontend administration
workflows and removes the generic module placeholder.

## Routes

- `/audit`
- `/jobs`

## Audit trail

- Audit summary metrics.
- Pagination up to 50 events per page.
- Date-range filtering.
- Action, outcome, severity, and module filtering.
- Free-text search.
- Audit-event details.
- Request context and actor information.
- Error details.
- Sanitized before, after, change, and metadata payloads.
- Authenticated filtered CSV export.

## Background jobs

- Job-definition listing.
- Enabled and disabled state.
- Per-farm versus global scope.
- Configured interval display.
- Paginated run history.
- Job-name and status filtering.
- Run details, results, timing, worker, and errors.
- Manual execution of per-farm jobs.
- Global jobs remain command-line only, matching backend rules.

## Backend contracts

- `GET /api/v1/audit`
- `GET /api/v1/audit/summary`
- `GET /api/v1/audit/export.csv`
- `GET /api/v1/audit/{audit_id}`
- `GET /api/v1/jobs/definitions`
- `GET /api/v1/jobs/runs`
- `GET /api/v1/jobs/runs/{run_id}`
- `POST /api/v1/jobs/{job_name}/run`

## Permissions

- `audit.view`
- `audit.export`
- `audit.manage`

## Placeholder removal

The generic `/(app)/[...module]` placeholder route is removed after the
real users, settings, audit, and jobs pages are present. Unknown application
paths now resolve through the normal Next.js not-found behavior.

## Stage 23 acceptance

Validate:

1. User creation, editing, activation, deactivation, and role assignment.
2. Role-definition inspection.
3. Farm-profile updates.
4. Operational setting updates and validation bounds.
5. Audit filtering, details, and CSV export.
6. Job definitions and run-history filtering.
7. Manual `alert_refresh` and `notification_delivery` execution where enabled.
8. Global `job_history_cleanup` remains unavailable from the browser.
9. Permission-aware navigation and action visibility.
10. Direct unauthorized API calls remain protected by FastAPI.
11. Mobile, tablet, laptop, and desktop layouts.
12. `/unknown-module` shows the standard not-found page rather than a
    misleading feature placeholder.

No backend source, package dependency, environment value, database schema,
or Alembic migration is changed by Stage 23C.
