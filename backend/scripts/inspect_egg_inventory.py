from __future__ import annotations

import ast
from pathlib import Path

from sqlalchemy import inspect

from app.core.database import SessionLocal


OUTPUT_PATH = Path("stage13_egg_inventory_report.txt")
EGG_MODELS_PATH = Path("app/modules/eggs/models.py")


def inspect_python_models() -> list[str]:
    lines: list[str] = [
        "PYTHON EGG MODEL INSPECTION",
        "=" * 60,
    ]

    if not EGG_MODELS_PATH.exists():
        lines.append("app/modules/eggs/models.py was not found.")
        return lines

    source = EGG_MODELS_PATH.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)

    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue

        lines.append(f"\nClass: {node.name}")

        table_name = None
        attributes: list[str] = []

        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id == "__tablename__"
                        and isinstance(
                            item.value,
                            ast.Constant,
                        )
                    ):
                        table_name = item.value.value

            if isinstance(item, ast.AnnAssign):
                if isinstance(item.target, ast.Name):
                    attributes.append(item.target.id)

        lines.append(f"Table: {table_name}")
        lines.append("Attributes: " + ", ".join(attributes))

    return lines


def inspect_database() -> list[str]:
    lines: list[str] = [
        "",
        "DATABASE EGG TABLE INSPECTION",
        "=" * 60,
    ]

    with SessionLocal() as database_session:
        bind = database_session.get_bind()
        database_inspector = inspect(bind)

        tables = [
            table_name
            for table_name in database_inspector.get_table_names()
            if "egg" in table_name.lower()
        ]

        if not tables:
            lines.append("No database tables containing 'egg' were found.")
            return lines

        for table_name in sorted(tables):
            lines.append(f"\nTable: {table_name}")

            columns = database_inspector.get_columns(table_name)

            for column in columns:
                lines.append(
                    "  - "
                    f"{column['name']}: "
                    f"{column['type']} "
                    f"nullable={column['nullable']}"
                )

            foreign_keys = database_inspector.get_foreign_keys(table_name)

            if foreign_keys:
                lines.append("  Foreign keys:")

                for foreign_key in foreign_keys:
                    lines.append(
                        "    - "
                        f"{foreign_key['constrained_columns']} "
                        "-> "
                        f"{foreign_key['referred_table']}."
                        f"{foreign_key['referred_columns']}"
                    )

    return lines


def main() -> None:
    report_lines = inspect_python_models() + inspect_database()

    OUTPUT_PATH.write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )

    print(f"Created: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
