"""
Shared pytest fixtures for the DB Foundation test suite.

Everything here talks to REAL PostgreSQL (per DB plan §40/§41): no
SQLite, no mocked constraints. `TEST_DATABASE_URL` (falling back to
`DATABASE_URL` + `_test` suffix, see app/core/config.py) is dropped and
recreated once per test session, then migrated to `head` via the real
Alembic migration chain — the schema under test is therefore always
exactly what `alembic upgrade head` produces, not a hand-rolled
`Base.metadata.create_all()`.

Isolation strategy: each test gets its own connection wrapped in an
explicit transaction that is rolled back in teardown. Deferred
constraint triggers only fire at COMMIT time, so any test that needs to
observe one explicitly calls `commit_deferred_checks(conn)`
(`SET CONSTRAINTS ALL IMMEDIATE`) *before* the implicit rollback — this
forces the deferred checks to run immediately, inside the still-open
transaction, without requiring an actual commit (and therefore without
leaking rows past the test).

Tests that must observe a REAL commit (the worker-reservation
concurrency test, the rollback test) manage their own connections/
transactions explicitly rather than using the `db_conn` fixture, and
clean up their own rows in a `finally` block.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Generator
from datetime import datetime, timedelta, timezone

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _test_db_url() -> str:
    import sys

    sys.path.insert(0, os.path.join(REPO_ROOT, "backend"))
    from app.core.config import get_test_database_url

    return get_test_database_url()


def _admin_url(db_url: str) -> str:
    """Same server, connected to the `postgres` maintenance database."""
    prefix, _, _dbname = db_url.rpartition("/")
    return f"{prefix}/postgres"


def _dbname(db_url: str) -> str:
    return db_url.rsplit("/", 1)[-1]


@pytest.fixture(scope="session")
def test_db_url() -> str:
    return _test_db_url()


@pytest.fixture(scope="session")
def recreated_test_database(test_db_url: str) -> Generator[str, None, None]:
    """Drops and recreates the test database fresh for this session."""
    admin_engine = sa.create_engine(_admin_url(test_db_url), isolation_level="AUTOCOMMIT")
    dbname = _dbname(test_db_url)
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
    admin_engine.dispose()
    yield test_db_url


@pytest.fixture(scope="session")
def alembic_config(recreated_test_database: str) -> Config:
    cfg = Config(os.path.join(REPO_ROOT, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(REPO_ROOT, "backend", "alembic"))
    cfg.set_main_option("sqlalchemy.url", recreated_test_database)
    cfg.attributes["configure_logger"] = False
    return cfg


@pytest.fixture(scope="session")
def migrated_engine(
    alembic_config: Config, recreated_test_database: str
) -> Generator[Engine, None, None]:
    """Runs `alembic upgrade head` once per session; yields a bound Engine."""
    command.upgrade(alembic_config, "head")
    engine = sa.create_engine(recreated_test_database, future=True)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_conn(migrated_engine: Engine) -> Generator[Connection, None, None]:
    """
    One connection + one explicit transaction per test. Rolled back in
    teardown so tests never leak rows into each other, including tests
    that call `commit_deferred_checks()` to force deferred triggers to
    run early.
    """
    conn = migrated_engine.connect()
    trans = conn.begin()
    try:
        yield conn
    finally:
        trans.rollback()
        conn.close()


def commit_deferred_checks(conn: Connection) -> None:
    """Force deferred constraints/triggers to run now, then restore deferred mode."""
    conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))

# ---------------------------------------------------------------------------
# Row factories — thin, explicit SQL helpers (not the ORM) so tests exercise
# the actual database constraints rather than any application-layer
# validation. Each returns the new row's primary key.
# ---------------------------------------------------------------------------


def make_user(conn: Connection, **overrides) -> uuid.UUID:
    row_id = overrides.get("id", uuid.uuid4())
    conn.execute(
        text(
            "INSERT INTO users (id, authz_version, status) "
            "VALUES (:id, :authz_version, :status)"
        ),
        {
            "id": row_id,
            "authz_version": overrides.get("authz_version", 1),
            "status": overrides.get("status", "ACTIVE"),
        },
    )
    return row_id


def make_worker_profile(conn: Connection, user_id: uuid.UUID, **overrides) -> uuid.UUID:
    row_id = overrides.get("id", uuid.uuid4())
    conn.execute(
        text(
            "INSERT INTO worker_profiles (id, user_id, hourly_rate, is_active) "
            "VALUES (:id, :user_id, :hourly_rate, :is_active)"
        ),
        {
            "id": row_id,
            "user_id": user_id,
            "hourly_rate": overrides.get("hourly_rate", 25.00),
            "is_active": overrides.get("is_active", True),
        },
    )
    return row_id


def make_organization(conn: Connection, **overrides) -> uuid.UUID:
    row_id = overrides.get("id", uuid.uuid4())
    conn.execute(text("INSERT INTO organizations (id) VALUES (:id)"), {"id": row_id})
    return row_id


def make_team(conn: Connection, organization_id: uuid.UUID, **overrides) -> uuid.UUID:
    row_id = overrides.get("id", uuid.uuid4())
    conn.execute(
        text("INSERT INTO teams (id, organization_id) VALUES (:id, :organization_id)"),
        {"id": row_id, "organization_id": organization_id},
    )
    return row_id


def make_project(conn: Connection, **overrides) -> uuid.UUID:
    row_id = overrides.get("id", uuid.uuid4())
    conn.execute(
        text(
            "INSERT INTO projects (id, latitude, longitude, city, state) "
            "VALUES (:id, :latitude, :longitude, :city, :state)"
        ),
        {
            "id": row_id,
            "latitude": overrides.get("latitude", 25.4358),
            "longitude": overrides.get("longitude", 78.5685),
            "city": overrides.get("city", "Jhansi"),
            "state": overrides.get("state", "Uttar Pradesh"),
        },
    )
    return row_id


def make_job_requirement(
    conn: Connection,
    project_id: uuid.UUID,
    workers_needed: int = 1,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    **overrides,
) -> uuid.UUID:
    row_id = overrides.get("id", uuid.uuid4())
    start_time = start_time or datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
    end_time = end_time or (start_time + timedelta(hours=8))
    conn.execute(
        text(
            "INSERT INTO job_requirements "
            "(id, project_id, workers_needed, start_time, end_time) "
            "VALUES (:id, :project_id, :workers_needed, :start_time, :end_time)"
        ),
        {
            "id": row_id,
            "project_id": project_id,
            "workers_needed": workers_needed,
            "start_time": start_time,
            "end_time": end_time,
        },
    )
    return row_id


def make_booking(
    conn: Connection,
    job_requirement_id: uuid.UUID,
    requester_id: uuid.UUID,
    status: str = "HELD",
    hold_expires_at: datetime | None = None,
    team_booking_group_id: uuid.UUID | None = None,
    **overrides,
) -> uuid.UUID:
    row_id = overrides.get("id", uuid.uuid4())
    if status == "HELD" and hold_expires_at is None:
        hold_expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    if status != "HELD":
        hold_expires_at = None
    conn.execute(
        text(
            "INSERT INTO bookings "
            "(id, job_requirement_id, requester_id, status, hold_expires_at, "
            " team_booking_group_id, updated_at) "
            "VALUES (:id, :job_requirement_id, :requester_id, :status, :hold_expires_at, "
            " :team_booking_group_id, now())"
        ),
        {
            "id": row_id,
            "job_requirement_id": job_requirement_id,
            "requester_id": requester_id,
            "status": status,
            "hold_expires_at": hold_expires_at,
            "team_booking_group_id": team_booking_group_id,
        },
    )
    return row_id


def make_team_booking_group(conn: Connection, booking_id: uuid.UUID, **overrides) -> uuid.UUID:
    row_id = overrides.get("id", uuid.uuid4())
    conn.execute(
        text("INSERT INTO team_booking_groups (id, booking_id) VALUES (:id, :booking_id)"),
        {"id": row_id, "booking_id": booking_id},
    )
    return row_id


def make_booking_item(
    conn: Connection,
    booking_id: uuid.UUID,
    resource_type: str,
    status: str,
    agreed_rate: str = "100.00",
    worker_profile_id: uuid.UUID | None = None,
    team_id: uuid.UUID | None = None,
    team_booking_group_id: uuid.UUID | None = None,
    **overrides,
) -> uuid.UUID:
    row_id = overrides.get("id", uuid.uuid4())
    conn.execute(
        text(
            "INSERT INTO booking_items "
            "(id, booking_id, resource_type, worker_profile_id, team_id, "
            " team_booking_group_id, status, agreed_rate) "
            "VALUES (:id, :booking_id, :resource_type, :worker_profile_id, :team_id, "
            " :team_booking_group_id, :status, :agreed_rate)"
        ),
        {
            "id": row_id,
            "booking_id": booking_id,
            "resource_type": resource_type,
            "worker_profile_id": worker_profile_id,
            "team_id": team_id,
            "team_booking_group_id": team_booking_group_id,
            "status": status,
            "agreed_rate": agreed_rate,
        },
    )
    return row_id


def make_worker_reservation(
    conn: Connection,
    worker_profile_id: uuid.UUID,
    booking_id: uuid.UUID,
    start_time: datetime,
    end_time: datetime,
    **overrides,
) -> uuid.UUID:
    row_id = overrides.get("id", uuid.uuid4())
    conn.execute(
        text(
            "INSERT INTO worker_reservations "
            "(id, worker_profile_id, booking_id, reservation_range) "
            "VALUES (:id, :worker_profile_id, :booking_id, "
            " tstzrange(:start_time, :end_time, '[)'))"
        ),
        {
            "id": row_id,
            "worker_profile_id": worker_profile_id,
            "booking_id": booking_id,
            "start_time": start_time,
            "end_time": end_time,
        },
    )
    return row_id


def make_full_individual_booking(
    conn: Connection,
    status: str = "HELD",
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> dict:
    """
    Builds one fully-shaped, valid individual booking (requester, worker,
    project, job_requirement, booking, one WORKER booking_item, one
    worker_reservation) and returns all the generated ids. Used as a
    starting point by tests that only want to break one specific
    invariant.
    """
    start_time = start_time or datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
    end_time = end_time or (start_time + timedelta(hours=8))

    requester_id = make_user(conn)
    worker_user_id = make_user(conn)
    worker_profile_id = make_worker_profile(conn, worker_user_id)
    project_id = make_project(conn)
    job_requirement_id = make_job_requirement(
        conn, project_id, workers_needed=1, start_time=start_time, end_time=end_time
    )
    booking_id = make_booking(conn, job_requirement_id, requester_id, status=status)
    booking_item_id = make_booking_item(
        conn,
        booking_id=booking_id,
        resource_type="WORKER",
        status=status,
        worker_profile_id=worker_profile_id,
    )
    reservation_id = make_worker_reservation(
        conn, worker_profile_id, booking_id, start_time, end_time
    )
    commit_deferred_checks(conn)

    return {
        "requester_id": requester_id,
        "worker_user_id": worker_user_id,
        "worker_profile_id": worker_profile_id,
        "project_id": project_id,
        "job_requirement_id": job_requirement_id,
        "booking_id": booking_id,
        "booking_item_id": booking_item_id,
        "reservation_id": reservation_id,
        "start_time": start_time,
        "end_time": end_time,
    }
