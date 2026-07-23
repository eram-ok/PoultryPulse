# Stage 24B3B2 — Farm Management Controls

Stage 24B3B2 turns the read-only platform farm registry into a complete customer-farm administration workspace.

## Added route

- `/platform/farms/new`

## Capabilities

- Atomic customer-farm registration with default settings.
- First farm-administrator creation and one-time invitation issuance.
- Idempotency protection for registration retries.
- Memory-only display of one-time setup URLs.
- Platform-safe farm profile editing.
- Farm activation, suspension, and deactivation.
- Required reasons for restrictive lifecycle actions.
- Invitation reissue and pending-invitation revocation.
- Invitation delivery, expiry, and error visibility.

## Security boundary

All writes pass through the platform-only BFF route, which uses separate HttpOnly platform cookies, validates same-origin state-changing requests, and forwards only `/platform/*` API paths. No client-supplied farm identity is used for tenant authorization.

## Validation

```powershell
npm run lint
npm run typecheck
npm run build
```

```powershell
python -m pytest tests/test_platform_farms.py tests/test_platform_onboarding.py tests/test_platform_auth.py -q
python -m pytest -q
alembic check
```
