from __future__ import annotations

from importlib import import_module
import sys
from pathlib import Path

import asyncio
import json

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


get_settings = import_module("app.core.config").get_settings

check_database_readiness = import_module("app.core.health").check_database_readiness


async def main() -> int:
    settings = get_settings()
    result = await check_database_readiness(
        timeout_seconds=(settings.readiness_database_timeout_seconds),
    )
    print(
        json.dumps(
            result,
            indent=2,
            default=str,
        )
    )
    return 0 if result["status"] == "up" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
