"""
booking_idempotency requester-scoped uniqueness (spec D.11; DB plan
§33/§42): UNIQUE(requester_id, idempotency_key), NOT a globally unique
idempotency_key.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from tests.db.conftest import (
    make_booking,
    make_job_requirement,
    make_project,
    make_user,
)


def _booking_for(conn: Connection, requester_id):
    project_id = make_project(conn)
    jr_id = make_job_requirement(conn, project_id, workers_needed=1)
    return make_booking(conn, jr_id, requester_id, status="HELD")


def _insert_idempotency(conn: Connection, requester_id, key: str, booking_id):
    conn.execute(
        text(
            "INSERT INTO booking_idempotency "
            "(id, requester_id, idempotency_key, request_hash, booking_id) "
            "VALUES (gen_random_uuid(), :requester_id, :key, 'hash-a', :booking_id)"
        ),
        {"requester_id": requester_id, "key": key, "booking_id": booking_id},
    )


def test_same_requester_same_key_twice_rejected(db_conn: Connection):
    requester_id = make_user(db_conn)
    booking_1 = _booking_for(db_conn, requester_id)
    booking_2 = _booking_for(db_conn, requester_id)

    _insert_idempotency(db_conn, requester_id, "key-123", booking_1)
    with pytest.raises(IntegrityError):
        _insert_idempotency(db_conn, requester_id, "key-123", booking_2)


def test_same_requester_different_key_accepted(db_conn: Connection):
    requester_id = make_user(db_conn)
    booking_1 = _booking_for(db_conn, requester_id)
    booking_2 = _booking_for(db_conn, requester_id)

    _insert_idempotency(db_conn, requester_id, "key-123", booking_1)
    _insert_idempotency(db_conn, requester_id, "key-456", booking_2)  # no exception


def test_different_requesters_same_key_accepted(db_conn: Connection):
    """
    DB plan §33: idempotency_key is NOT globally unique. Two different
    requesters using the identical key string must both succeed.
    """
    requester_a = make_user(db_conn)
    requester_b = make_user(db_conn)
    booking_a = _booking_for(db_conn, requester_a)
    booking_b = _booking_for(db_conn, requester_b)

    _insert_idempotency(db_conn, requester_a, "same-key", booking_a)
    _insert_idempotency(db_conn, requester_b, "same-key", booking_b)  # no exception
