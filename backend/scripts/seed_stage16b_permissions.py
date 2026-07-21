from __future__ import annotations

import argparse

from sqlalchemy import select

from app.core.database import SessionLocal
from app.modules.farms.models import Farm
from app.modules.users.models import Permission, Role


PERMISSIONS = [
    ("alerts.manage", "alerts", "Manage Persistent Alerts"),
    ("alerts.assign", "alerts", "Assign Alerts to Users"),
    (
        "alerts.acknowledge",
        "alerts",
        "Acknowledge Alerts",
    ),
    (
        "alerts.resolve",
        "alerts",
        "Resolve and Reopen Alerts",
    ),
    (
        "alerts.refresh",
        "alerts",
        "Refresh Operational Alerts",
    ),
    (
        "notifications.manage",
        "alerts",
        "Manage Notification Preferences",
    ),
    (
        "notifications.send",
        "alerts",
        "Send and Retry Notifications",
    ),
    (
        "notifications.view_deliveries",
        "alerts",
        "View Notification Delivery History",
    ),
]

ROLE_PERMISSION_CODES = {
    "Administrator": {code for code, _, _ in PERMISSIONS},
    "Manager": {code for code, _, _ in PERMISSIONS},
    "Owner": {code for code, _, _ in PERMISSIONS},
    "Attendant": {
        "alerts.acknowledge",
        "notifications.manage",
    },
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--farm-code", required=True)
    arguments = parser.parse_args()

    with SessionLocal() as session:
        farm = session.scalar(select(Farm).where(Farm.farm_code == arguments.farm_code))
        if farm is None:
            raise SystemExit(f"Farm {arguments.farm_code!r} was not found.")

        permission_map: dict[str, Permission] = {}

        for code, module, name in PERMISSIONS:
            permission = session.scalar(
                select(Permission).where(Permission.code == code)
            )
            if permission is None:
                permission = Permission(
                    code=code,
                    module=module,
                    name=name,
                )
                session.add(permission)
                session.flush()
            permission_map[code] = permission

        roles = list(session.scalars(select(Role).where(Role.farm_id == farm.id)).all())

        for role in roles:
            requested = ROLE_PERMISSION_CODES.get(
                role.name,
                set(),
            )
            existing = {permission.code for permission in role.permissions}
            for code in requested:
                if code not in existing:
                    role.permissions.append(permission_map[code])

        session.commit()

    print(f"Stage 16B notification permissions seeded for {arguments.farm_code}.")


if __name__ == "__main__":
    main()
