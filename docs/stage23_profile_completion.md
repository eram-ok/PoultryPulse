# Stage 23 Profile Completion

The top account menu linked to `/profile`, but the frontend did not contain
a corresponding route. After the generic catch-all placeholder was removed,
selecting Profile correctly exposed the missing implementation as a normal
not-found page.

This repair adds a real authenticated personal profile workspace.

## Route

- `/profile`

## Capabilities

- Display the signed-in user's full name and initials.
- Display username, email, telephone, account ID, creation date, and last login.
- Display active, verified, and password-change status.
- Display assigned roles and role status.
- Display effective permission modules and permission codes.
- Display the current farm context.
- Link to Change Password.
- Link to Farm Settings when `farms.view` is available.
- Link to User Administration when `users.view` is available.
- Edit the current user's name and contact information when `users.update`
  is available.

## Backend contract used for editing

- `PATCH /api/v1/users/{user_id}`

The backend currently requires `users.update` for profile edits and does not
provide a separate self-service profile-update endpoint. Accounts without
that permission receive a complete read-only profile and can still change
their own password through the authentication workflow.

No backend source, package dependency, environment value, migration, or
database schema is changed.
