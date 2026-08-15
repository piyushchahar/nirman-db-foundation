"""
Historical FK safety (spec Part D.14; DB plan §36/§42): deleting a
referenced row must not silently cascade-destroy historical
booking/reservation data. None of the FKs in this schema use
ON DELETE CASCADE from an entity table toward historical booking data;
the default NO ACTION behavior means such a DELETE is rejected instead,
and soft-delete (deleted_at) is the intended lifecycle mechanism.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from tests.db.conftest import make_full_individual_booking


def test_deleting_referenced_worker_profile_is_blocked(db_conn: Connection):
    ctx = make_full_individual_booking(db_conn, status="HELD")
    with pytest.raises(IntegrityError):
        db_conn.execute(
            text("DELETE FROM worker_profiles WHERE id = :id"),
            {"id": ctx["worker_profile_id"]},
        )


def test_deleting_referenced_project_is_blocked(db_conn: Connection):
    ctx = make_full_individual_booking(db_conn, status="HELD")
    with pytest.raises(IntegrityError):
        db_conn.execute(
            text("DELETE FROM projects WHERE id = :id"), {"id": ctx["project_id"]}
        )


def test_deleting_referenced_booking_is_blocked(db_conn: Connection):
    ctx = make_full_individual_booking(db_conn, status="HELD")
    with pytest.raises(IntegrityError):
        db_conn.execute(
            text("DELETE FROM bookings WHERE id = :id"), {"id": ctx["booking_id"]}
        )


def test_soft_deleting_worker_profile_preserves_booking_items(db_conn: Connection):
    ctx = make_full_individual_booking(db_conn, status="HELD")
    db_conn.execute(
        text("UPDATE worker_profiles SET deleted_at = now() WHERE id = :id"),
        {"id": ctx["worker_profile_id"]},
    )
    remaining = db_conn.execute(
        text("SELECT count(*) FROM booking_items WHERE id = :id"),
        {"id": ctx["booking_item_id"]},
    ).scalar()
    assert remaining == 1, "Soft-deleting the worker must not remove historical booking_items"


def test_no_cascade_delete_rule_from_worker_profiles_to_booking_items(db_conn: Connection):
    """
    Directly inspects information_schema to confirm booking_items.worker_profile_id
    has NOT been declared ON DELETE CASCADE (DB plan §36: "Audit every FK.
    Do not blindly use ON DELETE CASCADE").
    """
    row = db_conn.execute(
        text(
            "SELECT rc.delete_rule "
            "FROM information_schema.referential_constraints rc "
            "JOIN information_schema.table_constraints tc "
            "  ON tc.constraint_name = rc.constraint_name "
            "WHERE tc.table_name = 'booking_items' "
            "  AND tc.constraint_type = 'FOREIGN KEY' "
            "  AND rc.constraint_name LIKE '%worker_profile_id%'"
        )
    ).fetchall()
    for r in row:
        assert r[0] != "CASCADE"
