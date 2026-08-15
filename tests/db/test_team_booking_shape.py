"""
Deferred booking-shape trigger, team booking cases (spec D.9b; DB plan
§20/§24/§26/§42): exactly one TEAM booking_item, exactly workers_needed
WORKER booking_items, matching team_booking_group_id, exactly
workers_needed worker_reservations.

Also covers (Correction 3B, static audit): team_booking_groups.booking_id
UNIQUE constraint (spec D.9a) — a team_booking_groups row can never be
reused by more than one booking. This is a plain, immediate UNIQUE
constraint, unrelated to the deferred shape trigger tested elsewhere in
this file; placed here because it's the closest existing file already
scaffolding team_booking_groups rows.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError, InternalError

from tests.db.conftest import (
    commit_deferred_checks,
    make_booking,
    make_booking_item,
    make_job_requirement,
    make_organization,
    make_project,
    make_team,
    make_team_booking_group,
    make_user,
    make_worker_profile,
    make_worker_reservation,
)


def _team_booking_scaffold(conn: Connection, workers_needed: int = 2):
    requester_id = make_user(conn)
    org_id = make_organization(conn)
    team_id = make_team(conn, org_id)
    project_id = make_project(conn)
    start = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=8)
    jr_id = make_job_requirement(
        conn, project_id, workers_needed=workers_needed, start_time=start, end_time=end
    )
    booking_id = make_booking(conn, jr_id, requester_id, status="HELD")
    group_id = make_team_booking_group(conn, booking_id)
    # Attach the group to the booking (bookings.team_booking_group_id).
    conn.execute(
        text("UPDATE bookings SET team_booking_group_id = :gid WHERE id = :bid"),
        {"gid": group_id, "bid": booking_id},
    )
    worker_ids = []
    for _ in range(workers_needed):
        user_id = make_user(conn)
        worker_ids.append(make_worker_profile(conn, user_id))
    return {
        "booking_id": booking_id,
        "team_id": team_id,
        "group_id": group_id,
        "worker_ids": worker_ids,
        "workers_needed": workers_needed,
        "start": start,
        "end": end,
    }


def _add_team_item(conn: Connection, ctx: dict, status: str = "HELD"):
    return make_booking_item(
        conn,
        booking_id=ctx["booking_id"],
        resource_type="TEAM",
        status=status,
        team_id=ctx["team_id"],
        team_booking_group_id=ctx["group_id"],
    )


def _add_worker_items_and_reservations(conn: Connection, ctx: dict, status: str, count: int):
    for i in range(count):
        make_booking_item(
            conn,
            booking_id=ctx["booking_id"],
            resource_type="WORKER",
            status=status,
            worker_profile_id=ctx["worker_ids"][i],
        )
        make_worker_reservation(
            conn, ctx["worker_ids"][i], ctx["booking_id"], ctx["start"], ctx["end"]
        )


def test_valid_team_booking_shape_accepted(db_conn: Connection):
    ctx = _team_booking_scaffold(db_conn, workers_needed=2)
    _add_team_item(db_conn, ctx)
    _add_worker_items_and_reservations(db_conn, ctx, "HELD", ctx["workers_needed"])
    commit_deferred_checks(db_conn)  # must not raise


def test_missing_worker_items_rejected(db_conn: Connection):
    ctx = _team_booking_scaffold(db_conn, workers_needed=2)
    _add_team_item(db_conn, ctx)
    _add_worker_items_and_reservations(db_conn, ctx, "HELD", 1)  # only 1 of 2
    with pytest.raises(InternalError):
        commit_deferred_checks(db_conn)


def test_extra_worker_item_rejected(db_conn: Connection):
    ctx = _team_booking_scaffold(db_conn, workers_needed=1)
    _add_team_item(db_conn, ctx)
    # workers_needed=1 but scaffold still only creates 1 worker profile;
    # add a second unrelated worker to exceed the required count.
    extra_user = make_user(db_conn)
    from tests.db.conftest import make_worker_profile

    extra_worker = make_worker_profile(db_conn, extra_user)
    _add_worker_items_and_reservations(db_conn, ctx, "HELD", 1)
    make_booking_item(
        db_conn,
        booking_id=ctx["booking_id"],
        resource_type="WORKER",
        status="HELD",
        worker_profile_id=extra_worker,
    )
    make_worker_reservation(db_conn, extra_worker, ctx["booking_id"], ctx["start"], ctx["end"])
    with pytest.raises(InternalError):
        commit_deferred_checks(db_conn)


def test_missing_reservation_rejected(db_conn: Connection):
    ctx = _team_booking_scaffold(db_conn, workers_needed=2)
    _add_team_item(db_conn, ctx)
    # Add booking_items for both workers but a reservation for only one.
    for i in range(2):
        make_booking_item(
            db_conn,
            booking_id=ctx["booking_id"],
            resource_type="WORKER",
            status="HELD",
            worker_profile_id=ctx["worker_ids"][i],
        )
    make_worker_reservation(
        db_conn, ctx["worker_ids"][0], ctx["booking_id"], ctx["start"], ctx["end"]
    )
    with pytest.raises(InternalError):
        commit_deferred_checks(db_conn)


def test_mismatched_team_booking_group_rejected(db_conn: Connection):
    ctx = _team_booking_scaffold(db_conn, workers_needed=1)
    other_group_id = make_team_booking_group(
        db_conn, make_booking(
            db_conn,
            make_job_requirement(db_conn, make_project(db_conn), workers_needed=1),
            make_user(db_conn),
            status="HELD",
        )
    )
    # TEAM item points at a *different* group than bookings.team_booking_group_id.
    make_booking_item(
        db_conn,
        booking_id=ctx["booking_id"],
        resource_type="TEAM",
        status="HELD",
        team_id=ctx["team_id"],
        team_booking_group_id=other_group_id,
    )
    _add_worker_items_and_reservations(db_conn, ctx, "HELD", 1)
    with pytest.raises(InternalError):
        commit_deferred_checks(db_conn)


def test_extra_team_item_rejected(db_conn: Connection):
    ctx = _team_booking_scaffold(db_conn, workers_needed=1)
    org_id = make_organization(db_conn)
    other_team_id = make_team(db_conn, org_id)
    _add_team_item(db_conn, ctx)
    make_booking_item(
        db_conn,
        booking_id=ctx["booking_id"],
        resource_type="TEAM",
        status="HELD",
        team_id=other_team_id,
        team_booking_group_id=ctx["group_id"],
    )
    _add_worker_items_and_reservations(db_conn, ctx, "HELD", 1)
    with pytest.raises(InternalError):
        commit_deferred_checks(db_conn)


def test_individual_booking_with_wrong_workers_needed_rejected(db_conn: Connection):
    # No TEAM item present (individual shape) but workers_needed = 2 on the
    # job_requirement -> must be rejected per spec D.9b.
    requester_id = make_user(db_conn)
    project_id = make_project(db_conn)
    start = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=8)
    jr_id = make_job_requirement(
        db_conn, project_id, workers_needed=2, start_time=start, end_time=end
    )
    booking_id = make_booking(db_conn, jr_id, requester_id, status="HELD")
    user_id = make_user(db_conn)
    from tests.db.conftest import make_worker_profile

    worker_id = make_worker_profile(db_conn, user_id)
    make_booking_item(
        db_conn,
        booking_id=booking_id,
        resource_type="WORKER",
        status="HELD",
        worker_profile_id=worker_id,
    )
    make_worker_reservation(db_conn, worker_id, booking_id, start, end)
    with pytest.raises(InternalError):
        commit_deferred_checks(db_conn)


def test_team_booking_group_booking_id_unique(db_conn: Connection):
    """
    spec D.9a: team_booking_groups.booking_id is UNIQUE — a group must
    never belong to more than one booking (DB plan §20: "A group must
    not belong to multiple bookings."). Two team_booking_groups rows
    referencing the same booking_id must fail at the database level, not
    merely via application-level validation.
    """
    requester_id = make_user(db_conn)
    project_id = make_project(db_conn)
    jr_id = make_job_requirement(db_conn, project_id, workers_needed=1)
    booking_id = make_booking(db_conn, jr_id, requester_id, status="HELD")

    make_team_booking_group(db_conn, booking_id)  # first row: succeeds

    with pytest.raises(IntegrityError):
        db_conn.execute(
            text(
                "INSERT INTO team_booking_groups (id, booking_id) "
                "VALUES (gen_random_uuid(), :booking_id)"
            ),
            {"booking_id": booking_id},
        )
