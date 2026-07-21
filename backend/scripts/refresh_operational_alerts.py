from __future__ import annotations

import argparse
from datetime import date
from uuid import UUID

from sqlalchemy import select

from app.core.database import SessionLocal
from app.modules.alerts.service import AlertsService
from app.modules.farms.models import Farm
from app.modules.users.models import User


def parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--farm-code", required=True)
    parser.add_argument(
        "--requested-by",
        help=(
            "User UUID used for refresh audit history. "
            "Defaults to the first active farm user."
        ),
    )
    parser.add_argument("--as-of-date")
    parser.add_argument(
        "--queue-only",
        action="store_true",
    )
    arguments = parser.parse_args()

    with SessionLocal() as session:
        farm = session.scalar(select(Farm).where(Farm.farm_code == arguments.farm_code))
        if farm is None:
            raise SystemExit(f"Farm {arguments.farm_code!r} was not found.")

        if arguments.requested_by:
            requested_by = UUID(arguments.requested_by)
        else:
            user = session.scalar(
                select(User)
                .where(
                    User.farm_id == farm.id,
                    User.is_active.is_(True),
                )
                .order_by(User.created_at.asc())
            )
            if user is None:
                raise SystemExit("No active user exists for this farm.")
            requested_by = user.id

        result = AlertsService(session).refresh(
            farm.id,
            requested_by,
            as_of_date=parse_date(arguments.as_of_date),
            send_now=not arguments.queue_only,
        )

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
