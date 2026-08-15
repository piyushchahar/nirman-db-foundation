"""
job_requirements.workers_needed >= 1 and end_time > start_time CHECK
constraints (spec D.5; DB plan §16/§42).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from tests.db.conftest import make_project


def test_workers_needed_zero_rejected(db_conn: Connection):
    project_id = make_project(db_conn)
    start = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
    with pytest.raises(IntegrityError):
        db_conn.execute(
            text(
                "INSERT INTO job_requirements "
                "(id, project_id, workers_needed, start_time, end_time) "
                "VALUES (gen_random_uuid(), :project_id, 0, :start, :end)"
            ),
            {"project_id": project_id, "start": start, "end": start + timedelta(hours=1)},
        )


def test_workers_needed_negative_rejected(db_conn: Connection):
    project_id = make_project(db_conn)
    start = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
    with pytest.raises(IntegrityError):
        db_conn.execute(
            text(
                "INSERT INTO job_requirements "
                "(id, project_id, workers_needed, start_time, end_time) "
                "VALUES (gen_random_uuid(), :project_id, -1, :start, :end)"
            ),
            {"project_id": project_id, "start": start, "end": start + timedelta(hours=1)},
        )


def test_workers_needed_one_accepted(db_conn: Connection):
    project_id = make_project(db_conn)
    start = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
    db_conn.execute(
        text(
            "INSERT INTO job_requirements "
            "(id, project_id, workers_needed, start_time, end_time) "
            "VALUES (gen_random_uuid(), :project_id, 1, :start, :end)"
        ),
        {"project_id": project_id, "start": start, "end": start + timedelta(hours=1)},
    )  # no exception


def test_invalid_time_range_rejected(db_conn: Connection):
    project_id = make_project(db_conn)
    start = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
    with pytest.raises(IntegrityError):
        db_conn.execute(
            text(
                "INSERT INTO job_requirements "
                "(id, project_id, workers_needed, start_time, end_time) "
                "VALUES (gen_random_uuid(), :project_id, 1, :start, :end)"
            ),
            {"project_id": project_id, "start": start, "end": start - timedelta(hours=1)},
        )


def test_equal_start_end_rejected(db_conn: Connection):
    project_id = make_project(db_conn)
    start = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
    with pytest.raises(IntegrityError):
        db_conn.execute(
            text(
                "INSERT INTO job_requirements "
                "(id, project_id, workers_needed, start_time, end_time) "
                "VALUES (gen_random_uuid(), :project_id, 1, :start, :end)"
            ),
            {"project_id": project_id, "start": start, "end": start},
        )
