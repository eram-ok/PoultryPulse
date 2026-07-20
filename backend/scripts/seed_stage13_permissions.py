from __future__ import annotations

import argparse

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import SessionLocal
from app.modules.farms.models import Farm
from app.modules.users.models import Permission, Role


PERMISSIONS = [
    (
        "sales.view",
        "sales",
        "View Sales",
        "View customers, sales, payments and returns",
    ),
    (
        "customers.manage",
        "sales",
        "Manage Customers",
        "Create and manage customers",
    ),
    (
        "sales.create",
        "sales",
        "Create Sales",
        "Create and edit draft egg sales",
    ),
    (
        "sales.confirm",
        "sales",
        "Confirm Sales",
        "Confirm egg sales and reduce inventory",
    ),
    (
        "sales.cancel",
        "sales",
        "Cancel Sales",
        "Cancel confirmed or draft sales",
    ),
    (
        "payments.record",
        "sales",
        "Record Payments",
        "Record customer payments",
    ),
    (
        "payments.reverse",
        "sales",
        "Reverse Payments",
        "Reverse posted customer payments",
    ),
    (
        "sales.returns",
        "sales",
        "Manage Sale Returns",
        "Record and reverse egg sale returns",
    ),
]

ROLE_PERMISSIONS = {
    "Administrator": {permission[0] for permission in PERMISSIONS},
    "Owner": {
        "sales.view",
    },
    "Manager": {permission[0] for permission in PERMISSIONS},
    "Attendant": {
        "sales.view",
        "customers.manage",
        "sales.create",
        "payments.record",
        "sales.returns",
    },
}


def seed_stage13_permissions(farm_code: str) -> None:
    with SessionLocal() as database_session:
        farm = database_session.scalar(select(Farm).where(Farm.farm_code == farm_code))

        if farm is None:
            raise RuntimeError(f"Farm {farm_code!r} was not found.")

        permission_by_code: dict[str, Permission] = {}

        for code, module, name, description in PERMISSIONS:
            permission = database_session.scalar(
                select(Permission).where(Permission.code == code)
            )

            if permission is None:
                permission = Permission(
                    code=code,
                    module=module,
                    name=name,
                    description=description,
                )
                database_session.add(permission)
                database_session.flush()

            permission_by_code[code] = permission

        roles = list(
            database_session.scalars(
                select(Role)
                .options(selectinload(Role.permissions))
                .where(Role.farm_id == farm.id)
            ).all()
        )

        for role in roles:
            desired_codes = ROLE_PERMISSIONS.get(
                role.name,
                set(),
            )

            existing_codes = {permission.code for permission in role.permissions}

            for code in desired_codes - existing_codes:
                role.permissions.append(permission_by_code[code])

        database_session.commit()

    print(f"Stage 13 permissions seeded for {farm_code}.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--farm-code",
        required=True,
    )
    arguments = parser.parse_args()
    seed_stage13_permissions(arguments.farm_code)


if __name__ == "__main__":
    main()
