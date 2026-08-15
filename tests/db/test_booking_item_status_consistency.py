"""
Deferred constraint trigger: every committed booking_items.status must
equal its parent bookings.status (spec D.8/D.9/D.9b; DB plan §25/§26/§42).

Deferred triggers only fire at commit (or when explicitly forced with
`SET CONSTRAINTS ALL IMMEDIATE`). `commit_deferred_checks()` is used here
to observe the trigger without needing a real COMMIT, keeping the test
rollback-isolated.

Also covers (Correction 3A, static audit): bookings.hold_expires_at <->
status CHECK constraint (spec D.7, verbatim:
"(status = 'HELD' AND hold_expires_at IS NOT NULL) OR
 (status <> 'HELD' AND hold_expires_at IS NULL)"). This is a DIFFERENT,
plain, immediate CHECK constraint on `bookings` — not part of the
deferred shape/status trigger tested above — placed in this module
because it is the closest existing file dealing with bookings-level
status/lifecycle invariants; the required test file list (DB plan §41)
has no file dedicated solely to bookings' own CHECK constraints.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError, InternalError

from tests.db.conftest import (
    commit_deferred_checks,
    make_full_individual_booking,
    make_job_requirement,
    make_project,
    make_user,
)


def test_matching_status_accepted(db_conn: Connection):
    # make_full_individual_booking() already calls commit_deferred_checks()
    # internally; getting here without an exception is the assertion.
    make_full_individual_booking(db_conn, status="HELD")


def test_mismatched_status_rejected(db_conn: Connection):
    ctx = make_full_individual_booking(db_conn, status="HELD")

    # Directly desynchronize booking_items.status from bookings.status,
    # simulating a bypass of BookingStateMachine.
    db_conn.execute(
        text("UPDATE booking_items SET status = 'CONFIRMED' WHERE id = :id"),
        {"id": ctx["booking_item_id"]},
    )

    with pytest.raises(InternalError):
        commit_deferred_checks(db_conn)


def test_bookings_status_change_without_item_update_rejected(db_conn: Connection):
    ctx = make_full_individual_booking(db_conn, status="HELD")

    # bookings.status changes but booking_items.status does not follow —
    # this must also be caught (trigger is attached to booking_items and
    # worker_reservations; a bookings-only status flip with no touching of
    # either table will not itself re-fire validation until one of those
    # tables changes, but any subsequent write to booking_items/
    # worker_reservations for this booking must catch the inconsistency).
    db_conn.execute(
    text(
        "UPDATE bookings "
        "SET status = 'CONFIRMED', hold_expires_at = NULL "
        "WHERE id = :id"
    ),
    {"id": ctx["booking_id"]},
)
    db_conn.execute(
        text(
            "UPDATE booking_items "
            "SET status = status "
            "WHERE id = :id"
        ),
        {"id": ctx["booking_item_id"]},
    )

    with pytest.raises(InternalError):
        commit_deferred_checks(db_conn)

def _job_requirement_for_new_booking(conn: Connection) -> uuid.UUID:
    project_id = make_project(conn)
    return make_job_requirement(conn, project_id, workers_needed=1)


def test_held_status_with_null_hold_expires_at_rejected(db_conn: Connection):
    """
    spec D.7 CHECK: status = 'HELD' requires hold_expires_at IS NOT NULL.
    Inserted directly via raw SQL (bypassing the make_booking() helper,
    which always fills in a valid hold_expires_at for HELD) so this test
    exercises the actual database CHECK constraint, not application-level
    defaulting.
    """
    requester_id = make_user(db_conn)
    jr_id = _job_requirement_for_new_booking(db_conn)
    with pytest.raises(IntegrityError):
        db_conn.execute(
            text(
                "INSERT INTO bookings "
                "(id, job_requirement_id, requester_id, status, hold_expires_at, "
                " team_booking_group_id, updated_at) "
                "VALUES (gen_random_uuid(), :jr_id, :requester_id, 'HELD', NULL, "
                " NULL, now())"
            ),
            {"jr_id": jr_id, "requester_id": requester_id},
        )


def test_non_held_status_with_non_null_hold_expires_at_rejected(db_conn: Connection):
    """
    Inverse of the above: status <> 'HELD' requires hold_expires_at IS NULL.
    A REQUESTED booking with a hold_expires_at set must be rejected.
    """
    requester_id = make_user(db_conn)
    jr_id = _job_requirement_for_new_booking(db_conn)
    future = datetime.now(timezone.utc) + timedelta(minutes=15)
    with pytest.raises(IntegrityError):
        db_conn.execute(
            text(
                "INSERT INTO bookings "
                "(id, job_requirement_id, requester_id, status, hold_expires_at, "
                " team_booking_group_id, updated_at) "
                "VALUES (gen_random_uuid(), :jr_id, :requester_id, 'REQUESTED', :expires, "
                " NULL, now())"
            ),
            {"jr_id": jr_id, "requester_id": requester_id, "expires": future},
        )


def test_held_status_with_hold_expires_at_accepted(db_conn: Connection):
    requester_id = make_user(db_conn)
    jr_id = _job_requirement_for_new_booking(db_conn)
    future = datetime.now(timezone.utc) + timedelta(minutes=15)
    db_conn.execute(
        text(
            "INSERT INTO bookings "
            "(id, job_requirement_id, requester_id, status, hold_expires_at, "
            " team_booking_group_id, updated_at) "
            "VALUES (gen_random_uuid(), :jr_id, :requester_id, 'HELD', :expires, "
            " NULL, now())"
        ),
        {"jr_id": jr_id, "requester_id": requester_id, "expires": future},
    )  # no exception


def test_non_held_status_with_null_hold_expires_at_accepted(db_conn: Connection):
    requester_id = make_user(db_conn)
    jr_id = _job_requirement_for_new_booking(db_conn)
    db_conn.execute(
        text(
            "INSERT INTO bookings "
            "(id, job_requirement_id, requester_id, status, hold_expires_at, "
            " team_booking_group_id, updated_at) "
            "VALUES (gen_random_uuid(), :jr_id, :requester_id, 'REQUESTED', NULL, "
            " NULL, now())"
        ),
        {"jr_id": jr_id, "requester_id": requester_id},
    )  # no exception
