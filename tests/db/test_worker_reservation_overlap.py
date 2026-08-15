"""
GiST exclusion constraint on worker_reservations (spec D.10; DB plan
§30/§31/§42): PostgreSQL is the sole correctness authority for preventing
overlapping reservations for the same worker. All six scenarios from
DB plan §31 are covered.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from tests.db.conftest import (
    make_booking,
    make_job_requirement,
    make_project,
    make_user,
    make_worker_profile,
    make_worker_reservation,
)


def _hm(hour: int) -> datetime:
    return datetime(2026, 9, 1, hour, 0, tzinfo=timezone.utc)


def _booking_for_worker(conn: Connection) -> tuple:
    requester_id = make_user(conn)
    worker_user_id = make_user(conn)
    worker_id = make_worker_profile(conn, worker_user_id)
    project_id = make_project(conn)
    jr_id = make_job_requirement(conn, project_id, workers_needed=1)
    booking_id = make_booking(conn, jr_id, requester_id, status="HELD")
    return worker_id, booking_id


def _new_booking(conn: Connection, requester_id) -> tuple:
    project_id = make_project(conn)
    jr_id = make_job_requirement(conn, project_id, workers_needed=1)
    return make_booking(conn, jr_id, requester_id, status="HELD")


def test_overlapping_ranges_same_worker_rejected(db_conn: Connection):
    worker_id, booking_a = _booking_for_worker(db_conn)
    requester_id = make_user(db_conn)
    booking_b = _new_booking(db_conn, requester_id)

    make_worker_reservation(db_conn, worker_id, booking_a, _hm(9), _hm(17))
    with pytest.raises(IntegrityError):
        make_worker_reservation(db_conn, worker_id, booking_b, _hm(13), _hm(18))


def test_adjacent_ranges_same_worker_accepted(db_conn: Connection):
    worker_id, booking_a = _booking_for_worker(db_conn)
    requester_id = make_user(db_conn)
    booking_b = _new_booking(db_conn, requester_id)

    make_worker_reservation(db_conn, worker_id, booking_a, _hm(9), _hm(17))
    # [17:00, 20:00) does not overlap [9:00, 17:00) under [start, end) semantics.
    make_worker_reservation(db_conn, worker_id, booking_b, _hm(17), _hm(20))  # no exception


def test_earlier_adjacent_range_accepted(db_conn: Connection):
    worker_id, booking_a = _booking_for_worker(db_conn)
    requester_id = make_user(db_conn)
    booking_b = _new_booking(db_conn, requester_id)

    make_worker_reservation(db_conn, worker_id, booking_a, _hm(9), _hm(17))
    make_worker_reservation(db_conn, worker_id, booking_b, _hm(8), _hm(9))  # no exception


def test_different_workers_overlapping_accepted(db_conn: Connection):
    worker_a, booking_a = _booking_for_worker(db_conn)
    worker_b, booking_b = _booking_for_worker(db_conn)

    make_worker_reservation(db_conn, worker_a, booking_a, _hm(9), _hm(17))
    make_worker_reservation(db_conn, worker_b, booking_b, _hm(9), _hm(17))  # no exception


def test_identical_range_same_worker_rejected(db_conn: Connection):
    worker_id, booking_a = _booking_for_worker(db_conn)
    requester_id = make_user(db_conn)
    booking_b = _new_booking(db_conn, requester_id)

    make_worker_reservation(db_conn, worker_id, booking_a, _hm(9), _hm(17))
    with pytest.raises(IntegrityError):
        make_worker_reservation(db_conn, worker_id, booking_b, _hm(9), _hm(17))


def test_contained_range_same_worker_rejected(db_conn: Connection):
    worker_id, booking_a = _booking_for_worker(db_conn)
    requester_id = make_user(db_conn)
    booking_b = _new_booking(db_conn, requester_id)

    make_worker_reservation(db_conn, worker_id, booking_a, _hm(9), _hm(17))
    with pytest.raises(IntegrityError):
        make_worker_reservation(db_conn, worker_id, booking_b, _hm(11), _hm(13))


def test_partial_overlap_same_worker_rejected(db_conn: Connection):
    worker_id, booking_a = _booking_for_worker(db_conn)
    requester_id = make_user(db_conn)
    booking_b = _new_booking(db_conn, requester_id)

    make_worker_reservation(db_conn, worker_id, booking_a, _hm(9), _hm(17))
    with pytest.raises(IntegrityError):
        make_worker_reservation(db_conn, worker_id, booking_b, _hm(16), _hm(20))


def test_empty_range_rejected(db_conn: Connection):
    worker_id, booking_a = _booking_for_worker(db_conn)
    with pytest.raises(IntegrityError):
        db_conn.execute(
            text(
                "INSERT INTO worker_reservations "
                "(id, worker_profile_id, booking_id, reservation_range) "
                "VALUES (gen_random_uuid(), :worker_id, :booking_id, "
                " tstzrange(:t, :t, '[)'))"
            ),
            {"worker_id": worker_id, "booking_id": booking_a, "t": _hm(9)},
        )
