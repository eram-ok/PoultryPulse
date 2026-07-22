# Stage 22B — Suppliers, Expenses, Bills, Payments, and Cash Ledger

Stage 22B replaces the supplier and finance placeholders with live,
permission-aware commercial finance workflows.

## Routes

- `/suppliers`
- `/finance`

## Supplier capabilities

- Register and edit suppliers.
- Filter by supplier type and activity state.
- Activate and deactivate supplier records.
- View supplier statements with bills, payments, and balances.

## Finance capabilities

- Create and maintain expense categories.
- Record posted operating expenses.
- Void incorrect expenses and restore cash through an audited reversal.
- Record supplier bills and due dates.
- Record partial or full supplier payments.
- Reverse incorrect supplier payments.
- View the cash ledger with running balances.
- Post controlled cash adjustments.
- Synchronize customer sale payments into the cash ledger.

## Security

The existing Stage 20 same-origin BFF remains the only browser-to-backend
path. Tokens remain in HttpOnly cookies. The frontend hides actions that
the authenticated role cannot perform, while FastAPI remains the final
authorization authority.

## Permissions

- `suppliers.view`
- `suppliers.create`
- `suppliers.update`
- `finance.view`
- `expense_categories.manage`
- `expenses.record`
- `expenses.void`
- `supplier_bills.manage`
- `supplier_payments.record`
- `supplier_payments.reverse`
- `cash_ledger.adjust`
- `finance.reports`

No backend source, package dependency, environment value, database schema,
or Alembic migration is changed by Stage 22B.
