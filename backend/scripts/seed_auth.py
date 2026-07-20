import argparse
from getpass import getpass

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.modules.farms.models import Farm
from app.modules.users.models import Permission, Role, User


PERMISSIONS = [
    ("users.view", "users", "View users"),
    ("users.create", "users", "Create users"),
    ("users.update", "users", "Update users"),
    ("users.deactivate", "users", "Deactivate users"),
    ("roles.view", "roles", "View roles"),
    ("roles.create", "roles", "Create roles"),
    ("roles.update", "roles", "Update roles"),
    ("roles.assign", "roles", "Assign roles"),
    ("farms.view", "farms", "View farm information"),
    ("farms.create", "farms", "Create farms"),
    ("farms.update", "farms", "Update farm information"),
    (
        "farms.settings.update",
        "farms",
        "Update farm settings",
    ),
    ("houses.view", "houses", "View poultry houses"),
    ("houses.create", "houses", "Create poultry houses"),
    ("houses.update", "houses", "Update poultry houses"),
    ("flocks.view", "flocks", "View flocks"),
    ("flocks.create", "flocks", "Create flocks"),
    ("flocks.update", "flocks", "Update flocks"),
    ("production.view", "production", "View production"),
    ("production.create", "production", "Create production"),
    ("production.submit", "production", "Submit production"),
    ("production.confirm", "production", "Confirm production"),
    ("production.adjust", "production", "Adjust production"),
    ("eggs.view", "eggs", "View egg inventory"),
    ("eggs.adjust", "eggs", "Adjust egg inventory"),
    ("feed.view", "feed", "View feed information"),
    ("feed.purchase", "feed", "Record feed purchases"),
    ("feed.usage.create", "feed", "Record feed usage"),
    ("feed.adjust", "feed", "Adjust feed inventory"),
    ("health.view", "health", "View health information"),
    ("health.create", "health", "Create health records"),
    ("health.update", "health", "Update health records"),
    ("customers.view", "customers", "View customers"),
    ("customers.create", "customers", "Create customers"),
    ("customers.update", "customers", "Update customers"),
    ("sales.view", "sales", "View sales"),
    ("sales.create", "sales", "Create sales"),
    ("sales.confirm", "sales", "Confirm sales"),
    ("sales.cancel", "sales", "Cancel sales"),
    ("payments.view", "payments", "View payments"),
    ("payments.create", "payments", "Create payments"),
    ("payments.reverse", "payments", "Reverse payments"),
    ("expenses.view", "expenses", "View expenses"),
    ("expenses.create", "expenses", "Create expenses"),
    ("expenses.approve", "expenses", "Approve expenses"),
    ("expenses.cancel", "expenses", "Cancel expenses"),
    ("alerts.view", "alerts", "View alerts"),
    ("alerts.resolve", "alerts", "Resolve alerts"),
    ("reports.view", "reports", "View reports"),
    ("audit.view", "audit", "View audit logs"),
]


ROLE_PERMISSIONS = {
    "Administrator": "*",
    "Owner": [
        "farms.view",
        "farms.update",
        "farms.settings.update",
        "houses.view",
        "flocks.view",
        "production.view",
        "eggs.view",
        "feed.view",
        "health.view",
        "customers.view",
        "sales.view",
        "payments.view",
        "expenses.view",
        "alerts.view",
        "reports.view",
        "audit.view",
    ],
    "Manager": [
        "farms.view",
        "houses.view",
        "houses.create",
        "houses.update",
        "flocks.view",
        "flocks.create",
        "flocks.update",
        "production.view",
        "production.create",
        "production.submit",
        "production.confirm",
        "production.adjust",
        "eggs.view",
        "eggs.adjust",
        "feed.view",
        "feed.purchase",
        "feed.usage.create",
        "feed.adjust",
        "health.view",
        "health.create",
        "health.update",
        "customers.view",
        "sales.view",
        "expenses.view",
        "expenses.create",
        "expenses.approve",
        "alerts.view",
        "alerts.resolve",
        "reports.view",
    ],
    "Attendant": [
        "farms.view",
        "houses.view",
        "flocks.view",
        "production.view",
        "production.create",
        "production.submit",
        "eggs.view",
        "feed.view",
        "feed.usage.create",
        "health.view",
        "health.create",
        "alerts.view",
    ],
    "Sales Officer": [
        "farms.view",
        "eggs.view",
        "customers.view",
        "customers.create",
        "customers.update",
        "sales.view",
        "sales.create",
        "sales.confirm",
        "payments.view",
        "payments.create",
        "expenses.view",
        "reports.view",
    ],
}


