"""
Booking start integration tests.

Verifies that a CONFIRMED booking can transition to IN_PROGRESS
using a real PostgreSQL connection.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.engine import Connection

from tests.db.conftest import (
    make_booking,
    make_job_requirement,
    make_project,
    make_user,
)


def test_confirmed_booking_can_start(db_conn: Connection):
    requester_id = make_user(db_conn)
    project_id = make_project(db_conn)
    job_requirement_id = make_job_requirement(
        db_conn,
        project_id,
        workers_needed=1,
    )

    booking_id = make_booking(
        db_conn,
        job_requirement_id,
        requester_id,
        status="CONFIRMED",
    )

    db_conn.execute(
        text(
            "UPDATE bookings "
            "SET status = 'IN_PROGRESS', hold_expires_at = NULL "
            "WHERE id = :booking_id"
        ),
        {"booking_id": booking_id},
    )

    row = db_conn.execute(
        text(
            "SELECT status, hold_expires_at "
            "FROM bookings "
            "WHERE id = :booking_id"
        ),
        {"booking_id": booking_id},
    ).one()

    assert row.status == "IN_PROGRESS"
    assert row.hold_expires_at is None

