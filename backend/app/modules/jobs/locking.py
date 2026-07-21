from __future__ import annotations

import hashlib
import threading
from contextlib import contextmanager
from typing import Iterator
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session


_local_locks: dict[int, threading.Lock] = {}
_local_locks_guard = threading.Lock()


def advisory_lock_key(
    *,
    job_name: str,
    farm_id: UUID | None,
) -> int:
    raw = f"poultrypulse:{job_name}:{farm_id or 'global'}"
    digest = hashlib.blake2b(
        raw.encode("utf-8"),
        digest_size=8,
    ).digest()
    return int.from_bytes(
        digest,
        byteorder="big",
        signed=True,
    )


def _database_backend(
    database_session: Session,
) -> str:
    bind = database_session.get_bind()
    return bind.dialect.name


def _lock_engine(
    database_session: Session,
) -> Engine:
    bind = database_session.get_bind()
    if isinstance(bind, Engine):
        return bind
    if isinstance(bind, Connection):
        return bind.engine
    raise RuntimeError(
        "Could not resolve the database engine for background-job locking."
    )


@contextmanager
def background_job_lock(
    database_session: Session,
    *,
    job_name: str,
    farm_id: UUID | None,
) -> Iterator[bool]:
    key = advisory_lock_key(
        job_name=job_name,
        farm_id=farm_id,
    )

    if _database_backend(database_session) == "postgresql":
        with _lock_engine(database_session).connect() as connection:
            acquired = bool(
                connection.execute(
                    text("SELECT pg_try_advisory_lock(:lock_key)"),
                    {"lock_key": key},
                ).scalar_one()
            )
            try:
                yield acquired
            finally:
                if acquired:
                    connection.execute(
                        text("SELECT pg_advisory_unlock(:lock_key)"),
                        {"lock_key": key},
                    )
        return

    with _local_locks_guard:
        lock = _local_locks.setdefault(
            key,
            threading.Lock(),
        )

    acquired = lock.acquire(blocking=False)
    try:
        yield acquired
    finally:
        if acquired:
            lock.release()
