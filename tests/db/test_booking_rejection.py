"""
Booking rejection integration tests.

Verifies that REQUESTED and HELD bookings can transition to REJECTED
and that HELD bookings clear hold_expires_at.
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


def test_requested_booking_can_be_rejected(db_conn: Connection):
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
        status="REQUESTED",
    )

    db_conn.execute(
        text(
            "UPDATE bookings "
            "SET status = 'REJECTED', hold_expires_at = NULL "
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

    assert row.status == "REJECTED"
    assert row.hold_expires_at is None


def test_held_booking_can_be_rejected_and_hold_expiry_is_cleared(
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
        status="HELD",
        hold_expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )

    db_conn.execute(
        text(
            "UPDATE bookings "
            "SET status = 'REJECTED', hold_expires_at = NULL "
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

    assert row.status == "REJECTED"
    assert row.hold_expires_at is None
