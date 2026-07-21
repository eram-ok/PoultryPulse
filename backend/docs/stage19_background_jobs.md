# Stage 19 — Background Jobs and Scheduled Operations

Stage 19 introduces a dependency-free scheduler for PoultryPulse.

## Jobs

- `alert_refresh`: refreshes operational alerts for every farm.
- `notification_delivery`: processes pending and retryable notification deliveries.
- `job_history_cleanup`: removes old job-run records according to retention settings.

## Deployment modes

The recommended production mode is a dedicated worker:

```text
python -m app.modules.jobs.worker
```

The API can also host the scheduler when both `BACKGROUND_JOBS_ENABLED`
and `BACKGROUND_JOBS_RUN_IN_API` are true. Database advisory locks and
database-backed due checks prevent duplicate execution across processes.

## Monitoring

Administrators with audit permissions can inspect:

- `GET /api/v1/jobs/definitions`
- `GET /api/v1/jobs/runs`
- `GET /api/v1/jobs/runs/{run_id}`
- `POST /api/v1/jobs/{job_name}/run`

Every execution is persisted in `background_job_runs` and emits a
system audit record.

## Manual execution

```text
python scripts/run_background_job.py job_history_cleanup
python scripts/run_background_job.py alert_refresh --farm-id <UUID>
python scripts/run_background_job.py notification_delivery --farm-id <UUID>
```
