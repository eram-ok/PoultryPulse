# Stage 24B3B1 — Platform Farm Registry and Read-Only Detail

This stage adds the first half of the platform customer-farm workspace.

## Routes

- `/platform/farms`
- `/platform/farms/[farmId]`

## Registry

The farm registry provides server-backed pagination, free-text search,
lifecycle-status filtering, usage totals, active-session totals, and direct
navigation to a farm detail page.

## Farm detail

The detail page shows platform-safe profile fields, tenant lifecycle state,
usage totals, recent login information, and first-administrator onboarding and
invitation delivery status.

Write controls are intentionally deferred to Stage 24B3B2.

## Invitation URL hardening

New invitation URLs place the secret token in the URL fragment
(`#token=...`) instead of the query string. URL fragments are not included in
ordinary HTTP requests, reducing exposure in web-server and reverse-proxy
access logs. The public account-setup page remains backward compatible with
older query-string links.

## Validation

```powershell
Set-Location .\frontend
npm run lint
npm run typecheck
npm run build

Set-Location ..\backend
python -m pytest tests/test_platform_farms.py tests/test_platform_onboarding.py -q
python -m pytest -q
alembic check
```
