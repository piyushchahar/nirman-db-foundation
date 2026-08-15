"""
outbox_events persistence, defaults, required fields, indexes (spec D.12;
DB plan §34/§37/§42). Persistence only — no dispatcher behavior tested
or implied.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError


def test_insert_with_required_fields_and_defaults(db_conn: Connection):
    event_id = uuid.uuid4()
    aggregate_id = uuid.uuid4()
    db_conn.execute(
        text(
            "INSERT INTO outbox_events "
            "(id, event_type, aggregate_type, aggregate_id, payload) "
            "VALUES (:id, 'BookingConfirmed', 'Booking', :aggregate_id, "
            " '{\"foo\": \"bar\"}'::jsonb)"
        ),
        {"id": event_id, "aggregate_id": aggregate_id},
    )
    row = db_conn.execute(
        text(
            "SELECT processed_at, attempts, last_error FROM outbox_events WHERE id = :id"
        ),
        {"id": event_id},
    ).one()
    assert row.processed_at is None
    assert row.attempts == 0
    assert row.last_error is None


def test_missing_event_type_rejected(db_conn: Connection):
    with pytest.raises(IntegrityError):
        db_conn.execute(
            text(
                "INSERT INTO outbox_events "
                "(id, event_type, aggregate_type, aggregate_id, payload) "
                "VALUES (gen_random_uuid(), NULL, 'Booking', gen_random_uuid(), '{}'::jsonb)"
            )
        )


def test_missing_payload_rejected(db_conn: Connection):
    with pytest.raises(IntegrityError):
        db_conn.execute(
            text(
                "INSERT INTO outbox_events "
                "(id, event_type, aggregate_type, aggregate_id, payload) "
                "VALUES (gen_random_uuid(), 'X', 'Booking', gen_random_uuid(), NULL)"
            )
        )


def test_required_dispatcher_indexes_exist(db_conn: Connection):
    index_names = {ix["name"] for ix in inspect(db_conn).get_indexes("outbox_events")}
    assert "ix_outbox_pending" in index_names
    assert "ix_outbox_aggregate" in index_names
