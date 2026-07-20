import argparse

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import SessionLocal
from app.modules.farms.models import Farm
from app.modules.users.models import Permission, Role


SUPPLIER_PERMISSIONS = [
    (
        "suppliers.view",
        "suppliers",
        "View suppliers",
    ),
    (
        "suppliers.create",
        "suppliers",
        "Create suppliers",
    ),
    (
        "suppliers.update",
        "suppliers",
        "Update suppliers",
    ),
]


ROLE_PERMISSION_CODES = {
    "Administrator": {
        "suppliers.view",
        "suppliers.create",
        "suppliers.update",
    },
    "Owner": {
        "suppliers.view",
    },
    "Manager": {
        "suppliers.view",
        "suppliers.create",
        "suppliers.update",
    },
}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create Stage 7 supplier permissions and assign them to PoultryPulse roles."
        )
    )

    parser.add_argument(
        "--farm-code",
        required=True,
    )

    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()

    with SessionLocal() as database_session:
        farm = database_session.scalar(
            select(Farm).where(Farm.farm_code == arguments.farm_code.strip().upper())
        )

        if farm is None:
            raise SystemExit(f"No farm exists with code {arguments.farm_code!r}.")

        permission_map: dict[str, Permission] = {}

        for code, module, name in SUPPLIER_PERMISSIONS:
            permission = database_session.scalar(
                select(Permission).where(Permission.code == code)
            )

            if permission is None:
                permission = Permission(
                    code=code,
                    module=module,
                    name=name,
                )

                database_session.add(permission)
                database_session.flush()

            permission_map[code] = permission

        for role_name, permission_codes in ROLE_PERMISSION_CODES.items():
            role = database_session.scalar(
                select(Role)
                .options(selectinload(Role.permissions))
                .where(
                    Role.farm_id == farm.id,
                    Role.name == role_name,
                )
            )

            if role is None:
                print(f"Role {role_name!r} was not found; it was skipped.")
                continue

            existing_codes = {permission.code for permission in role.permissions}

            for permission_code in permission_codes:
                if permission_code not in existing_codes:
                    role.permissions.append(permission_map[permission_code])

        database_session.commit()

        print("Stage 7 permissions configured.")
        print(f"Farm: {farm.name}")
        print(f"Farm code: {farm.farm_code}")
        print("Permissions: " + ", ".join(permission_map))


if __name__ == "__main__":
    main()
