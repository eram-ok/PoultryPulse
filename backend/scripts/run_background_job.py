from __future__ import annotations

import argparse
from importlib import import_module
import json
from pathlib import Path
import sys
from uuid import UUID


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one PoultryPulse background job.",
    )
    parser.add_argument("job_name")
    parser.add_argument(
        "--farm-id",
        type=UUID,
        default=None,
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()

    database_module = import_module(
        "app.core.database",
    )
    constants_module = import_module(
        "app.modules.jobs.constants",
    )
    service_module = import_module(
        "app.modules.jobs.service",
    )
    audit_registry = import_module(
        "app.modules.audit.commercial_registry",
    )
    audit_registry.install_commercial_auditing()

    with database_module.SessionLocal() as session:
        run = service_module.BackgroundJobsService(
            session,
        ).run(
            job_name=arguments.job_name,
            farm_id=arguments.farm_id,
            trigger=(constants_module.BackgroundJobTrigger.MANUAL.value),
            force=True,
        )

    print(
        json.dumps(
            {
                "id": str(run.id),
                "job_name": run.job_name,
                "farm_id": (str(run.farm_id) if run.farm_id else None),
                "status": run.status,
                "duration_ms": run.duration_ms,
                "result": run.result_json,
                "error_type": run.error_type,
                "error_message": run.error_message,
            },
            indent=2,
            default=str,
        )
    )
    return 0 if run.is_successful else 1


if __name__ == "__main__":
    raise SystemExit(main())
