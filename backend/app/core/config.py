"""
Minimal configuration for TASK-DB-FOUNDATION-001.

This module intentionally contains no business logic. It only resolves
the PostgreSQL connection string from the environment so that the
SQLAlchemy engine, Alembic, and the test suite can all share one
source of truth for how to reach the database.
"""

from __future__ import annotations

import os


def get_database_url(*, sync: bool = True) -> str:
    """
    Returns the PostgreSQL connection URL.

    The DATABASE_URL environment variable is authoritative. A local
    default is provided only to make `docker-compose up` -> tests a
    zero-config experience; it is not meant for production use.

    sync=True  -> postgresql+psycopg2://...   (used by Alembic, sync engine)
    sync=False -> postgresql+asyncpg://...    (reserved; not used by this task,
                                                 the DB foundation does not ship
                                                 an async engine, but the hook
                                                 is kept here so a later task
                                                 doesn't have to touch config.py)
    """
    url = os.environ.get("DATABASE_URL")
    if url is None:
        url = (
            "postgresql+psycopg2://nirman:nirman@localhost:5432/nirman"
            if sync
            else "postgresql+asyncpg://nirman:nirman@localhost:5432/nirman"
        )
    return url


def get_test_database_url() -> str:
    """
    Returns the PostgreSQL connection URL used by the test suite.

    Defaults to TEST_DATABASE_URL, falling back to DATABASE_URL with the
    database name suffixed with `_test` if not explicitly set, so tests
    never accidentally run against a development database by default.
    """
    url = os.environ.get("TEST_DATABASE_URL")
    if url is not None:
        return url

    base = get_database_url(sync=True)
    if base.rsplit("/", 1)[-1].endswith("_test"):
        return base
    prefix, _, dbname = base.rpartition("/")
    return f"{prefix}/{dbname}_test"
def get_jwt_secret() -> str:
    """
    Returns the JWT signing secret.

    The secret must be supplied through the JWT_SECRET environment variable.
    """
    secret = os.environ.get("JWT_SECRET")

    if not secret:
        raise RuntimeError("JWT_SECRET environment variable is not configured")

    return secret
