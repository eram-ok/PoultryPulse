# Stage 17C1 — Farm Operations Auditing

Stage 17C1 applies the Stage 17 audit trail to farm-operation services without
rewriting their routers or changing their transaction behavior.

## Covered domains

- flocks and population transactions;
- daily egg production;
- egg inventory adjustments, issues and reversals;
- feed items, purchases, usage, wastage and inventory;
- veterinary products and vaccination schedules;
- health incidents and treatment records;
- mortality and culling records.

## Integration model

Each selected service method is wrapped once at application startup. The
wrapper captures a safe before snapshot where applicable, calls the original
service method unchanged, captures the returned model, and records success or
failure. The wrapper is idempotent and cannot be installed twice.

## Linked effects

- flock creation creates an initial population placement;
- production confirmation posts graded eggs to inventory;
- feed purchase and usage change feed inventory;
- bird-loss creation and reversal change flock population.

## Database

No schema change or Alembic migration is required. Stage 17C1 uses the
`audit_logs` table created in Stage 17A.
