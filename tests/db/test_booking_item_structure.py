"""
booking_items WORKER/TEAM resource XOR CHECK constraint (spec D.9;
DB plan §23/§42).
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from tests.db.conftest import (
    make_booking,
    make_job_requirement,
    make_organization,
    make_project,
    make_team,
    make_team_booking_group,
    make_user,
    make_worker_profile,
)


def _base_booking(conn: Connection, workers_needed: int = 1):
    requester_id = make_user(conn)
    worker_user_id = make_user(conn)
    worker_id = make_worker_profile(conn, worker_user_id)
    project_id = make_project(conn)
    jr_id = make_job_requirement(conn, project_id, workers_needed=workers_needed)
    booking_id = make_booking(conn, jr_id, requester_id, status="HELD")
    return booking_id, worker_id


def test_worker_item_with_team_id_set_rejected(db_conn: Connection):
    booking_id, worker_id = _base_booking(db_conn)
    with pytest.raises(IntegrityError):
        db_conn.execute(
            text(
                "INSERT INTO booking_items "
                "(id, booking_id, resource_type, worker_profile_id, team_id, "
                " team_booking_group_id, status, agreed_rate) "
                "VALUES (gen_random_uuid(), :booking_id, 'WORKER', :worker_id, "
                " gen_random_uuid(), NULL, 'HELD', 100.00)"
            ),
            {"booking_id": booking_id, "worker_id": worker_id},
        )


def test_worker_item_without_worker_profile_id_rejected(db_conn: Connection):
    booking_id, _worker_id = _base_booking(db_conn)
    with pytest.raises(IntegrityError):
        db_conn.execute(
            text(
                "INSERT INTO booking_items "
                "(id, booking_id, resource_type, worker_profile_id, team_id, "
                " team_booking_group_id, status, agreed_rate) "
                "VALUES (gen_random_uuid(), :booking_id, 'WORKER', NULL, NULL, "
                " NULL, 'HELD', 100.00)"
            ),
            {"booking_id": booking_id},
        )


def test_team_item_with_worker_profile_id_set_rejected(db_conn: Connection):
    org_id = make_organization(db_conn)
    team_id = make_team(db_conn, org_id)
    booking_id, worker_id = _base_booking(db_conn, workers_needed=2)
    group_id = make_team_booking_group(db_conn, booking_id)
    with pytest.raises(IntegrityError):
        db_conn.execute(
            text(
                "INSERT INTO booking_items "
                "(id, booking_id, resource_type, worker_profile_id, team_id, "
                " team_booking_group_id, status, agreed_rate) "
                "VALUES (gen_random_uuid(), :booking_id, 'TEAM', :worker_id, :team_id, "
                " :group_id, 'HELD', 100.00)"
            ),
            {"booking_id": booking_id, "worker_id": worker_id, "team_id": team_id, "group_id": group_id},
        )


def test_team_item_without_group_id_rejected(db_conn: Connection):
    org_id = make_organization(db_conn)
    team_id = make_team(db_conn, org_id)
    booking_id, _worker_id = _base_booking(db_conn, workers_needed=2)
    with pytest.raises(IntegrityError):
        db_conn.execute(
            text(
                "INSERT INTO booking_items "
                "(id, booking_id, resource_type, worker_profile_id, team_id, "
                " team_booking_group_id, status, agreed_rate) "
                "VALUES (gen_random_uuid(), :booking_id, 'TEAM', NULL, :team_id, "
                " NULL, 'HELD', 100.00)"
            ),
            {"booking_id": booking_id, "team_id": team_id},
        )


def test_valid_worker_item_accepted(db_conn: Connection):
    booking_id, worker_id = _base_booking(db_conn)
    db_conn.execute(
        text(
            "INSERT INTO booking_items "
            "(id, booking_id, resource_type, worker_profile_id, team_id, "
            " team_booking_group_id, status, agreed_rate) "
            "VALUES (gen_random_uuid(), :booking_id, 'WORKER', :worker_id, NULL, "
            " NULL, 'HELD', 100.00)"
        ),
        {"booking_id": booking_id, "worker_id": worker_id},
    )  # no exception


def test_valid_team_item_accepted(db_conn: Connection):
    org_id = make_organization(db_conn)
    team_id = make_team(db_conn, org_id)
    booking_id, _worker_id = _base_booking(db_conn, workers_needed=2)
    group_id = make_team_booking_group(db_conn, booking_id)
    db_conn.execute(
        text(
            "INSERT INTO booking_items "
            "(id, booking_id, resource_type, worker_profile_id, team_id, "
            " team_booking_group_id, status, agreed_rate) "
            "VALUES (gen_random_uuid(), :booking_id, 'TEAM', NULL, :team_id, "
            " :group_id, 'HELD', 100.00)"
        ),
        {"booking_id": booking_id, "team_id": team_id, "group_id": group_id},
    )  # no exception
