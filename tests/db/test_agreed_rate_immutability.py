"""
booking_items.agreed_rate is write-once: any UPDATE that changes it (or
sets it NULL) must fail (spec D.9, verbatim trigger; DB plan §27/§28/§44).
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError, InternalError

from tests.db.conftest import (
    make_booking,
    make_full_individual_booking,
    make_job_requirement,
    make_project,
    make_user,
    make_worker_profile,
)


def test_update_to_different_value_rejected(db_conn: Connection):
    ctx = make_full_individual_booking(db_conn, status="HELD")
    with pytest.raises(InternalError):
        db_conn.execute(
            text("UPDATE booking_items SET agreed_rate = 999.99 WHERE id = :id"),
            {"id": ctx["booking_item_id"]},
        )


def test_update_to_same_value_accepted(db_conn: Connection):
    ctx = make_full_individual_booking(db_conn, status="HELD")
    # agreed_rate is 100.00 by default in make_booking_item(); re-setting the
    # same value must not raise (IS DISTINCT FROM is false, trigger no-ops).
    db_conn.execute(
        text("UPDATE booking_items SET agreed_rate = 100.00 WHERE id = :id"),
        {"id": ctx["booking_item_id"]},
    )


def test_update_to_null_rejected(db_conn: Connection):
    ctx = make_full_individual_booking(db_conn, status="HELD")
    with pytest.raises(InternalError):
        db_conn.execute(
            text("UPDATE booking_items SET agreed_rate = NULL WHERE id = :id"),
            {"id": ctx["booking_item_id"]},
        )


def test_agreed_rate_not_null_on_insert(db_conn: Connection):
    requester_id = make_user(db_conn)
    project_id = make_project(db_conn)
    jr_id = make_job_requirement(db_conn, project_id, workers_needed=1)
    booking_id = make_booking(db_conn, jr_id, requester_id, status="HELD")
    worker_user_id = make_user(db_conn)
    worker_id = make_worker_profile(db_conn, worker_user_id)

    with pytest.raises(IntegrityError):
        db_conn.execute(
            text(
                "INSERT INTO booking_items "
                "(id, booking_id, resource_type, worker_profile_id, team_id, "
                " team_booking_group_id, status, agreed_rate) "
                "VALUES (gen_random_uuid(), :booking_id, 'WORKER', :worker_id, NULL, "
                " NULL, 'HELD', NULL)"
            ),
            {"booking_id": booking_id, "worker_id": worker_id},
        )
