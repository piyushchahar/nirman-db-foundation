"""
Booking completion integration tests.

Verifies that an IN_PROGRESS booking can be confirmed complete after
the worker has marked it complete.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.engine import Connection

from tests.db.conftest import (
    make_booking,
    make_job_requirement,
    make_project,
    make_user,
)


def test_in_progress_booking_can_be_confirmed_complete(
    db_conn: Connection,
):
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
        status="IN_PROGRESS",
    )

    marked_at = datetime.now(timezone.utc)

    db_conn.execute(
        text(
            "UPDATE bookings "
            "SET marked_complete_by_worker_at = :marked_at "
            "WHERE id = :booking_id"
        ),
        {
            "booking_id": booking_id,
            "marked_at": marked_at,
        },
    )

    confirmed_at = datetime.now(timezone.utc)

    db_conn.execute(
        text(
            "UPDATE bookings "
            "SET confirmed_complete_by_homeowner_at = :confirmed_at, "
            "status = 'COMPLETED' "
            "WHERE id = :booking_id "
            "AND status = 'IN_PROGRESS' "
            "AND marked_complete_by_worker_at IS NOT NULL"
        ),
        {
            "booking_id": booking_id,
            "confirmed_at": confirmed_at,
        },
    )

    row = db_conn.execute(
        text(
            "SELECT status, marked_complete_by_worker_at, "
            "confirmed_complete_by_homeowner_at "
            "FROM bookings "
            "WHERE id = :booking_id"
        ),
        {"booking_id": booking_id},
    ).one()

    assert row.status == "COMPLETED"
    assert row.marked_complete_by_worker_at is not None
    assert row.confirmed_complete_by_homeowner_at is not None
