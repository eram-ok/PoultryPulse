# Stage 21A — Alerts, Flocks, and Houses

Stage 21A replaces the first three operational placeholder pages with
authenticated, permission-aware workflows backed by the existing FastAPI
contracts.

## Alerts

The alert workspace provides:

- active, unread, critical, acknowledged, and assigned-to-me counters
- search, severity, status, unread, assignment, and dismissed filters
- responsive desktop table and mobile cards
- alert detail sheet with event history
- mark read and unread
- dismiss and restore
- assign to the current user
- acknowledge, resolve, and reopen with operational notes
- manual alert refresh for users with `alerts.refresh`

## Flocks

The flock workspace provides:

- paginated flock listing
- search, status, and production-stage filters
- current population, active, laying, and planned summaries
- responsive table and mobile cards
- flock creation
- flock editing
- population summary and house-occupancy progress
- population transaction history
- controlled manual population movements
- permission-aware create, update, and adjustment actions

Mortality and culling should be recorded through the Bird Losses workflow
rather than through manual population adjustments.

## Houses

The house workspace provides:

- paginated house listing
- search and status filters
- house, active, capacity, and maintenance summaries
- responsive table and mobile cards
- house creation and editing
- activate and deactivate actions
- permission-aware action visibility

## Architecture

Stage 21A uses the Stage 20 same-origin authenticated proxy:

```text
Browser
  -> /api/backend/*
  -> Next.js authenticated route handler
  -> FastAPI /api/v1/*
  -> PostgreSQL
```

Authentication tokens remain in HttpOnly cookies and are not stored in browser
local storage or session storage.

## Backend impact

Stage 21A does not modify:

- FastAPI source
- SQLAlchemy models
- Alembic migrations
- PostgreSQL tables or data
- npm dependencies
- environment variables

## Validation

The implementation was checked with:

```text
npm run lint
npm run typecheck
```

The Next.js production bundle compiled successfully and generated the
`/alerts`, `/flocks`, and `/houses` routes. The validation environment used
one build worker after TypeScript had already passed separately.
