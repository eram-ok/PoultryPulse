
from __future__ import annotations

import argparse
import sys
from getpass import getpass
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.modules.platform.models import PlatformUser
from app.modules.platform.repository import (
    PlatformAuthRepository,
)
from app.modules.platform.schemas import (
    PlatformBootstrapIdentity,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create the first PoultryPulse platform "
            "super administrator."
        )
    )
    parser.add_argument(
        "--username",
        required=True,
        help="Global platform username.",
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Platform administrator email.",
    )
    parser.add_argument(
        "--first-name",
        required=True,
    )
    parser.add_argument(
        "--last-name",
        required=True,
    )
    parser.add_argument(
        "--no-password-change",
        action="store_true",
        help=(
            "Do not require a password change after "
            "the first successful login."
        ),
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    password = getpass("Platform administrator password: ")
    confirmation = getpass("Confirm password: ")

    if password != confirmation:
        print("The supplied passwords do not match.")
        return 1

    try:
        identity = PlatformBootstrapIdentity(
            username=arguments.username,
            email=arguments.email,
            first_name=arguments.first_name,
            last_name=arguments.last_name,
            password=password,
        )
    except ValidationError as error:
        print("The platform administrator details are invalid:")
        for item in error.errors():
            location = ".".join(
                str(part)
                for part in item.get("loc", ())
            )
            print(
                f"  - {location}: {item.get('msg')}"
            )
        return 1

    with SessionLocal() as database_session:
        repository = PlatformAuthRepository(
            database_session
        )

        if (
            repository.get_user_by_username(
                identity.username
            )
            is not None
        ):
            print(
                "A platform user already uses this username."
            )
            return 1

        if (
            repository.get_user_by_email(
                str(identity.email)
            )
            is not None
        ):
            print(
                "A platform user already uses this email."
            )
            return 1

        user = PlatformUser(
            username=identity.username,
            email=str(identity.email).lower(),
            password_hash=hash_password(
                identity.password
            ),
            first_name=identity.first_name,
            last_name=identity.last_name,
            is_active=True,
            is_super_admin=True,
            must_change_password=(
                not arguments.no_password_change
            ),
        )
        database_session.add(user)

        try:
            database_session.commit()
        except IntegrityError:
            database_session.rollback()
            print(
                "The platform administrator could not "
                "be created because a unique value exists."
            )
            return 1

        print(
            "Created PoultryPulse platform super administrator: "
            f"{user.username}"
        )
        print(
            "No password was printed or stored in plain text."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
