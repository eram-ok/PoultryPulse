# Stage 24B1B — Farm Lifecycle Control

Stage 24B1B gives the separate PoultryPulse platform identity boundary
exclusive control over customer-farm onboarding and lifecycle state.

## Lifecycle model

Each farm now has one current lifecycle state:

- `ACTIVE`
- `SUSPENDED`
- `DEACTIVATED`

The existing `is_active` field remains in place for compatibility with the
farm authentication boundary. Database constraints keep it synchronized with
the lifecycle state:

- `ACTIVE` means `is_active = true`;
- `SUSPENDED` and `DEACTIVATED` mean `is_active = false`.

Restrictive state changes require a reason. The database records the time and
platform administrator responsible for the latest lifecycle action. Historical
state changes remain available through `platform_audit_logs`.

Suspension and deactivation revoke every unrevoked farm refresh token in the
same database transaction. Existing access tokens stop working immediately
because every protected farm request re-checks the farm's active state.

## Platform-only routes

The platform super-administrator API includes:

```text
GET    /api/v1/platform/farms
POST   /api/v1/platform/farms
GET    /api/v1/platform/farms/{farm_id}
PATCH  /api/v1/platform/farms/{farm_id}
POST   /api/v1/platform/farms/{farm_id}/activate
POST   /api/v1/platform/farms/{farm_id}/suspend
POST   /api/v1/platform/farms/{farm_id}/deactivate
```

Farm lists support search, lifecycle-state filtering and pagination. Results
include safe usage totals such as active users, users who logged in recently,
active refresh sessions and the latest farm-user login time.

## Atomic onboarding

Platform onboarding creates these records in one transaction:

- the farm;
- farm settings;
- Administrator, Owner, Manager, Attendant and Sales Officer roles;
- the first farm administrator;
- the platform audit event.

The first farm administrator receives a generated temporary password through
the one-time onboarding response. Only its password hash is stored. The
temporary password is excluded from application logs and audit metadata, and
the response is marked `Cache-Control: no-store`. The administrator must change
the password after first login.

New tenant roles do not receive the obsolete `farms.create` permission.
Ordinary farm users cannot register additional farms through `/api/v1/farms`
and cannot alter lifecycle fields through the tenant profile-update route.

## Isolation guarantees

This stage does not add farm impersonation or support-mode access. Platform
users still cannot call farm-user APIs, and farm users cannot call platform
farm-management APIs.

Suspension, deactivation and activation never delete or reassign farm data.
Reactivation restores access to the existing farm and its users while
preserving all operational records.
