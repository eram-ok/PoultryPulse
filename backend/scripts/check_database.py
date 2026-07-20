from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine


def main() -> None:
    """Confirm that PoultryPulse can connect to PostgreSQL."""

    try:
        with engine.connect() as connection:
            result = (
                connection.execute(
                    text(
                        """
                    SELECT
                        current_database() AS database_name,
                        current_user AS database_user,
                        current_setting('TimeZone') AS timezone,
                        version() AS postgres_version
                    """
                    )
                )
                .mappings()
                .one()
            )

        print("PoultryPulse database connection successful.")
        print(f"Database: {result['database_name']}")
        print(f"User: {result['database_user']}")
        print(f"Timezone: {result['timezone']}")
        print(f"PostgreSQL: {result['postgres_version']}")

    except SQLAlchemyError as exc:
        print("PoultryPulse could not connect to PostgreSQL.")
        print(f"Error: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