ROLE_DESCRIPTIONS = {
    "Administrator": "Full access to PoultryPulse.",
    "Owner": "Farm oversight and reporting access.",
    "Manager": "Operational poultry farm management.",
    "Attendant": "Daily production and farm data entry.",
    "Sales Officer": "Customer, sale and payment management.",
}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create default PoultryPulse roles, permissions "
            "and the first administrator."
        )
    )

    parser.add_argument(
        "--farm-code",
        required=True,
        help="Existing farm code, for example PP-FARM-001.",
    )

    parser.add_argument(
        "--username",
        default="admin",
    )

    parser.add_argument(
        "--email",
        default="admin@poultrypulse.local",
    )

    parser.add_argument(
        "--first-name",
        default="PoultryPulse",
    )

    parser.add_argument(
        "--last-name",
        default="Administrator",
    )

    return parser.parse_args()


def read_password() -> str:
    while True:
        password = getpass("Enter the administrator password: ")
        confirmation = getpass("Confirm the administrator password: ")

        if password != confirmation:
            print("The passwords do not match.")
            continue

        if len(password) < 12:
            print("Use a password containing at least 12 characters.")
            continue

        return password


def main() -> None:
    arguments = parse_arguments()
    password = read_password()

    with SessionLocal() as database_session:
        farm = database_session.scalar(
            select(Farm).where(Farm.farm_code == arguments.farm_code.strip().upper())
        )

        if farm is None:
            raise SystemExit(f"No farm was found with code {arguments.farm_code!r}.")

        permission_map: dict[str, Permission] = {}

        for code, module, name in PERMISSIONS:
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

        all_permissions = list(permission_map.values())
        role_map: dict[str, Role] = {}

        for role_name, assigned_codes in ROLE_PERMISSIONS.items():
            role = database_session.scalar(
                select(Role)
                .options(selectinload(Role.permissions))
                .where(
                    Role.farm_id == farm.id,
                    Role.name == role_name,
                )
            )

            if role is None:
                role = Role(
                    farm_id=farm.id,
                    name=role_name,
                    description=ROLE_DESCRIPTIONS[role_name],
                    is_system_role=True,
                    is_active=True,
                )
                database_session.add(role)
                database_session.flush()

            if assigned_codes == "*":
                role.permissions = all_permissions
            else:
                role.permissions = [permission_map[code] for code in assigned_codes]

            role_map[role_name] = role

        normalized_username = arguments.username.strip().lower()
        normalized_email = arguments.email.strip().lower()

        existing_user = database_session.scalar(
            select(User)
            .options(selectinload(User.roles))
            .where(
                User.farm_id == farm.id,
                User.username == normalized_username,
            )
        )

        administrator_role = role_map["Administrator"]

        if existing_user is None:
            administrator = User(
                farm_id=farm.id,
                username=normalized_username,
                email=normalized_email,
                telephone=None,
                password_hash=hash_password(password),
                first_name=arguments.first_name.strip(),
                last_name=arguments.last_name.strip(),
                is_active=True,
                is_verified=True,
                must_change_password=False,
            )

            administrator.roles.append(administrator_role)
            database_session.add(administrator)

            result_message = "Administrator account created successfully."
        else:
            existing_user.password_hash = hash_password(password)
            existing_user.email = normalized_email
            existing_user.is_active = True
            existing_user.is_verified = True

            if administrator_role not in existing_user.roles:
                existing_user.roles.append(administrator_role)

            result_message = "Existing administrator account updated."

        database_session.commit()

        print()
        print(result_message)
        print(f"Farm: {farm.name}")
        print(f"Farm code: {farm.farm_code}")
        print(f"Username: {normalized_username}")
        print(f"Email: {normalized_email}")
        print(f"Permissions created: {len(permission_map)}")
        print(f"Roles configured: {len(role_map)}")


if __name__ == "__main__":
    main()
