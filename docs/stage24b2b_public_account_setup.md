# Stage 24B2B — Public Account Setup Interface

Stage 24B2B completes the customer-facing portion of secure farm onboarding.

## Added interface

- `/setup-account?token=<one-time-token>`
- responsive invitation validation and password setup
- clear farm and first-administrator identity confirmation
- password strength and matching validation
- successful handoff to the normal farm-user login page

## Same-origin BFF routes

- `POST /api/onboarding/invitations/validate`
- `POST /api/onboarding/invitations/accept`

The BFF routes:

- enforce same-origin browser requests;
- forward tokens only in JSON request bodies;
- never create authentication cookies;
- never write invitation values to application logs;
- return `Cache-Control: no-store`;
- map backend-unavailable failures to safe client errors.

## Token handling

The public component reads the token from the initial query string or URL fragment,
holds it only in React memory, and immediately removes it from the visible browser URL.
It does not use cookies, local storage, session storage, analytics, or persistent state.
The token is cleared from component state after acceptance or terminal validation failure.

## Scope boundary

This stage does not add:

- platform administrator login;
- platform navigation;
- the platform farm dashboard;
- support access or impersonation;
- new frontend dependencies.

Those capabilities remain in later Stage 24B milestones.

## Validation

Run from `frontend`:

```powershell
npm run lint
npm run typecheck
npm run build
```

Run from `backend`:

```powershell
python -m pytest tests/test_platform_onboarding.py -q
python -m pytest -q
alembic check
```
