import argparse

from sqlalchemy import select

from app.core.database import SessionLocal
from app.modules.eggs.service import EggInventoryService
from app.modules.farms.models import Farm
from app.modules.production.constants import (
    ProductionRecordStatus,
)
from app.modules.production.models import (
    DailyEggProduction,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Post previously confirmed production records into egg inventory.")
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

        productions = list(
            database_session.scalars(
                select(DailyEggProduction)
                .where(
                    DailyEggProduction.farm_id == farm.id,
                    DailyEggProduction.status == ProductionRecordStatus.CONFIRMED.value,
                )
                .order_by(
                    DailyEggProduction.production_date,
                    DailyEggProduction.created_at,
                )
            ).all()
        )

        inventory_service = EggInventoryService(database_session)

        created_transaction_count = 0

        for production in productions:
            created_by = (
                production.confirmed_by
                or production.last_updated_by
                or production.recorded_by
            )

            created_transactions = inventory_service.post_confirmed_production(
                production,
                created_by,
                commit=False,
            )

            created_transaction_count += len(created_transactions)

        database_session.commit()

        print("Egg inventory backfill completed.")
        print(f"Farm: {farm.name}")
        print(f"Farm code: {farm.farm_code}")
        print(f"Confirmed production records checked: {len(productions)}")
        print(f"Inventory transactions created: {created_transaction_count}")


if __name__ == "__main__":
    main()
