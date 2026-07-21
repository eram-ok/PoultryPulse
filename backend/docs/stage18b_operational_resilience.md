# Stage 18B — Operational Resilience

Stage 18B adds production-oriented runtime diagnostics without
changing PoultryPulse business tables or API authentication.

## Health endpoints

- `GET /api/v1/health` remains backward compatible.
- `GET /api/v1/health/live` confirms that the API process is alive.
- `GET /api/v1/health/ready` checks PostgreSQL and returns HTTP 503
  when the database is unavailable.

Health responses are marked `no-store` so proxies and browsers do not
cache stale service status.

## Structured logging

`LOG_FORMAT=json` produces one JSON object per line for production log
collectors. Request logs contain method, path, status, duration, client
IP and request ID. Bodies, authorization headers and query strings are
not logged.

## Database resilience

The SQLAlchemy engine now supports configurable pool size, overflow,
timeout, recycle and connection timeout settings. Sessions roll back
when request handling raises an exception, and the engine is disposed
during application shutdown.

## Startup checks

`STARTUP_DATABASE_CHECK_ENABLED=true` performs a database probe during
application startup. When `STARTUP_DATABASE_CHECK_REQUIRED=true`, a
failed probe prevents the application from accepting traffic.

The startup check is optional. The readiness endpoint remains the
authoritative signal for load balancers and orchestrators.

## Production command

A basic Procfile is included:

```text
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
```

Scale workers according to available memory and database pool capacity.
The total possible database connections are approximately:

```text
workers × (DATABASE_POOL_SIZE + DATABASE_MAX_OVERFLOW)
```

Keep that total below the PostgreSQL server connection limit.

## Manual readiness check

Run:

```powershell
python .\scripts\check_readiness.py
```

It exits with status 0 when PostgreSQL is available and status 1 when
the readiness check fails.
