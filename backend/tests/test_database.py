from sqlalchemy import inspect, text

from app.core.database import engine


def test_database_connection() -> None:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar_one()

    assert result == 1


def test_expected_tables_exist() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    expected_tables = {
        "alembic_version",
        "farms",
        "farm_settings",
        "permissions",
        "roles",
        "role_permissions",
        "users",
        "user_roles",
        "refresh_tokens",
        "poultry_houses",
        "suppliers",
        "flocks",
        "flock_population_transactions",
        "daily_egg_productions",
        "egg_inventory_transactions",
        "feed_items",
        "feed_purchases",
        "feed_usages",
        "feed_inventory_transactions",
    }

    assert expected_tables.issubset(table_names)
