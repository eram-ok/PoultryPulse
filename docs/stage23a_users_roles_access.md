# Stage 23A — Users, Roles, and Access Management

Stage 23A replaces the `/users` placeholder with a live, permission-aware
administration workspace.

## Route

- `/users`

## Capabilities

- List paginated farm users.
- Filter the currently loaded page by identity, contact, role, or status.
- Create a user with a secure temporary password.
- Require a password change at first sign-in.
- Edit user names, contact details, verification, and password-change flags.
- Activate inactive accounts.
- Deactivate accounts other than the signed-in administrator.
- Assign and remove existing active roles.
- Inspect role descriptions, modules, and permission codes.
- Display full user account details and last-login information.

## Backend contracts

- `GET /api/v1/users`
- `POST /api/v1/users`
- `GET /api/v1/users/{user_id}`
- `PATCH /api/v1/users/{user_id}`
- `POST /api/v1/users/{user_id}/activate`
- `POST /api/v1/users/{user_id}/deactivate`
- `POST /api/v1/users/{user_id}/roles/{role_id}`
- `DELETE /api/v1/users/{user_id}/roles/{role_id}`
- `GET /api/v1/roles`

## Permissions

- `users.view`
- `users.create`
- `users.update`
- `users.deactivate`
- `roles.view`
- `roles.assign`

## Deliberate limitation

The backend has no route for creating or editing role definitions. The
frontend therefore treats roles as read-only definitions and only supports
their assignment or removal. This avoids presenting controls that cannot
be completed by the API.

No backend source, package dependency, environment value, database schema,
or Alembic migration is changed by Stage 23A.
