# Stage 23B — Farm Profile and Operational Settings

Stage 23B replaces the `/settings` placeholder with live farm profile and
operational configuration workflows.

## Route

- `/settings`

## Farm profile

- View the signed-in farm.
- Update farm code and name.
- Update owner and contact information.
- Update district and address.
- Store a farm logo URL.
- Update timezone and three-letter currency code.
- Display farm status as read-only.

## Operational settings

- Eggs per tray.
- Low-production alert threshold.
- Mortality alert threshold.
- Vaccination reminder lead time.
- Session-timeout setting.
- Negative-stock policy.
- Customer-credit policy.
- Maximum invoice discount percentage.

## Backend contracts

- `GET /api/v1/farms/{farm_id}`
- `PATCH /api/v1/farms/{farm_id}`
- `GET /api/v1/farms/{farm_id}/settings`
- `PATCH /api/v1/farms/{farm_id}/settings`

## Permissions

- `farms.view`
- `farms.update`
- `farms.settings.update`

## Deliberate safeguards

The farm-active status is displayed but not editable because the inspected
API has no dedicated farm-reactivation workflow. Deactivating the current
farm could make the application unusable.

The API contains farm creation, but the current authentication model has no
farm-switching workflow and list access returns the signed-in farm context.
The frontend therefore does not expose second-farm creation.

No backend source, dependency, environment value, database schema, or
Alembic migration is changed by Stage 23B.
