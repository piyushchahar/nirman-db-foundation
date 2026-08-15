"""
availability_windows: NOT NULL worker_profile_id, CHECK end_time >
start_time, and confirmation that no is_available_now-style column, no
team_id, and no recurrence columns exist (spec D.4; DB plan §12/§17/§50).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from tests.db.conftest import make_user, make_worker_profile


def test_valid_window_accepted(db_conn: Connection):
    user_id = make_user(db_conn)
    worker_id = make_worker_profile(db_conn, user_id)
    start = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
    db_conn.execute(
        text(
            "INSERT INTO availability_windows (id, worker_profile_id, start_time, end_time) "
            "VALUES (gen_random_uuid(), :worker_id, :start, :end)"
        ),
        {"worker_id": worker_id, "start": start, "end": start + timedelta(hours=8)},
    )  # no exception


def test_invalid_range_rejected(db_conn: Connection):
    user_id = make_user(db_conn)
    worker_id = make_worker_profile(db_conn, user_id)
    start = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
    with pytest.raises(IntegrityError):
        db_conn.execute(
            text(
                "INSERT INTO availability_windows "
                "(id, worker_profile_id, start_time, end_time) "
                "VALUES (gen_random_uuid(), :worker_id, :start, :end)"
            ),
            {"worker_id": worker_id, "start": start, "end": start - timedelta(hours=1)},
        )


def test_null_worker_profile_id_rejected(db_conn: Connection):
    start = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
    with pytest.raises(IntegrityError):
        db_conn.execute(
            text(
                "INSERT INTO availability_windows "
                "(id, worker_profile_id, start_time, end_time) "
                "VALUES (gen_random_uuid(), NULL, :start, :end)"
            ),
            {"start": start, "end": start + timedelta(hours=1)},
        )


def test_no_forbidden_columns_on_worker_profiles(db_conn: Connection):
    columns = {
        c["name"] for c in inspect(db_conn).get_columns("worker_profiles")
    }
    forbidden = {
        "is_available_now",
        "is_available",
        "currently_available",
        "is_free",
        "current_availability",
        "available_now",
    }
    assert not (columns & forbidden), f"Forbidden availability columns present: {columns & forbidden}"


def test_no_forbidden_columns_on_availability_windows(db_conn: Connection):
    columns = {
        c["name"] for c in inspect(db_conn).get_columns("availability_windows")
    }
    forbidden = {"team_id", "is_recurring", "recurrence_rule"}
    assert not (columns & forbidden), f"Forbidden columns present: {columns & forbidden}"
