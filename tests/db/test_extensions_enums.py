"""
Verifies required PostgreSQL extensions and enum types exist with the
exact label sets defined in the spec (DB plan §41/§42 SCHEMA section).
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection


def test_btree_gist_extension_installed(db_conn: Connection):
    result = db_conn.execute(
        text("SELECT 1 FROM pg_extension WHERE extname = 'btree_gist'")
    ).scalar()
    assert result == 1


def _enum_labels(conn: Connection, type_name: str) -> set[str]:
    rows = conn.execute(
        text(
            "SELECT e.enumlabel FROM pg_enum e "
            "JOIN pg_type t ON t.oid = e.enumtypid "
            "WHERE t.typname = :type_name"
        ),
        {"type_name": type_name},
    ).fetchall()
    return {r[0] for r in rows}


def test_user_status_enum(db_conn: Connection):
    assert _enum_labels(db_conn, "user_status") == {"ACTIVE", "SUSPENDED", "DISABLED"}


def test_booking_status_enum(db_conn: Connection):
    assert _enum_labels(db_conn, "booking_status") == {
        "REQUESTED",
        "HELD",
        "CONFIRMED",
        "IN_PROGRESS",
        "COMPLETED",
        "REJECTED",
        "EXPIRED",
        "CANCELLED",
    }


def test_resource_type_enum(db_conn: Connection):
    assert _enum_labels(db_conn, "resource_type") == {"WORKER", "TEAM"}


def test_reviewee_type_enum(db_conn: Connection):
    assert _enum_labels(db_conn, "reviewee_type") == {"WORKER", "ORGANIZATION", "HOMEOWNER"}
