from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.services.booking_service import BookingService

from tests.db.conftest import (
    commit_deferred_checks,
    make_booking,
    make_job_requirement,
    make_project,
    make_user,
    make_worker_profile,
)


def test_assign_worker_persists_booking_item_and_reservation(db_conn):
    requester_id = make_user(db_conn)
    worker_user_id = make_user(db_conn)
    worker_profile_id = make_worker_profile(db_conn, worker_user_id)

    project_id = make_project(db_conn)

    start_time = datetime(
        2026,
        9,
        10,
        9,
        0,
        tzinfo=timezone.utc,
    )
    end_time = start_time + timedelta(hours=8)

    job_requirement_id = make_job_requirement(
        db_conn,
        project_id,
        workers_needed=1,
        start_time=start_time,
        end_time=end_time,
    )

    booking_id = make_booking(
        db_conn,
        job_requirement_id,
        requester_id,
        status="REQUESTED",
    )

    session = Session(bind=db_conn)

    try:
        booking = session.get(Booking, booking_id)

        service = BookingService(session)

        result = service.assign_worker(
            booking,
            worker_profile_id=worker_profile_id,
            agreed_rate="100.00",
        )

        assert result.id == booking_id

        commit_deferred_checks(db_conn)

        item = db_conn.execute(
            text(
                """
                SELECT
                    resource_type,
                    worker_profile_id,
                    status,
                    agreed_rate
                FROM booking_items
                WHERE booking_id = :booking_id
                """
            ),
            {"booking_id": booking_id},
        ).mappings().one()

        assert item["resource_type"] == "WORKER"
        assert item["worker_profile_id"] == worker_profile_id
        assert item["status"] == "REQUESTED"
        assert str(item["agreed_rate"]) == "100.00"

        reservation = db_conn.execute(
            text(
                """
                SELECT
                    worker_profile_id,
                    reservation_range
                FROM worker_reservations
                WHERE booking_id = :booking_id
                """
            ),
            {"booking_id": booking_id},
        ).mappings().one()

        assert reservation["worker_profile_id"] == worker_profile_id

        assert db_conn.execute(
            text(
                """
                SELECT count(*)
                FROM booking_items
                WHERE booking_id = :booking_id
                """
            ),
            {"booking_id": booking_id},
        ).scalar() == 1

        assert db_conn.execute(
            text(
                """
                SELECT count(*)
                FROM worker_reservations
                WHERE booking_id = :booking_id
                """
            ),
            {"booking_id": booking_id},
        ).scalar() == 1

    finally:
        session.close()
