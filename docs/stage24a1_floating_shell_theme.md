# Stage 24A1 — Floating Application Shell and Rich Theme

Stage 24A1 establishes the new PoultryPulse visual foundation without
changing any backend contract or business workflow.

## Changes

- Replaces the edge-to-edge desktop sidebar with a floating rounded panel.
- Adds desktop sidebar minimization and expansion.
- Keeps the PoultryPulse mark visible while minimized.
- Makes the sidebar logo return to `/dashboard`.
- Adds a visible dashboard logo to the mobile topbar.
- Redesigns mobile navigation as a floating rounded sheet.
- Converts the topbar into a floating glass-style panel.
- Adds richer light-mode green, blue, and amber surfaces.
- Refines dark-mode contrast while preserving the existing theme toggle.
- Adds layered application background color and subtle decorative glows.
- Improves global card rounding, depth, borders, and shadow consistency.
- Preserves permission-aware navigation and all existing routes.
- Preserves the alert counter, search menu, theme control, profile menu,
  farm settings, change password, and logout workflows.

## Deliberate scope

The existing dashboard header already displays a time-aware greeting with
the signed-in user's first name. Stage 24A1 preserves that behavior.

Dashboard KPI composition and individual dashboard cards are refined in
Stage 24A2. Landing-page branding, tenant-specific logos and backgrounds,
multi-tenant farm architecture, email delivery, and Docker setup remain
separate stages.

## Acceptance

Validate:

1. Expanded desktop sidebar.
2. Minimized desktop sidebar.
3. Logo remains visible while minimized.
4. Logo returns to `/dashboard`.
5. All permission-aware navigation links remain correct.
6. Mobile navigation opens and closes correctly.
7. Mobile topbar logo returns to `/dashboard`.
8. Search, alerts, theme, profile, settings, password, and logout work.
9. Light and dark modes have readable contrast.
10. Every existing route remains usable at mobile, tablet, laptop, and
    desktop widths.

No backend source, package dependency, environment value, database schema,
or Alembic migration is changed.
