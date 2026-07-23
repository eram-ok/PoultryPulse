# Stage 24B3A — Platform Authentication Boundary and Shell

Stage 24B3A introduces the frontend platform-administration boundary.

## Identity separation

Platform sessions use dedicated HttpOnly cookies:

- `poultrypulse_platform_access_token`
- `poultrypulse_platform_refresh_token`

They are separate from farm-user cookies and are accepted only by the
platform BFF routes.

## Routes

Public:

- `/platform/login`

Protected:

- `/platform`
- `/platform/dashboard`
- `/platform/change-password`

BFF:

- `POST /api/platform/auth/login`
- `GET /api/platform/auth/refresh`
- `POST /api/platform/auth/logout`
- `GET /api/platform/auth/session`
- `POST /api/platform/auth/change-password`
- `/api/platform/backend/[...path]`

The authenticated platform proxy permits only backend paths beginning with
`/platform/`.

## Dashboard foundation

The overview uses the existing platform farm-list API to show real totals for:

- all farms;
- active farms;
- suspended farms;
- deactivated farms.

The full farm registry, onboarding controls, and lifecycle workspace are
implemented in Stage 24B3B.

## Validation

Run from `frontend`:

```powershell
npm run lint
npm run typecheck
npm run build
```

Run from `backend`:

```powershell
python -m pytest tests/test_platform_auth.py tests/test_platform_farms.py -q
python -m pytest -q
alembic check
```
