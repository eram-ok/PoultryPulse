from __future__ import annotations

import argparse
from uuid import UUID

from sqlalchemy import select

from app.core.database import SessionLocal
from app.modules.alerts.constants import (
    AlertDeliveryChannel,
)
from app.modules.alerts.service import AlertsService
from app.modules.users.models import User


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", required=True)
    parser.add_argument(
        "--channel",
        required=True,
        choices=[channel.value for channel in AlertDeliveryChannel],
    )
    parser.add_argument("--destination")
    arguments = parser.parse_args()

    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.id == UUID(arguments.user_id)))
        if user is None:
            raise SystemExit("User was not found.")

        delivery = AlertsService(session).send_test_notification(
            user.farm_id,
            user,
            channel=arguments.channel,
            destination=arguments.destination,
        )

    print(
        f"status={delivery.status} "
        f"provider={delivery.provider_name} "
        f"message_id={delivery.provider_message_id} "
        f"error={delivery.last_error}"
    )


if __name__ == "__main__":
    main()
