"""
Migration verification (DB plan §39): upgrade head -> inspect -> downgrade
base -> inspect -> upgrade head -> inspect, against a REAL PostgreSQL
database, run on a dedicated ephemeral database so it never disturbs the
schema the rest of the suite depends on (`migrated_engine` in conftest.py).
"""

from __future__ import annotations

import os

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from tests.db.conftest import REPO_ROOT, _admin_url, _dbname, _test_db_url

MIGRATION_TEST_DB_URL = _test_db_url().rsplit("/", 1)[0] + "/nirman_migration_verify"

EXPECTED_TABLES = {
    "users",
    "worker_profiles",
    "organizations",
    "teams",
    "team_members",
    "projects",
    "project_locations",
    "job_requirements",
    "availability_windows",
    "bookings",
    "team_booking_groups",
    "booking_items",
    "worker_reservations",
    "booking_idempotency",
    "outbox_events",
    "reviews",
    "alembic_version",
}

EXPECTED_ENUMS = {"user_status", "booking_status", "resource_type", "reviewee_type"}


@pytest.fixture(scope="module")
def migration_verify_engine():
    admin_engine = sa.create_engine(
        _admin_url(MIGRATION_TEST_DB_URL), isolation_level="AUTOCOMMIT"
    )
    dbname = _dbname(MIGRATION_TEST_DB_URL)
    with admin_engine.connect() as conn:
        conn.execute(
            text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = :dbname AND pid <> pg_backend_pid()"
            ),
            {"dbname": dbname},
        )
        conn.execute(text(f'DROP DATABASE IF EXISTS "{dbname}"'))
        conn.execute(text(f'CREATE DATABASE "{dbname}"'))

    cfg = Config(os.path.join(REPO_ROOT, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(REPO_ROOT, "backend", "alembic"))
    cfg.set_main_option("sqlalchemy.url", MIGRATION_TEST_DB_URL)

    engine = sa.create_engine(MIGRATION_TEST_DB_URL, future=True)
    yield engine, cfg

    engine.dispose()
    with admin_engine.connect() as conn:
        conn.execute(
            text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = :dbname AND pid <> pg_backend_pid()"
            ),
            {"dbname": dbname},
        )
        conn.execute(text(f'DROP DATABASE IF EXISTS "{dbname}"'))
    admin_engine.dispose()


def _installed_enums(engine) -> set[str]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT typname FROM pg_type WHERE typtype = 'e'")
        ).fetchall()
    return {r[0] for r in rows}


def _installed_tables(engine) -> set[str]:
    return set(inspect(engine).get_table_names())


def test_upgrade_head_creates_full_schema(migration_verify_engine):
    engine, cfg = migration_verify_engine
    command.upgrade(cfg, "head")

    tables = _installed_tables(engine)
    missing = EXPECTED_TABLES - tables
    assert not missing, f"Missing tables after upgrade head: {missing}"

    enums = _installed_enums(engine)
    missing_enums = EXPECTED_ENUMS - enums
    assert not missing_enums, f"Missing enum types after upgrade head: {missing_enums}"

    with engine.connect() as conn:
        ext = conn.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'btree_gist'")
        ).scalar()
        assert ext == 1, "btree_gist extension not installed after upgrade head"

        triggers = conn.execute(
            text(
                "SELECT tgname FROM pg_trigger WHERE tgname IN "
                "('booking_items_agreed_rate_immutable', "
                " 'ct_booking_items_shape_validation', "
                " 'ct_worker_reservations_shape_validation')"
            )
        ).fetchall()
        assert {t[0] for t in triggers} == {
            "booking_items_agreed_rate_immutable",
            "ct_booking_items_shape_validation",
            "ct_worker_reservations_shape_validation",
        }

        excl = conn.execute(
            text(
                "SELECT conname FROM pg_constraint "
                "WHERE conname = 'worker_reservations_no_overlap' AND contype = 'x'"
            )
        ).scalar()
        assert excl == "worker_reservations_no_overlap"


def test_downgrade_base_removes_schema(migration_verify_engine):
    engine, cfg = migration_verify_engine
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")

    tables = _installed_tables(engine)
    domain_tables = EXPECTED_TABLES - {"alembic_version"}
    leftover = domain_tables & tables
    assert not leftover, f"Tables still present after downgrade base: {leftover}"

    enums = _installed_enums(engine)
    leftover_enums = EXPECTED_ENUMS & enums
    assert not leftover_enums, f"Enum types still present after downgrade base: {leftover_enums}"


def test_upgrade_head_again_is_reproducible(migration_verify_engine):
    engine, cfg = migration_verify_engine
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")

    tables = _installed_tables(engine)
    missing = EXPECTED_TABLES - tables
    assert not missing, f"Missing tables after second upgrade head: {missing}"
