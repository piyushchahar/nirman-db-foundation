"""
Transactional rollback test (spec Part D; DB plan §43): a transaction
that creates booking + booking_items + worker_reservations and then
fails must leave NONE of those rows behind. Verified against a REAL
PostgreSQL commit/rollback cycle using a dedicated connection (not the
`db_conn` fixture, since that fixture's own teardown rollback would make
this test trivially true regardless of whether the code under test
behaves correctly).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from tests.db.conftest import (
    make_booking,
    make_booking_item,
    make_job_requirement,
    make_project,
    make_user,
    make_worker_profile,
    make_worker_reservation,
)


def test_failed_transaction_leaves_no_partial_state(migrated_engine: Engine):
    conn = migrated_engine.connect()
    trans = conn.begin()

    requester_id = make_user(conn)
    worker_user_id = make_user(conn)
    worker_id = make_worker_profile(conn, worker_user_id)
    project_id = make_project(conn)
    start = datetime(2026, 9, 3, 9, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=8)
    jr_id = make_job_requirement(
        conn, project_id, workers_needed=1, start_time=start, end_time=end
    )
    booking_id = make_booking(conn, jr_id, requester_id, status="HELD")
    booking_item_id = make_booking_item(
        conn,
        booking_id=booking_id,
        resource_type="WORKER",
        status="HELD",
        worker_profile_id=worker_id,
    )
    reservation_id = make_worker_reservation(conn, worker_id, booking_id, start, end)

    # Intentionally trigger a failure: try to give this booking a second
    # WORKER booking_item with a duplicate id (primary key violation),
    # forcing the whole transaction to abort.
    with pytest.raises(IntegrityError):
        conn.execute(
            text(
                "INSERT INTO booking_items "
                "(id, booking_id, resource_type, worker_profile_id, team_id, "
                " team_booking_group_id, status, agreed_rate) "
                "VALUES (:id, :booking_id, 'WORKER', :worker_id, NULL, NULL, "
                " 'HELD', 100.00)"
            ),
            {"id": booking_item_id, "booking_id": booking_id, "worker_id": worker_id},
        )

    trans.rollback()
    conn.close()

    # Verify from a completely fresh connection that nothing persisted.
    verify_conn = migrated_engine.connect()
    try:
        booking_count = verify_conn.execute(
            text("SELECT count(*) FROM bookings WHERE id = :id"), {"id": booking_id}
        ).scalar()
        item_count = verify_conn.execute(
            text("SELECT count(*) FROM booking_items WHERE booking_id = :id"),
            {"id": booking_id},
        ).scalar()
        reservation_count = verify_conn.execute(
            text("SELECT count(*) FROM worker_reservations WHERE booking_id = :id"),
            {"id": booking_id},
        ).scalar()
        assert booking_count == 0
        assert item_count == 0
        assert reservation_count == 0
    finally:
        verify_conn.close()
