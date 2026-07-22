# Stage 22C — Reports, Analytics, Dashboard Activity, and Acceptance

Stage 22C completes the commercial and analytics frontend.

## Route

- `/reports`

## Dashboard correction

The dashboard `Record activity` button previously had no route, event
handler, or menu. Stage 22C connects it to the existing permission-aware
quick actions:

- Record production
- Record sale
- Record health incident
- Other quick actions defined by the authenticated role

## Reports

- Performance summary
- Multi-metric trend chart
- Current-versus-previous period comparison
- Executive highlights and operational alerts
- Cash-flow analysis
- Profitability analysis
- Performance CSV export
- Trends CSV export
- Alerts CSV export

## Existing backend contracts

- `GET /api/v1/reports/performance`
- `GET /api/v1/reports/trends`
- `GET /api/v1/reports/comparison`
- `GET /api/v1/reports/executive-summary`
- `GET /api/v1/reports/exports/performance.csv`
- `GET /api/v1/reports/exports/trends.csv`
- `GET /api/v1/reports/exports/alerts.csv`
- `GET /api/v1/finance/reports/cash-flow`
- `GET /api/v1/finance/reports/profitability`

## Permissions

- `reports.view`
- `finance.reports`
- Activity-menu entries are filtered by each workflow permission.

## Stage 22 acceptance

Validate:

1. Customer creation and statements.
2. Draft, confirmed, paid, returned, cancelled, and reversed sales states.
3. Supplier creation, activation, and statements.
4. Expenses, bills, payments, reversals, and the cash ledger.
5. Performance, trends, comparison, executive, cash-flow, and
   profitability reports.
6. All CSV downloads.
7. Dashboard `Record activity` navigation.
8. Restricted-role button visibility and backend 403 enforcement.
9. Mobile, tablet, laptop, and desktop layouts.
10. Login, refresh-token rotation, logout, and offline error handling.

Stage 22C changes no backend source, migration, dependency, environment
value, or PostgreSQL schema.
