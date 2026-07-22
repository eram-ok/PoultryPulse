# Stage 22A — Customers, Sales, Payments, and Returns

Stage 22A replaces the commercial placeholder with authenticated,
permission-aware customer and egg-sales workflows.

## Routes

- `/sales`
- `/sales/new`
- `/sales/new?edit=<invoice-id>`

## Capabilities

### Customers

- Create and edit customer accounts.
- Maintain customer status and credit limits.
- View current balances and available credit.
- Open complete customer account statements.

### Sales

- Create and edit draft egg invoices.
- Add up to ten invoice lines.
- Sell eggs by piece, tray, or crate.
- Confirm invoices and deduct egg inventory.
- Cancel draft invoices with audited reasons.

### Payments

- Record receipts against confirmed invoices.
- View posted and reversed payments.
- Reverse erroneous payments with audited reasons.

### Returns

- Return eligible quantities from confirmed invoices.
- Restore returned eggs to inventory.
- Update invoice and customer balances.
- Reverse erroneous returns with audited reasons.

## Security

The frontend uses the existing Stage 20 same-origin BFF. Authentication
tokens remain in HttpOnly cookies. Buttons are permission-aware, while
the backend remains the final authorization authority.

## Backend contracts used

- `GET/POST /api/v1/sales/customers`
- `GET/PATCH /api/v1/sales/customers/{customer_id}`
- `GET /api/v1/sales/customers/{customer_id}/statement`
- `GET/POST /api/v1/sales/invoices`
- `GET/PATCH /api/v1/sales/invoices/{sale_id}`
- `POST /api/v1/sales/invoices/{sale_id}/confirm`
- `POST /api/v1/sales/invoices/{sale_id}/cancel`
- `GET/POST /api/v1/sales/payments`
- `POST /api/v1/sales/payments/{payment_id}/reverse`
- `GET/POST /api/v1/sales/returns`
- `POST /api/v1/sales/returns/{return_id}/reverse`
- `GET /api/v1/sales/summary`

No backend source, package dependency, Alembic migration, environment
value, or PostgreSQL schema change is required.
