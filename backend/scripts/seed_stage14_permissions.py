from __future__ import annotations

import argparse

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import SessionLocal
from app.modules.farms.models import Farm
from app.modules.users.models import Permission, Role


PERMISSIONS = [
    (
        "finance.view",
        "finance",
        "View Finance",
        "View expenses, supplier bills, cash flow and reports",
    ),
    (
        "expense_categories.manage",
        "finance",
        "Manage Expense Categories",
        "Create and maintain expense categories",
    ),
    (
        "expenses.record",
        "finance",
        "Record Expenses",
        "Create and post farm operating expenses",
    ),
    (
        "expenses.void",
        "finance",
        "Void Expenses",
        "Void posted farm operating expenses",
    ),
    (
        "supplier_bills.manage",
        "finance",
        "Manage Supplier Bills",
        "Create, update and void supplier bills",
    ),
    (
        "supplier_payments.record",
        "finance",
        "Record Supplier Payments",
        "Record payments against supplier bills",
    ),
    (
        "supplier_payments.reverse",
        "finance",
        "Reverse Supplier Payments",
        "Reverse posted supplier bill payments",
    ),
    (
        "cash_ledger.adjust",
        "finance",
        "Adjust Cash Ledger",
        "Record controlled cash ledger adjustments",
    ),
    (
        "finance.reports",
        "finance",
        "View Finance Reports",
        "View cash flow, expense and profitability reports",
    ),
]

ROLE_PERMISSIONS = {
    "Administrator": {permission[0] for permission in PERMISSIONS},
    "Owner": {
        "finance.view",
        "finance.reports",
    },
    "Manager": {permission[0] for permission in PERMISSIONS},
    "Attendant": {
        "finance.view",
        "expenses.record",
        "supplier_payments.record",
    },
}


def seed_stage14_permissions(farm_code: str) -> None:
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

    print(f"Stage 14 permissions seeded for {farm_code}.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--farm-code",
        required=True,
    )
    arguments = parser.parse_args()
    seed_stage14_permissions(arguments.farm_code)


if __name__ == "__main__":
    main()
